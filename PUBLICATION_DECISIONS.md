# Publication decisions

Two questions cannot be settled by a scanner, because they are judgement calls
about employer visibility rather than about secrets. This file states the risk,
the benefit and a recommendation for each, plus the decisions already taken on
everything else.

The automated gate (`python tools/check_public.py`) is green: **0 findings**
across every text file in the tree. What follows is what the scanner cannot
decide.

---

## A. Employer repository names

**Item.** The package names repositories directly: `knowledge-db-ingestion-preprocessor`,
`legal-kb-health-service`, `legal-kb-dashboard`,
`knowledge-db-ingestion-loader`, and sixteen more. They appear in
the contribution ledger, the audit documents and several diagram captions.

**Risk.**

- It identifies an internal project structure by name. A reader learns that
  BP-ITCS runs an `ibp` platform with a legal knowledge subsystem, and can infer
  the service decomposition.
- Repository names are searchable. If any of these repositories ever becomes
  reachable, the names give an attacker a directory listing they would otherwise
  have to guess.
- Some employers treat internal project naming as confidential by default, even
  when the names are descriptive.

**Benefit.**

- It is what makes the contribution claims checkable. "466 of 498 commits in
  `knowledge-db-ingestion-preprocessor`" can be verified by anyone
  with repository access; "466 of 498 commits in a legal ingestion service"
  cannot.
- The names are purely functional. `knowledge-db-ingestion-preprocessor`
  describes what it does and reveals no business logic, customer, or commercial
  arrangement.
- Naming real repositories is normal senior-engineering portfolio practice and
  reads as confident rather than careless.

**Recommendation: keep them in the private evidence package; generalise them in
the public one.**

Concretely:

| Where | Treatment |
|---|---|
| `private/audit/` (excluded from a public remote) | keep exact repository names — this is the evidence trail and it is worthless generalised |
| Public diagrams, deck, README, microsite | use the **service** names (Ingestion Preprocessor, Legal KB Health Service, …), which are already what the diagrams say |
| The one public artefact that names repositories | diagram 12's ledger, which uses the short form (`knowledge-db-ingestion-preprocessor`) with the `` prefix dropped |

Dropping the `` prefix is the whole mitigation and it costs nothing:
the short names still make the ledger checkable to anyone inside, and they no
longer publish the employer's namespace convention. This is already how diagram
12 renders them.

**This has been done.** The audit now lives in `private/audit/`, which
`.gitignore` excludes from a public remote. The public tree contains no
repository names except the short forms in diagram 12's ledger.

---

## B. Exact legal corpus composition

**Item.** The package states which laws are ingested and which are certified —
BGB, ZPO, VVG, VAG, StGB, StPO, HGB, AktG, GWB, KWG, WpHG, BDSG, UrhG, UWG,
InsO, OWiG, GewO, BetrVG, KSchG, AGG, AO, BSIG, TDDDG, VGV, GeschGehG, DDG, plus
GDPR, the EU AI Act, CRA, CER and eIDAS.

**Risk.**

- The selection is a product decision. It reveals the compliance scope
  BP-ITCS's platform targets, which is commercially meaningful information a
  competitor could use to infer the product's positioning.
- The certification split (25 German complete, 0 EU certified) reveals where the
  product is weaker. That is honest and it is also a competitive detail.
- It is the closest thing in this package to business information rather than
  engineering information.

**Benefit.**

- Every one of these laws is public. Their text, structure and citation graph
  are published by the German federal government and the EU. Nothing about the
  list is secret in itself.
- It is what makes the parsing work legible. "We parse German statutes" is
  vague; "BGB carries three evidence documents where ZPO carries one, which is
  what exposed a gate defect" is a real engineering story that requires naming
  the laws.
- The corpus scale (52 registered, 25 certified) is the only honest quantitative
  claim in the portfolio. Removing it leaves no measurable statement at all.

**Recommendation: keep the engineering examples; drop the exhaustive list.**

Concretely:

