"""Build index.html at the repository root -- one static file, no build step,
no CDN.

The SVGs are inlined rather than referenced, for three reasons: it works from
the filesystem with no server, the diagrams inherit the page theme, and every
node carries data-role and data-level so the authorship overlay can be a CSS
rule instead of a second set of artwork.

    python tools/gen_site.py
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCH = ROOT / "assets" / "architecture"


def svg(name: str, *, caption: str = "", figno: str = "") -> str:
    """Inline one diagram as a zoomable figure."""
    path = ARCH / f"{name}.svg"
    if not path.exists():
        return f'<p class="missing">Diagram not built: {name}.svg</p>'
    markup = path.read_text(encoding="utf-8")
    # Strip the fixed pixel size so CSS can scale it; keep the viewBox.
    markup = re.sub(r'\swidth="\d+"\sheight="\d+"', ' ', markup, count=1)
    return f"""<figure class="fig" data-diagram="{name}">
  <div class="fig-frame" tabindex="0" role="group"
       aria-label="{caption or name}. Scroll to zoom, drag to pan.">
    <div class="fig-stage">{markup}</div>
  </div>
  <figcaption><span class="fig-no">{figno}</span>{caption}
    <a class="fig-open" href="assets/architecture/{name}.svg" target="_blank"
       rel="noopener">Open the SVG</a></figcaption>
</figure>"""


SECTIONS: list[tuple[str, str, str]] = []


def section(sid: str, nav: str, html: str, *, interview: bool = False) -> None:
    SECTIONS.append((sid, nav, html))
    if interview:
        INTERVIEW.append(sid)


INTERVIEW: list[str] = []


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
def build() -> str:
    section("overview", "System overview", f"""
<h2>Two workstreams, one platform</h2>
<p class="lede">Both workstreams do the same fundamental thing: take a document
that somebody else authored, and turn it into knowledge a machine can query
without losing track of where it came from. One does it for German and EU
legislation, the other for insurance documents.</p>
<p>They share Kafka, PostgreSQL, MinIO, Qdrant and Neo4j, and they share no
topics, databases or collections. The Legal Knowledge Database is five
services and I implemented four of them; the document workstream is three
services I extended, one of which I started.</p>
{svg("01-ai-systems-landscape", figno="01",
     caption="The landscape. Colour is engineering role; border weight and the "
             "corner marker are authorship.")}
<div class="grid-3">
  <div class="stat">
    <p class="stat-n">4</p>
    <p class="stat-l">services I implemented, out of 20 repositories inspected</p>
  </div>
  <div class="stat">
    <p class="stat-n">14</p>
    <p class="stat-l">verification gates, of which seven are required for the
      aggregate badge</p>
  </div>
  <div class="stat">
    <p class="stat-n">52</p>
    <p class="stat-l">laws in the registry — 32 German, 20 EU; 25 certified as
      structurally complete</p>
  </div>
</div>
<p class="fine">Counts are read from <code>app/data/law_registry.yaml</code> and
<code>audit/reports/corpus-certification-ledger.md</code> as of 2026-09-12. The
service README states 31 and 51; the registry has moved since, and the registry
wins.</p>
""", interview=True)

    section("executive", "One-paragraph version", f"""
<h2>The one-paragraph version</h2>
<p class="lede">A platform that does not only make authoritative information
searchable, but makes claims about that information falsifiable.</p>
{svg("16-executive-overview", figno="02",
     caption="Level 1. Four capabilities, no technology names.")}
""")

    section("legal", "Legal Knowledge Database", f"""
<h2>The Legal Knowledge Database</h2>
<p class="lede">Five services in two groups \u2014 a three-stage ingestion
pipeline and a two-part control plane \u2014 over three Kafka topics and four
stores, with one rule that makes the whole thing verifiable: exactly one service
may write each store.</p>
<p>The ingestion pipeline is the entity producer, the preprocessor and the
loader. The control plane is the health service and the dashboard. I implemented
four of the five; the entity producer predates legal ingestion and I extended
it for EU sources.</p>
<p>That rule is not a convention. It was arrived at by removing a violation. An
earlier version of the loader deleted canonical rows, and it could never have
succeeded — <code>currency_observations</code> references <code>laws</code> with
<code>ON DELETE RESTRICT</code> and is append-only, so the delete was refused
every time, after Qdrant and Neo4j had already been cleared and committed. The
fix was to delete the code path and rename the replacement so the route states
its scope: <code>DELETE /laws/&#123;key&#125;/projections</code>.</p>
{svg("02-legal-knowledge-database", figno="03",
     caption="Level 3. Exact services, topics, routes and stores.")}
<h3>The two boundaries</h3>
<p>Reading this architecture wrong is easy in exactly one place, so it is
annotated three times in the source diagrams. <code>law.structured</code> means
canonical PostgreSQL is committed and nothing else — no vector exists, no graph
edge exists. <code>law.embedded</code> is the completion boundary: it is
published only after both derived stores converge under an exact count fence,
and it is the event that makes the preprocessor verify the law without anyone
asking it to.</p>
""", interview=True)

    section("journey", "Document journey", f"""
<h2>One law, end to end</h2>
<p class="lede">Eleven stages. Each one either produces evidence, or is measured
against evidence produced earlier.</p>
{svg("03-document-ingestion-lifecycle", figno="04",
     caption="From publisher to queryable knowledge.")}
<p>Two orderings in that sequence are load-bearing. The independent source
inventory is built <em>before</em> the parser runs, so the denominator used to
check the extraction does not come from the thing being checked. And the
archive-mirror row is written <em>last of all</em> — after the object has been
uploaded, read back, hashed and size-checked — because that row is what the
raw-integrity gate treats as evidence. A row that exists has to mean bytes that
were verified.</p>
{svg("04-source-to-trusted-corpus", figno="05",
     caption="The conceptual spine. Derived knowledge is never the evidence for "
             "itself.")}
""", interview=True)

    section("storage", "Knowledge storage", f"""
<h2>Why four stores</h2>
<p class="lede">Each store is here because the others cannot do its job. The
limitation row is the real justification.</p>
{svg("05-multistore-knowledge-architecture", figno="06",
     caption="Four stores, four jobs, one writer each.")}
<h3>How they stay in step without a distributed transaction</h3>
<p>Every derived identifier is a pure function of PostgreSQL content. A Qdrant
point id is <code>uuid5(namespace, chunk_id)</code>. A graph node is
<code>MERGE</code>-d by id, a law node by code. Identity is derived, never
generated — so re-running a delivery converges to the same state rather than
duplicating it. That single property is what replaces a transaction across a
relational store, a vector store and a graph store, and it is why a Kafka
redelivery is safe rather than dangerous.</p>
""", interview=True)

    section("trust", "Trust & verification", f"""
