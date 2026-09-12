# Verification deep dive

For when an interviewer says "go deeper on the verification". This is the part
of the work that is genuinely unusual, so it is worth being able to go six or
seven minutes on it without reaching for a diagram.

Every claim below is proved against source in the private evidence pack
(`private/audit/10-verification-claim-proof.md`); the public summary is
[`docs/architecture/evidence-summary.md`](../docs/architecture/evidence-summary.md).
Open `17-verification-essence.svg` to start, `06-verification-and-reconciliation.svg`
if they want the gate inventory.

---

## Open with the problem, not the solution

> The thing that makes verification hard in a pipeline like this isn't writing
> checks. It's that the checks tend to be written against the same understanding
> as the code they're checking — so they pass for the same reason the code is
> wrong.
>
> We had a concrete instance of that. The module that supplied the parser's
> completeness denominator was also the module the gate re-ran to verify it. One
> implementation answered the question *and* marked its own answer. A defect
> inside it would have been common-mode: parser, gate and contract all wrong
> together, and nothing in the pipeline able to see it.

That framing is what makes the rest land. If you start with "we have fourteen
gates", it sounds like test coverage.

---

## 1. The independent oracle

> So there's a second inventory of the same markup, and it's independent in
> mechanism rather than just in file.
>
> Production parses the whole tree with `defusedxml`, walks it with
> `root.iter()` and `find`, and builds text with `"".join(itertext())`. The
> oracle streams `lxml.etree.iterparse` events, tracks an explicit tag stack,
> and accumulates character data from each element's `.text` and `.tail` as the
> stream passes.
>
> Different library, different traversal model, different text assembly. And it
> imports nothing from the application package — its only imports are `io`,
> `re`, `dataclasses` and `lxml`.

**If pushed on why that matters:** two implementations that share a traversal
strategy share its blind spots. Changing the traversal is what makes the second
reading worth having.

**Be honest about the boundary:** only the oracle is independent. There are
about 46 tools in that directory and at least one deliberately *does* import the
parser — it's a differential that compares the two. "All our tools are
independent" would be false.

## 2. The prover proves itself first

> Before any claim is made about the law you asked about, the harness has to
> reproduce the stored reference and citation identity sets of *every* already-
> complete law, under today's rules. If that baseline fails, the run prints
> "the prover has not proven itself; no verdict issued" and exits. Nothing gets
> a verdict — including the law being certified.

**The good follow-up, if they ask whether that's ever fired:** yes, and it's
currently firing. Adding one law's two long-form names to the registry moved
eight reference identities across four already-certified laws — BGB, StPO,
TDDDG and UWG. Every one was read against source and is correct. But those four
laws' stored generations no longer reproduce under the current registry, so the
baseline fails and no law gets a verdict until they're replayed.

That is the mechanism working, not a defect. It is also a real operational cost,
and saying so is the point.

## 3. Ruleset provenance

> Every stored generation records three digests: over the parser, over the
> reference extractor, and over the registry. They're SHA-256 over the raw file
> bytes, length-prefixed so concatenation can't make two different file sets
> hash the same.
>
> A byte change is a rule change. There's no normalisation, no AST comparison,
> no tokenisation.

**The story that proves it:** a lint pass sorted the imports in those files.
`parser_rule_sha256` moved from `38eb6f833d0ab5ab` to `b36ddd87ed592417` with no
behaviour change at all, and every stored generation's recorded ruleset stopped
matching the installed one. We kept the digest byte-exact and disabled the
import-sort rule for those three files instead, with the reason recorded in
`pyproject.toml`.

**If they say that's over-strict:** a digest that tolerates "harmless" edits
can't tell you whether a stored law still reproduces, which is the only thing
the mechanism is for. Three files exempt from one lint rule is the cheaper
inconsistency.

**Precision if EU law comes up:** the rule surface is declared per source
family. German law's parser surface is two files; FORMEX's is seven, and its
reference surface another six.

## 4. The gates themselves

> Fourteen gate ids. Thirteen can be answered from stored data alone; the
> fourteenth compares what the publisher is serving *right now* against the
> declared profile, so it needs an observation only the caller that fetched it
> holds — it's supplied separately rather than computed from the database.
>
> Seven are required for the aggregate badge. The other seven are recorded and
> displayed anyway, because a measurement nobody can see isn't a measurement.
>
> All fourteen apply to a German law. Twelve apply to an EU law — two are
> structurally inapplicable to FORMEX and say so in code with a named reason
> rather than silently not running.

**The detail worth volunteering:** `not_run` had to be split into two meanings.
"This gate doesn't apply to this source family" and "this gate hasn't run yet"
are both recorded as not-run, because that's what the row is — no measurement
was taken. But rendering them identically had invited the reading that an EU law
was half-verified when it was fully verified by the gates that apply to it.

## 5. Observer and judge are separate

> Currency is the one gate that depends on the outside world, so it's split
> across two services. The health service polls the publisher and writes an
> observation bound to a capture id. The preprocessor's gate reads that
> evidence and decides what it means — it never fetches anything itself.
>
> The observer records what was served; the judge decides what it implies.
> Neither can quietly do the other's job.

## 6. What verification is not

Volunteer these. They make the whole thing more credible, not less.

> **A count matching is not proof.** A citation misread onto a provision that
> does exist produces no orphan, moves no count, and fails no gate. That's why
> there's a separate human review of citation targets alongside the machine
> gates.
>
> **`COMPLETE` is machine structural assurance, not legal review.** It says the
> law was extracted and preserved faithfully from its captured source — not that
> the law was interpreted correctly. No law in the corpus is human-certified.
>
> **And the source isn't the official publication.** The German consolidated
> text we ingest isn't the Bundesgesetzblatt. That's true of every German law in
> the corpus and it's stated in the ledger.

## 7. The one I'd fix

> The checker version is hand-maintained, and it failed to move once when a
> gate's semantics changed. So verdicts written either side of that change are
> indistinguishable — ten laws hold a verdict computed under the previous
> reading with nothing to mark it.
>
> It's recorded as verifier-provenance debt in the revalidation matrix. The fix
> is to derive the version from the gate implementations rather than maintaining
> a string, and it's the first thing I'd change in that layer.

---

## If they ask the sharpest possible question

**"How do you know the oracle itself is right?"**

The honest answer, and it's a good one:

> I don't, independently — and that's why it isn't the only layer. The oracle
> gives a denominator derived differently from the parser, so the two agreeing
> is evidence neither has a defect the other shares. It isn't proof that both
> are right.
>
> On two laws we went further and checked against a third throwaway inventory
> written for those audits, which agreed. That's the practical ceiling: each
> additional independent derivation makes a common-mode defect less likely
> without ever excluding it.
>
> What the system does instead of claiming certainty is refuse. If pre-flight
> meets structure it doesn't recognise, the law is blocked before ingestion
> rather than ingested and reviewed afterwards. And a law whose ruleset no
> longer matches gets no verdict at all rather than a stale one.
