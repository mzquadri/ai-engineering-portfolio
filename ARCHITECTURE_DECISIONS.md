# Architecture decisions

Nine decisions that shaped the Legal Knowledge Database, each with the context
that forced it, the reason, what it cost, what else was available, and what is
still wrong with it.

These are reconstructed from the repositories — code, ADRs, audit records, commit
messages and code comments — not from memory. Two of them (ADR-003 and ADR-004 in
`architecture`) exist as formal ADRs; the rest are decisions visible
in the implementation and its documentation.

---

## 1. Event-driven ingestion, with no REST trigger

**Context.** A law enters the corpus on first ingest, on re-ingest after the
publisher changes it, and on replay after a parser change. Three situations, one
outcome.

**Decision.** Ingestion is reachable only by a matching Kafka event. The
preprocessor has no route that starts a parse; the loader has no route that
starts a projection. The only HTTP surfaces are verification, search, and
lifecycle steps that the health service orchestrates.

**Reason.** Making first ingest and recovery the same code path means the
recovery path is exercised every day rather than on the day it is needed. It also
makes the trigger auditable: what happened is a message someone can read.

**Trade-off.** Debugging a stuck ingest means reading consumer state rather than
re-issuing a request. There is no way to force a single law through
synchronously, which is occasionally what you want.

**Alternative considered.** A REST endpoint per service, with Kafka only for
notification. Rejected because it creates two paths into the same state, and the
less-used one rots.

**Current limitation.** No dead-letter topic. A permanently unprocessable law is
redelivered for ever and blocks its partition until a human intervenes.

---

## 2. Object storage for the source, separate from everything derived

**Context.** A claim about a law has to be checkable against what the publisher
actually served, months later, after the publisher has moved on.

**Decision.** Captured bytes go to MinIO under a fresh `{eventId}/{filename}`
prefix per request, hashed with SHA-256 before anything parses them. A second
bucket holds raw evidence with object lock enabled.

**Reason.** Evidence and derived knowledge have different lifecycles. Derived
knowledge is rebuildable and gets replaced on every re-ingest; evidence must
survive exactly as it arrived, and it must survive a law being withdrawn from the
corpus.

**Trade-off.** Storage grows monotonically, and the retention policy is
explicitly recorded as *not yet approved* — so held objects are retained by
default with no expiry.

**Alternative considered.** Storing the source as a BLOB in PostgreSQL. Rejected
because it couples evidence retention to database maintenance and makes an
append-only guarantee harder to state.

**Current limitation.** The capture bucket is immutable *by key*, not by policy.
No versioning, no content-addressing, no deduplication — identical bytes
submitted twice produce two objects, and an orphaned capture is possible because
MinIO is written before Kafka and nothing removes it if publication then fails.

---

## 3. Relational plus graph plus vector, rather than one store

**Context.** Three different questions get asked of the same corpus: what does
this provision say, what is semantically similar to this question, and what does
this provision cite.

**Decision.** PostgreSQL holds canonical state; Qdrant holds dense and sparse
vectors; Neo4j holds the provision reference graph; MinIO holds the source bytes.

**Reason.** Each store is present because the others cannot do its job, and the
limitation is the justification:

| Store | Cannot |
|---|---|
| PostgreSQL | search by meaning |
| Qdrant | follow a citation chain; enforce referential integrity |
| Neo4j | search by meaning |
| MinIO | be queried at all |

The graph specifically: German and EU provisions cite each other across statutes,
and a compliance answer often needs the cited provision as well as the matched
one. A vector hit finds the match; it does not find what the match points at.

**Trade-off.** Four operational dependencies, four failure modes, and a
consistency problem that would not exist with one store.

**Alternative considered.** PostgreSQL with `pgvector` and a recursive CTE for
reference traversal. Genuinely viable for a corpus of this size, and it would
have removed the consistency problem entirely. Rejected because hybrid dense +
sparse retrieval with server-side fusion was a first-class requirement and Qdrant
does it in one round trip, and because the graph queries were expected to grow
past what a CTE reads well.