<h2>Can we trust what is being served?</h2>
<p class="lede">The system answers that with fourteen gates and four separate
statuses, and it deliberately refuses to answer it with one badge.</p>
<p>Seven gates are required for the aggregate the dashboard shows; the other
seven are recorded and displayed anyway, because a measurement nobody can see is
not a measurement. All fourteen apply to a German law. Twelve apply to an EU
law: <code>fidelity.xml_byte_partition</code> and
<code>structure.source_profile</code> are structurally inapplicable to FORMEX
and say so in code, with a named reason rather than silence.</p>
{svg("17-verification-essence", figno="07",
     caption="The short version: six mechanisms, each one there to stop the "
             "verification layer from confirming itself.")}
{svg("06-verification-and-reconciliation", figno="08",
     caption="The full version: the gate inventory, how a verdict is produced, "
             "and the three operations that touch a law.")}
<h3>What the gates cannot see</h3>
<p>A count matching is not proof. A citation misread onto a provision that does
exist produces no orphan, moves no count, and fails no gate — which is why a
separate human review of citation targets sits alongside the machine gates, and
why <code>COMPLETE</code> is defined as machine structural assurance rather than
legal review. No law in the corpus claims to be human-certified.</p>
{svg("14-failure-recovery-and-trust", figno="09",
     caption="Fifteen documented failures, and the recovery that exists — or "
             "the statement that none does.")}
""", interview=True)

    section("query", "Retrieval & answering", f"""
<h2>The query path</h2>
<p class="lede">Deliberately separate from the ingestion path. Nothing here
writes a store, and nothing here parses a law.</p>
{svg("07-rag-query-flow", figno="10",
     caption="Query time. The answering stage is an existing component whose "
             "repository is not in the inspected workspace.")}
<p>Retrieval is hybrid and single-round-trip: BGE-M3 produces a dense and a
sparse vector from one pass, both are prefetched, and Qdrant fuses them
server-side with reciprocal rank fusion. Dense catches meaning — a query for
“duty to disclose” reaches the German <span lang="de">Anzeigepflicht</span>.
Sparse catches exact tokens, which is what a citation like <code>§&nbsp;19
VVG</code> actually is.</p>
<p>One refusal is worth more than the retrieval design. FlagEmbedding truncates
silently past the model's 8192-token window, so the loader counts tokens first
and raises for the whole law rather than storing a vector for text the model
never fully saw. A silently truncated embedding is undetectable afterwards: it
has the right dimensionality, sits in the right collection, and is wrong.</p>
""", interview=True)

    section("operations", "Operator workflow", f"""
<h2>The operator control plane</h2>
<p class="lede">Four actions, and what each one actually triggers behind the
button.</p>
{svg("08-operator-control-plane", figno="10",
     caption="Ingest, Verify, Reconcile, Withdraw — and the double gate on the "
             "two that change the corpus.")}
{svg("09-reingestion-state-machine", figno="12",
     caption="What a reader sees at each state of a re-ingest, including the "
             "window where the stores legitimately disagree.")}
{svg("15-document-state-machine", figno="13",
     caption="The states a law occupies, reconstructed from code rather than "
             "from a generic lifecycle template.")}
<p>Withdrawing a law is not deleting it. The <code>laws</code> row survives,
<code>withdrawn_at</code> is set, and no MinIO object, raw document, publisher
capture, currency observation or verification check is touched by any step. A law
leaving the corpus does not make the record of what its publisher served
untrue.</p>
""")

    section("documents", "Document intelligence", f"""
<h2>Insurance document AI</h2>
<p class="lede">A template is the extraction contract, not the model. That is
what lets the model change without the pipeline changing.</p>
{svg("10-insurance-document-ai", figno="14",
     caption="From PDF to structured understanding, with the six document "
             "templates that define what structured means.")}
<p>The most portable piece of domain knowledge in that repository is a string:
<code>"Look for: Policennummer, VS-Nr., Vertragsnummer, Police Nr."</code>.
German insurance-document literacy, encoded as data, reviewable by someone who
knows insurance but not Python, and carried between models without retraining.</p>
""")


    section("radiology", "Medical imaging", f"""
<h2>Multi-label chest X-ray classification</h2>
<p class="lede">A research/prototype medical-imaging classification pipeline —
internally named &ldquo;AI Radiologist&rdquo;. Five findings, one calibrated
decision threshold each, and a Grad-CAM++ attribution map.</p>
<p class="fine"><strong>Scope:</strong> this is a prototype. It is not a medical
device, it has no regulatory clearance, it was not clinically validated or
deployed, and it does not assist or replace a clinician. The internal project
name is recorded here because that is what the repository calls it — it is not a
claim about clinical role.</p>
<p>Five findings — atelectasis, cardiomegaly, consolidation, edema and
effusion — each with an ICD-10 code and its own decision threshold. The
thresholds are Youden&rsquo;s J optima from a validation set, which is why they
differ so widely: cardiomegaly is called positive at <code>0.130</code> and
effusion only at <code>0.424</code>. A single global cut-off would have been
wrong for every class.</p>
{svg("18-ai-radiologist", figno="17",
     caption="The inference path, the five decision thresholds, and the one "
             "decision worth defending.")}
<h3>A design decision, separated into fact and interpretation</h3>
<p><strong>What the code contains.</strong> A per-finding anatomical prior —
cardiomegaly centre-left, effusion lower, edema perihilar, each with a boost
factor. The mask is boost-only: it emphasises, it never suppresses. The flag
controlling it is <code>USE_ANATOMICAL_HINTS = False</code>, commented
&ldquo;DISABLED — trust Grad-CAM fully&rdquo;, and the surrounding comments
state that the model&rsquo;s attention is the ground truth for localisation and
that the hints are soft only.</p>
<p><strong>My reading of it, which the code does not state.</strong> An
engineering concern is that an anatomical prior could bias localisation towards
expected anatomy, so the attribution would tend to agree with the label rather
than show what the model actually used. That rationale is my interpretation of
the decision — the source documents &ldquo;trust the model&rsquo;s
attention&rdquo;, not an argument about explanation bias.</p>
<p>I also read it as the same shape of decision as the legal corpus&rsquo;s
independent oracle — a check that shares the assumption of the thing it checks
cannot falsify it. That parallel is my own framing across two codebases, not a
claim that either was built with the other in mind.</p>
""", interview=True)

    section("compliance", "AI Compliance", f"""
