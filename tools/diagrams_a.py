"""Diagrams 01-05: landscape, platform, lifecycle, trust spine, stores.

Every node here exists in the repositories. See
private/audit/07-evidence-matrix.md for the claim-by-claim sourcing.
"""

from __future__ import annotations

import design_tokens as T
from svg_kit import (Box, Canvas, card, edge, lane, lane_around, note,
                     pill, step, store, text_el, write)

OUT = "assets/architecture"


# ===========================================================================
# 01 - The AI landscape: two workstreams, one platform
# ===========================================================================
def d01_landscape() -> None:
    c = Canvas(1920, 1460,
               eyebrow="Level 2 \u00b7 Landscape",
               title="AI engineering systems I worked on at BP-ITCS",
               subtitle="Four workstreams over one event-driven platform. "
                        "Colour is engineering role; border weight and the "
                        "corner marker are authorship.")
    c.background()
    y0 = c.header()
    c.byline()

    # ---------------- sources, across the top
    sw = (c.width - 2 * T.SAFE - 40 - 3 * 18) / 4
    sx = T.SAFE + 20
    srcs = []
    for i, (name, sub, meta, icon) in enumerate([
        ("gesetze-im-internet.de", "German federal law, GII-NORM XML",
         "ZIP per law", "globe"),
        ("EUR-Lex / CELLAR", "EU acts, FORMEX v4", "CELEX \u00b7 fmx4", "globe"),
        ("Insurance documents", "policies, claims, invoices, conditions",
         "PDF \u00b7 PNG \u00b7 TIFF \u00b7 WEBP", "document"),
        ("Medical images", "chest radiographs", "entityType: MEDICAL_IMAGE",
         "document"),
    ]):
        srcs.append(card(c, Box(sx + i * (sw + 18), y0 + 44, sw), name,
                         role="source", level="external", icon=icon,
                         subtitle=sub, meta=[meta]))
    lane_around(c, srcs, "Authoritative sources and inputs",
                caption="outside the system", accent="source")

    # ---------------- workstream A: Legal Knowledge Database
    ay = max(b.bottom for b in srcs) + 62
    aw = (c.width - 2 * T.SAFE - 36) * 0.58
    acw = (aw - 40 - 2 * 16) / 3
    ax = T.SAFE + 20
    ep = card(c, Box(ax, ay, acw), "Entity Producer",
              role="event", level="extended", icon="service",
              subtitle="Captures source bytes as evidence",
              meta=[":4675 \u00b7 java"])
    pre = card(c, Box(ax + acw + 16, ay, acw), "Ingestion Preprocessor",
               role="trust", level="primary", icon="service",
               subtitle="Structures, cites, owns 14 gates",
               meta=[":4698 \u00b7 python"])
    lo = card(c, Box(ax + 2 * (acw + 16), ay, acw), "Ingestion Loader",
              role="ai", level="primary", icon="service",
              subtitle="Embeds, converges derived stores",
              meta=[":4697 \u00b7 BGE-M3"])
    ay2 = max(ep.bottom, pre.bottom, lo.bottom) + 16
    dash = card(c, Box(ax, ay2, acw), "Legal KB Dashboard",
                role="ui", level="primary", icon="ui",
                subtitle="Operator interface. Decides nothing.",
                meta=[":3000 \u00b7 next.js"])
    hs = card(c, Box(ax + acw + 16, ay2, acw), "Health Service",
              role="ui", level="primary", icon="service",
              subtitle="Control and verification boundary",
              meta=[":8000 \u00b7 /api/v1"])
    bot = card(c, Box(ax + 2 * (acw + 16), ay2, acw), "Legal Chatbot",
               role="ai", level="integrated", icon="brain",
               subtitle="Grounded answers over the corpus",
               meta=["existing component"])
    lane_around(c, [ep, pre, lo, dash, hs, bot],
                "A \u00b7 Legal Knowledge Database",
                caption="five services \u00b7 four implemented by me",
                accent="trust")

    # ---------------- workstream B: AI Compliance (the consumer)
    bx = T.SAFE + aw + 36
    bwid = c.width - T.SAFE - bx - 20
    cui = card(c, Box(bx + 20, ay, bwid), "Assessment UI + backend",
               role="ui", level="integrated", icon="ui",
               subtitle="Structured questionnaire and website scan; publishes "
                        "work and consumes results",
               meta=[":4000 \u00b7 :4010 \u00b7 ai_compliance"])
    ckb = card(c, Box(bx + 20, cui.bottom + 16, bwid), "Knowledge processor",
               role="ai", level="integrated", icon="brain",
               subtitle="Reads the questionnaire graph and the legal corpus, "
                        "returns a grounded assessment",
               meta=["ibp.events.ai.processed"])
    crp = card(c, Box(bx + 20, ckb.bottom + 16, bwid), "Compliance report",
               role="trust", level="integrated", icon="document",
               subtitle="Rendered to PDF behind a short-lived token",
               meta=["assessment-evidence"])
    lane_around(c, [cui, ckb, crp], "B \u00b7 AI Compliance",
                caption="the product the corpus serves \u00b7 existing",
                accent="ui")

    edge(c, lo, ckb, kind="verify", role="trust", side_a="e", side_b="w",
         ta=0.5, tb=0.35, label="questionnaire graph")

    # ---------------- workstream C and D, side by side
    cy = max(dash.bottom, hs.bottom, bot.bottom, crp.bottom) + 62
    hw = (c.width - 2 * T.SAFE - 36) / 2
    dcw = (hw - 40 - 16) / 2

    dx = card(c, Box(T.SAFE + 20, cy, dcw), "Document Extractor",
              role="ai", level="extended", icon="document",
              subtitle="Docling conversion, then template-driven LLM field "
                       "extraction",
              meta=["6 insurance templates"])
    ix = card(c, Box(T.SAFE + 20 + dcw + 16, cy, dcw), "Indexing Service",
              role="ai", level="extended", icon="bolt",
              subtitle="Chunks, embeds, upserts vectors per domain; DLQ on "
                       "failure",
              meta=["I created this service"])
    rg = card(c, Box(T.SAFE + 20, max(dx.bottom, ix.bottom) + 16, dcw),
              "RAG Service", role="ai", level="integrated", icon="brain",
              subtitle="Retrieval-only chat and query extraction",
              meta=["/chat \u00b7 /query"])
    gl = card(c, Box(T.SAFE + 20 + dcw + 16, rg.y, dcw), "Glaux UI",
              role="ui", level="shared", icon="ui",
              subtitle="Event dashboard with live service health",
              meta=["next.js \u00b7 STOMP"])
    lane_around(c, [dx, ix, rg, gl], "C \u00b7 Document Intelligence",
                caption="extended by me", accent="ai")

    rx = T.SAFE + hw + 36
    rcw = (hw - 40 - 16) / 2
    clf = card(c, Box(rx + 20, cy, rcw), "DenseNet-121 classifier",
               role="ai", level="extended", icon="brain",
               subtitle="Five findings, sigmoid per class, one calibrated "
                        "threshold each",
               meta=["DenseNet121-v2.0.0"])
    cam = card(c, Box(rx + 20 + rcw + 16, cy, rcw), "Grad-CAM++ attribution",
               role="trust", level="extended", icon="shield",
               subtitle="Shows which regions drove each positive finding; "
                        "anatomical priors deliberately off",
               meta=["heatmaps to MinIO"])
    sev = card(c, Box(rx + 20, max(clf.bottom, cam.bottom) + 16, rcw),
               "Severity + ICD-10", role="ui", level="extended", icon="ui",
               subtitle="Urgency bands and a clinical code per finding",
               meta=["HIGH \u00b7 MODERATE \u00b7 LOW"])
    syn = card(c, Box(rx + 20 + rcw + 16, sev.y, rcw), "Synthetic test data",
               role="source", level="extended", icon="document",
               subtitle="VVG-compliant German insurance document set and "
                        "generator, so no real customer document is needed",
               meta=["ai-contract-data"])
    lane_around(c, [clf, cam, sev, syn],
                "D \u00b7 Medical-imaging classification + test data",
                caption="research prototype \u00b7 extended by me",
                accent="trust")

    # ---------------- shared platform
    py = max(rg.bottom, gl.bottom, sev.bottom, syn.bottom) + 62
    pw = c.width - 2 * T.SAFE
    swid2 = (pw - 40 - 4 * 16) / 5
    px = T.SAFE + 20
    stores = []
    for i, (name, kind, sub, meta) in enumerate([
        ("PostgreSQL", "relational", "canonical state + evidence",
         "writer: preprocessor"),
        ("Qdrant", "vector", "dense 1024 + sparse", "writer: loader"),
        ("Neo4j", "graph", "provisions + questionnaire", "writer: loader"),
        ("MinIO", "bucket", "captures, evidence, images",
         "writer: producer"),
    ]):
        stores.append(store(c, Box(px + i * (swid2 + 16), py, swid2), name,
                            kind=kind, subtitle=sub, meta=[meta]))
    kaf = card(c, Box(px + 4 * (swid2 + 16), py, swid2), "Apache Kafka",
               role="event", level="integrated", icon="bolt",
               subtitle="KRaft \u00b7 the spine all four workstreams share",
               meta=["ibp-kafka \u00b7 :29192"])
    lane_around(c, stores + [kaf], "Shared platform",
                caption="existing infrastructure \u00b7 one writer per store",
                accent="store")

    c.fit(max(kaf.bottom, max(s.bottom for s in stores)) + 16,
          legend_spec=dict(
              roles=["source", "event", "ai", "store", "trust", "ui"],
              flows=["sync", "async", "verify"],
              levels=["primary", "extended", "shared", "integrated",
                      "external"]))
    write(c, f"{OUT}/01-ai-systems-landscape.svg")


