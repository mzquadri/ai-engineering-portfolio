# Interview walkthrough

Four lengths of the same story, then the questions an interviewer is likely to
ask and answers that are defensible against the code.

**One rule for using this:** everything below is either verified in the
repositories or explicitly framed as a design consideration. Where a question
has no implemented answer, the honest answer is written out — do not improvise a
better-sounding one.

Recommended diagram to have open: `assets/architecture/13-interview-system-overview.svg`
for the 5-minute version, `02-legal-knowledge-database.svg` if they want depth.

---

## 30 seconds

> I implemented four of the five services in the Legal Knowledge Database at
> BP-ITCS — the system that turns published German and EU law into
> machine-readable knowledge you can verify. Every store has exactly one writer,
> every stored generation records the digest of the rules that produced it, and
> the system refuses to certify a law it cannot independently reproduce from the
> publisher's own bytes. The interesting part was never the retrieval; it was
> provenance and giving operators control of the lifecycle.

---

## 2 minutes

> German and EU legislation is published as XML in two unrelated markup families,
> and it changes without telling you. Once you extract it into vectors and a
> graph for retrieval, you are holding three representations of the same law, any
> of which can drift from the source.
>
> The system is five services and I built four of them. An ingestion
> preprocessor parses a captured law
> against an inventory built independently from the source markup, extracts
> citations down to provision level, and owns canonical PostgreSQL. A loader
> embeds the chunks with BGE-M3 and converges Qdrant and Neo4j to one database
> snapshot, each fenced on an exact count. A health service is the control and
> verification boundary — it polls the publisher, triggers re-ingest, asks the
> preprocessor to run the gates, and reconciles the stores. And a dashboard is the
> operator interface, which deliberately decides nothing: every badge it shows was
> decided by a verification gate and read back through one backend.
>
> The rule that makes the whole thing verifiable is that exactly one service
> writes each store. I did not arrive at that by agreeing to it — I arrived at it
> by deleting the one code path that violated it.
>
> Fourteen gates measure what is stored against what the publisher served. Seven
> are required for the aggregate badge; all fourteen are recorded and displayed,
> because a measurement nobody can see is not a measurement. Twenty-five German
> laws are certified structurally complete. No EU law is, and I can tell you
> exactly why.

---

## 5 minutes — the architecture walkthrough

Follow the six moves in `13-interview-system-overview.svg`.

**1. Acquire.** The health service downloads the publisher's own file — a ZIP
from `gesetze-im-internet.de`, or a FORMEX bundle from CELLAR by content
negotiation. It hands the bytes to the entity producer, which hashes them with
SHA-256, writes them to MinIO under a fresh `eventId` prefix, and publishes one
event. The producer parses nothing: no ZIP, no XML, no section model. It moves
bytes and builds an envelope.

*Why it matters:* a claim about a law is only as good as the bytes it came from,
so the digest exists before anything interprets them.

**2. Structure.** The preprocessor filters the topic, looks the law up in a
registry that decides its canonical key, its parser and its source slug, and
dispatches to one of two parsers — GII-NORM for German law, FORMEX v4 for EU
acts. It extracts citations into provision-level identity tuples, chunks the
active sections, and commits everything in one transaction along with three
digests over the rules it used.

*Why it matters:* the extraction is measured against a second inventory of the
same markup, built on a deliberately different XML stack and importing no
parser code. The denominator cannot share a defect with the thing being
measured.

**3. Persist.** Canonical PostgreSQL. Roughly thirty-five tables across four
concerns: canonical legal state, source evidence, assurance and provenance, and
currency. The evidence tables are append-only. The archive-mirror row is written
last of all, after the object has been uploaded, read back, hashed and
size-checked, because that row is what the raw-integrity gate treats as evidence.

**4. Project.** The loader reads the law from one `REPEATABLE READ` snapshot,
embeds the active chunks with BGE-M3 — dense 1024 and sparse LEXICAL from one
pass — then converges Qdrant and Neo4j in a deliberate order, each fenced on an
exact count. It publishes completion only after both fences pass, and commits the
Kafka offset last.

*The detail I would offer here:* FlagEmbedding truncates silently past the
model's 8192-token window, so the loader counts tokens first and raises for the
whole law rather than storing a vector for text the model never fully saw. A
silently truncated embedding has the right dimensionality, sits in the right
collection, and is wrong.

**5. Verify.** Publishing `law.embedded` is what makes the preprocessor run the
gates — nobody asks it to. Fourteen gates cover structural fidelity, citation
correctness, cross-store equality and source currency. The prover proves itself
first: if any already-certified law no longer reproduces under today's rules, no
law gets a verdict, including the one being certified.