<h2>AI Compliance — what the corpus is for</h2>
<p class="lede">The customer-facing assessment product. It is the reason the
Legal Knowledge Database has to be verifiable rather than merely searchable.</p>
<p>A customer works through a structured questionnaire; a headless browser
scans their site for evidence the questionnaire cannot ask for; a knowledge
processor reads the questionnaire graph together with the legal corpus and
produces a grounded assessment; the result is rendered to a PDF report behind a
short-lived token.</p>
{svg("19-ai-compliance", figno="18",
     caption="The product, and the questionnaire bridge into the legal "
             "corpus. Authorship is marked per component.")}
<h3>Why the corpus has to be verifiable</h3>
<p>A compliance report tells an insurance customer whether they meet an
obligation, and cites the provision it relied on. If the corpus behind that
citation has drifted from what the publisher actually served, the report is
confidently wrong and nobody downstream can tell. The gates, the provenance
digests and the four separate trust answers exist so that this product&rsquo;s
output is defensible.</p>
<p class="fine">Whose work this is: the assessment UI, the backend, the website
scan and the knowledge processor were built by colleagues and their
repositories are outside the workspace this portfolio was audited from, so no
internal detail is drawn. The questionnaire ingestion path is a
colleague&rsquo;s feature living inside a service I implemented — I own the
loader, its Kafka handling and its embedding and graph-write layers; the
questionnaire service on top of them is marked <em>Integration / shared</em>
rather than claimed.</p>
""", interview=True)

    section("events", "Event-driven systems", f"""
<h2>Ten topics, two pipelines, one broker</h2>
<p class="lede">Exact topic names, their producers and their consumers — and the
places where the two pipelines differ in maturity.</p>
{svg("11-event-driven-pipelines", figno="19",
     caption="The topic inventory, plus the four delivery properties that were "
             "designed rather than inherited.")}
""")

    section("contributions", "My contributions", f"""
<h2>What I built, extended and integrated</h2>
<p class="lede">Commit shares are from <code>git shortlog</code> on 2026-09-12. A
commit count is evidence of weight, not of line ownership, so every specific
claim names a file or a commit.</p>
{svg("12-my-contributions", figno="20",
     caption="Grouped by engineering responsibility, with an explicit list of "
             "what I did not build.")}
<p class="fine">The four-level authorship encoding is consistent across every
diagram here: a 2px accent border and a filled corner marker for what I
implemented, a thinner border and a hollow marker for what I extended, a
hairline for existing platform components, and a dashed hairline for external
systems. Use the authorship control in the header to dim everything that is not
primary work.</p>
""", interview=True)

    section("challenges", "Engineering challenges", """
<h2>Five problems worth describing</h2>
<p class="lede">Derived from commits, audit records and code comments. Each one
has a constraint, a decision, a trade-off, and a consequence that was actually
observed.</p>

<article class="case">
  <h3>A verification gate that was wrong in a way counting could not reveal</h3>
  <p><strong>Problem.</strong> ZPO passed <code>fidelity.source_substructure</code>
  cleanly and became the validation specimen for the evidence gates. BGB then
  reported every structural path three times.</p>
  <p><strong>Constraint.</strong> The gate had to hold for any German law, and a
  per-law exception would make the corpus unprovable as a whole: a rule that
  fires for one key cannot be validated by any other law's evidence.</p>
  <p><strong>Decision.</strong> Treat it as a defect in the gate, not in the
  data. ZPO's active version happens to carry a single evidence document; BGB
  carries three — one current and two superseded — and the gate pooled them.</p>
  <p><strong>Trade-off.</strong> Fixing the gate invalidated the confidence
  ZPO's pass had bought, and the rule became: audit each law's own structure
  read-only before re-ingesting it, and treat a count that matches another law's
  as a coincidence to verify rather than a baseline.</p>
  <p><strong>Consequence.</strong> Only running the gate against a second law
  exposed it. One specimen is not a test suite.</p>
</article>

<article class="case">
  <h3>Import sorting invalidated the provenance of the whole corpus</h3>
  <p><strong>Problem.</strong> A lint pass sorted the imports in three files.
  <code>parser_rule_sha256</code> moved from <code>38eb6f833d0ab5ab</code> to
  <code>b36ddd87ed592417</code>, with no behaviour change at all, and every
  stored generation's recorded ruleset stopped matching the installed one.</p>
  <p><strong>Constraint.</strong> The digest has to be exact to be worth
  anything. A provenance mechanism that tolerates “harmless” edits cannot tell
  you whether a stored law still reproduces.</p>
  <p><strong>Decision.</strong> Keep the digest byte-exact and disable
  <code>I001</code> for those three files, recording why in
  <code>pyproject.toml</code>.</p>
  <p><strong>Trade-off.</strong> Three files are now exempt from a
  project-wide lint rule, which is a real inconsistency, accepted because the
  alternative weakens the only mechanism that can detect rule drift.</p>
  <p><strong>Consequence.</strong> The registry is part of the rule set too. A
  code comment records the reason: adding one long form moved eight citations in
  the AktG work.</p>
</article>

<article class="case">
  <h3>Two stores, one snapshot, no distributed transaction</h3>
  <p><strong>Problem.</strong> A law's vectors and its graph have to agree with
  canonical PostgreSQL, and Kafka can redeliver any message at any time.</p>
  <p><strong>Constraint.</strong> No distributed transaction across a relational
  store, a vector store and a graph store — the operational cost is not worth
  paying for a corpus that is re-derivable.</p>
  <p><strong>Decision.</strong> Make every derived identifier a pure function of
  PostgreSQL content, read the law from one <code>REPEATABLE READ</code>
  snapshot, converge each store in a deliberate order, and fence each on an
  exact count before publishing completion.</p>
  <p><strong>Trade-off.</strong> A real window exists between the canonical
  commit and the projection fences where the stores disagree. It is short, it is
  reported honestly by reconciliation as <code>DRIFT_DETECTED</code>, and
  nothing serves a partial law while it is open.</p>
  <p><strong>Consequence.</strong> Redelivery became a non-event, which is what
  made the absence of automatic retry survivable.</p>
</article>

<article class="case">
  <h3>An endpoint that documented a measurement no code performed</h3>
  <p><strong>Problem.</strong> The health service's validation endpoints
  returned a job with <code>status="completed"</code> and the note “Live health
  check completed against actual corpus stores”. The handler queried nothing.</p>
  <p><strong>Constraint.</strong> At the time there was no way for that service
  to invoke the gates, which live in the preprocessor.</p>
  <p><strong>Decision.</strong> Delete the four endpoints and write down, in the
  API reference, that the documentation had asserted a measurement no
  implementation performed.</p>
  <p><strong>Trade-off.</strong> A visible capability was removed rather than
  quietly left in place, which looks like regression until you read why.</p>
  <p><strong>Consequence.</strong> <code>POST /laws/&#123;key&#125;/verify</code>
  replaced them once the gates could actually be invoked. A green result from a
  check that never ran is worse than no check.</p>