# ===========================================================================
# 02 - Legal Knowledge Database, engineering level
# ===========================================================================
def d02_platform() -> None:
    c = Canvas(*T.W16x10,
               eyebrow="Level 3 · Engineering",
               title="Legal Knowledge Database — full architecture",
               subtitle="Exact services, topics, routes and stores. One writer per "
                        "store is an enforced rule, not a convention: the arrows "
                        "marked exclusive write are the only writes that exist.")
    c.background()
    y0 = c.header()
    c.byline()

    cw, gap = 300, 52
    col = [T.SAFE + 50 + i * (cw + gap) for i in range(5)]

    # Row 1: acquisition
    lane(c, Box(T.SAFE - 8, y0, c.width - 2 * T.SAFE + 16, 196),
         "1 · Acquire and prove the source", accent="source",
         caption="bytes in, digest recorded, nothing parsed")

    src = card(c, Box(col[0], y0 + 40, cw), "Official publishers",
               role="source", level="external", icon="globe",
               subtitle="gesetze-im-internet.de · publications.europa.eu",
               meta=["allowlisted hosts only"])
    hs_f = card(c, Box(col[1], y0 + 40, cw), "Health Service — fetch",
                role="ui", level="primary", icon="service",
                subtitle="Downloads the source itself; resolves CELEX for EU acts",
                meta=["POST /laws/{key}/reingest"])
    ep = card(c, Box(col[2], y0 + 40, cw), "Entity Producer",
              role="event", level="extended", icon="service",
              subtitle="Envelope, SHA-256, capture, publish. Parses nothing.",
              meta=["POST /events · :4675",
                    "file ≤ 1 MiB · url ≤ 50 MiB"])
    cap = store(c, Box(col[3], y0 + 40, cw), "MinIO · captures",
                kind="bucket", level="extended",
                subtitle="{eventId}/{filename} — a new prefix per request",
                meta=["legal-knowledge-database-laws"])
    ev = store(c, Box(col[4], y0 + 40, cw), "MinIO · evidence",
               kind="bucket", level="extended",
               subtitle="Object lock enabled. Release is a compliance procedure.",
               meta=["...-database-evidence · WORM"])

    edge(c, src, hs_f, kind="sync", role="source", label="fetch")
    edge(c, hs_f, ep, kind="sync", role="ui", label="POST")
    edge(c, ep, cap, kind="own", role="store", label="PUT")
    edge(c, cap, ev, kind="verify", role="store", label="mirror")

    # Row 2: structure
    y1 = y0 + 212
    lane(c, Box(T.SAFE - 8, y1, c.width - 2 * T.SAFE + 16, 240),
         "2 · Structure, cite and prove what was produced", accent="trust",
         caption="sole canonical writer")

    tin = pill(c, col[0] + 14, y1 + 46, "legal.knowledge.database.events.inbound")
    pre = card(c, Box(col[1], y1 + 86, cw), "Ingestion Preprocessor",
               role="trust", level="primary", icon="service",
               subtitle="Registry → parser dispatch → references → "
                        "chunks → one transaction",
               meta=["gii_norm: 32 laws · formex_v4: 20",
                     "filter domain=LEGAL, IMPORTED"])
    pg = store(c, Box(col[2], y1 + 86, cw), "PostgreSQL",
               kind="relational", level="primary",
               subtitle="Canonical state, source evidence, assurance, currency",
               meta=["~35 tables · 9 views · 84 migrations"])
    gates = card(c, Box(col[3], y1 + 86, cw), "14 verification gates",
                 role="trust", level="primary", icon="shield",
                 subtitle="Structural fidelity, citations, store equality, currency",
                 meta=["7 badge-required · DE 14 · EU 12"])
    prov = card(c, Box(col[4], y1 + 86, cw), "Ruleset provenance",
                role="trust", level="primary", icon="shield",
                subtitle="Three digests over parser, extractor and registry bytes",
                meta=["a byte change is a rule change"])

    edge(c, tin, pre, kind="async", role="event", side_a="s", side_b="n", tb=0.4)
    edge(c, ep, tin, kind="async", role="event", side_a="s", side_b="n",
         ta=0.35, bend=y1 + 30)
    edge(c, pre, pg, kind="own", role="store", label="writes")
    edge(c, pg, gates, kind="verify", role="trust", label="measure")
    edge(c, gates, prov, kind="verify", role="trust")

    # Row 3: derive + serve
    y2 = y1 + 256
    lane(c, Box(T.SAFE - 8, y2, c.width - 2 * T.SAFE + 16, 250),
         "3 · Derive searchable projections, then close the loop",
         accent="ai", caption="sole writer of both derived stores")

    tst = pill(c, col[0] + 14, y2 + 46, "law.structured")
    lo = card(c, Box(col[1], y2 + 86, cw), "Ingestion Loader",
              role="ai", level="primary", icon="service",
              subtitle="One REPEATABLE READ snapshot → embed → converge "
                       "→ count fences",
              meta=["BGE-M3 · 8192-token window",
                    "refuses the law rather than truncate"])
    qd = store(c, Box(col[2], y2 + 86, cw), "Qdrant",
               kind="vector", level="primary",
               subtitle="dense 1024 cosine + sparse LEXICAL, RRF fusion",
               meta=["legal-knowledge-database-german-law",
                     "point id = uuid5(ns, chunk_id)"])
    ne = store(c, Box(col[3], y2 + 86, cw), "Neo4j",
               kind="graph", level="primary",
               subtitle="Provision reference graph, MERGE by id",
               meta=["(:LawSection) (:Law)",
                     "[:REFERS_TO] [:CITES_LAW]"])
    temb = pill(c, col[4] + 30, y2 + 110, "law.embedded")

    edge(c, pre, tst, kind="async", role="event", side_a="s", side_b="n",
         ta=0.3, bend=y2 + 30)
    edge(c, tst, lo, kind="async", role="event", side_a="s", side_b="n", tb=0.35)
    edge(c, pg, lo, kind="verify", role="store", side_a="s", side_b="n",
         ta=0.25, tb=0.8, label="read-only")
    edge(c, lo, qd, kind="own", role="store", label="1st")
    edge(c, qd, ne, kind="own", role="store", label="2nd")
    edge(c, ne, temb, kind="async", role="event", side_b="w")

    nb = note(c, col[4], temb.bottom + 22, cw,
              ["law.structured means PostgreSQL committed only.",
               "law.embedded is the completion boundary — published after both "
               "count fences pass, and it is what makes the preprocessor verify "
               "the law without anyone asking."],
              accent="trust", title="The two boundaries")

    c.fit(max(nb.bottom, ne.bottom, lo.bottom) + 10, legend_spec=dict(
        roles=["source", "event", "ai", "store", "trust", "ui"],
        flows=["sync", "async", "verify", "own"],
        levels=["primary", "extended", "external"]))
    write(c, f"{OUT}/02-legal-knowledge-database.svg")


