# Publication checklist

Run before this package goes anywhere public — GitHub, Gitea, a personal site, or
into an interview as a shared link.

## 1. The automated gate

```bash
cd portfolio
python tools/check_public.py
```

It scans every text file in the tree for internal hostnames, private IP ranges,
password and token assignments, known development credentials from compose files,
private keys, AWS keys, JWTs, and tool session metadata. It exits non-zero on any
finding.

**Status at last run (2026-09-12): 61 text files scanned, 0 findings.**

`private/` is skipped by name -- it is the evidence pack and it deliberately
contains the strings it documents as redacted. Two files are allow-listed for
the same reason: the scanner itself and `PUBLICATION_DECISIONS.md`.

## 2. What was removed, and what replaced it

Full reasoning: `private/audit/08-public-redaction-review.md` (private pack);
public summary: [evidence-summary.md](docs/architecture/evidence-summary.md).

| Removed | Replaced with |
|---|---|
| Internal Git hostnames, including the IP-literal form | "internal Git host" |
| Internal container registry hostname and repository paths | "internal container registry" |
| The internal LLM inference endpoint | "internal OpenAI-compatible endpoint" |
| The exact served model checkpoint name | "a Gemma-class 26B MoE checkpoint, NVFP4" |
| Every credential, including local development defaults | nothing — they are absent |
| Third-party insurer policy PDFs in the workspace root | not referenced, not described |
| Screenshots of the live operator UI | original vector artwork reproducing the information design |
| Client assurance documents and per-law audit records | aggregate facts only, which are statements about public law |
| Colleague names in public-facing artefacts | "a small platform team" |

Deliberately **kept**, because they are private-network service names with no
routable meaning and are necessary to explain the architecture: container names
(`ibp-postgres`, `ibp-qdrant`, …), localhost ports, Kafka topic names, store and
collection and bucket names, gate identifiers, table and view names.

## 3. Manual review before publishing

- [x] **Repository names.** Resolved: the public tree uses short repository
      names with the employer prefix dropped (e.g.
      `knowledge-db-ingestion-preprocessor`), per PUBLICATION_DECISIONS §A.
      Employer-branded filenames were renamed; BP-ITCS remains in prose as
      context.
- [ ] **Corpus composition.** The package states which German and EU laws are
      ingested, which reveals something about the product's compliance scope. The
      laws are public and the selection is the obvious one for German insurance
      compliance. **Your call.**
- [ ] **Employer permission.** Confirm your own position on publishing
      architecture derived from employer repositories, whatever the redaction
      state.
- [ ] **Read the hero image.** `assets/png/ai-engineering-architecture-4k.png`
      is the artefact most likely to be seen out of context. Check it says only
      what you want it to.

## 4. Accuracy gate

The point of the audit was that nothing here is decorative. Before publishing,
confirm these are still true — they were true on 2026-09-12:

- [ ] No diagram claims a component that does not exist in a repository.
      Verified against `private/audit/07-evidence-matrix.md`.
- [ ] No GDMS Rule Mapper appears as built work. It is named only where it is
      explained as absent.
- [ ] "Production-oriented" is used; "in production" is not.
- [ ] No business impact metric appears anywhere.
- [ ] Every authorship claim uses one of the five defined levels, and the
      "what I did not build" list is present on the contributions diagram and in
      the audit.
- [ ] The three documentation-versus-code inconsistencies found during the audit
      are still disclosed rather than quietly resolved in the portfolio's favour.

```bash
# regenerate everything, then run both gates
python tools/gen_diagrams.py && python tools/gen_hero.py \
  && python tools/gen_site.py && python tools/gen_drawio.py \
  && python tools/gen_deck.py \
  && python tools/check_links.py && python tools/check_public.py
```

A diagram whose text would clip raises rather than rendering, so a clean build is
evidence that no label is truncated.

## 5. If you publish to a public Git host

- [ ] Commit only `portfolio/`. Nothing in this package requires the application
      repositories to be published.
- [ ] Check the commit message contains no tool session metadata, model
      attribution or session URL. The scanner checks the working tree, not your
      commit message.
- [ ] `assets/png/` is ~15 MB. Consider whether it belongs in Git, in a release
      artefact, or regenerated on demand from the SVGs (`tools/export_png.py`).
- [ ] Confirm `private/` is excluded. `git status` must not list it.
- [ ] The six public SVGs in `docs/architecture/` are now **generated** copies —
      `tools/gen_diagrams.py` rewrites them on every run and
      `tools/check_links.py` fails if they drift. They were hand-copied once and
      drifted within a day, which is precisely the defect class this portfolio
      documents elsewhere.

## 6. After publishing

- [ ] Open `index.html` from the published URL and confirm the inlined SVGs
      render, the authorship overlay toggles, and the interview walkthrough
      advances.
- [ ] Check it at phone width. The page body must not scroll sideways; only the
      diagram frames scroll horizontally.
- [ ] Confirm the theme toggle works and that the light theme is legible —
      `localStorage` may be unavailable, and the page must still render.
