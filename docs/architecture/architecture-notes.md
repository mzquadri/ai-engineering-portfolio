# Architecture notes

The detail behind each diagram, and the evidence behind each number. Where a
repository document and its code disagree, this follows the code and says so.

---

## 0. Terminology, fixed once

One term per concept, used the same way in every diagram, document and slide.

| Term | Means exactly | Not to be used for |
|---|---|---|
| **Legal Knowledge Database** | the whole system: five deployable services over four stores and three topics. The proper noun; the repositories and the topic namespace `legal.knowledge.database.*` both use it. | never "Legal Knowledge Platform" |
| **ingestion pipeline** | the three-stage chain entity producer → preprocessor → loader | not the whole system |
| **control plane** | the health service plus the dashboard, taken together | not a single service |
| **Legal KB** | only as part of a real service name — `legal-kb-health-service`, `legal-kb-dashboard` | not as a name for the system |
| **legal pipeline** / **document pipeline** | only when contrasting the two workstreams' Kafka topic sets | not as a synonym for the ingestion pipeline |
| **verification** | running the gates and recording a verdict per gate. Observer only: changes no version, section, chunk, vector or edge. | not reconciliation |
| **reconciliation** | comparing PostgreSQL identity tuples against what Qdrant and Neo4j hold now. Read-only, repairs nothing. | not verification |
| **evidence** | the publisher's captured bytes, their digests, the archive mirror, and the publisher-capture records. Append-only; never touched by withdrawal. | not derived knowledge |
| **derived projection** | Qdrant vectors and the Neo4j graph — rebuildable from canonical state, never the source of a claim | not evidence |
| **active corpus** | the laws currently served: a `laws` row with no `withdrawn_at` | not "everything ever ingested" |
| **trusted corpus** | the conceptual output of verification — what may be served to a question about the law, subject to four separate trust answers | not a database or a table |

**The service count, stated so it can never mislead:** the Legal Knowledge
Database is **five** services. I implemented **four** of them — the preprocessor,
the loader, the health service and the dashboard. The fifth, the entity producer,
existed before legal ingestion and I extended it for EU sources. A sixth
component, the legal chatbot, is an existing service whose repository is not in
the inspected workspace.

---

## 1. Services and ports

| Service | Port | Language | Owns |
|---|---|---|---|
| Entity Producer | 4675 | Java / Spring Boot | MinIO captures |
| Ingestion Preprocessor | 4698 | Python / FastAPI | canonical PostgreSQL, archive mirror |
| Ingestion Loader | 4697 | Python / FastAPI | Qdrant, Neo4j |
| Legal KB Health Service | 8000 | Python / FastAPI | currency, snapshots, audit log |
| Legal KB Dashboard | 3000 | TypeScript / Next.js 16 | nothing |
| Document Extractor | — | Python / FastAPI + Kafka | nothing (reads MinIO) |
| Indexing Service | — | Python | Qdrant document collections |
| RAG Service | — | Python / FastAPI | nothing |
| AI Prediction Service | — | Python | MinIO heatmaps |

The loader deliberately has no `container_name` and publishes a host **port
range** (`4710-4711:4697`) rather than a single port, because it is the one
service designed to be scaled.

## 2. The single-writer rule

| Store | Sole writer |
|---|---|
| PostgreSQL — corpus tables | Preprocessor |
| PostgreSQL — `currency_*`, `corpus_snapshots`, `audit_log` | Health Service |
| MinIO — captures | Entity Producer |
| MinIO — archive mirror / evidence | Preprocessor |
| Qdrant | Loader |
| Neo4j | Loader |

The rule was arrived at by removing a violation, not by agreeing to one. An
earlier loader version deleted canonical rows and could never have succeeded:
`currency_observations` references `laws` with `ON DELETE RESTRICT` and is
append-only, so the delete was refused every time — after Qdrant and Neo4j had
already been cleared and committed. The endpoint was deleted and the replacement
renamed to `DELETE /laws/{law_key}/projections`, so the path states its scope.

One exception remains, recorded as debt rather than resolved by weakening the
rule: a flag-gated `purge_postgres` path in the loader, reachable only behind
`LIFECYCLE_ACTIONS_ENABLED`, which nothing calls today.

