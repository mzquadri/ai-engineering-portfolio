# Start here — interview cheat sheet

**This file is for me, not for recruiters.** It says exactly what to open, when,
and what to say over it.

Open before the call:

1. `index.html` — press **Interview walkthrough**, leave it on step 1
2. `presentation/ai-engineering-portfolio.pdf` — for a screen share
3. This file, on a second screen

---

## The clock

| Time | Open | Say |
|---|---|---|
| **0–30s** | Slide 1, or the hero image | The 60-second intro from `interview/60-second-introduction.md`. Do not start with the architecture. |
| **30s–2min** | `13-interview-system-overview.svg` (slide 12 uses it) | The seven stages, left to right. Then point at the authorship strip and say which four services are mine. Get that out early. |
| **2–5min** | `02-legal-knowledge-database.svg` (slide 3) | Five services, three topics, four stores. Land the two boundaries: `law.structured` is PostgreSQL only, `law.embedded` is completion. |
| **5–8min** | `17-verification-essence.svg` (slide 5) | The six mechanisms. This is the part that differentiates the work — spend the most time here. |
| **8–10min** | `12-my-contributions.svg` (slide 9) | The ledger. Name what is not mine before they ask. |

If they only give you five minutes, do 0–30s, then 30s–2min, then jump straight
to verification. Skip the full platform diagram.

---

## Answer-to-artefact map

| If they ask… | Open | Path |
|---|---|---|
| "Walk me through the system" | Interview overview | `assets/architecture/13-interview-system-overview.svg` |
| "Show me the real architecture" | Full platform | `assets/architecture/02-legal-knowledge-database.svg` |
| "How do you know the data is right?" | Verification, short | `assets/architecture/17-verification-essence.svg` |
| "Go deeper on verification" | Verification, full — the 14-gate table | `assets/architecture/06-verification-and-reconciliation.svg` |
| "Prove those verification claims" | The source-level proof | `private/audit/10-verification-claim-proof.md` (private) · public summary: `docs/architecture/evidence-summary.md` |
| "What happens when it fails?" | Failure and recovery, 15 rows | `assets/architecture/14-failure-recovery-and-trust.svg` |
| "How do you keep the stores in sync?" | Four stores, one writer each | `assets/architecture/05-multistore-knowledge-architecture.svg` |
| "How does the AI part work?" | Query path | `assets/architecture/07-rag-query-flow.svg` |
| "What does a document actually go through?" | Eleven stages | `assets/architecture/03-document-ingestion-lifecycle.svg` |
| "What can an operator do?" | Control plane | `assets/architecture/08-operator-control-plane.svg` |
| "What are the lifecycle states?" | State machine | `assets/architecture/15-document-state-machine.svg` |
| "What did *you* build?" | Contribution ledger | `assets/architecture/12-my-contributions.svg` |
| "Why did you choose X?" | Nine decisions with trade-offs | `ARCHITECTURE_DECISIONS.md` |
| "Any non-legal AI work?" | Document intelligence | `assets/architecture/10-insurance-document-ai.svg` |
| "Any computer vision?" | AI Radiologist | `assets/architecture/18-ai-radiologist.svg` |
| "What is the corpus actually used for?" | AI Compliance | `assets/architecture/19-ai-compliance.svg` |
| "Tell me about the event architecture" | Ten topics, two pipelines | `assets/architecture/11-event-driven-pipelines.svg` |
| "Explain it to a non-engineer" | Level 1 | `assets/architecture/16-executive-overview.svg` |
| Long-form answers to likely questions | — | `INTERVIEW_WALKTHROUGH.md` |

---

## Speaker notes, per artefact

### `13-interview-system-overview` — the default opener

> Seven stages. Sources on the left are the German and EU publishers — outside
> the system. Then ingestion captures the bytes and hashes them. Knowledge
> processing parses and cites and embeds. Storage is four stores with one writer
> each. Verification measures what is stored against what was served. What comes
> out is a corpus you can ask trust questions about, and the last stage is
> retrieval.
>
> The green-bordered boxes are the four services I implemented. The producer
> I extended. The stores and the chatbot existed.

Then stop and let them pick a stage.

### `17-verification-essence` — the differentiator

Lead with the *why*, not the *what*:

> The problem with a verification layer is that it usually confirms itself. The
> module that supplies the parser's denominator was also the module the gate
> re-ran to check it — so a defect inside it would make the parser, the gate and
> the contract all wrong together, and nothing in the pipeline could see it.
>
> So there is a second reading of the same markup on a different XML stack that
> imports no parser code. And the prover checks itself before it checks
> anything: if any already-certified law stops reproducing under today's rules,
> no law gets a verdict at all.

Then the honest limit, unprompted — it lands better volunteered:

> A count matching is not proof. A citation misread onto a provision that does
> exist moves no count and fails no gate. And `COMPLETE` is machine structural
> assurance, not legal review.

### `12-my-contributions` — get ahead of the ownership question

