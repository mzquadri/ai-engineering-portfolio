"""Diagrams 20-21: the local environment, and one assessment end to end.

Two views the rest of the set does not carry.

Diagram 20 is the only deployment view in the pack. Every other diagram is
logical -- responsibilities, stores, trust -- and none of them answers "what
actually runs, on which port, built from which repository". The figures come
from the service and port inventory and the single-writer table:

  docs/architecture/architecture-notes.md  sections 1, 2, 9, 12
  ARCHITECTURE_DECISIONS.md                decisions 2, 3, 5; ADR-003, ADR-004

Diagram 21 joins two halves that are drawn separately and never meet on one
canvas: 19-ai-compliance stops at the knowledge processor, and 07-rag-query-flow
begins at an already-formed query. The join is the thing worth seeing, because
it is where a customer-facing report acquires its dependency on a verified
corpus.

  docs/architecture/architecture-notes.md  section 11, section 5
  assets/architecture/07-rag-query-flow.svg
  assets/architecture/19-ai-compliance.svg

Both diagrams follow the same rule as the rest of the pack: a component is
drawn solid only if a file in the inspected workspace evidences it. Components
recorded as absent are drawn dashed and labelled, never omitted silently and
never implied to exist.
"""

from __future__ import annotations

import design_tokens as T
from svg_kit import (Box, Canvas, card, edge, lane_around, matrix, note, pill,
                     store, text_el, write)

OUT = "assets/architecture"

# Service, repository, stack and host port, read from architecture-notes.md
# section 1.
#
# The repository column carries only names that appear in the evidence pack --
# seven of eleven. The other four services are named in the service inventory
# but their repository names are not published anywhere in this portfolio, so
# the cell is a dash. A dash means "not in evidence", never "does not exist",
# and the footnote says so. Inferring `document-extractor` from "Document
# Extractor" would have been a guess set in mono, and mono in this pack means
# copied verbatim from source.
#
# A dash in the port column means the service publishes no host port in the
# compose environment: it is reachable only over the compose network, or only
# by Kafka.
REPOS = [
    ("Entity Producer", "—", "Java · Spring Boot", ":4675", "neutral"),
    ("Ingestion Preprocessor", "knowledge-db-ingestion-preprocessor",
     "Python · FastAPI", ":4698", "ai"),
    ("Ingestion Loader", "knowledge-db-ingestion-loader",
     "Python · FastAPI", ":4710-4711", "ai"),
    ("Legal KB Health Service", "legal-kb-health-service",
     "Python · FastAPI", ":8000", "ui"),
    ("Legal KB Dashboard", "legal-kb-dashboard",
     "TypeScript · Next.js 16", ":3000", "ui"),
    ("Shared library", "ai-utils", "Python · imported by the services",
     "—", "neutral"),
    ("The environment itself", "local-env", "Docker Compose · YAML",
     "—", "event"),
]

# The other workstreams. They run in the same Compose environment and share
# the broker, but none of them is part of the Legal Knowledge Database, so
# they appear once as a single muted row rather than as service cards --
# otherwise this diagram stops being a view of one system.
OTHER_WORKSTREAMS = (
    "Document Extractor · Indexing Service · RAG Service · "
    "AI Prediction Service · Docling Serve :5001"
)

# architecture-notes.md section 2, verbatim. Drawn as a table rather than as
# arrows because six ownership edges across a store row would have to cross
# each other, and the design system forbids an arrow crossing a node.
WRITERS = [
    ("PostgreSQL — corpus tables", "Ingestion Preprocessor", "search by meaning"),
    ("PostgreSQL — currency, snapshots, audit", "Health Service", "—"),
    ("Qdrant", "Ingestion Loader", "follow a citation chain"),
    ("Neo4j", "Ingestion Loader", "search by meaning"),
    ("MinIO — captures", "Entity Producer", "be queried at all"),
    ("MinIO — archive mirror / evidence", "Ingestion Preprocessor", "—"),
]