**Current limitation.** Vehicle for drift. Mitigated by decision 4, not
eliminated.

---

## 4. Derive identity instead of coordinating writes

**Context.** Two derived stores must agree with a canonical one, and Kafka can
redeliver any message at any time.

**Decision.** Every derived identifier is a pure function of PostgreSQL content —
`uuid5(namespace, chunk_id)` for a Qdrant point, `MERGE` by id for a graph
section, `MERGE` by code for a law node. The loader reads the law through one
`REPEATABLE READ READ ONLY` snapshot and fences each store's convergence on an
exact count before publishing completion.

**Reason.** It makes redelivery a non-event. Re-running a delivery converges to
the same state instead of duplicating it, which removes the need for a
distributed transaction across three heterogeneous stores.

**Trade-off.** A real window exists between the canonical commit and the
projection fences, during which PostgreSQL holds the new generation and the
derived stores hold the old one. Reconciliation reports that as
`DRIFT_DETECTED` if it samples inside it.

**Alternative considered.** A two-phase commit or an outbox with a saga. Rejected
because the derived stores are rebuildable from the canonical one, so coordinated
commit buys a guarantee the corpus does not need — at the cost of a failure mode
in the coordinator.

**Current limitation.** The window is accepted, not eliminated. Nothing serves a
partial law, but a reconciliation sweep timed inside it reports drift that is
about to resolve itself.

---

## 5. One writer per store, enforced by deletion

**Context.** When a row is wrong, "which service wrote it?" has to have one
answer.

**Decision.** The preprocessor is the sole writer of canonical PostgreSQL and the
archive mirror. The loader is the sole writer of Qdrant and Neo4j. The health
service owns only its own currency, snapshot and audit tables. The dashboard
writes nothing, anywhere, and ships with no database, queue or object-store
client.

**Reason.** It is the property that makes every other guarantee provable. A gate
that measures a store can trust that one service produced what it is measuring.

**Trade-off.** Some operations span services and need orchestration rather than a
single transaction — withdrawal is the clearest case, and it needed a dedicated
sequencer with five machine-readable outcomes.

**Alternative considered.** Letting whichever service holds the request write
whichever store it needs. That is what an earlier version of the loader did, and
it could never have worked: `currency_observations` references `laws` with
`ON DELETE RESTRICT` and is append-only, so the canonical delete was refused
every time — *after* Qdrant and Neo4j had already been cleared and committed. The
resolution was to delete the code path, not to relax the constraint.

**Current limitation.** One flag-gated `purge_postgres` path survives in the
loader behind `LIFECYCLE_ACTIONS_ENABLED`. Nothing calls it, and it is recorded
as lifecycle debt rather than used as precedent for a second canonical writer.

---

## 6. Separate source evidence from derived knowledge, in the schema

**Context.** A verification gate that reads the same rows the pipeline wrote is
checking the pipeline against itself.

**Decision.** Four separate concerns in one database: canonical legal state;
source evidence (append-only); assurance and provenance; and currency. The
structural oracle builds its inventory from the source markup with the standard
library and `defusedxml`, importing no parser code. The archive-mirror row is
written last, after upload, read-back, hash and size check, because that row is
the raw-integrity gate's evidence.

**Reason.** The denominator must not come from the thing being measured.

**Trade-off.** Two implementations of "what does this XML contain" have to be
maintained, and they will occasionally disagree for reasons that are not defects.

**Alternative considered.** Trusting the parser and checking only internal
consistency. Rejected because it cannot detect a systematic misreading — which is
exactly the failure the structural gates found.

**Current limitation.** The oracle is GII-shaped. FORMEX oracle tools exist, but
the end-to-end certification contract does not, which is why no EU law is
certified.

---

## 7. Verify after ingestion, triggered by the ingestion itself

**Context.** A verification step that someone has to remember to run is a
verification step that eventually does not run.