**6. Operate.** Four actions from one control plane: ingest or re-ingest, verify,
reconcile, withdraw. Only re-ingest and withdraw change the corpus, and both are
double-gated behind two independent flags. Re-ingest is zero-downtime: nothing is
purged first, so the old generation stays queryable and a failed ingest leaves it
untouched.

**Close on the shape.** Four stores exist because each does something the others
cannot: PostgreSQL cannot search by meaning, Qdrant cannot follow a citation
chain or enforce integrity, Neo4j cannot search by meaning, and MinIO cannot be
queried at all. They stay in step without a distributed transaction because every
derived identifier is a pure function of PostgreSQL content — so a Kafka
redelivery converges instead of duplicating.

---

## 10 minutes — the deep version

Everything above, plus these five.

### The gate that was wrong in a way counting could not reveal

ZPO passed `fidelity.source_substructure` cleanly and became the validation
specimen for the evidence gates. BGB then reported every structural path three
times.

The gate was pooling evidence documents. ZPO's active version happens to carry a
single evidence document; BGB carries three — one current and two superseded. The
defect was in the gate, not the data, and only running it against a second law
exposed it. A per-law exception was not an option: a rule that fires for one key
cannot be validated by any other law's evidence, so a special case makes the
corpus unprovable as a whole.

What changed afterwards was process: audit each law's own structure read-only
before re-ingesting it, and treat a count that matches another law's as a
coincidence to verify rather than a baseline.

### Import sorting invalidated the provenance of the entire corpus

`app/core/provenance.py` hashes the raw bytes of the parser, the reference
extractor and the registry, length-prefixed, into three digests recorded with
every generation.

A lint pass sorted the imports in those files. `parser_rule_sha256` moved from
`38eb6f833d0ab5ab` to `b36ddd87ed592417` with no behaviour change at all, and
every stored generation's recorded ruleset stopped matching the installed one.

I kept the digest byte-exact and disabled the import-sort rule for those three
files, with the reason recorded in `pyproject.toml`. The alternative — a digest
that tolerates "harmless" edits — cannot tell you whether a stored law still
reproduces, which is the only thing the mechanism is for.

The registry is part of that rule set too, and a code comment records why: adding
one long form moved eight citations in the AktG work.

### Why no EU law is certified

EU acts parse, ingest and are queryable. FORMEX gate implementations exist for
served text, substructure, citation completeness and reference extraction. What
does not exist is the end-to-end certification contract: the pre-flight detectors
are GII-shaped, so the prover stops at the capture digest and returns
`INCONCLUSIVE` for a FORMEX law.

That is a missing assurance contract, not a missing parser, and the distinction
is worth making precisely — because "we support EU law" and "we can prove our EU
extraction" are different claims.

### The endpoint that documented a measurement no code performed

The health service had four validation endpoints. In live mode the handler built
a job with `status="completed"` and the note "Live health check completed against
actual corpus stores", wrote that row, and returned it — without invoking any
gate. The gates live in the preprocessor, and at the time this service had no way
to call them.

I deleted the endpoints and wrote down in the API reference that the
documentation had asserted a measurement no implementation performed.
`POST /laws/{key}/verify` replaced them once the gates could actually be invoked.
A green result from a check that never ran is worse than no check.

### The running container was not the repository

Withdrawal was complete in the repository, the docs and the tests, and
un-exercisable against the running stack for every law. The local overlay images
are built once and not rebuilt when files change, so the preprocessor was missing
a module entirely and the loader still served the pre-rename route.

The misdirection cost more than the bug: an absent FastAPI route returns 404, and
the health service maps a 404 from the canonical step to `NOT_FOUND` — "no such
law". So the symptom reads as a data problem about the law you named. The fix to
the process was to verify the running image rather than the repo — diff the
container's files, or read the live route table from `/openapi.json` — and that
is now a written ADR plus a boot-time check.

---

## Likely questions, and answers that hold

### Why PostgreSQL **and** Neo4j **and** Qdrant **and** object storage?

Because each one cannot do what another does, and I can name the limitation:

- PostgreSQL holds canonical state with referential integrity, and cannot search
  by meaning.
- Qdrant does semantic and hybrid retrieval, and cannot follow a citation chain
  or enforce integrity.
- Neo4j traverses provision references, and cannot search by meaning.
- MinIO holds the publisher's bytes and their digests, and cannot be queried at
  all.

The reason a graph is there rather than a join table is specific: German and EU
provisions cite each other across statutes, and a compliance answer often needs
the cited provision as well as the matched one. A vector hit finds the match; it
does not find what the match points at.

### How do you keep four stores synchronised?