# ===========================================================================
# 20 - The local environment
# ===========================================================================
def d20_runtime() -> None:
    c = Canvas(1920, 2600,
               eyebrow="Runtime · the Legal Knowledge Database",
               title="Repositories, images and the stack that actually runs",
               subtitle="The only deployment view in this pack, scoped to the "
                        "Legal Knowledge Database: five services, one Docker "
                        "Compose environment on a lab host, and four stores "
                        "behind a single-writer rule. No production "
                        "deployment is claimed anywhere.")
    c.background()
    y0 = c.header()
    c.byline()

    # ------------------------------------------------------------------ repos
    ry = y0 + 36
    c.add(text_el("SOURCE · FIVE SERVICES, A SHARED LIBRARY, AND THE "
                  "ENVIRONMENT ITSELF",
                  T.SAFE, ry, "lane", T.ROLE["ui"]))
    ry += 18
    repo_m = matrix(c, T.SAFE, ry,
                    ["Service", "Repository, where evidenced", "Stack",
                     "Host port"],
                    [[svc, repo, stack, port]
                     for svc, repo, stack, port, _ in REPOS],
                    widths=[300, 420, 300, 160], rowh=30,
                    mono_cols={1, 3},
                    accents=[a for *_, a in REPOS],
                    label="matrix:repositories")

    nx = T.SAFE + 1180 + 40
    nw = c.width - T.SAFE - nx
    rn = note(c, nx, ry + 6, nw,
              ["Four of these are mine end to end: the preprocessor, the "
               "loader, the health service and the dashboard. The entity "
               "producer existed before legal ingestion and I extended it for "
               "EU sources.",
               "The dashboard owning nothing is a design position, not an "
               "omission. It ships with no database, queue or object-store "
               "client at all, so there is no code path by which the operator "
               "surface could write the corpus it reports on."],
              accent="ui", title="Whose repositories these are")
    note(c, nx, rn.bottom + 20, nw,
         ["local-env is the repository that makes the others runnable: the "
          "Compose files, the service YAML and the pinned dependency set.",
          "It is the answer to “where does the environment live” — "
          "the environment is itself a versioned repository rather than a "
          "document describing one."],
         accent="event", title="The environment is a repository")

    # ------------------------------------------------------------------ build
    by = repo_m.bottom + 66
    bw = (c.width - 2 * T.SAFE - 2 * 44) / 3
    b1 = card(c, Box(T.SAFE, by, bw), "Images built in CI",
              role="neutral", level="integrated", icon="service",
              subtitle="Each service image is built by CI and run from Docker "
                       "Compose on a lab host. There is no production "
                       "deployment and none is claimed.",
              meta=["docker compose · CI-built images"])
    b2 = card(c, Box(T.SAFE + bw + 44, by, bw),
              "ADR-003 · rebuild discipline",
              role="warn", level="integrated", icon="alert",
              subtitle="Written after the local overlay images were found "
                       "running code that predated completed work — while "
                       "the repository, the docs and the tests all said "
                       "otherwise.",
              meta=["the failure that looked like success"])
    b3 = card(c, Box(T.SAFE + 2 * (bw + 44), by, bw),
              "ADR-004 · editable install + boot check",
              role="trust", level="integrated", icon="shield",
              subtitle="Supersedes ADR-003. The package is installed editable "
                       "and a boot-time check runs, so a drifted container "
                       "fails at startup instead of serving a route table "
                       "nobody expected.",
              meta=["fail at boot, not at request time"])
    for a, b in ((b1, b2), (b2, b3)):
        edge(c, a, b, kind="sync", role="warn", gap=5)
    lane_around(c, [b1, b2, b3],
                "Build · how dependencies reach a container",
                caption="two ADRs, the second replacing the first",
                accent="warn")

    # ---------------------------------------------------------------- runtime
    sy = max(b1.bottom, b2.bottom, b3.bottom) + 78
    sgap = 26.0
    sw = (c.width - 2 * T.SAFE - 4 * sgap) / 5
    sx = [T.SAFE + i * (sw + sgap) for i in range(5)]

    s_ep = card(c, Box(sx[0], sy, sw), "Entity Producer",
                role="neutral", level="extended", icon="service",
                subtitle="Polls the publishers, captures the bytes, announces "
                         "the capture",
                meta=[":4675 · java"])
    s_pp = card(c, Box(sx[1], sy, sw), "Ingestion Preprocessor",
                role="ai", level="primary", icon="brain",
                subtitle="Parses GII-NORM and FORMEX, writes canonical state, "
                         "then runs the gates",
                meta=[":4698 · python"])
    # Kept to two wrapped lines so it matches the preprocessor's height: an
    # edge between cards of different heights routes with a visible jog.
    s_ld = card(c, Box(sx[2], sy, sw), "Ingestion Loader",
                role="ai", level="primary", icon="bolt",
                subtitle="Embeds and projects into the vector and graph "
                         "stores — built to scale",
                meta=[":4710-4711 · port range"])
    s_hs = card(c, Box(sx[3], sy, sw), "Health Service",
                role="ui", level="primary", icon="service",
                subtitle="Currency, snapshots and the audit log. Judges "
                         "freshness evidence; never fetches it.",
                meta=[":8000 · python"])
    s_db = card(c, Box(sx[4], sy, sw), "Operator Dashboard",
                role="ui", level="primary", icon="ui",
                subtitle="Re-ingest, verify, reconcile and withdraw from one "
                         "narrow control plane. Writes nothing.",
                meta=[":3000 · next.js 16"])
    legal_kb = [s_ep, s_pp, s_ld, s_hs, s_db]
    edge(c, s_ep, s_pp, kind="async", role="event", gap=5)
    edge(c, s_pp, s_ld, kind="async", role="event", gap=5)
    edge(c, s_hs, s_db, kind="sync", role="ui", gap=5)

    # The other workstreams share this environment and this broker, but they
    # are not the Legal Knowledge Database. One muted row keeps the deployment
    # view honest without letting four unrelated services dilute the subject.
    s_other = card(c, Box(T.SAFE, max(b.bottom for b in legal_kb) + 30,
                          c.width - 2 * T.SAFE),
                   "Other workstreams · same environment, same broker",
                   role="neutral", level="integrated", icon="service",
                   subtitle="Document intelligence and the medical-imaging "
                            "prototype run beside the Legal Knowledge "
                            "Database and share the Compose network, but "
                            "none of them is part of it. They are drawn here "
                            "once, as context, and nowhere else on this page.",
                   meta=[OTHER_WORKSTREAMS])

    lane_around(c, legal_kb + [s_other],
                "Runtime · docker compose, five host ports",
                caption="compose network · one lab host", accent="ui")

    # -------------------------------------------------------------- transport
    ty = s_other.bottom + 60
    c.add(text_el("TRANSPORT · FIVE OF THE TEN TOPICS, ACROSS TWO PIPELINES",
                  T.SAFE, ty, "lane", T.ROLE["event"]))
    ty += 20
    p1 = pill(c, T.SAFE, ty, "legal.knowledge.database.questionnaire.structured")
    p2 = pill(c, p1.right + 22, ty, "law.embedded")
    p3 = pill(c, p2.right + 22, ty, "ibp.events.inbound")
    p4 = pill(c, T.SAFE, ty + 40, "ibp.events.ai.processed")
    p5 = pill(c, p4.right + 22, ty + 40, "ibp.events.document.indexed.dlq")

    # The note clears BOTH pill rows, not just the second one. Measuring
    # against p5 alone put it underneath the row-one pills.
    tnx = max(p3.right, p5.right) + 46
    tn = note(c, tnx, ty - 8, c.width - T.SAFE - tnx,
              ["Ingestion has no REST trigger. First ingest, re-ingest and "
               "replay are the same code path, so the recovery path is "
               "exercised daily rather than on the day it is needed."],
              accent="event", title="Why there is no ingest endpoint")

    # ------------------------------------------------------------ persistence
    qy = max(p5.bottom, tn.bottom) + 70
    stw = (c.width - 2 * T.SAFE - 3 * 40) / 4
    k_pg = store(c, Box(T.SAFE, qy, stw), "PostgreSQL",
                 kind="relational", level="primary",
                 subtitle="Canonical legal state, source evidence, assurance "
                          "and currency — four concerns, one database",
                 meta=["cannot: search by meaning"])
    k_qd = store(c, Box(T.SAFE + stw + 40, qy, stw), "Qdrant",
                 kind="vector", level="primary",
                 subtitle="Dense and sparse vectors in one collection, fused "
                          "server-side at query time",
                 meta=["point id = uuid5(ns, chunk_id)"])
    k_n4 = store(c, Box(T.SAFE + 2 * (stw + 40), qy, stw), "Neo4j",
                 kind="graph", level="primary",
                 subtitle="The provision reference graph — what each "
                          "provision cites, across statutes",
                 meta=["MERGE by id · REFERS_TO · CITES_LAW"])
    k_mo = store(c, Box(T.SAFE + 3 * (stw + 40), qy, stw), "MinIO",
                 kind="bucket", level="extended",
                 subtitle="The publisher's bytes, hashed before anything "
                          "parses them, plus an object-locked evidence bucket",
                 meta=["{eventId}/{filename} · SHA-256"])
    lane_around(c, [k_pg, k_qd, k_n4, k_mo],
                "Persistence · three databases and one object store",
                caption="each present because the others cannot do its job",
                accent="store")

    # ------------------------------------------------------- the writer table
    wy = max(k_pg.bottom, k_qd.bottom, k_n4.bottom, k_mo.bottom) + 54
    c.add(text_el("THE SINGLE-WRITER RULE · ONE ANSWER TO “WHICH "
                  "SERVICE WROTE THIS?”",
                  T.SAFE, wy, "lane", T.ROLE["trust"]))
    wy += 18
    wm = matrix(c, T.SAFE, wy,
                ["Store", "Sole writer", "What it cannot do"],
                [[s, w, cannot] for s, w, cannot in WRITERS],
                widths=[420, 330, 330], rowh=30, accents=["store"] * 6,
                label="matrix:writers")

    wn = note(c, T.SAFE + 1080 + 40, wy + 6,
              c.width - T.SAFE - (T.SAFE + 1080 + 40),
              ["The rule was arrived at by removing a violation, not by "
               "agreeing to one. An earlier loader deleted canonical rows and "
               "could never have worked: currency_observations references "
               "laws with ON DELETE RESTRICT and is append-only, so the "
               "delete was refused every time — after Qdrant and Neo4j had "
               "already been cleared and committed.",
               "The resolution was to delete the code path, not to relax the "
               "constraint. One flag-gated purge path survives in the loader, "
               "recorded as debt; nothing calls it."],
              accent="trust", title="How the rule was arrived at")

    # ---------------------------------------------------------- what is absent
    ay = max(wm.bottom, wn.bottom) + 66
    aw = (c.width - 2 * T.SAFE - 2 * 40) / 3
    a1 = card(c, Box(T.SAFE, ay, aw), "No dead-letter topic · legal pipeline",
              role="warn", level="external", icon="alert",
              subtitle="A permanently unprocessable law is redelivered for "
                       "ever and blocks its partition until a human "
                       "intervenes. The document pipeline has a DLQ; the "
                       "legal one does not.",
              meta=["the clearest gap in the pipeline"])
    a2 = card(c, Box(T.SAFE + aw + 40, ay, aw),
              "No monitoring plane in the delivered stack",
              role="warn", level="external", icon="alert",
              subtitle="Prometheus and Alertmanager rules were written and "
                       "promtool-tested, then withdrawn. Nothing in the "
                       "running stack scrapes or alerts.",
              meta=["built, tested, withdrawn"])
    a3 = card(c, Box(T.SAFE + 2 * (aw + 40), ay, aw),
              "No agentic retrieval graph",
              role="warn", level="external", icon="alert",
              subtitle="A ten-node design exists in the architecture "
                       "material. langgraph is commented out and the "
                       "retrieval package is empty.",
              meta=["designed, not implemented"])
    lane_around(c, [a1, a2, a3],
                "Drawn because it is absent · recorded in the repository",
                caption="dashed, so it can never read as delivered",
                accent="warn")

    c.fit(max(a1.bottom, a2.bottom, a3.bottom) + 14, footnote=dict(
        lines=["Nothing here is a production topology. The stack runs from "
               "Docker Compose with CI-built images on a lab host, which is "
               "why the ports are host ports and why the loader is the only "
               "service publishing a range rather than a single one.",
               "Every port, language and ownership claim on this page is read "
               "from the service inventory and the single-writer table in "
               "docs/architecture/architecture-notes.md. Where a store is "
               "written by two services, both rows appear — the rule is "
               "one writer per concern, not one writer per database.",
               "A dash in the repository column means the repository name is "
               "not published anywhere in this portfolio — not that the "
               "service has no repository. The entity producer is in that "
               "position, and guessing a plausible name for it would have "
               "put an invented identifier in a column set in mono, which in "
               "this pack means copied verbatim from source."],
        accent="store", title="What this diagram does and does not claim"),
        legend_spec=dict(
            roles=["event", "ai", "store", "trust", "ui", "warn", "neutral"],
            flows=["sync", "async"],
            levels=["primary", "extended", "integrated", "external"]))
    write(c, f"{OUT}/20-local-environment.svg")