# ===========================================================================
# 03 - One document's journey
# ===========================================================================
def d03_lifecycle() -> None:
    c = Canvas(*T.W16x9,
               eyebrow="Document journey",
               title="One law, from publisher to queryable knowledge",
               subtitle="Eleven stages. Each one either produces evidence or is "
                        "measured against evidence produced earlier.")
    c.background()
    y0 = c.header()
    c.byline()

    stages = [
        ("Discover", "source", "globe",
         "Registry names the law, its parser and its publisher slug",
         "app/data/law_registry.yaml"),
        ("Acquire", "source", "globe",
         "Health service downloads the ZIP, or resolves CELEX at CELLAR",
         "Accept: application/zip;mtype=fmx4"),
        ("Prove the bytes", "trust", "shield",
         "SHA-256 over the captured bytes, carried on the event as zipHash",
         "fidelity.raw_integrity"),
        ("Capture", "store", "bucket",
         "Written to MinIO under a fresh eventId prefix, then published",
         "{eventId}/{filename}"),
        ("Inventory the source", "trust", "shield",
         "An independent walker builds the denominator, importing no parser code",
         "tools/oracle_gii_structure.py"),
        ("Parse", "ai", "service",
         "GII-NORM or FORMEX v4, dispatched from the registry",
         "gii_norm | formex_v4"),
        ("Extract references", "ai", "service",
         "Citations resolved to provision-level identity tuples",
         "relationship_extractor.py"),
        ("Chunk", "ai", "bolt",
         "Retrieval units for active sections only",
         "chunks · evidence_chunker"),
        ("Persist canonically", "store", "relational",
         "One transaction: rows plus the three ruleset digests",
         "PostgreSQL · law.structured"),
        ("Embed and project", "ai", "brain",
         "BGE-M3 dense + sparse, then converge Qdrant and Neo4j under count fences",
         "PostgreSQL · law.embedded"),
        ("Verify", "trust", "shield",
         "14 gates run automatically on completion; the verdict becomes the badge",
         "verification_checks"),
    ]

    cols, cw, gx, gy = 4, 408, 32, 24
    for i, (name, role, icon, sub, meta) in enumerate(stages):
        r, cidx = divmod(i, cols)
        x = T.SAFE + cidx * (cw + gx)
        y = y0 + r * 136
        b = card(c, Box(x + 34, y, cw - 34), name, role=role, level="primary",
                 icon=icon, subtitle=sub, meta=[meta])
        step(c, x + 15, y + 24, i + 1, accent=role)
        if cidx < cols - 1 and i < len(stages) - 1:
            c.add(f'<path d="M{x + cw} {y + 26} L{x + cw + gx - 6} {y + 26}" '
                  f'stroke="{T.rail(role, 0.6)}" stroke-width="1.4" '
                  f'marker-end="url(#ah-{role}-solid)"/>')
        elif cidx == cols - 1 and i < len(stages) - 1:
            c.add(f'<path d="M{x + cw / 2} {b.bottom + 4} '
                  f'L{x + cw / 2} {b.bottom + 13} '
                  f'L{T.SAFE + cw / 2} {b.bottom + 13} '
                  f'L{T.SAFE + cw / 2} {y + 136 - 6}" fill="none" '
                  f'stroke="{T.rail("neutral", 0.45)}" stroke-width="1.2" '
                  f'stroke-dasharray="4 4"/>')

    note(c, T.SAFE, y0 + 3 * 136 + 10, 880,
         ["The order is not arbitrary. The source inventory (5) comes before the "
          "parser (6) so the denominator cannot be derived from the thing under "
          "test. The archive-mirror row is written last of all, after the object "
          "has been uploaded, read back, hashed and size-checked, because that "
          "row is what the raw-integrity gate treats as evidence."],
         accent="trust", title="Why this sequence")
    note(c, T.SAFE + 920, y0 + 3 * 136 + 10, c.width - T.SAFE - (T.SAFE + 920),
         ["Ingestion has no REST trigger. The only way a law enters the pipeline "
          "is a matching Kafka event, which is what makes replay and re-ingest the "
          "same code path rather than two."],
         accent="event", title="No back door")

    c.fit(y0 + 3 * 136 + 130, legend_spec=dict(
        roles=["source", "ai", "store", "trust"], flows=["sync"]))
    write(c, f"{OUT}/03-document-ingestion-lifecycle.svg")


