# Evidence summary

How this portfolio was assembled, what it deliberately does not claim, and how
the verification claims were checked. This is the public version; it carries the
method and the findings without the file-level forensics.

The full trail is ten documents held privately — repository map, service
inventory, data-store inventory, event and topic inventory, API inventory, model
inventory, evidence matrix, redaction review, contribution map, and a
claim-by-claim verification proof. It is available on request. It is not
published because every sensitive string in the workspace turned out to live in
it: internal hostnames, private IP ranges, the inference endpoint, colleague
names, and exact repository paths.

---

## Method

1. **Read before drawing.** Twenty repositories were inspected — source,
   configuration, Docker Compose files, migrations, tests, tooling and
   documentation — before any diagram was authored.
2. **Authorship from git, not memory.** `git shortlog -sne` per repository,
   then a per-repository classification into five levels. Commit share is
   treated as evidence of weight, never as proof of authorship.
3. **One evidence matrix.** Every claim in the portfolio was entered in a table
   with its source file, the evidence, and a confidence rating. Anything rated
   below *High* carries a qualifier wherever it appears; anything with no
   evidence was excluded rather than softened.
4. **Verification claims re-proved separately.** The six claims that make the
   verification layer distinctive were re-checked directly against source
   *after* the diagrams were built, so the check could contradict the artwork.
   It did once — see below.
5. **Redaction as a runnable gate**, not a promise:
   `python tools/check_public.py`. It exits non-zero on any internal hostname,
   private IP range, credential, token, private key or session metadata.

---

## The verification claims, proved against source

Six claims, each re-verified on 2026-09-12 in
`knowledge-db-ingestion-preprocessor`.

| Claim | Verdict |
|---|---|
| **14 verification gates** | **Confirmed.** Fourteen gate-id constants in `app/verification/gates.py`. Thirteen are answerable from stored data; the fourteenth compares what the publisher is serving *now* against the declared profile, so it needs a live observation and is supplied separately. |
| **An independent structural oracle exists** | **Confirmed, and stronger than first documented.** The module that supplied the parser's completeness denominator was also the module the gate re-ran to check it — so a defect inside it would be common-mode: parser, gate and contract wrong together, with nothing in the pipeline able to see it. The oracle exists to break that. |
| **The oracle imports no parser code** | **Confirmed.** Its only imports are `io`, `re`, `dataclasses` and `lxml.etree`. Zero application imports. |
| **The prover proves itself first** | **Confirmed, verbatim in code.** Before any claim about a law, the baseline must reproduce the stored reference and citation identity sets of every already-complete law under today's rules. If it fails, the run prints "the prover has not proven itself; no verdict issued" and exits — no law gets a verdict, including the one being certified. |
| **Ruleset provenance digests** | **Confirmed, with a refinement.** Three digests per stored generation, over the parser, the reference extractor and the registry. The rule surface is declared **per source family** — the German surface is two files, the EU surface seven plus six more for references. |
| **A byte-level rule change invalidates provenance** | **Confirmed.** The digest is SHA-256 over `read_bytes()`, length-prefixed so concatenation cannot make two different file sets collide. No normalisation, no AST comparison, no tokenisation. |

### The one correction

An earlier draft of this portfolio said the oracle "walks the source XML with
the standard library and `defusedxml`". **That describes production, not the
oracle.** Verified: production uses `xml.etree.ElementTree` with
`defusedxml.ElementTree.parse` and a full-tree walk; the oracle uses
`lxml.etree.iterparse` streaming events with an explicit tag stack, and
accumulates character data from each element's `.text` and `.tail`.

Corrected everywhere. The corrected claim is stronger: *different library,
different traversal model, different text assembly, zero shared code* is a
better independence argument than "it uses the standard library".

**The boundary, stated honestly:** only the oracle is independent. Of roughly 46
tools in that directory, at least one deliberately does import the parser — it
is a differential that compares the two. "All our tools are independent" would
be false.

---

## The AI Radiologist claims, proved against source

Read on 2026-09-12 from `ai-prediction-service/src/ai_prediction/` and the
shared `ai-utils` constants and event model.

| Claim | Verdict |
|---|---|
| DenseNet-121, five findings, multi-label | **Confirmed.** `models.densenet121` with a dropout + linear head sized to the label list; sigmoid per class, so several findings can be positive at once. |
| Model identifier `DenseNet121-v2.0.0`, 224 × 224 input | **Confirmed** — both are named constants. |
| Five findings with ICD-10 codes | **Confirmed.** Atelectasis J98.11, Cardiomegaly I51.7, Consolidation R91.8, Edema J81.0, Effusion J90 — each with clinical metadata. |
| One calibrated threshold per finding | **Confirmed.** 0.329 / 0.130 / 0.234 / 0.233 / 0.424, annotated in source as Youden's J optima from a validation set. |
| Presence and urgency computed separately | **Confirmed.** Presence compares against the per-class threshold; urgency is a fixed band — HIGH ≥ 0.70, MODERATE ≥ 0.40, else LOW. |
| **Grad-CAM++**, not Grad-CAM | **Confirmed — and corrected.** The implementation cites Chattopadhay et al., *Grad-CAM++*, WACV 2018. An earlier draft of this portfolio said "Grad-CAM"; every reference now says Grad-CAM++. |
| Anatomical priors built and then disabled | **Confirmed.** A per-finding region prior exists with a boost factor, behind a flag that is set to off, with the reason recorded beside it. |