| Keep | Drop or generalise |
|---|---|
| Named laws where they carry an engineering point — BGB and ZPO in the gate-defect story, DDG in the registry-provenance story, the EU AI Act as a FORMEX example | The full enumeration of all 52 registry entries |
| The aggregate figures: 52 registered, 32 German / 20 EU, 25 certified `COMPLETE`, 0 EU certified | A law-by-law certification table in any public artefact |
| "German and EU compliance-relevant legislation" as the scope description | Anything that reads as a product roadmap |

The current package already complies: no public artefact contains a law-by-law
table. The enumeration above exists only in this file and in the private audit
documents, which quote the ledger. **No change needed in the public tree.**

---

## C. Decisions already taken, recorded for completeness

| Item | Risk | Benefit of keeping | Decision |
|---|---|---|---|
| Internal Git and registry hostnames | direct infrastructure disclosure | none | **Removed.** Replaced with "internal Git host" / "internal container registry" |
| Private IP addresses (the older Gitea remote) | direct infrastructure disclosure | none | **Removed** |
| Internal LLM inference endpoint | a reachable internal service | none | **Removed.** Described as "internal OpenAI-compatible endpoint" |
| The exact served model checkpoint name | narrows the internal stack | small — it is a public model | **Generalised** to "a Gemma-class 26B MoE checkpoint, NVFP4" |
| Development credentials from compose defaults | teaches the naming pattern; indefensible in an interview | none | **Removed** |
| `.env` files | secrets | none | **Never read.** Only `.env.example` and compose defaults were inspected |
| Live operator UI screenshots | shows real corpus data and internal UI | moderate — they are good screenshots | **Not republished.** Replaced with original vector artwork of the same information design |
| Client assurance documents (`CLIENT_ASSURANCE.md`, `AUDIT_FINDINGS.md`, …) | client-facing language, possibly contractual | none for a portfolio | **Not republished.** The engineering mechanisms are cited from code instead |
| Third-party insurer policy PDFs in the workspace | third-party copyright and customer-adjacent content | none | **Excluded.** Not read for content, not referenced |
| Colleague names | personal data; they did not consent to appear in my portfolio | attribution accuracy | **Aggregate in the private audit** (attribution requires it, and the data is in every commit); **absent from all public artefacts**, which say "a small platform team" |
| Container names, localhost ports, topic names, store/collection/bucket names, gate ids, table and view names | low — private-network identifiers with no routable meaning | high — the architecture is unexplainable without them | **Kept** |
| Synthetic insurance documents (`ai-contract-data`) | none — invented insurer, invented policyholder | demonstrates test-data design | **Described, not reproduced** |

---

## D. What a reader can still reconstruct, and why that is acceptable

The package is detailed enough that a competent engineer could reimplement the
architecture. That is the point of a portfolio, and it is not a disclosure
problem:

- **No credential, endpoint or dataset is included**, so reimplementation
  requires doing the work rather than obtaining access.
- **The hard parts are design positions, not secrets** — a structural oracle on
  an independent XML stack, byte-level ruleset provenance, one writer per store.
  Publishing those is publishing engineering judgement.
- **The corpus is public law.** Anyone can fetch the same sources.

The residual exposure is therefore competitive rather than technical, and it is
bounded by decisions A and B above.

---

## E. Recommended final position

1. Run `python tools/check_public.py` — must be 0 findings. ✅
2. Publish the public tree: microsite, diagram pack, editable sources, deck,
   `docs/architecture/`, the interview material, the generators.
3. **Keep `private/audit/` out of the public repository** — already arranged
   by `.gitignore`. It is the
   evidence trail — exact file paths, line numbers, per-repository authorship,
   and the three documentation-versus-code discrepancies found in employer
   repositories. All of it is legitimate and none of it is for strangers. Keep
   it in a private repository or a local directory, and link to it only when an
   interviewer asks how the claims were verified.
4. Leave the aggregate corpus figures in. Leave the named-law engineering
   stories in. Do not add a law-by-law table.
5. Before pushing, confirm your own position on publishing architecture derived
   from employer repositories. That is the one item no file in this package can
   decide for you.