# ===========================================================================
# 04 - Source of truth to trusted corpus
# ===========================================================================
def d04_trusted_corpus() -> None:
    c = Canvas(*T.W16x9,
               eyebrow="The spine",
               title="From source of truth to trusted corpus",
               subtitle="The conceptual shape of the system. Derived knowledge is "
                        "never the evidence for itself.")
    c.background()
    y0 = c.header()
    c.byline()

    bands = [
        ("Source of truth", "source",
         "What the publisher actually served, and when",
         ["The publisher's own bytes", "SHA-256 digest at capture time",
          "Object-locked evidence copy", "A described fetch, bound to a capture id"],
         "Nothing downstream may contradict this layer."),
        ("Ingest", "event",
         "Turn bytes into rows, under a recorded rule set",
         ["Registry decides what the law is", "Parser dispatched, never guessed",
          "Citations resolved to identities", "Three ruleset digests recorded"],
         "A generation remembers the rules that made it."),
        ("Derived knowledge", "ai",
         "Representations built for retrieval, not for record",
         ["PostgreSQL — canonical rows", "Qdrant — dense + sparse vectors",
          "Neo4j — provision graph", "Each derived id is a function of the rows"],
         "Rebuildable from the layer above. Never the source of a claim."),
        ("Verify", "trust",
         "Measure what is stored against what was served",
         ["14 gates, 4 dimensions", "An independent structural oracle",
          "Cross-store equality, by exact count", "Currency judged from recorded evidence"],
         "The prover proves itself first, or issues no verdict at all."),
        ("Reconcile", "ui",
         "Answer the live question, change nothing",
         ["PostgreSQL identity tuples read", "Qdrant and Neo4j compared",
          "LIVE_CONSISTENT · DRIFT_DETECTED", "CHECK_UNAVAILABLE is also an answer"],
         "The last sweep's answer, not a standing guarantee."),
        ("Trusted corpus", "trust",
         "What may be served to a question about the law",
         ["A verdict per gate, not one badge", "Freshness of the verdict itself",
          "Currency of the publisher's file", "Live store integrity"],
         "Four separate questions. Merging them would hide which one failed."),
    ]

    bw = (c.width - 2 * T.SAFE - 5 * 22) / 6
    maxh = 0
    boxes = []
    for i, (title, role, sub, bullets, foot) in enumerate(bands):
        x = T.SAFE + i * (bw + 22)
        b = card(c, Box(x, y0 + 34, bw), title, role=role, level="primary",
                 icon={"source": "globe", "event": "bolt", "ai": "brain",
                       "trust": "shield", "ui": "ui"}[role],
                 subtitle=sub)
        boxes.append((b, role, bullets, foot))
        maxh = max(maxh, b.h)

    # normalise heights visually by placing bullet blocks at one baseline
    _d04_bottoms: list[float] = []
    by = y0 + 34 + maxh + 18
    for i, (b, role, bullets, foot) in enumerate(boxes):
        x = b.x
        yy = by
        for bl in bullets:
            from svg_kit import wrap, line_height
            lines = wrap(bl, "meta", bw - 20, where=f"band bullet {bl!r}")
            c.add(f'<circle cx="{x + 5}" cy="{yy - 4}" r="2.2" '
                  f'fill="{T.rail(role, 0.9)}"/>')
            for j, ln in enumerate(lines):
                c.add(text_el(ln, x + 14, yy + j * line_height("meta"),
                              "meta", T.INK_MUTED))
            yy += len(lines) * line_height("meta") + 7
        fb = note(c, x, yy + 6, bw, [foot], accent=role)
        _d04_bottoms.append(fb.bottom)
        if i < len(boxes) - 1:
            ax = x + bw + 4
            c.add(f'<path d="M{ax} {b.cy} L{ax + 13} {b.cy}" '
                  f'stroke="{T.rail(role, 0.75)}" stroke-width="1.8" '
                  f'marker-end="url(#ah-{role}-solid)"/>')

    c.fit(max(_d04_bottoms), footnote=dict(
        lines=["Read right to left and the reason for the shape appears: to trust "
               "the corpus you need reconciliation; to reconcile you need "
               "verification; to verify you need derived knowledge and the "
               "evidence it came from; and to have evidence you must have proven "
               "the bytes before parsing them. Every layer's claim is falsifiable "
               "against the layer above it, which is what the word trusted is "
               "doing in the last box."],
        accent="trust", title="Why the order is the architecture"),
        legend_spec=dict(roles=["source", "event", "ai", "trust", "ui"]))
    write(c, f"{OUT}/04-source-to-trusted-corpus.svg")