# ===========================================================================
# 21 - The Legal Knowledge Database, as two pipelines
# ===========================================================================
# The gate inventory of section 5, grouped by the question each group answers
# rather than listed flat -- diagram 06 already lists all fourteen. The DE/EU
# column follows the code, not the repository's gate reference, which marks
# fewer gates EU-applicable than formex.py actually implements.
GATE_GROUPS = [
    ("Structural fidelity",
     "Was the law's structure read completely, and does the stored text match "
     "the source?",
     "structure.section_inventory", "DE · EU"),
    ("Citation correctness",
     "Were the references extracted, down to provision level, and all of them?",
     "fidelity.citation_completeness", "DE · EU"),
    ("Cross-store equality",
     "Do the vector payloads and the graph match the canonical rows for this "
     "generation?",
     "fidelity.qdrant_payload", "DE · EU"),
    ("Source currency",
     "Is this still what the publisher is serving today?",
     "currency.source_state", "DE · EU"),
    ("Provenance",
     "Was it produced under the rule set recorded with it?",
     "provenance.pipeline_profile", "DE · EU"),
    ("Byte partition",
     "Is every byte of the source markup accounted for?",
     "fidelity.xml_byte_partition", "DE only"),
]


def d21_legal_kb_pipelines() -> None:
    c = Canvas(1920, 2400,
               eyebrow="Legal Knowledge Database · the whole system",
               title="Two pipelines over one corpus",
               subtitle="Pipeline A ingests the law, proves it, and stores it. "
                        "Pipeline B answers questions from it. A writes every "
                        "store; B writes none — which is why a retrieval bug "
                        "cannot corrupt the corpus, and why a question cannot "
                        "trigger a re-ingest.")
    c.background()
    y0 = c.header()
    c.byline()

    # ------------------------------------------------- pipeline A · ingestion
    ry = y0 + 46
    srcw = 300.0
    s_de = card(c, Box(T.SAFE, ry, srcw), "German federal publisher",
                role="source", level="external", icon="globe",
                subtitle="gesetze-im-internet.de. The health service "
                         "downloads the publisher's own ZIP.",
                meta=["gii_norm · 32 of 52 laws"])
    s_eu = card(c, Box(T.SAFE, s_de.bottom + 22, srcw), "EU · CELLAR",
                role="source", level="external", icon="globe",
                subtitle="A FORMEX v4 bundle fetched by content negotiation. "
                         "CELLAR is the repository, FORMEX the markup, and "
                         "CELEX the identifier the act is resolved by.",
                meta=["formex_v4 · 20 of 52 laws"])

    stx = T.SAFE + srcw + 44
    stw = (c.width - T.SAFE - stx - 3 * 26) / 4
    sx = [stx + i * (stw + 26) for i in range(4)]

    a1 = card(c, Box(sx[0], ry, stw), "1 · Acquire",
              role="ui", level="primary", icon="service",
              subtitle="The health service fetches the publisher's own file "
                       "and resolves CELEX for EU acts. It observes and "
                       "judges freshness; it never parses.",
              meta=[":8000 · health service"])
    a2 = card(c, Box(sx[1], ry, stw), "2 · Capture",
              role="event", level="extended", icon="service",
              subtitle="SHA-256 before anything interprets the bytes, written "
                       "to object storage under a fresh prefix, then one "
                       "event. The producer parses nothing — no ZIP, no XML, "
                       "no section model.",
              meta=[":4675 · entity producer"])
    a3 = card(c, Box(sx[2], ry, stw), "3 · Structure",
              role="ai", level="primary", icon="brain",
              subtitle="A registry decides the canonical key and the parser; "
                       "GII-NORM or FORMEX v4 then extracts citations to "
                       "provision level and chunks the active sections — all "
                       "in one transaction, with three ruleset digests.",
              meta=[":4698 · preprocessor"])
    a4 = card(c, Box(sx[3], ry, stw), "4 · Project",
              role="ai", level="primary", icon="bolt",
              subtitle="One REPEATABLE READ snapshot, embedded with BGE-M3 — "
                       "dense 1024 and sparse from a single pass — then "
                       "Qdrant and Neo4j converged in order, each fenced on "
                       "an exact count. Tokens are counted first, so the law "
                       "is refused rather than stored as a truncated vector.",
              meta=[":4710-4711 · loader"])

    edge(c, s_de, a1, kind="sync", role="source", tb=0.3, gap=5)
    edge(c, s_eu, a1, kind="sync", role="source", tb=0.74, gap=5)
    for u, v in ((a1, a2), (a2, a3), (a3, a4)):
        edge(c, u, v, kind="async", role="event", gap=5)
    lane_around(c, [s_de, s_eu, a1, a2, a3, a4],
                "Pipeline A · ingestion — publisher's bytes to a stored, "
                "provable law",
                caption="no REST trigger · first ingest, re-ingest and replay "
                        "are one code path", accent="ai")

    # -------------------------------------------------------------- the corpus
    cy = max(s_eu.bottom, a4.bottom) + 168
    kw = (c.width - 2 * T.SAFE - 3 * 40) / 4
    k_pg = store(c, Box(T.SAFE, cy, kw), "PostgreSQL · the laws",
                 kind="relational", level="primary",
                 subtitle="Canonical legal state as tables, plus source "
                          "evidence, assurance and currency — four concerns, "
                          "the evidence tables append-only",
                 meta=["~35 tables", "sole writer: preprocessor"])
    k_qd = store(c, Box(T.SAFE + kw + 40, cy, kw), "Qdrant · the vectors",
                 kind="vector", level="primary",
                 subtitle="One point per chunk, dense and sparse together in "
                          "one collection, both law families side by side",
                 meta=["uuid5(ns, chunk_id)", "sole writer: loader"])
    k_n4 = store(c, Box(T.SAFE + 2 * (kw + 40), cy, kw),
                 "Neo4j · the relations",
                 kind="graph", level="primary",
                 subtitle="Which provision cites which, across statutes — "
                          "exactly what a vector hit cannot tell you",
                 meta=["REFERS_TO · CITES_LAW", "sole writer: loader"])
    k_mo = store(c, Box(T.SAFE + 3 * (kw + 40), cy, kw),
                 "MinIO · the source bytes",
                 kind="bucket", level="extended",
                 subtitle="What the publisher actually served, hashed on "
                          "arrival and mirrored into an object-locked bucket",
                 meta=["{eventId}/{filename}", "sole writer: entity producer"])

    # Four write edges share one channel, staggered 26px apart so none of them
    # overlaps another -- the design system allows sharing a channel, never
    # overlapping in it.
    ch = cy - 150
    edge(c, a2, k_mo, kind="own", role="store", side_a="s", side_b="n",
         ta=0.5, tb=0.5, bend=ch, label="captures")
    edge(c, a3, k_pg, kind="own", role="store", side_a="s", side_b="n",
         ta=0.5, tb=0.5, bend=ch + 26, label="exclusive write")
    edge(c, a4, k_qd, kind="own", role="store", side_a="s", side_b="n",
         ta=0.34, tb=0.5, bend=ch + 52, label="1st")
    edge(c, a4, k_n4, kind="own", role="store", side_a="s", side_b="n",
         ta=0.66, tb=0.5, bend=ch + 78, label="2nd")
    lane_around(c, [k_pg, k_qd, k_n4, k_mo],
                "The corpus · three databases, and the evidence behind them",
                caption="one writer per store, arrived at by removing a "
                        "violation", accent="store")

    # ------------------------------------------------------------ verification
    vy = max(k_pg.bottom, k_qd.bottom, k_n4.bottom, k_mo.bottom) + 108
    vw = (c.width - 2 * T.SAFE - 2 * 44) / 3
    v1 = card(c, Box(T.SAFE, vy, vw), "Fourteen gates, run by the ingest",
              role="trust", level="primary", icon="shield",
              subtitle="Publishing law.embedded is what runs them — nobody "
                       "asks. They cover structural fidelity, citation "
                       "correctness, cross-store equality and source "
                       "currency, and the verdict is never one badge.",
              meta=["7 badge-required · 7 recorded"])
    v2 = card(c, Box(T.SAFE + vw + 44, vy, vw),
              "A denominator that cannot share the defect",
              role="trust", level="primary", icon="shield",
              subtitle="The structural inventory is read a second time on a "
                       "different XML stack, importing no parser code. And "
                       "the prover proves itself first: if an already-"
                       "certified law stops reproducing under today's rules, "
                       "no law gets a verdict — including the one being "
                       "certified.",
              meta=["lxml iterparse · zero application imports"])
    v3 = card(c, Box(T.SAFE + 2 * (vw + 44), vy, vw),
              "Reconciliation · a different question",
              role="trust", level="primary", icon="bolt",
              subtitle="Verification asks whether this generation was "
                       "extracted faithfully. Reconciliation asks whether the "
                       "stores agree right now. It is read-only, repairs "
                       "nothing, and says when it cannot tell.",
              meta=["LIVE_CONSISTENT | DRIFT_DETECTED", "CHECK_UNAVAILABLE"])
    edge(c, v1, k_pg, kind="verify", role="trust", side_a="n", side_b="s",
         ta=0.28, tb=0.3, label="measure")
    edge(c, v3, k_n4, kind="verify", role="trust", side_a="n", side_b="s",
         ta=0.72, tb=0.62, label="compare")
    lane_around(c, [v1, v2, v3],
                "Verification · asked and answered after every ingest",
                caption="observer only · changes no version, chunk, vector "
                        "or edge", accent="trust")

    # ----------------------------------------------------- pipeline B · query
    by = max(v1.bottom, v2.bottom, v3.bottom) + 108
    bw = (c.width - 2 * T.SAFE - 3 * 30) / 4
    bx = [T.SAFE + i * (bw + 30) for i in range(4)]

    b1 = card(c, Box(bx[0], by, bw), "Question",
              role="ui", level="integrated", icon="ui",
              subtitle="An operator search, or a question arriving as an event",
              meta=["GET /search · ibp.events.inbound"])
    b2 = card(c, Box(bx[1], by, bw), "Embed the question",
              role="ai", level="primary", icon="brain",
              subtitle="BGE-M3 — the same model that embedded the corpus. A "
                       "different model would make the comparison meaningless.",
              meta=["dense 1024 + sparse"])
    b3 = card(c, Box(bx[2], by, bw), "Hybrid retrieval",
              role="ai", level="primary", icon="bolt",
              subtitle="Dense and sparse prefetch, fused server-side by "
                       "reciprocal rank fusion in one round trip",
              meta=["reads Qdrant · writes nothing",
                    "prefetch = max(limit, 20)"])
    b4 = card(c, Box(bx[3], by, bw), "Cited chunks",
              role="trust", level="primary", icon="document",
              subtitle="The law key and section number travel in the payload, "
                       "so a citation is data rather than generated text",
              meta=["section_number · law"])

    by2 = max(b1.bottom, b2.bottom, b3.bottom, b4.bottom) + 36
    b5 = card(c, Box(bx[0], by2, bw), "Graph expansion",
              role="store", level="integrated", icon="graph",
              subtitle="A vector hit finds the matching provision; the graph "
                       "finds what that provision points at, which a legal "
                       "answer usually needs as well",
              meta=["reads Neo4j · writes nothing"])
    b6 = card(c, Box(bx[1], by2, bw), "Legal Chatbot",
              role="ai", level="integrated", icon="brain",
              subtitle="Consumes ibp.events.inbound and publishes "
                       "ibp.events.ai.processed. Its environment contract is "
                       "fully visible; its repository is not in the workspace "
                       "this portfolio was audited from.",
              meta=["no internal detail drawn"])
    b7 = card(c, Box(bx[2], by2, bw), "LLM",
              role="ai", level="integrated", icon="brain",
              subtitle="Self-hosted behind an OpenAI-compatible endpoint; the "
                       "container runs fully offline for weights",
              meta=["HF_HUB_OFFLINE=1"])
    b8 = card(c, Box(bx[3], by2, bw), "Grounded answer",
              role="ui", level="integrated", icon="document",
              subtitle="Returned with the provisions it was built from",
              meta=["ibp.events.ai.processed"])

    for u, v in ((b1, b2), (b2, b3), (b3, b4)):
        edge(c, u, v, kind="sync", role="ai", gap=5)
    for u, v in ((b5, b6), (b6, b7), (b7, b8)):
        edge(c, u, v, kind="sync", role="ai", gap=5)
    edge(c, b4, b5, kind="sync", role="trust", side_a="s", side_b="n",
         ta=0.5, tb=0.5, bend=by2 - 18)
    lane_around(c, [b1, b2, b3, b4, b5, b6, b7, b8],
                "Pipeline B · query — a question answered from the stored "
                "corpus",
                caption="nothing here writes a store, and nothing here parses "
                        "a law", accent="ui")

    # ------------------------------------------------- what the gates ask
    gy = max(b5.bottom, b6.bottom, b7.bottom, b8.bottom) + 60
    c.add(text_el("WHAT THE FOURTEEN GATES ACTUALLY ASK · SIX GROUPS, "
                  "ONE EXAMPLE EACH", T.SAFE, gy, "lane", T.ROLE["trust"]))
    gy += 18
    gm = matrix(c, T.SAFE, gy,
                ["Group", "The question it answers", "Example gate id",
                 "Applies to"],
                [[g, q, ex, fam] for g, q, ex, fam in GATE_GROUPS],
                widths=[260, 520, 420, 160], rowh=34, mono_cols={2},
                accents=["trust"] * len(GATE_GROUPS),
                label="matrix:gate-groups")

    nx = T.SAFE + 1360 + 40
    nw = c.width - T.SAFE - nx
    gn = note(c, nx, gy + 4, nw,
              ["Two of the fourteen are structurally inapplicable to EU "
               "sources, and both say so in code with a named reason rather "
               "than silently not running.",
               "EU acts parse, ingest and are queryable, but no EU law is "
               "certified: the end-to-end assurance contract does not exist "
               "yet, so the prover returns INCONCLUSIVE for a FORMEX law. A "
               "missing contract, not a missing parser."],
              accent="warn", title="Where the DE and EU answers differ")

    # ----------------------------------------------------------------- notes
    ny = max(gm.bottom, gn.bottom) + 46
    half = (c.width - 2 * T.SAFE) / 2 - 18
    n1 = note(c, T.SAFE, ny, half,
              ["The two pipelines share one corpus and nothing else. Every "
               "component in A writes exactly one store and the write arrows "
               "above are the only writes that exist; every component in B "
               "reads and returns. That separation is why a retrieval bug "
               "cannot corrupt the corpus, and why a question cannot start an "
               "ingest.",
               "It is also why B has no verification gate of its own and "
               "needs none. B trusts the corpus because A proved it before it "
               "was served."],
              accent="ai", title="Two paths, one corpus")
    note(c, T.SAFE + half + 36, ny, half,
         ["Three limits worth stating with the rest. There is no dead-letter "
          "topic on this pipeline, so a permanently unprocessable law is "
          "redelivered for ever and blocks its partition until a human "
          "intervenes.",
          "The chatbot and the LLM are existing components whose repositories "
          "are outside the audited workspace, so no internal detail of them "
          "is drawn. And validating each cited section against the corpus "
          "before an answer is shown — the check that would catch a "
          "hallucinated citation — is a design position here, not delivered "
          "work."],
         accent="warn", title="What is not solved")

    c.fit(n1.bottom + 14, legend_spec=dict(
        roles=["source", "event", "ai", "store", "trust", "ui"],
        flows=["sync", "async", "own", "verify"],
        levels=["primary", "extended", "integrated", "external"]))
    write(c, f"{OUT}/21-legal-knowledge-database-pipelines.svg")


ALL = [d20_runtime, d21_legal_kb_pipelines]