</article>

<article class="case">
  <h3>The running container was not the repository</h3>
  <p><strong>Problem.</strong> Withdrawal was complete in the repository, the
  docs and the tests — and un-exercisable against the running stack for every
  law. The overlay images are built once and not rebuilt when files change, so
  the preprocessor was missing a module entirely and the loader still served the
  pre-rename route.</p>
  <p><strong>Constraint.</strong> An absent route returns 404, and the health
  service maps a 404 from the canonical step to <code>NOT_FOUND</code> — “no
  such law”. The symptom therefore reads as a data problem about the law you
  named.</p>
  <p><strong>Decision.</strong> Verify the running image rather than the repo:
  diff the container's files, or read the live route table from
  <code>/openapi.json</code>, before concluding a feature works or is
  broken.</p>
  <p><strong>Trade-off.</strong> Rebuild discipline is now a written ADR and a
  boot-time check rather than a habit.</p>
  <p><strong>Consequence.</strong> The misdirection cost more than the bug. What
  is running is not automatically what is written.</p>
</article>
""", interview=True)

    section("decisions", "Design principles", """
<h2>What I would keep, and what I would change</h2>
<div class="grid-2">
  <div class="panel panel-keep">
    <h3>Keep</h3>
    <ul>
      <li><strong>One writer per store.</strong> It turns “which service made
      this row wrong?” into a question with exactly one answer.</li>
      <li><strong>Derive identity, never generate it.</strong> Idempotency for
      free, across stores, with no coordination.</li>
      <li><strong>Separate the observer from the judge.</strong> The health
      service records what the publisher served; the preprocessor's gate decides
      what that means. Neither can quietly do the other's job.</li>
      <li><strong>Refuse rather than approximate.</strong> Blocking a law with
      unrecognised structure, and refusing a law whose chunks would truncate,
      both cost throughput and both prevent a silent corruption.</li>
      <li><strong>Keep four trust answers apart.</strong> One green badge would
      hide which question failed.</li>
      <li><strong>Write the limitations into the artefact.</strong> Every
      diagram in the source repositories states what it cannot promise.</li>
    </ul>
  </div>
  <div class="panel panel-change">
    <h3>Change</h3>
    <ul>
      <li><strong>Add a dead-letter path to the legal pipeline.</strong> Today a
      permanently unprocessable law is redelivered for ever and blocks its
      partition. The document pipeline already has one.</li>
      <li><strong>Make the checker version impossible to forget.</strong> It
      failed to move once when a gate's semantics changed, so verdicts either
      side of that change are indistinguishable. Derive it from the gate
      implementations rather than maintaining it by hand.</li>
      <li><strong>Content-address the captures.</strong> Immutable by key is not
      immutable by policy: identical bytes submitted twice produce two objects,
      and an orphaned capture is possible because MinIO is written before
      Kafka.</li>
      <li><strong>Generate the gate list once.</strong> Three hand-maintained
      copies exist downstream; that is recorded as a known defect and it is the
      cause of the doc-versus-code drift found during this audit.</li>
      <li><strong>Build the FORMEX assurance contract.</strong> EU acts parse,
      ingest and are queryable, and none can be certified, because the
      pre-flight detectors are GII-shaped.</li>
      <li><strong>Re-own canonical deletion.</strong> A flag-gated purge path
      still contradicts the single-writer rule. It is recorded as debt rather
      than resolved by weakening the rule.</li>
    </ul>
  </div>
</div>
<p class="fine">Longer form, with context and alternatives for each:
<a href="ARCHITECTURE_DECISIONS.md">ARCHITECTURE_DECISIONS.md</a>.</p>
""", interview=True)

    section("evidence", "Evidence & scope", """
<h2>How this was assembled, and what it does not claim</h2>
<p class="lede">Twenty repositories were read before anything was drawn. Every
claim on this site is traceable to a file, and the ones that are not are labelled
as unverified rather than smoothed over.</p>
<div class="grid-2">
  <div class="panel">
    <h3>Verified in code</h3>
    <ul>
      <li>Service names, ports, topics, routes, gate identifiers, table and view
      names, collection and bucket names — all read from source or
      configuration.</li>
      <li>Store ownership, count fences, identity derivation, delivery ordering
      — read from the implementations.</li>
      <li>Commit shares — <code>git shortlog -sne</code> per repository.</li>
      <li>Corpus counts — the registry file and the generated certification
      ledger.</li>
    </ul>
  </div>
  <div class="panel">
    <h3>Not claimed</h3>
    <ul>
      <li><strong>No GDMS Rule Mapper.</strong> Asked for in the brief; no
      repository, topic, consumer, class, configuration or document for it exists
      anywhere in the workspace. Not drawn.</li>
      <li><strong>No production deployment.</strong> Only Docker Compose stacks
      and CI image builds are evidenced. “Production-oriented” is the accurate
      word.</li>
      <li><strong>No PaddleOCR, no DeepSeek-OCR, no Redis.</strong> None appears
      in any dependency, configuration or source file.</li>
      <li><strong>No business impact metrics.</strong> None exists in any
      repository, so none is stated.</li>
      <li><strong>No agentic RAG graph.</strong> A ten-node design exists in the
      architecture material; <code>langgraph</code> is commented out and the
      retrieval package is empty. Labelled design throughout.</li>
    </ul>
  </div>
</div>
<h3>Inconsistencies found between documentation and code</h3>
<ol class="findings">
  <li>The health service's API reference states there is no delete endpoint. The
  route exists at <code>app/api.py:585</code>, implemented by
  <code>app/withdrawal.py</code>, and is documented correctly in the
  architecture doc. The route was removed and later reintroduced; that section
  was not updated. <strong>This site follows the code.</strong></li>
  <li>The preprocessor README states 31 German laws and 51 in total. The registry
  holds 32 and 52 — <code>DDG</code> was added on 2026-09-03.</li>
  <li>The gate reference marks seven gates as EU-applicable, while
  <code>families/formex.py</code> implements four of the ones it excludes. The
  same file states checker version <code>:9</code> where the code says
  <code>:10</code>. Its own header names the cause: three hand-maintained copies
  of the gate list exist downstream.</li>