> Four services are mine by commit share and by design. Two classifications
> deliberately disagree with the commit count: the indexing service is 9 of 30
> commits but the two commits that created it are mine; and the contract-data
> repository is 7 of 9 but it is a data set, not a service, so I call it a
> contribution rather than an implementation.
>
> The RAG service is zero of 56 commits. The Glaux UI is five of 243. Those are
> not mine.

### `14-failure-recovery-and-trust` — the senior signal

> Fifteen failures the repositories actually document. Three are labelled
> accepted and one is labelled a gap — there is no dead-letter topic on the
> legal pipeline, so one permanently unprocessable law blocks its partition
> until a human intervenes. The document pipeline does have one. That asymmetry
> has no justification and it is the first thing I would fix.

### `18-ai-radiologist` — the breadth answer

> Five findings, multi-label, sigmoid per class — a study can show several at
> once. Each finding has its own decision threshold, calibrated with Youden's J
> on a validation set, which is why they differ so much: cardiomegaly is
> positive at 0.130, effusion only at 0.424. A single global cut-off would have
> been wrong for every class.
>
> And presence is not urgency. Presence uses the calibrated threshold; urgency
> uses fixed bands. Different questions.

Then the part worth telling:

> I built a soft anatomical prior per finding — cardiomegaly centre-left,
> effusion at the costophrenic angles — and then switched it off. A prior that
> pulls the attribution map towards where the finding usually appears makes the
> explanation agree with the expectation instead of showing what the model
> actually used. Same principle as the legal oracle, reached separately.

Say the limits unprompted: research-grade, not a certified device, no clinical
accuracy claim.

### `19-ai-compliance` — the "so what" answer

> This is what the legal corpus is for. A customer answers a questionnaire, a
> headless browser scans their site, and a processor reads the questionnaire
> graph plus the corpus to produce a cited compliance report.
>
> That citation is why the corpus has to be verified rather than just indexed.
> If it drifted from what the publisher served, the report is confidently wrong
> and nobody downstream can tell.

Be immediately clear about ownership:

> The product is a colleague's work. I built the corpus and the loader the
> questionnaire path runs inside — that path itself is also a colleague's
> feature, so I mark it Integration / shared rather than claim it.

### `05-multistore-knowledge-architecture` — the "why four databases" question

> Each one is there because the others cannot do its job, and I can name the
> limitation for each. Then: they stay in step without a distributed transaction
> because every derived identifier is a pure function of PostgreSQL content —
> `uuid5` of the chunk id for a Qdrant point, `MERGE` by id for a graph node. So
> re-running a delivery converges instead of duplicating.

---

## Numbers to have exact

Getting one of these wrong is worse than not knowing it.

| Figure | Value |
|---|---|
| Services in the Legal Knowledge Database | **5** — 3 ingestion + 2 control plane |
| Services I implemented | **4** — preprocessor, loader, health service, dashboard |
| Verification gates | **14** — 13 answerable from stored data, 1 needs a live publisher observation |
| Gates required for the badge | **7** |
| Gates applicable to a German law / an EU law | **14 / 12** |
| Laws in the registry | **52** — 32 German, 20 EU |
| Laws certified `COMPLETE` | **25**, all German |
| EU laws certified | **0** |
| Laws human-certified | **0** |
| Kafka topics, legal / document | **3 / 7** (10 total) |
| Stores | **4** — PostgreSQL, Qdrant, Neo4j, MinIO |
| BGE-M3 dense dimensions / token window | **1024 / 8192** |
| Repositories inspected | **20** |
| Workstreams | **4** — legal knowledge, AI compliance, document intelligence, AI Radiologist |
| Radiology findings / thresholds | **5**, one calibrated threshold each (Youden's J) |
| Radiology model | **DenseNet121-v2.0.0**, 224×224, sigmoid per class |
| Urgency bands | HIGH ≥ 0.70 · MODERATE ≥ 0.40 · else LOW |

---

## Three traps

**"Is this in production?"** — No. Docker Compose with CI-built images, in a lab
environment, against the real published corpus. The design is
production-oriented; the deployment is not production. Say it flatly and move
on; hedging here is what damages credibility.

**"What was the business impact?"** — No repository contains a metric of that
kind and I will not invent one. Then redirect to what is measurable: 25 laws
certified against their own publisher sources, 14 gates, four stores with one
writer each.

**"So it's a RAG system?"** — It contains retrieval. The work was provenance,
structural verification and lifecycle control. If you lead with RAG they will
assume the hard part was prompting.

---

## Do not say

- "I built the platform." Four of five services, and the platform is bigger
  than the Legal Knowledge Database.
- "We verify everything." Seven of fourteen gates are badge-required, no EU law
  is certified, and a count matching is not proof.
- "It's fully automated." Nothing self-heals, deliberately. Lifecycle actions are
  operator decisions behind two flags.
- Any number you are not sure of. Say "I'd have to check the ledger" — the
  portfolio is built so that is a credible answer.