**Authorship.** The calibrated thresholds and the severity model were introduced
by me in the shared library (the commit that added them is the one that also
records the Youden's J provenance). The Grad-CAM++ analyser, the DenseNetV2
integration and the DirectML build target are also mine. Overall commit share in
that service is a minority, so the service is classed *Significant
contribution*, not *Primary implementation*.

**Not claimed.** Research-grade only: no certified medical device, no regulatory
clearance, and no clinical accuracy figure appears anywhere in this portfolio.

---

## The AI Compliance claims, proved against source

Read from the environment contracts in `local-env/ibp/ai-compliance{,-backend}/`
and from the questionnaire path inside the ingestion loader.

| Claim | Verdict |
|---|---|
| A questionnaire-based assessment product with a website scan | **Confirmed** from the environment contract: a Next.js UI on Bun, a Spring Boot backend on JDK 25, its own PostgreSQL database, and a headless-browser scan endpoint. |
| Results flow back over Kafka with a dead-letter topic | **Confirmed** — a results topic, a consumer group, and a dedicated DLT are all declared. |
| Reports are rendered to PDF behind a short-lived token | **Confirmed** — a render endpoint and a 120-second token TTL are configured. |
| A questionnaire graph in Neo4j with embeddings | **Confirmed.** Question, Answer and ComplianceFlag nodes each carry a 1024-dim embedding; relationships are `HAS_QUESTION`, `HAS_OPTION`, `TRIGGERS_FLAG`. |
| The loader ingests it on a second, independent consumer path | **Confirmed** — a dedicated service module, a distinct topic, and a content-hash skip. |
| The processor needs no embedding model of its own | **Confirmed** — it reads embeddings straight from the graph. |

**Authorship, stated precisely.** The product is **not mine** — UI, backend,
website scan and knowledge processor were built by colleagues, and their
repositories are outside the audited workspace, so no internal detail is drawn.
The questionnaire ingestion path is a **colleague's feature inside a service I
implemented**: I implemented the loader, its Kafka handling and its embedding and
graph-write layers; the questionnaire service on top is classed *Integration /
shared* and its author is credited in the private evidence pack.

This workstream is why the verification layer exists. A compliance report cites
a provision; if the corpus behind that citation has drifted from what the
publisher served, the report is confidently wrong and nobody downstream can
tell.

---

## What the portfolio does not claim

| | |
|---|---|
| **Production deployment** | Not claimed. Only Docker Compose stacks and CI image builds are evidenced — no Kubernetes manifest, no cloud infrastructure. The wording used throughout is *production-oriented*. |
| **Business impact metrics** | Not claimed. No repository contains one, so none is stated. |
| **A GDMS Rule Mapper** | **Excluded.** It was named in the brief for this portfolio. A case-insensitive search of the entire workspace returned two hits, both inside base64-encoded raster images in unrelated files. No repository, topic, consumer, class, configuration or document for it exists. It is not drawn. |
| **PaddleOCR, DeepSeek-OCR, Redis** | **Excluded.** None appears in any dependency, configuration or source file. |
| **An agentic RAG graph** | **Labelled design, not delivered.** A ten-node design exists in the architecture material; `langgraph` is commented out and the retrieval package is empty. |
| **Answer-level citation validation** | **Labelled design, not delivered.** Regex-extracting cited sections and checking each against the corpus is designed and not implemented. |
| **EU law certification** | **Zero EU laws are certified.** The parsers work and EU acts are queryable; the end-to-end assurance contract for them does not exist, because the pre-flight detectors are GII-shaped. |
| **Human legal certification** | **No law in the corpus is human-certified.** `COMPLETE` means machine structural assurance — the law was extracted and preserved faithfully from its captured source, not that it was interpreted correctly. |
| **A monitoring plane** | Built, promtool-tested, then **withdrawn** from the delivered stack. Not drawn in the delivered architecture. |

---

## Inconsistencies found in the source repositories

Found while auditing my own work, and disclosed rather than quietly resolved in
the portfolio's favour. Where a document and its code disagree, the portfolio
follows the code.

1. **A service's API reference states there is no delete endpoint.** The route
   exists, is implemented by a dedicated orchestrator module, and is documented
   correctly in that service's architecture document and sequence diagram. The
   route was removed and later reintroduced; that one section was not updated.
2. **A README states 31 German laws and 51 in total.** The registry holds 32 and
   52 — one law was added and the README has not caught up. The portfolio quotes
   the registry.
3. **The gate reference marks seven gates as EU-applicable**, while the FORMEX
   gate family implements four of the ones it excludes. The same file states a
   checker version one behind the code. The file's own header names the cause:
   three hand-maintained copies of the gate list exist downstream.

The third is the reason "generate the gate list once" appears in the
*what I would change* list.

---

## What was redacted, and why

Removed rather than obscured:

- internal Git and container-registry hostnames, including an IP-literal form
- private IP ranges
- the internal LLM inference endpoint
- the exact served model checkpoint (generalised to its public family and
  quantisation)
- every credential, including local development defaults from compose files
- third-party insurer policy documents present in the workspace
- screenshots of the live operator interface, which showed real corpus data
- client-facing assurance documents
- colleague names — present in the private audit because attribution requires
  it, absent from every public artefact

Deliberately **kept**, because they are private-network identifiers with no
routable meaning and the architecture cannot be explained without them: service
and container names, localhost ports, Kafka topic names, store, collection and
bucket names, gate identifiers, and table and view names.

The subject matter is public law — BGB, ZPO, VVG, GDPR, the EU AI Act — so law
keys, section numbers, citation structures and CELEX identifiers needed no
redaction. That is what lets this description be concrete rather than abstract.

Two judgement calls remain, and they are employer-visibility decisions rather
than technical ones: publishing repository names, and publishing the corpus
composition. Both are worked through in
[PUBLICATION_DECISIONS.md](../../PUBLICATION_DECISIONS.md).