I do not synchronise them. I derive them, and I make every derived identifier a
pure function of the canonical content:

- a Qdrant point id is `uuid5(namespace, chunk_id)`;
- a graph section node is `MERGE`-d by id;
- a law node is `MERGE`-d by code.

So re-running any delivery converges to the same state rather than duplicating
it. Then each store's convergence is fenced on an exact count before completion
is published, and PostgreSQL is read through a single `REPEATABLE READ` snapshot
so the whole projection is built from one consistent view.

There is no distributed transaction, and that is deliberate: the derived stores
are rebuildable from the canonical one, so the cost of a coordinated commit buys
something the corpus does not need.

### What happens when ingestion partially fails?

It depends where, and the repository enumerates the cases rather than
generalising:

- Validation or size failure: nothing written, nothing published.
- Download or mandatory upload failure: 502, nothing published.
- Best-effort upload failure on a small uploaded capture: tolerated — publication
  continues with the inline copy and the event simply has no MinIO URL.
- Kafka ack timeout: 503, and the send **may** already have reached the broker. A
  retry mints a new `eventId`, so the same bytes land under a second prefix.
  There is no transaction across MinIO and Kafka, and no compensation.
- Qdrant converged, Neo4j failed: no completion event, the offset stays
  uncommitted, the consume loop ends. Redelivery re-runs both stores from a fresh
  snapshot.
- Crash between publish and commit: both stores are already converged; the event
  may be published twice, and a unique index on `capture_id` absorbs it.

And the honest part: there is no dead-letter topic, no bounded retry and no
automatic repair on the legal pipeline. A permanently unprocessable law is
redelivered for ever and blocks its partition until a human intervenes.

### What does re-ingestion actually mean?

A new capture of the same law, producing a new generation, with no downtime.

It does **not** purge first. Each store's own write path replaces the law
safely — PostgreSQL in one transaction, Qdrant upsert-then-delete-stale, Neo4j
merge-by-id — so the old generation answers queries throughout, and a failed
ingest leaves it untouched.

There is one window worth naming: between the canonical commit and the projection
fences, PostgreSQL holds the new generation while the derived stores still hold
the old one. Reconciliation will report that as `DRIFT_DETECTED` if it samples
inside it. It is short, it is accepted rather than hidden, and nothing serves a
partial law.

The operational rule that costs the most to learn: the identity differential
against the previous generation must be computed and written down **before** the
replay, because a replay deletes the old generation's section and reference rows
and the differential cannot be recomputed afterwards.

### How do you establish document provenance?

Four layers, each independently checkable:

1. **Bytes.** SHA-256 over the captured file at capture time, carried on the
   event and stored.
2. **Storage.** A fresh `eventId` prefix per capture, so a re-ingest never
   overwrites an earlier one; a separate evidence bucket with object lock, whose
   hold release is a documented compliance procedure with separation of duties.
3. **Rules.** Three digests over the parser, the reference extractor and the
   registry, recorded per generation. A byte change is a rule change.
4. **Fetch.** A publisher capture record, so `provenance.publisher_capture` can
   ask whether this version's archive is bound to a described fetch.

And the limitation, because it is in the diagram: the capture bucket is immutable
*by key*, not by policy. No versioning, no content-addressing, no deduplication.
Identical bytes submitted twice produce two objects.

### How is stale knowledge detected?

The health service polls the publisher and writes a `currency_observations` row
bound to a capture id. The preprocessor's `currency.source_state` gate reads that
evidence and judges it — it never fetches anything itself.

That separation is the point: the observer records what the publisher served, the
judge decides what it means, and neither can quietly do the other's job. The
outcome surfaces as `SOURCE_CHANGED_REINGEST_REQUIRED`, and the dashboard keeps
it as its own axis rather than folding it into the verification badge — because a
law can be structurally perfect and out of date.

### Why Kafka here at all?

Three reasons, in order of how much they mattered:

1. **The event is the trigger.** Law ingestion has no REST entry point. Replay,
   re-ingest and first ingest are the same code path, which means the recovery
   path is the one that gets exercised daily.
2. **Partitioning by identity.** The key is `law_key`, so one law maps to one
   partition and two generations of the same law can never be processed
   concurrently. That is a correctness property, not a throughput one.
3. **Completion as a published fact.** `law.embedded` closes three loops at once:
   it triggers verification, records a currency observation, and advances the
   dashboard's progress display. None of those three had to know about the
   others.

What Kafka is *not* doing here is buffering high throughput. The corpus is fifty
laws.

### How does OCR fallback work?

In the current document extractor, it does not: conversion is delegated to
Docling Serve with `do_ocr: "false"`.