# ===========================================================================
# 05 - Multi-store knowledge architecture
# ===========================================================================
def d05_multistore() -> None:
    c = Canvas(*T.W16x9,
               eyebrow="Knowledge storage",
               title="Four stores, four jobs, one writer each",
               subtitle="Each store is here because the others cannot do its job. "
                        "The limitation row is the actual justification.")
    c.background()
    y0 = c.header()
    c.byline()

    cols = [
        ("PostgreSQL", "relational", "Canonical record",
         "Sole writer: Preprocessor (corpus) · Health Service (currency)",
         ["Laws, versions, sections, chunks",
          "Citations and law-level references",
          "Source evidence, append-only",
          "Gate verdicts and ruleset provenance",
          "Currency observations and audit log"],
         "Cannot search by meaning.",
         "ON DELETE RESTRICT on currency_observations is why a wrong delete is "
         "impossible rather than discouraged."),
        ("Qdrant", "vector", "Semantic retrieval",
         "sole writer: loader",
         ["One point per chunk",
          "dense 1024, cosine, named dense",
          "sparse LEXICAL from the same model",
          "payload: law, section_number, title, raw_text",
          "RRF fusion server-side"],
         "Cannot follow a citation chain, cannot enforce integrity.",
         "Point id is uuid5(ns, chunk_id), so a re-run overwrites and never "
         "duplicates."),
        ("Neo4j", "graph", "Reference traversal",
         "sole writer: loader",
         ["(:LawSection {id}) · (:Law {code})",
          "[:REFERS_TO] → LawSection",
          "[:CITES_LAW] → Law",
          "Stub nodes for cited-but-not-ingested",
          "MERGE by id; never recreated"],
         "Cannot search by meaning.",
         "A vector hit finds the matched provision. A compliance answer often "
         "needs the one it cites."),
        ("MinIO", "bucket", "Immutable evidence",
         "Writers: Entity Producer (captures) · Preprocessor (mirror)",
         ["Captures under {eventId}/{filename}",
          "Evidence bucket with object lock",
          "Digest and size verified on read-back",
          "Mirror row written last, as the gate's evidence",
          "Never touched by withdrawal"],
         "Cannot be queried at all; it holds bytes and digests.",
         "Captures are immutable by key, not by policy — no versioning, no "
         "content-addressing, no dedup."),
    ]

    bw = (c.width - 2 * T.SAFE - 3 * 26) / 4
    _d05_bottoms: list[float] = []
    from svg_kit import line_height, wrap
    for i, (name, kind, job, owner, holds, cannot, insight) in enumerate(cols):
        x = T.SAFE + i * (bw + 26)
        b = store(c, Box(x, y0 + 30, bw), name, kind=kind, level="primary",
                  subtitle=job, meta=[owner])
        yy = b.bottom + 26
        c.add(text_el("HOLDS", x, yy, "lane", T.INK_FAINT))
        yy += 18
        for h in holds:
            lines = wrap(h, "meta", bw - 16, where=f"store holds {h!r}")
            c.add(f'<circle cx="{x + 4}" cy="{yy - 4}" r="2" '
                  f'fill="{T.rail("store", 0.85)}"/>')
            for j, ln in enumerate(lines):
                c.add(text_el(ln, x + 12, yy + j * line_height("meta"), "meta",
                              T.INK_MUTED))
            yy += len(lines) * line_height("meta") + 6
        yy += 10
        nb = note(c, x, yy, bw, [cannot], accent="warn", title="Cannot")
        ib = note(c, x, nb.bottom + 16, bw, [insight], accent="trust",
                  title="Design consequence")
        _d05_bottoms.append(ib.bottom)

    c.fit(max(_d05_bottoms), footnote=dict(
        lines=["Every derived identifier is a pure function of PostgreSQL "
               "content: uuid5(namespace, chunk_id) for a Qdrant point, MERGE by "
               "id for a graph node, MERGE by code for a law node. Identity is "
               "derived, never generated — and that single property is what makes "
               "Kafka redelivery idempotent across two stores with no distributed "
               "transaction, and is the real answer to how the stores stay in "
               "step."],
        accent="ai",
        title="The mechanism that replaces a distributed transaction"),
        legend_spec=dict(roles=["store"], levels=["primary"]))
    write(c, f"{OUT}/05-multistore-knowledge-architecture.svg")


ALL = [d01_landscape, d02_platform, d03_lifecycle, d04_trusted_corpus, d05_multistore]