**Decision.** The loader publishes `law.embedded` after both stores converge; the
preprocessor consumes that topic and runs every applicable gate. Verification
happens because ingestion completed, not because anyone asked.

**Reason.** It makes the measured state the normal state. It also gives the
dashboard a badge that is always about the current generation, since the verdict
is written by the same event that made the generation live.

**Trade-off.** Gates run on every ingest whether or not anything changed, which
costs time on a corpus-wide replay.

**Alternative considered.** Verifying inline, before publishing. Rejected because
the gates read Qdrant and Neo4j, which the preprocessor deliberately cannot
write — so the measurement has to happen after the writer has finished.

**Current limitation.** `CHECKER_VERSION` is hand-maintained and failed to move
once when a gate's semantics changed, so verdicts either side of that change are
indistinguishable. The code comment records it; the fix is to derive the version
from the gate implementations.

---

## 8. Reconciliation is read-only, and says when it cannot tell

**Context.** "Are the stores consistent right now?" is a different question from
"was this generation extracted faithfully?", and answering them with the same
mechanism would conflate them.

**Decision.** A reconciliation sweep reads PostgreSQL identity tuples, compares
what Qdrant and Neo4j hold, and reports exactly one of `LIVE_CONSISTENT`,
`DRIFT_DETECTED` or `CHECK_UNAVAILABLE`. It writes nothing and repairs nothing.

**Reason.** `CHECK_UNAVAILABLE` is the important part. A store that cannot be
reached is not the same as a store that disagrees, and collapsing the two
produces either false alarms or false confidence.

**Trade-off.** Drift is detected but not fixed. Someone has to decide.

**Alternative considered.** Auto-repair on drift. Rejected for a legal corpus: an
automatic self-heal that silently re-derives knowledge is, after the fact,
indistinguishable from one that silently corrupted it.

**Current limitation.** `LIVE_CONSISTENT` is the last sweep's answer, not a
standing guarantee, and the UI has to say so — which it does.

---

## 9. Lifecycle actions are operator decisions, double-gated

**Context.** Re-ingesting or withdrawing a law changes what the corpus serves.

**Decision.** Both require `DATA_SOURCE=live` **and**
`LIFECYCLE_ACTIONS_ENABLED=true`. Verification and reconciliation require
neither. Re-ingest does not purge first; withdrawal is sequenced canonical-first,
projections-second, and touches no evidence.

**Reason.** Measuring should be cheaper than changing, or it gets done less often.
Two independent flags mean a service configured for read-only inspection cannot
be talked into a mutation by a single misconfiguration.

**Trade-off.** Recovery needs a human, and the system cannot restore itself
overnight.

**Alternative considered.** A scheduled freshness sweep that re-ingests anything
stale. The polling half of that exists and writes evidence; the acting half was
deliberately not built.

**Current limitation.** Because nothing self-heals, a corpus left unattended will
drift from its publishers and report it accurately while doing nothing about it.

---

## Two formal ADRs in the architecture repository

| ADR | Decision |
|---|---|
| **ADR-003** | Container rebuild discipline — written after the local overlay images were found to be running code that predated completed work, while the repository, docs and tests all said otherwise. |
| **ADR-004** | Editable install with a boot-time check, superseding ADR-003 — so a drifted container fails at startup instead of serving a route table nobody expected. |

`ADR-001` (Neo4j mirrors PostgreSQL sections) and `ADR-002` (parser dispatch) are
also recorded there, by other authors.

---

## The decision underneath all nine

Every one of these trades convenience for falsifiability. A silent approximation
is cheaper at every individual step — tolerate a truncated embedding, ingest a law
whose structure you do not recognise, let a second service write a store, report
one green badge instead of four answers — and each of those cheap choices removes
the system's ability to tell you, later, that something is wrong.

The consistent answer was to refuse instead: block a law with unrecognised
structure, raise for a whole law rather than store a misleading vector, delete a
code path rather than document an exception, and keep four trust questions apart
even though one badge would look better.