It existed in the version I built before that. Extraction detected the Unicode
replacement character in the output and routed to an OCR path, because a PDF
extracted as text can silently return `U+FFFD` where the font mapping failed —
which looks like successful extraction to every downstream check. That detection
is the part worth keeping: it converts a silent corruption into a routable
failure.

PaddleOCR and DeepSeek-OCR appear in no dependency, configuration or source file
in this workspace, so I would not claim experience with either here.

### How do you prevent hallucinated legal answers?

Mostly upstream of the model, and I would be precise about the split:

**What ships.** Retrieval returns chunks whose payload carries the law key and
section number, so a citation is data travelling with the text rather than
something the model produced. The corpus itself is gated — structural fidelity,
citation completeness, cross-store equality and currency all measured before
anything is served. And the operator UI never merges four trust answers into one
green badge, so a stale or drifted law is visible as such.

**What does not ship.** Answer-level citation validation — regex-extracting the
sections an answer cites and checking each against the corpus — is designed and
not implemented. It costs no model call, and it targets the specific failure that
makes a legal assistant dangerous: a confident citation of a provision that does
not exist. I would frame it as the next thing I would build, not as something I
built.

### What did *you* personally implement?

Four of the Legal Knowledge Database's five services, by commit share and by
design authorship: the ingestion preprocessor (466 of 498 commits), the dashboard
(144 of 167), the health service (123 of 148) and the loader (77 of 94). The
fifth, the entity producer, I extended — it existed before legal ingestion did.

Named things inside them: the fourteen gates, the independent structural oracle,
the prover, the ruleset provenance digests, the derived identity model, the count
fences, the withdrawal orchestrator, the completion consumer, cross-store
reconciliation, the hybrid retrieval path, both XML parsers, and the TrustPanel's
four-axis model.

Extended, not built: the entity producer, where I added EU/CELLAR ingestion via
the Claim-Check pattern and made Kafka publication broker-confirmed before HTTP
success; the document extractor, where I added the dual LLM-plus-regex extraction
service and the mojibake detection; the indexing service, which I originated and
someone else continued; the shared `ai-utils` library; and the prediction service,
where I added Grad-CAM++ and a calibrated severity system.

Not mine: the Java entity platform, the RAG service (zero commits), the Glaux UI
(five of two hundred and forty-three), the legal chatbot, and every third-party
store.

### What would you redesign today?

Six things, and I would lead with the first:

1. **Add a dead-letter path to the legal pipeline.** Today one unprocessable law
   blocks a partition indefinitely. The document pipeline already has a DLQ; the
   legal one does not, and that asymmetry has no justification.
2. **Derive the checker version from the gate implementations.** It is
   hand-maintained and it failed to move once when a gate's semantics changed, so
   verdicts either side of that change are indistinguishable. The code comment
   says so.
3. **Generate the gate list once.** Three hand-maintained copies exist
   downstream, and that is the direct cause of the documentation-versus-code
   drift I found while auditing my own repositories for this portfolio.
4. **Content-address the captures.** Immutable by key is weaker than immutable by
   policy, and it permits both duplicate captures and orphaned objects.
5. **Build the FORMEX assurance contract**, so EU acts can be certified rather
   than merely ingested.
6. **Re-own canonical deletion.** A flag-gated purge path in the loader still
   contradicts the single-writer rule. It is recorded as debt, deliberately, and
   it should be resolved by moving the responsibility rather than by softening
   the rule.

### Is this in production?

No, and I would not let that be ambiguous. The stack runs under Docker Compose
with CI-built images, in a lab environment, against the real published corpus.
There is no Kubernetes manifest and no cloud infrastructure in any of the
repositories. The design is production-oriented — single-writer ownership,
idempotent consumption, evidence retention, double-gated lifecycle actions — but
"production-oriented" is the accurate phrase and "in production" would not be.

### Do you have business impact numbers?

No. No repository contains a metric of that kind, and I am not going to
manufacture one. What I can quantify is the engineering: twenty-five laws
certified structurally complete against their own publisher sources, fourteen
gates, four stores with one writer each, and a corpus where every stored item is
re-derivable from the publisher's own bytes under a recorded rule set.

---

## Two things to avoid saying

- **"It's a RAG system."** It contains retrieval, but the work was provenance,
  structural verification and lifecycle control. Leading with RAG invites the
  assumption that the hard part was prompt engineering.
- **"We verify everything."** Seven of fourteen gates are required for the
  badge; no EU law is certified; no law is human-certified; and a count matching
  is not proof. Each of those caveats makes the claim stronger, not weaker,
  because it shows the limits were measured rather than assumed.