## 3. Identity, and why redelivery is safe

```
law_key ──► sections.id   ──► (:LawSection {id})     MERGE by id
        └─► chunks.id     ──► uuid5(ns, chunk_id)    deterministic point id
target_law ────────────────► (:Law {code})           MERGE by code
```

Every derived identifier is a pure function of PostgreSQL content. Identity is
**derived, never generated**, which is what makes a Kafka redelivery converge to
the same state instead of duplicating it — and is why the system needs no
distributed transaction across a relational store, a vector store and a graph
store.

## 4. Convergence, in order

The loader reads one `REPEATABLE READ READ ONLY` snapshot and then:

1. pre-flights obsolete graph nodes, refusing the load if an obsolete section is
   still cited by another law;
2. embeds the active chunks;
3. Qdrant — upsert the generation, delete stale ids, **fence on an exact count**;
4. Neo4j — clear edges and orphan stubs, delete obsolete sections, merge
   sections, reconcile stubs, merge `REFERS_TO` then `CITES_LAW`, **fence on
   exact counts**;
5. publish `law.embedded`, await the broker ack, and commit the Kafka offset
   **last of all**.

Qdrant is written before Neo4j, which makes one failure combination unreachable
on the Kafka path. A crash between publish and commit redelivers and may publish
twice; a unique index on `capture_id` in `currency_observations` absorbs that.

## 5. The fourteen gates

| Gate | Badge | DE | EU |
|---|---|---|---|
| `fidelity.raw_integrity` | required | ✓ | ✓ |
| `currency.source_state` | required | ✓ | ✓ |
| `provenance.pipeline_profile` | required | ✓ | ✓ |
| `structure.section_inventory` | required | ✓ | ✓ |
| `fidelity.qdrant_payload` | required | ✓ | ✓ |
| `fidelity.neo4j_graph` | required | ✓ | ✓ |
| `fidelity.xml_byte_partition` | required | ✓ | — |
| `fidelity.served_text` | recorded | ✓ | ✓ |
| `fidelity.reference_extraction` | recorded | ✓ | ✓ |
| `fidelity.source_structure` | recorded | ✓ | ✓ |
| `fidelity.source_substructure` | recorded | ✓ | ✓ |
| `fidelity.citation_completeness` | recorded | ✓ | ✓ |
| `provenance.publisher_capture` | recorded | ✓ | ✓ |
| `structure.source_profile` | recorded | ✓ | — |

Two gates are structurally inapplicable to EU (FORMEX) sources, and both say so
in code with a named reason — `not_applicable_to_source_family` and
`element_profile_is_gii_only` — rather than silently not running.

> **Documentation drift, recorded.** The repository's gate reference marks only
> seven gates as EU-applicable, while `app/verification/families/formex.py`
> implements four of the ones it excludes. The same file states checker version
> `:9` where the code says `:10`. Its own header names the cause: three
> hand-maintained copies of the gate list exist downstream. This table follows
> the code.

## 6. Corpus figures

| | |
|---|---|
| Registry | **52** laws — 32 `gii_norm`, 20 `formex_v4` |
| `ingestion_order` | 44 laws, each exactly once |
| `ingestible: false` | 9 entries, retained for citation resolution only |
| Certified `COMPLETE` | **25**, all German |
| Certified EU laws | **0**, and none is currently possible |
| `HUMAN_STRUCTURALLY_CERTIFIED` | **0** |

Read from `app/data/law_registry.yaml` and
`audit/reports/corpus-certification-ledger.md` on 2026-09-12. The service README
states 31 German and 51 total; `DDG` was added on 2026-09-03 and the README has
not caught up.

`COMPLETE` means extraction and preservation were proven faithful against the
law's own captured source. It does **not** mean legal review, and the ledger
states explicitly that GII consolidated text is not the official publication —
which is true of every German law in the corpus.

## 7. Three operations, one mutation