</ol>
<p class="fine">The method and the headline findings are in
<a href="docs/architecture/evidence-summary.md">evidence-summary.md</a>. The
full trail \u2014 ten documents naming exact file paths, per-repository
authorship and three documentation-versus-code discrepancies \u2014 is held
privately and available on request. No credential, internal hostname, endpoint
or client document appears anywhere in this published package.</p>
""")

    nav = "\n".join(
        f'<li><a href="#{sid}" data-nav="{sid}">{label}</a></li>'
        for sid, label, _ in SECTIONS)
    body = "\n".join(
        f'<section id="{sid}" class="sec'
        f'{" is-interview" if sid in INTERVIEW else ""}">{html}</section>'
        for sid, _, html in SECTIONS)
    steps = [sid for sid, _, _ in SECTIONS if sid in INTERVIEW]
    return PAGE.format(nav=nav, body=body, steps=",".join(f'"{s}"' for s in steps),
                       hero=HERO)


# ---------------------------------------------------------------------------
# The hero: the most characteristic artefact in this system's world is an
# evidence record, so that is what opens the page -- not a statistic.
# ---------------------------------------------------------------------------
HERO = """
<header class="hero" id="top">
  <div class="hero-copy">
    <p class="kicker">Mohd Zamin Quadri &nbsp;/&nbsp; AI Engineer &nbsp;/&nbsp;
      BP-ITCS</p>
    <h1>Turning published law<br>into knowledge you can<br>
      <em>check</em>.</h1>
    <p class="hero-sub">Production-oriented AI engineering across legal knowledge
      infrastructure, document intelligence, retrieval and data integrity. Five
      services take a statute from the body that publishes it to a queryable
      corpus that can prove what it contains — and refuse to serve what it
      cannot. I implemented four of them.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="#overview">Read the architecture</a>
      <button class="btn" id="interviewBtn" type="button">
        Interview walkthrough</button>
      <a class="btn btn-quiet" href="INTERVIEW_WALKTHROUGH.md">Talk track</a>
    </div>
  </div>

  <div class="hero-art" aria-label="An evidence record for one German statute"
       role="img">
    <div class="rec">
      <div class="rec-top">
        <span class="rec-law">BGB</span>
        <span class="rec-sec">&sect;&nbsp;312c</span>
        <span class="rec-badge">verified</span>
      </div>
      <dl class="rec-body">
        <dt>captured from</dt><dd>gesetze-im-internet.de</dd>
        <dt>raw sha-256</dt><dd class="mono">690acc15&hellip;1dc6fde</dd>
        <dt>parser rule</dt><dd class="mono">b36ddd87ed592417</dd>
        <dt>registry rule</dt><dd class="mono">a3f1b2c4&hellip;</dd>
        <dt>cites</dt><dd>&sect;&nbsp;312i BGB &middot; DDG</dd>
      </dl>
      <div class="rec-gates" id="gateRow">
        <span class="gh">14 gates</span>
        <span class="gates"></span>
      </div>
      <p class="rec-foot">Machine structural assurance. Not legal review.</p>
    </div>
  </div>
