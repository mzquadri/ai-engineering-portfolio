# 3-minute walkthrough

Spoken, over `assets/architecture/13-interview-system-overview.svg`. Seven
stages, left to right. About 420 words.

Have the diagram on screen before you start talking. Point, don't describe the
picture — they can see the picture.

---

## 0:00 — Frame it (20s)

> Seven stages, and the thing to notice is that four of them exist only because
> the other three can't be trusted on their own.
>
> Left to right: the publishers, ingestion, processing, storage, verification,
> the trusted corpus, and retrieval.

## 0:20 — Sources and ingestion (25s)

> The sources are the German federal publisher and the EU's CELLAR service.
> Those are outside the system — I don't control what they serve or when they
> change it.
>
> Ingestion does one thing: it takes the publisher's own file, hashes it with
> SHA-256, writes it to object storage under a fresh prefix, and publishes one
> event. It parses nothing. No ZIP, no XML, no section model. That's deliberate
> — a claim about a law is only as good as the bytes it came from, so the digest
> exists before anything interprets them.

## 0:45 — Processing (35s)

> Then the preprocessor. It looks the law up in a registry that decides its
> canonical key, its parser and its source slug, dispatches to one of two
> parsers — German GII-NORM or EU FORMEX — extracts citations down to
> provision level, chunks the active sections, and commits all of it in one
> transaction.
>
> And alongside the rows it stores three hashes: of the parser, of the reference
> extractor, and of the registry. So every stored version of a law remembers the
> rules that produced it.
>
> The loader then embeds the chunks with BGE-M3 and converges the vector store
> and the graph store to that one database snapshot.

## 1:20 — Storage (25s)

> Four stores, and each is there because the others can't do its job. Postgres
> holds the canonical record and can't search by meaning. Qdrant does semantic
> and hybrid retrieval and can't follow a citation chain. Neo4j traverses
> provision references and can't search by meaning. Object storage holds the
> publisher's bytes and can't be queried at all.
>
> One writer each. That rule is why "which service made this row wrong?" always
> has exactly one answer.

## 1:45 — Verification (45s) — spend the time here

> This is the part I'd want to be asked about.
>
> Fourteen gates measure what's stored against what was served. But the real
> problem with a verification layer is that it usually confirms itself — the
> module that produced the parser's denominator was also the module the gate
> re-ran to check it. A defect in there makes the parser, the gate and the
> contract all wrong together, and nothing downstream can see it.
>
> So there's a second reading of the same markup, on a different XML stack, that
> imports no parser code. And the prover checks itself before it checks
> anything: if any law we'd already certified stops reproducing under today's
> rules, no law gets a verdict — including the one you're asking about.

## 2:30 — Trusted corpus and retrieval (20s)

> What comes out isn't "the data is good" — it's four separate answers. Is it
> verified, how old is that verdict, has the publisher moved, and do the derived
> stores still match. Deliberately never merged into one badge, because a green
> summary hides which one failed.
>
> Retrieval is hybrid — dense and sparse in one pass, fused server-side — and
> citations travel as payload rather than as something a model generated.

## 2:50 — Ownership (15s)

> Five services. I implemented four: the preprocessor, the loader, the control
> plane API and the dashboard. The producer existed before legal ingestion and I
> extended it. The stores and the chatbot I integrated.

---

## Then stop.

Do not continue into failure handling unless they ask. If they do, switch to
`14-failure-recovery-and-trust.svg` and lead with the gap:

> There's no dead-letter topic on the legal pipeline. One permanently
> unprocessable law blocks its partition until a human intervenes. The document
> pipeline has one; this one doesn't, and that asymmetry has no justification.