| | Changes the corpus? | Requires |
|---|---|---|
| Reconciliation | no | nothing beyond live mode |
| Verify | no | `DATA_SOURCE=live` |
| Re-ingest | **yes** | `DATA_SOURCE=live` **and** `LIFECYCLE_ACTIONS_ENABLED` |
| Withdraw | **yes** | `DATA_SOURCE=live` **and** `LIFECYCLE_ACTIONS_ENABLED` |

Re-ingest is zero-downtime and does not purge first. Each store's own write path
replaces the law safely — PostgreSQL in one transaction, Qdrant
upsert-then-delete-stale, Neo4j merge-by-id — so the old generation stays
queryable throughout and a failed ingest leaves it untouched.

Withdrawal is sequenced canonical-first, projections-second, and the order is not
interchangeable: canonical withdrawal is the step that can be refused, and once
it commits the law is no longer served whatever happens next. Nothing about
withdrawal touches evidence.

## 8. Failure modes worth knowing

| Situation | What happens |
|---|---|
| MinIO fails on an uploaded capture | tolerated; publication continues with the inline copy |
| MinIO fails on a downloaded capture | 502; nothing published |
| Kafka ack times out | 503 — and the send may already have reached the broker; a retry mints a new `eventId` |
| Orphaned capture | possible; MinIO is written before Kafka and nothing removes it |
| Qdrant converges, Neo4j fails | no `law.embedded`, offset uncommitted, loop ends; redelivery re-runs both |
| Stores disagree at rest | reconciliation reports `DRIFT_DETECTED`; an operator decides |
| A store is unreachable | `CHECK_UNAVAILABLE` — a first-class answer, distinct from disagreement |
| Permanently unprocessable law | **no dead-letter topic.** Redelivered for ever, blocking its partition |

The last row is the clearest gap in the pipeline. The document-intelligence
pipeline has a DLQ (`ibp.events.document.indexed.dlq`); the legal pipeline does
not.

## 9. Document intelligence

Conversion is delegated to a Docling Serve sidecar
(`ghcr.io/docling-project/docling-serve-cpu`) on port 5001, currently called with
`do_ocr: "false"`. Field extraction is template-driven: discovery, guided
extraction, re-extraction, then post-validation.

Six preset document types define what "structured" means:
`VERSICHERUNGSPOLICE` (10 fields), `SCHADENMELDUNG` (10),
`VERSICHERUNGSVERTRAG` (8), `RECHNUNG` (4), `ARZTBERICHT` (2), `AUSWEIS` (2).
Each field carries an `extraction_hint` naming the German label variants to look
for — domain literacy encoded as data, portable between models without
retraining.

Indexing is domain-configured: `domains/insurance.yaml` and
`domains/medical.yaml` declare the Qdrant collection, payload index fields,
topics, consumer group, and a `metadata.domain` filter that routes a shared
topic. Vehicle, property, health and beneficiary domains are **not** modelled;
no template or configuration for them exists.

## 10. AI Radiologist — chest X-ray classification

| | |
|---|---|
| Model | `DenseNet121-v2.0.0`, torchvision DenseNet-121 with a dropout + linear head |
| Input | 224 × 224; images re-encoded at a max dimension of 800 |
| Output | five findings, **sigmoid per class** — a study can show several at once, so this is multi-label, not multi-class |
| Explainability | **Grad-CAM++** over the final convolutional block (Chattopadhay et al., WACV 2018) |
| Acceleration | CUDA, plus a DirectML build target for Intel Arc |
| Transport | consumes `ibp.events.inbound`, publishes `ibp.events.ai.processed`; heatmaps written to object storage |

### Five findings, five thresholds

| Finding | Threshold | ICD-10 |
|---|---|---|
| Atelectasis | 0.329 | J98.11 |
| Cardiomegaly | 0.130 | I51.7 |
| Consolidation | 0.234 | R91.8 |
| Edema | 0.233 | J81.0 |
| Effusion | 0.424 | J90 |

The thresholds are **Youden's J optima** from a validation set, so each one
maximises sensitivity plus specificity for its own class rather than for the
average. A global cut-off would have been wrong for every class: the same raw
score means different things for cardiomegaly and for effusion.

**Presence and urgency are answered separately.** Presence uses the calibrated
per-class threshold. Urgency uses fixed probability bands — `HIGH` at 0.70,
`MODERATE` at 0.40, otherwise `LOW`. Collapsing the two would make a confident
low-acuity finding look like an emergency.