</header>
"""


PAGE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Engineering Systems &mdash; Mohd Zamin Quadri</title>
<meta name="description" content="Architecture portfolio: legal knowledge
infrastructure, document intelligence, retrieval and verification engineering at
BP-ITCS.">
<style>
/* ---------------------------------------------------------------- tokens */
:root {{
  --canvas:#070A0F; --canvas-alt:#0A0F16; --surface:#0E141C;
  --surface-2:#141C26; --hair:#1C2736; --grid:#16202C;
  --ink:#E8EEF6; --ink-mid:#9FB0C3; --ink-low:#667B91;
  --source:#A78BFA; --event:#22D3EE; --ai:#818CF8; --store:#F0B429;
  --trust:#34D399; --ui:#60A5FA; --warn:#F87171; --neutral:#7D8B9C;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",
          Georgia,"Times New Roman",serif;
  --sans:Inter,"Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,
         sans-serif;
  --mono:"JetBrains Mono","Cascadia Code",Consolas,"SF Mono",Menlo,monospace;
  --rail:288px; --measure:74ch;
}}
html[data-theme="light"] {{
  --canvas:#FBFCFD; --canvas-alt:#F3F6F9; --surface:#FFFFFF;
  --surface-2:#F7F9FB; --hair:#DCE4EC; --grid:#E7EDF3;
  --ink:#111820; --ink-mid:#42556A; --ink-low:#6A7D91;
  --source:#7C3AED; --event:#0891B2; --ai:#4F46E5; --store:#B45309;
  --trust:#047857; --ui:#1D4ED8; --warn:#B91C1C; --neutral:#556575;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
html,body {{ overflow-x:hidden; max-width:100%; }}
@media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} }}
body {{
  margin:0; background:var(--canvas); color:var(--ink); font-family:var(--sans);
  font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased;
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),
                   linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:40px 40px; background-attachment:fixed;
}}
body::before {{
  content:""; position:fixed; inset:0 0 auto 0; height:70vh; pointer-events:none;
  background:radial-gradient(80% 60% at 50% 0%,
    color-mix(in srgb,var(--ui) 9%,transparent),transparent 70%);
}}

/* ---------------------------------------------------------------- type */
h1,h2,h3 {{ font-family:var(--serif); font-weight:600; letter-spacing:-.012em; }}
h1 {{ font-size:clamp(1.95rem,5.4vw,4.5rem); line-height:1.04; margin:.1em 0 .5em;
     font-weight:500; }}
h1 em {{ font-style:italic; color:var(--trust); }}
h2 {{ font-size:clamp(1.7rem,2.6vw,2.35rem); line-height:1.15; margin:0 0 .55em; }}
h3 {{ font-size:1.17rem; line-height:1.3; margin:2.1em 0 .5em; font-weight:600; }}
p {{ max-width:min(var(--measure),100%); margin:0 0 1.05em; }}
.lede,.fine,li,figcaption {{ overflow-wrap:break-word; }}
.lede {{ font-size:1.14rem; color:var(--ink); max-width:66ch; }}
.fine {{ font-size:.855rem; color:var(--ink-low); max-width:80ch; }}
code,.mono {{ font-family:var(--mono); font-size:.875em;
  background:color-mix(in srgb,var(--ink) 7%,transparent);
  padding:.08em .34em; border-radius:4px; }}
.mono {{ background:none; padding:0; }}
a {{ color:var(--ui); text-decoration-color:color-mix(in srgb,var(--ui) 40%,transparent);
     text-underline-offset:.18em; }}
a:hover {{ text-decoration-color:var(--ui); }}
:focus-visible {{ outline:2px solid var(--ui); outline-offset:2px; border-radius:3px; }}

/* ---------------------------------------------------------------- chrome */
.topbar {{
  position:sticky; top:0; z-index:40; display:flex; gap:10px 14px;
  align-items:center; flex-wrap:wrap;
  padding:10px 26px; backdrop-filter:blur(14px);
  background:color-mix(in srgb,var(--canvas) 84%,transparent);
  border-bottom:1px solid var(--hair);
}}
.topbar .who {{ font-family:var(--serif); font-size:1.02rem; margin-right:auto; }}
.topbar .who span {{ color:var(--ink-low); font-family:var(--sans);
  font-size:.78rem; margin-left:.6em; }}
.ctl {{ font:inherit; font-size:.82rem; color:var(--ink-mid); cursor:pointer;
  background:var(--surface); border:1px solid var(--hair); border-radius:7px;
  padding:5px 11px; }}
.ctl:hover {{ color:var(--ink); border-color:color-mix(in srgb,var(--ui) 45%,var(--hair)); }}
.ctl[aria-pressed="true"] {{ color:var(--canvas); background:var(--trust);
  border-color:var(--trust); }}

.shell {{ display:grid;
  grid-template-columns:var(--rail) minmax(0,1fr);
  gap:0 44px; max-width:1680px; margin:0 auto; padding:0 26px 120px; }}
nav.rail {{ position:sticky; top:56px; align-self:start; height:max-content;
  padding:34px 0 0; }}
nav.rail ol {{ list-style:none; margin:0; padding:0; }}
nav.rail a {{ display:block; padding:6px 0 6px 14px; font-size:.875rem;
  color:var(--ink-low); text-decoration:none;
  border-left:2px solid var(--hair); }}
nav.rail a:hover {{ color:var(--ink); }}
nav.rail a[aria-current="true"] {{ color:var(--ink); border-left-color:var(--trust); }}
nav.rail .rail-foot {{ margin-top:22px; padding-left:14px; font-size:.78rem;
  color:var(--ink-low); border-left:2px solid transparent; }}
nav.rail .rail-note {{ margin-top:12px; padding-top:12px;
  border-top:1px solid var(--hair); font-size:.74rem; }}

/* ---------------------------------------------------------------- hero */
.hero {{ grid-column:1/-1; display:grid; grid-template-columns:1.06fr .94fr;
  gap:56px; align-items:center; padding:74px 0 64px; }}
.kicker {{ font-size:.8rem; color:var(--ink-low); margin:0; }}
.hero-sub {{ font-size:1.08rem; color:var(--ink-mid); max-width:60ch; }}
.hero-actions {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:26px; }}
.btn {{ font:inherit; font-size:.9rem; padding:10px 18px; border-radius:9px;
  border:1px solid var(--hair); background:var(--surface); color:var(--ink);
  cursor:pointer; text-decoration:none; }}
.btn:hover {{ border-color:color-mix(in srgb,var(--ui) 50%,var(--hair)); }}
.btn-primary {{ background:var(--trust); border-color:var(--trust);
  color:#04140C; font-weight:600; }}
.btn-quiet {{ background:none; color:var(--ink-mid); }}

.rec {{ border:1px solid color-mix(in srgb,var(--trust) 32%,var(--hair));
  border-radius:14px; background:var(--surface); padding:22px 24px 18px;
  box-shadow:0 0 0 1px color-mix(in srgb,var(--trust) 8%,transparent),
             0 30px 70px -40px #000; }}
.rec-top {{ display:flex; align-items:baseline; gap:12px;
  padding-bottom:14px; border-bottom:1px solid var(--hair); }}
.rec-law {{ font-family:var(--serif); font-size:1.5rem; }}
.rec-sec {{ font-family:var(--mono); font-size:1rem; color:var(--ink-mid); }}
.rec-badge {{ margin-left:auto; font-size:.72rem; letter-spacing:.06em;
  text-transform:uppercase; color:var(--trust);
  border:1px solid color-mix(in srgb,var(--trust) 45%,transparent);
  border-radius:999px; padding:3px 10px; }}
.rec-body {{ display:grid; grid-template-columns:12.5ch 1fr; gap:7px 16px;
  margin:16px 0 18px; font-size:.845rem; }}
.rec-body dt {{ color:var(--ink-low); }}
.rec-body dd {{ margin:0; color:var(--ink-mid); overflow-wrap:anywhere; }}
.rec-gates {{ display:flex; align-items:center; gap:12px; }}
.gh {{ font-size:.78rem; color:var(--ink-low); }}
.gates {{ display:flex; gap:5px; flex-wrap:wrap; }}
.gates i {{ width:13px; height:16px; display:block; opacity:0;
  background:color-mix(in srgb,var(--trust) 70%,transparent);
  clip-path:polygon(50% 0,100% 22%,100% 62%,50% 100%,0 62%,0 22%); }}
.gates i.on {{ opacity:1; }}
.gates i.na {{ background:color-mix(in srgb,var(--ink-low) 55%,transparent); }}
@media (prefers-reduced-motion:no-preference) {{
  .gates i {{ transition:opacity .22s ease; }}
}}
.rec-foot {{ margin:14px 0 0; font-size:.78rem; color:var(--ink-low); }}

/* ---------------------------------------------------------------- sections */
.sec {{ padding:58px 0; border-top:1px solid var(--hair); }}
.sec:first-of-type {{ border-top:0; }}
.fig {{ margin:30px 0 8px; }}
.fig-frame {{ position:relative; overflow:hidden; cursor:grab;
  border:1px solid var(--hair); border-radius:12px; background:var(--canvas);
  max-height:min(76vh,900px); }}
.fig-frame.dragging {{ cursor:grabbing; }}
.fig-stage {{ transform-origin:0 0; }}
.fig-stage svg {{ display:block; width:100%; height:auto; }}
figcaption {{ margin-top:10px; font-size:.85rem; color:var(--ink-low);
  max-width:none; display:flex; flex-wrap:wrap; gap:0 .7em;
  align-items:baseline; }}
.fig-no {{ font-family:var(--mono); color:var(--trust); margin-right:.7em; }}
.fig-open {{ font-size:.82rem; white-space:nowrap; }}
.missing {{ color:var(--warn); font-family:var(--mono); font-size:.85rem; }}

.grid-2 {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px;
  margin:22px 0; }}
.grid-3 {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:22px;
  margin:26px 0; }}
.stat {{ border-left:2px solid var(--trust); padding:2px 0 2px 16px; }}
.stat-n {{ font-family:var(--serif); font-size:2.5rem; line-height:1; margin:0; }}
.stat-l {{ font-size:.86rem; color:var(--ink-mid); margin:.5em 0 0; max-width:34ch; }}
.panel {{ border:1px solid var(--hair); border-radius:12px; padding:20px 22px;
  background:var(--surface); }}
.panel h3 {{ margin-top:0; }}
.panel ul {{ margin:0; padding-left:1.15em; }}
.panel li {{ margin-bottom:.62em; color:var(--ink-mid); font-size:.925rem; }}
.panel li strong {{ color:var(--ink); font-weight:600; }}
.panel-keep {{ border-color:color-mix(in srgb,var(--trust) 30%,var(--hair)); }}
.panel-change {{ border-color:color-mix(in srgb,var(--store) 30%,var(--hair)); }}
.case {{ border-left:2px solid var(--hair); padding:2px 0 2px 20px;
  margin:26px 0; max-width:86ch; }}
.case h3 {{ margin-top:0; }}
.case p {{ font-size:.945rem; color:var(--ink-mid); margin-bottom:.7em; }}
.case strong {{ color:var(--ink); }}
.findings {{ max-width:86ch; color:var(--ink-mid); font-size:.93rem;
  padding-left:1.3em; }}
.findings li {{ margin-bottom:.75em; }}

/* -------------------------------------------------- authorship overlay */
body.own-only .fig svg g[data-level="integrated"],
body.own-only .fig svg g[data-level="external"] {{ opacity:.24; }}
body.own-only .fig svg g[data-level="extended"] {{ opacity:.62; }}

/* -------------------------------------------------- interview mode */
body.interview .sec:not(.is-interview) {{ display:none; }}
body.interview nav.rail a:not(.iv) {{ opacity:.3; pointer-events:none; }}
.ivbar {{ display:none; }}
body.interview .ivbar {{ display:flex; gap:12px; align-items:center;
  grid-column:1/-1; margin:0 0 6px; padding:12px 16px; border-radius:10px;
  background:var(--surface); border:1px solid
  color-mix(in srgb,var(--trust) 30%,var(--hair)); }}
.ivbar p {{ margin:0; font-size:.88rem; color:var(--ink-mid); max-width:none; }}
.ivbar .spacer {{ margin-left:auto; }}

/* -------------------------------------------------- print / export */
@media print {{
  :root {{ --canvas:#fff; --canvas-alt:#fff; --surface:#fff; --surface-2:#fff;
    --hair:#bbb; --grid:transparent; --ink:#000; --ink-mid:#333;
    --ink-low:#555; }}
  body {{ background:#fff !important; background-image:none !important; }}
  body::before {{ display:none; }}
  .topbar, nav.rail, .ivbar, .hero-actions, .fig-open {{ display:none !important; }}
  .shell {{ display:block; padding:0; max-width:none; }}
  .sec {{ break-inside:avoid; padding:20px 0; }}
  .fig-frame {{ max-height:none; overflow:visible; border-color:#bbb; }}
  .fig-stage {{ transform:none !important; min-width:0; }}
  .fig, .panel, .case, .stat {{ break-inside:avoid; }}
  h2, h3 {{ break-after:avoid; }}
  a[href^="http"]::after {{ content:" (" attr(href) ")"; font-size:.8em;
    color:#555; }}
}}

/* -------------------------------------------------- responsive */
main {{ min-width:0; }}

@media (max-width:1180px) {{
  .shell {{ grid-template-columns:minmax(0,1fr); }}
  nav.rail {{ position:static; padding-top:18px; }}
  nav.rail ol {{ display:flex; flex-wrap:wrap; gap:2px 6px; min-width:0; }}
  nav.rail a {{ border-left:0; border-bottom:2px solid var(--hair);
    padding:5px 9px; }}
  .hero {{ grid-template-columns:1fr; gap:34px; padding:44px 0 40px; }}
}}
@media (max-width:820px) {{
  .grid-2,.grid-3 {{ grid-template-columns:1fr; }}
  .shell {{ padding:0 16px 80px; }}
  .topbar {{ padding:9px 16px; }}
  .fig-frame {{ overflow-x:auto; max-height:none; }}
  .fig-stage {{ min-width:900px; }}
  .rec-body {{ grid-template-columns:1fr; gap:2px 0; }}
  .rec-body dt {{ margin-top:8px; }}
}}
</style>
</head>
<body>

<div class="topbar">
  <p class="who">Mohd Zamin Quadri<span>AI Engineer, BP-ITCS</span></p>
  <button class="ctl" id="ownBtn" type="button" aria-pressed="false">
    Highlight my work</button>
  <button class="ctl" id="themeBtn" type="button">Light</button>
</div>

<div class="shell">
{hero}

  <nav class="rail" aria-label="Sections">
    <ol>{nav}</ol>
    <p class="rail-foot">Twenty repositories inspected. Every claim traceable to
      a file.</p>
    <p class="rail-foot rail-note">Personal portfolio by Mohd Zamin Quadri.
      Architecture case studies based on systems I contributed to at BP-ITCS.
      Not official BP-ITCS documentation; internal implementation details are
      generalised or omitted.</p>
  </nav>

  <main>
    <div class="ivbar" role="status">
      <p><strong id="ivStep">Step 1 of 8</strong> &nbsp;
        <span id="ivHint">Start with the landscape: two workstreams, one
        platform.</span></p>
      <span class="spacer"></span>
      <button class="ctl" id="ivPrev" type="button">Previous</button>
      <button class="ctl" id="ivNext" type="button">Next</button>
      <button class="ctl" id="ivExit" type="button">Exit</button>
    </div>
{body}
  </main>
</div>

<script>
/* ---- one orchestrated moment: the gate row fills once, left to right ---- */
(function () {{
  var row = document.querySelector('#gateRow .gates');
  if (!row) return;
  var kinds = ['on','on','on','on','on','on','on','on','on','on','on','on',
               'na','na'];
  kinds.forEach(function (k, i) {{
    var el = document.createElement('i');
    el.title = k === 'na' ? 'not applicable to this source family'
                          : 'gate passed';
    row.appendChild(el);
    var reduce = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
    if (reduce) {{ el.classList.add(k); return; }}
    setTimeout(function () {{ el.classList.add(k); }}, 380 + i * 58);
  }});
}})();

/* ---- theme ---- */
(function () {{
  var btn = document.getElementById('themeBtn');
  var root = document.documentElement;
  var saved = null;
  try {{ saved = localStorage.getItem('zq-theme'); }} catch (e) {{}}
  if (saved) root.setAttribute('data-theme', saved);
  function sync() {{
    btn.textContent = root.getAttribute('data-theme') === 'dark'
      ? 'Light' : 'Dark';
  }}
  sync();
  btn.addEventListener('click', function () {{
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try {{ localStorage.setItem('zq-theme', next); }} catch (e) {{}}
    sync();
  }});
}})();

/* ---- authorship overlay: a CSS rule over data-level, not second artwork ---- */
(function () {{
  var btn = document.getElementById('ownBtn');
  btn.addEventListener('click', function () {{
    var on = document.body.classList.toggle('own-only');
    btn.setAttribute('aria-pressed', String(on));
    btn.textContent = on ? 'Showing my work' : 'Highlight my work';
  }});
}})();

/* ---- figure zoom and pan ---- */
document.querySelectorAll('.fig-frame').forEach(function (frame) {{
  var stage = frame.querySelector('.fig-stage');
  var z = 1, x = 0, y = 0, dragging = false, px = 0, py = 0;
  function apply() {{
    stage.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + z + ')';
  }}
  frame.addEventListener('wheel', function (e) {{
    if (!e.ctrlKey && Math.abs(e.deltaY) < 1) return;
    e.preventDefault();
    var prev = z;
    z = Math.min(6, Math.max(1, z * (e.deltaY < 0 ? 1.12 : 0.89)));
    var r = frame.getBoundingClientRect();
    var cx = e.clientX - r.left, cy = e.clientY - r.top;
    x = cx - (cx - x) * (z / prev);
    y = cy - (cy - y) * (z / prev);
    if (z === 1) {{ x = 0; y = 0; }}
    apply();
  }}, {{ passive: false }});
  frame.addEventListener('pointerdown', function (e) {{
    if (z === 1) return;
    dragging = true; px = e.clientX; py = e.clientY;
    frame.classList.add('dragging'); frame.setPointerCapture(e.pointerId);
  }});
  frame.addEventListener('pointermove', function (e) {{
    if (!dragging) return;
    x += e.clientX - px; y += e.clientY - py; px = e.clientX; py = e.clientY;
    apply();
  }});
  frame.addEventListener('pointerup', function () {{
    dragging = false; frame.classList.remove('dragging');
  }});
  frame.addEventListener('dblclick', function () {{
    z = 1; x = 0; y = 0; apply();
  }});
  frame.addEventListener('keydown', function (e) {{
    if (e.key === '+' || e.key === '=') {{ z = Math.min(6, z * 1.2); apply(); }}
    if (e.key === '-') {{ z = Math.max(1, z / 1.2); if (z === 1) {{ x = 0; y = 0; }} apply(); }}
    if (e.key === '0') {{ z = 1; x = 0; y = 0; apply(); }}
  }});
}});

/* ---- which section am I in ---- */
(function () {{
  var links = [].slice.call(document.querySelectorAll('nav.rail a'));
  var byId = {{}};
  links.forEach(function (a) {{ byId[a.getAttribute('data-nav')] = a; }});
  var obs = new IntersectionObserver(function (entries) {{
    entries.forEach(function (en) {{
      if (!en.isIntersecting) return;
      links.forEach(function (a) {{ a.removeAttribute('aria-current'); }});
      var a = byId[en.target.id];
      if (a) a.setAttribute('aria-current', 'true');
    }});
  }}, {{ rootMargin: '-20% 0px -70% 0px' }});
  document.querySelectorAll('section.sec').forEach(function (s) {{
    obs.observe(s);
  }});
}})();

/* ---- interview walkthrough: a guided sequence, not a filter ---- */
(function () {{
  var steps = [{steps}];
  var hints = {{
    'overview': 'Two workstreams on one platform. Four of the five legal '
              + 'services are mine.',
    'legal': 'Five services: a three-stage ingestion pipeline plus a '
         + 'two-part control plane. One writer per store.',
    'journey': 'One law end to end. Note what happens before the parser runs.',
    'storage': 'Why four stores, and how they stay in step without a '
             + 'distributed transaction.',
    'trust': 'The part to spend the most time on: fourteen gates, four '
           + 'separate answers.',
    'query': 'Query time is separate from ingestion time, on purpose.',
    'contributions': 'What I built, what I extended, and what I did not.',
    'challenges': 'Pick one problem and go deep. The gate defect is the best '
                + 'one.',
    'radiology': 'Prototype, not a device. Five findings, five thresholds, '
               + 'then the prior you switched off.',
    'compliance': 'This is what the corpus is for. Be clear the product is '
                + 'not your code.',
    'decisions': 'Close on what you would change. Have the dead-letter answer '
               + 'ready.'
  }};
  var i = 0;
  var bar = {{
    step: document.getElementById('ivStep'),
    hint: document.getElementById('ivHint')
  }};
  function show() {{
    var id = steps[i];
    bar.step.textContent = 'Step ' + (i + 1) + ' of ' + steps.length;
    bar.hint.textContent = hints[id] || '';
    document.querySelectorAll('nav.rail a').forEach(function (a) {{
      a.classList.toggle('iv', steps.indexOf(a.getAttribute('data-nav')) > -1);
    }});
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({{ block: 'start' }});
  }}
  function enter() {{
    document.body.classList.add('interview');
    document.getElementById('interviewBtn').textContent = 'In walkthrough';
    i = 0; show();
  }}
  function exit() {{
    document.body.classList.remove('interview');
    document.getElementById('interviewBtn').textContent =
      'Interview walkthrough';
    document.querySelectorAll('nav.rail a').forEach(function (a) {{
      a.classList.remove('iv');
    }});
  }}
  document.getElementById('interviewBtn').addEventListener('click', function () {{
    document.body.classList.contains('interview') ? exit() : enter();
  }});
  document.getElementById('ivNext').addEventListener('click', function () {{
    i = Math.min(steps.length - 1, i + 1); show();
  }});
  document.getElementById('ivPrev').addEventListener('click', function () {{
    i = Math.max(0, i - 1); show();
  }});
  document.getElementById('ivExit').addEventListener('click', exit);
  document.addEventListener('keydown', function (e) {{
    if (!document.body.classList.contains('interview')) return;
    if (e.key === 'ArrowRight') {{ i = Math.min(steps.length - 1, i + 1); show(); }}
    if (e.key === 'ArrowLeft') {{ i = Math.max(0, i - 1); show(); }}
    if (e.key === 'Escape') exit();
  }});
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    out = ROOT / "index.html"
    out.write_text(build(), encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"wrote {out.relative_to(ROOT)}  {kb:,.0f} KB  "
          f"{len(SECTIONS)} sections, {len(INTERVIEW)} in the walkthrough")