### The anatomical prior that was built and then switched off

A soft prior exists for each finding — cardiomegaly centre-left, effusion at the
costophrenic angles, edema perihilar — each able to nudge the attribution map
towards where that finding usually appears. The flag controlling it is set to
**off**, with the reason recorded beside it: the attribution map is the
evidence, and the priors are only hints.

A prior that moves the heatmap towards the expected region makes the explanation
agree with the expectation instead of revealing what the model used — the
explanation would confirm the assumption it was meant to test. This is the same
principle as the legal corpus's independent structural oracle, reached
separately in a different domain.

**Not claimed:** this is a research-grade classifier with explainability and
calibrated thresholds. It is not a certified medical device, it carries no
regulatory clearance, and no clinical accuracy figure appears anywhere in this
portfolio.

---

## 11. AI Compliance — the product the corpus serves

The customer-facing assessment product, and the reason the Legal Knowledge
Database has to be verifiable rather than merely searchable.

| Component | Role |
|---|---|
| Assessment UI | Next.js on Bun, `:4000`; structured questionnaire; password, magic-link or SSO |
| Compliance backend | Spring Boot on JDK 25, `:4010`; owns assessments in PostgreSQL `ai_compliance` |
| Website scan | drives a headless browser over the customer's site for evidence the questionnaire cannot ask for |
| Knowledge processor | reads the questionnaire graph and the legal corpus, returns a grounded assessment |
| Report | rendered to PDF by a headless browser behind a render token with a 120-second TTL |

Transport: the backend publishes to `ibp.events.inbound` and consumes results
from `ibp.events.ai.processed`, with undeliverable results going to a dedicated
dead-letter topic. Evidence is held in its own object-storage bucket.

### The questionnaire bridge

A second, independent consumer path inside the ingestion loader, alongside the
law pipeline:

```
questionnaire version published to object storage
        ↓  domain: AI_COMPLIANCE · entityType: QUESTIONNAIRE
legal.knowledge.database.questionnaire.structured
        ↓
loader: fetch → skip if the content hash is unchanged → embed → store
        ↓
Neo4j: Question / Answer / ComplianceFlag nodes, each with a 1024-dim embedding
        ↓
knowledge processor reads Q/A/Flag and embeddings straight from the graph
```

Graph shape: `(QuestionSection)-[:HAS_QUESTION]->(Question)`,
`(Question)-[:HAS_OPTION]->(Answer)`, `(Answer)-[:TRIGGERS_FLAG]->(ComplianceFlag)`.
Because the embeddings live in the graph, the processor needs no embedding model
of its own.

### Why this makes verification non-negotiable

A compliance report tells an insurance customer whether they meet an obligation
and cites the provision it relied on. If the corpus behind that citation has
drifted from what the publisher served, the report is confidently wrong and
nobody downstream can tell. The gates, the provenance digests and the four
separate trust answers are what make that output defensible.

### Authorship, stated precisely

The product is **not my work** — the UI, the backend, the website scan and the
knowledge processor were built by colleagues, and their repositories are outside
the workspace this portfolio was audited from, so no internal detail is drawn.

The questionnaire ingestion path is a **colleague's feature inside a service I
implemented**: I implemented the loader, its Kafka handling, and its embedding and
graph-write layers; the questionnaire service built on top of them is classed
*Integration / shared* and its author is credited in the private evidence pack.

---

## 12. What is not here

- **No GDMS Rule Mapper.** No repository, topic, consumer, class, configuration
  or document for it exists anywhere in the inspected workspace.
- **No PaddleOCR, DeepSeek-OCR or Redis.** None appears in any dependency,
  configuration or source file.
- **No agentic RAG graph.** A ten-node design exists in the architecture
  material; `langgraph` is commented out and the retrieval package is empty.
- **No monitoring plane in the delivered stack.** Prometheus and Alertmanager
  rules were built, promtool-tested, and then withdrawn.
- **The legal chatbot's internals.** Its environment contract is fully visible;
  its repository is not in this workspace, so no internal detail is drawn.
