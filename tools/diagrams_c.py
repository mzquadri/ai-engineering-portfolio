"""Diagrams 10-16: document AI, event pipelines, contributions, interview view,
failure/recovery, document state machine, executive view."""

from __future__ import annotations

import design_tokens as T
from svg_kit import (Box, Canvas, card, edge, lane_around, legend, line_height,
                     matrix, note, pill, state, step, store, text_el, wrap,
                     write)

OUT = "assets/architecture"


# ===========================================================================
# 10 - Insurance document AI
# ===========================================================================
def d10_insurance() -> None:
    c = Canvas(1920, 1200,
               eyebrow="Document intelligence",
               title="Insurance document AI — from PDF to structured "
                     "understanding",
               subtitle="A template is the extraction contract, not the model. "
                        "That is what lets the model change without the pipeline "
                        "changing.")
    c.background()
    y0 = c.header()
    c.byline()

    cw, gap = 288, 58
    ry = y0 + 44
    cols = [T.SAFE + i * (cw + gap) for i in range(5)]

    up = card(c, Box(cols[0], ry, cw), "Document arrives",
              role="source", level="integrated", icon="document",
              subtitle="Uploaded through the platform UI and stored in MinIO; an "
                       "event names it",
              meta=["ibp.events.inbound", "bucket: ibp-documents"])
    dx = card(c, Box(cols[1], ry, cw), "Document Extractor",
              role="ai", level="extended", icon="service",
              subtitle="Filters by domain and entity type, downloads the file, "
                       "converts it, extracts fields",
              meta=["accepted_domains: INSURANCE", "python · fastapi + kafka"])
    dl = card(c, Box(cols[2], ry, cw), "Docling Serve",
              role="ai", level="integrated", icon="brain",
              subtitle="Sidecar that converts PDF and image bytes to Markdown "
                       "over HTTP",
              meta=["docling-serve-cpu :5001", 'do_ocr: "false"'])
    ex = card(c, Box(cols[3], ry, cw), "Extraction agent",
              role="ai", level="extended", icon="bolt",
              subtitle="Discovery, guided extraction and re-extraction against "
                       "the active template, then post-validation",
              meta=["prompt_builder · post_validator",
                    "max 6000 chars per call"])
    ix = card(c, Box(cols[4], ry, cw), "Indexing Service",
              role="ai", level="extended", icon="bolt",
              subtitle="Optional LLM mapping, overlapping chunks, embeddings, "
                       "vector upsert",
              meta=["domain-configured", "DLQ on failure"])

    edge(c, up, dx, kind="async", role="event", label="event", mono=False)
    edge(c, dx, dl, kind="sync", role="ai", label="POST")
    edge(c, dl, ex, kind="sync", role="ai", label="markdown")
    edge(c, ex, ix, kind="async", role="event")

    ty = max(b.bottom for b in (up, dx, dl, ex, ix)) + 26
    t1 = pill(c, cols[1] + 30, ty, "ibp.events.document.extracted")
    t2 = pill(c, cols[3] + 40, ty, "ibp.events.document.indexed")
    t3 = pill(c, cols[4] + 40, ty + 40, "ibp.events.document.indexed.dlq",
              role="warn")
    lane_around(c, [up, dx, dl, ex, ix, t1, t2, t3],
                "Extract · structure · index", accent="ai",
                caption="extended by me")

    # ---- templates
    sy = t3.bottom + 48
    c.add(text_el("THE EXTRACTION CONTRACT", T.SAFE, sy, "lane", T.ROLE["trust"]))
    sy += 16
    tm = matrix(c, T.SAFE, sy,
                ["Document type", "Fields", "Identifier"],
                [["VERSICHERUNGSPOLICE", "policy_number, customer_name, "
                  "customer_id, insurer, effective_date, expiry_date, "
                  "coverage_amount, vm_number, issue_date, currency",
                  "customer_name"],
                 ["SCHADENMELDUNG", "claim_number, policy_number, incident_date, "
                  "report_date, claimant_name, customer_id, contract_number, "
                  "damage_description, damage_amount, damage_location",
                  "claimant_name"],
                 ["VERSICHERUNGSVERTRAG", "contract_number, policy_number, "
                  "customer_name, customer_id, signing_date, contract_start, "
                  "contract_end, premium", "customer_name"],
                 ["RECHNUNG", "invoice_number, invoice_date, total_amount, "
                  "vendor_name", "—"],
                 ["ARZTBERICHT", "patient_name, diagnosis", "patient_name"],
                 ["AUSWEIS", "full_name, id_number", "full_name"]],
                widths=[300, 700, 220], rowh=44, mono_cols={0, 1, 2},
                accents=["ai"] * 6, label="matrix:templates")

    fx = T.SAFE + 1260
    fw = c.width - T.SAFE - fx
    n1 = note(c, fx, sy, fw,
              ['Every field carries an extraction_hint naming the German label '
               'variants to look for: "Look for: Policennummer, VS-Nr., '
               'Vertragsnummer, Police Nr."',
               "That is domain literacy encoded as data. It moves between models "
               "without retraining, and it is reviewable by someone who knows "
               "insurance but not Python."],
              accent="trust", title="Why hints, not fine-tuning")
    n2 = note(c, fx, n1.bottom + 20, fw,
              ["Templates live in entity-reader and are published as versioned "
               "snapshots on ibp.events.templates, which the extractor, the "
               "indexer and the RAG service all follow.",
               "Without that, a schema change means three services holding three "
               "stale copies of the same contract."],
              accent="event", title="One contract, three consumers")
    n3 = note(c, fx, n2.bottom + 20, fw,
              ["Extraction was hardened against what real documents actually do: "
               "a policy-number regex rebuilt around three observed failure "
               "modes, a title-anchor fast path for conditions documents, German "
               "umlaut mojibake repair, and replacement-character detection to "
               "catch a PDF that extracted as text but lost its font mapping.",
               "A silent corruption that looks like success is worse than a "
               "failure, which is the same principle the legal pipeline's gates "
               "are built on."],
              accent="warn", title="What field extraction actually cost")

    qy = max(tm.bottom, n3.bottom) + 40
    qs = store(c, Box(T.SAFE, qy, 420), "Qdrant · per-domain collections",
               kind="vector", level="extended",
               subtitle="Routing is a declared filter on metadata.domain over a "
                        "shared topic, not a topic split",
               meta=["ibp_documents_insurance", "ibp_medical_images"])
    rg = card(c, Box(T.SAFE + 450, qy, 420), "RAG Service",
              role="ai", level="integrated", icon="brain",
              subtitle="Retrieval-only chat and query extraction; domain planners "
                       "turn a request into a retrieval plan",
              meta=["/chat · /query · /stats"])
    pdn = card(c, Box(T.SAFE + 900, qy, 420), "AI Prediction Service",
               role="ai", level="extended", icon="bolt",
               subtitle="DenseNet-121 chest X-ray classification with Grad-CAM++ "
                        "heatmaps written to MinIO",
               meta=["medical domain · not insurance"])
    edge(c, ix, qs, kind="own", role="store", side_a="s", side_b="n",
         ta=0.5, tb=0.6, bend=qy - 26)
    edge(c, qs, rg, kind="verify", role="store")
    lane_around(c, [qs, rg, pdn], "Retrieve · serve", accent="store")

    c.fit(max(qs.bottom, rg.bottom, pdn.bottom) + 22, footnote=dict(
        lines=["The correction worth making explicitly: this pipeline models "
               "customer, policy, coverage, claim, contract, invoice and identity "
               "documents, plus a medical report. It does not model vehicle, "
               "property, health or beneficiary domains — no template or "
               "domain configuration for them exists, so none is drawn."],
        accent="warn", title="What is and is not modelled"),
        legend_spec=dict(roles=["source", "event", "ai", "store", "trust", "warn"],
                         flows=["sync", "async", "verify", "own"],
                         levels=["extended", "integrated"]))
    write(c, f"{OUT}/10-insurance-document-ai.svg")


# ===========================================================================
# 11 - Event-driven pipelines
# ===========================================================================
def d11_events() -> None:
    c = Canvas(1920, 1200,
               eyebrow="Event-driven architecture",
               title="Ten topics, two pipelines, one broker",
               subtitle="Exact topic names, their producers and their consumers. "
                        "The two pipelines differ in maturity, and the diagram "
                        "shows the difference rather than smoothing it.")
    c.background()
    y0 = c.header()
    c.byline()

    tm = matrix(c, T.SAFE, y0 + 36,
                ["Topic", "Produced by", "Consumed by", "What it means"],
                [["legal.knowledge.database.events.inbound", "Entity Producer",
                  "Ingestion Preprocessor",
                  "a capture exists; here is its envelope and digest"],
                 ["legal.knowledge.database.law.structured", "Preprocessor",
                  "Ingestion Loader",
                  "canonical PostgreSQL is committed — and nothing more"],
                 ["legal.knowledge.database.law.embedded", "Loader",
                  "Preprocessor, Health Service",
                  "both derived stores are durably converged: the completion "
                  "boundary"],
                 ["legal.knowledge.database.questionnaire.structured",
                  "questionnaire path", "not inspectable here",
                  "needs verification — producer lives outside this workspace"],
                 ["ibp.events.inbound", "platform UI and backend",
                  "Document Extractor, Legal Chatbot",
                  "a document or a question has arrived"],
                 ["ibp.events.document.extracted", "Document Extractor",
                  "Indexing Service",
                  "markdown and extracted fields are attached to the event"],
                 ["ibp.events.document.indexed", "Indexing Service",
                  "downstream consumers", "chunks are embedded and searchable"],
                 ["ibp.events.document.indexed.dlq", "Indexing Service",
                  "operators", "this document could not be indexed"],
                 ["ibp.events.templates", "Document Extractor",
                  "Indexing Service, RAG Service",
                  "a versioned template snapshot, so three services share one "
                  "contract"],
                 ["ibp.events.ai / ibp.events.ai.processed", "AI services",
                  "entity handlers", "an AI result is ready to persist"]],
                widths=[520, 310, 330, 546], rowh=40, mono_cols={0},
                accents=["event"] * 3 + ["warn"] + ["ai"] * 6,
                label="matrix:topics")

    # ---- delivery semantics
    dy = tm.bottom + 42
    c.add(text_el("DELIVERY SEMANTICS THAT WERE DESIGNED, NOT INHERITED",
                  T.SAFE, dy, "lane", T.ROLE["trust"]))
    dy += 18
    dw = (c.width - 2 * T.SAFE - 3 * 24) / 4
    items = [
        ("Partitioned by law identity", "event",
         "The Kafka key is law_key, so one law maps to one partition and two "
         "generations of the same law can never be processed concurrently.",
         "fix: key inbound events by law identity"),
        ("Publish, then commit", "trust",
         "The loader converges both stores, publishes law.embedded, awaits the "
         "broker ack, and commits the offset last. A crash in between "
         "redelivers.",
         "the commit is last of all"),
        ("Duplicates absorbed, not prevented", "ui",
         "A redelivery may publish law.embedded twice. currency_observations "
         "carries a unique index on capture_id, so the second one cannot record "
         "a second observation.",
         "unique (capture_id)"),
        ("Skips commit too", "store",
         "A non-matching event has its offset committed and is skipped, so a "
         "foreign event cannot wedge the consumer or block its partition.",
         "domain=LEGAL, IMPORTED"),
    ]
    bottoms = []
    for i, (name, role, body, meta) in enumerate(items):
        x = T.SAFE + i * (dw + 24)
        b = card(c, Box(x, dy, dw), name, role=role, level="primary",
                 icon={"event": "bolt", "trust": "shield", "ui": "ui",
                       "store": "relational"}[role],
                 subtitle=body, meta=[meta])
        bottoms.append(b.bottom)

    ny = max(bottoms) + 34
    n1 = note(c, T.SAFE, ny, (c.width - 2 * T.SAFE) / 2 - 16,
              ["The legal pipeline has no dead-letter topic, no bounded retry and "
               "no backoff. A permanently unprocessable law is redelivered for "
               "ever and blocks its partition; the consume loop ends and waits "
               "for a human to restart the pod. Nothing re-ingests, rebuilds or "
               "rolls back on its own.",
               "The document pipeline does have a DLQ. That difference is real, "
               "and it is the clearest piece of outstanding work in the legal "
               "workstream."],
              accent="warn", title="What is missing, stated as missing")
    note(c, c.width / 2 + 8, ny, (c.width - 2 * T.SAFE) / 2 - 16,
         ["Redelivery is safe because identity is derived rather than generated. "
          "A Qdrant point id is uuid5(namespace, chunk_id); a graph node is "
          "MERGE-d by id; a law node is MERGE-d by code. Re-running a delivery "
          "converges to a byte-identical state.",
          "That is the property that replaces a distributed transaction across "
          "three stores, and it is why the absence of automatic retry is "
          "survivable rather than dangerous: a manual restart is just another "
          "delivery."],
         accent="trust", title="Why redelivery is not a risk")

    c.fit(n1.bottom + 66, footnote=dict(
        lines=["Note on scope: the brief for this portfolio asked for a "
               "GDMS Rule Mapper with gdms.* topics. No repository, topic, "
               "consumer, class, configuration or document for it exists "
               "anywhere in the inspected workspace — a case-insensitive "
               "search returned two hits, both inside base64 image data in "
               "unrelated files. It is therefore not drawn, and the event-driven "
               "work shown here is the work the repositories actually contain."],
        accent="warn", title="On a system that is not here"),
        legend_spec=dict(roles=["event", "ai", "store", "trust", "ui", "warn"]))
    write(c, f"{OUT}/11-event-driven-pipelines.svg")


# ===========================================================================
# 12 - My contributions
# ===========================================================================
def d12_contributions() -> None:
    c = Canvas(1920, 1400,
               eyebrow="Contribution map",
               title="What I built, what I contributed to, and what I did not",
               subtitle="Five classes, applied to all 20 inspected "
                        "repositories. Commit share is evidence of weight, not "
                        "of authorship \u2014 where the two disagree, the "
                        "reason is stated and the conservative class wins.")
    c.background()
    y0 = c.header()
    c.byline()

    # ---- the five classes, as the key
    c.add(text_el("THE FIVE CLASSES", T.SAFE, y0 + 18, "lane", T.ROLE["trust"]))
    keys = [
        ("primary", "Primary implementation",
         "I wrote the service and its design docs; majority of commits"),
        ("extended", "Significant contribution",
         "named features in a service someone else built, or that I started"),
        ("shared", "Integration / shared",
         "wired, configured or contributed to; not mine to claim"),
        ("integrated", "Existing platform",
         "built by colleagues or third parties; my work depends on it"),
        ("external", "External / upstream",
         "outside the system entirely"),
    ]
    kw = (c.width - 2 * T.SAFE - 4 * 16) / 5
    kb = []
    for i, (level, label, detail) in enumerate(keys):
        kb.append(card(c, Box(T.SAFE + i * (kw + 16), y0 + 34, kw), label,
                       role="trust" if level in ("primary", "extended") else "neutral",
                       level=level, subtitle=detail))

    # ---- the repository ledger
    ly = max(b.bottom for b in kb) + 34
    c.add(text_el("EVERY REPOSITORY, CLASSIFIED", T.SAFE, ly, "lane",
                  T.ROLE["ui"]))
    ly += 16
    rows = [
        ["knowledge-db-ingestion-preprocessor", "466 / 498", "Primary",
         "two parsers, 14 gates, oracle, prover, provenance, 84 migrations"],
        ["legal-kb-dashboard", "144 / 167", "Primary",
         "7 pages, 27 components, 9 route handlers, the four-axis TrustPanel"],
        ["legal-kb-health-service", "123 / 148", "Primary",
         "23 routes, completion consumer, reconciliation, withdrawal orchestrator"],
        ["knowledge-db-ingestion-loader", "77 / 94", "Primary",
         "BGE-M3 embedding, hybrid retrieval, dual-store convergence fences"],
        ["local-env", "63 / 113", "Significant",
         "the whole legal-knowledge-database profile, WAL archiving, object lock"],
        ["entity-producer", "46 / 116", "Significant",
         "EU/CELLAR Claim-Check ingestion, broker-confirmed publish, law-identity keying"],
        ["document-extractor", "27 / 63", "Significant",
         "dual LLM+regex extraction, multi-format input, mojibake detection"],
        ["ai-utils", "17 / 61", "Significant",
         "zipHash on BinaryAttachment, consumer commit(), configurable poll interval"],
        ["ai-prediction-service", "14 / 51", "Significant",
         "Grad-CAM++ analyser, DenseNetV2 integration, calibrated severity thresholds"],
        ["architecture", "10 / 13", "Significant",
         "arc42 documentation, ADR-003 and ADR-004"],
        ["indexing-service", "9 / 30", "Significant",
         "I created the service; others continued it. Commit share understates it."],
        ["ai-contract-data", "7 / 9", "Significant",
         "VVG-compliant synthetic document set + generator. Data, not a service."],
        ["glaux-ui", "5 / 243", "Integration / shared", "minor changes only"],
        ["entity-handler", "5 / 46", "Integration / shared", "minor changes only"],
        ["utils", "5 / 109", "Integration / shared", "minor changes only"],
        ["entity-reader", "1 / 47", "Existing platform", "consumed for templates"],
        ["entity-ui-handler", "1 / 29", "Existing platform", "not my work"],
        ["rag-service", "0 / 56", "Existing platform",
         "zero commits. Reads what my upstream services produce."],
        ["parent", "0 / 43", "Existing platform", "shared Maven parent"],
        ["base-images", "0 / 10", "Existing platform", "shared container bases"],
    ]
    cls_accent = {"Primary": "trust", "Significant": "ai",
                  "Integration / shared": "ui", "Existing platform": "neutral"}
    mt = matrix(c, T.SAFE, ly,
                ["Repository", "My commits", "Class", "What the class rests on"],
                rows, widths=[430, 160, 250, 968], rowh=30, mono_cols={0, 1},
                accents=[cls_accent[r[2]] for r in rows],
                label="matrix:contribution-ledger")

    # ---- grouped, named contributions
    gy = mt.bottom + 34
    c.add(text_el("WHAT THAT WORK ACTUALLY WAS", T.SAFE, gy, "lane",
                  T.ROLE["trust"]))
    gy += 16
    groups = [
        ("Verification / reliability", "trust", [
            "14 gates across fidelity, citations, store equality and currency",
            "A structural oracle on a different XML stack, importing no parser code",
            "A prover that proves itself first or issues no verdict at all",
            "Ruleset provenance digests over raw bytes, per source family",
            "Pre-flight blocking before ingestion rather than review after it",
        ]),
        ("Data architecture", "store", [
            "~35 tables, 9 views, 84 migrations across four separated concerns",
            "One writer per store, enforced by deleting the path that violated it",
            "Derived identity that makes redelivery idempotent with no 2PC",
            "Exact count fences on both derived stores",
            "Object-locked evidence storage and WAL archiving",
        ]),
        ("AI & document intelligence", "ai", [
            "BGE-M3 dense + sparse; refuse the law rather than truncate",
            "Hybrid retrieval with server-side RRF fusion",
            "German GII-NORM and EU FORMEX v4 parsers",
            "Citation extraction to provision-level identity tuples",
            "Template-driven field extraction hardened against real documents",
        ]),
        ("Event-driven & operations", "event", [
            "A three-topic contract with two distinct completion boundaries",
            "EU/CELLAR ingestion via the Claim-Check pattern",
            "Broker-confirmed publication before HTTP success",
            "Four operator actions, each with real error and outcome states",
            "46 assurance and operational tools; a diagram standard across 5 repos",
        ]),
    ]
    gw = (c.width - 2 * T.SAFE - 3 * 20) / 4
    bottoms = []
    for i, (name, role, items) in enumerate(groups):
        x = T.SAFE + i * (gw + 20)
        b = card(c, Box(x, gy, gw), name, role=role, level="primary",
                 icon={"trust": "shield", "store": "relational", "ai": "brain",
                       "event": "bolt"}[role])
        yy = b.bottom + 14
        for it in items:
            lines = wrap(it, "meta", gw - 20, where=f"contrib {it!r}")
            c.add(f'<circle cx="{x + 5}" cy="{yy - 4}" r="2.1" '
                  f'fill="{T.rail(role, 0.9)}"/>')
            for k, ln in enumerate(lines):
                c.add(text_el(ln, x + 14, yy + k * line_height("meta"), "meta",
                              T.INK_MUTED))
            yy += len(lines) * line_height("meta") + 6
        bottoms.append(yy)

    c.fit(max(bottoms) - 4, footnote=dict(
        lines=["Not mine, and stated so wherever this system is described: the "
               "Java entity platform, the RAG service (zero commits), the Glaux "
               "UI, the legal chatbot, and every third-party store. No "
               "production deployment is claimed \u2014 only Docker Compose "
               "stacks and CI image builds are evidenced. No business impact "
               "metric is claimed, because none exists in any repository.",
               "The single sentence: I implemented four of the five services in "
               "the Legal Knowledge Database \u2014 the system that turns "
               "published German and EU law into verifiable machine-readable "
               "knowledge, where every store has exactly one writer and the "
               "system refuses to certify a law it cannot independently "
               "reproduce from the publisher's own bytes."],
        accent="trust", title="What I did not build"),
        legend_spec=dict(levels=["primary", "extended", "shared", "integrated",
                                 "external"]))
    write(c, f"{OUT}/12-my-contributions.svg")


# ===========================================================================
# 13 - Interview system overview
# ===========================================================================
def d13_interview() -> None:
    c = Canvas(1920, 1000,
               eyebrow="Interview view \u00b7 Level 2",
               title="From authoritative source to trusted, queryable knowledge",
               subtitle="Seven stages. The green-bordered components are the four "
                        "services I implemented; everything else is marked for "
                        "what it actually is.")
    c.background()
    y0 = c.header()
    c.byline()

    # (stage, role, icon, components as (name, level, one-line))
    STAGES = [
        ("Authoritative\nsources", "source", "globe",
         [("gesetze-im-internet.de", "external", "German federal law"),
          ("EUR-Lex / CELLAR", "external", "EU acts, FORMEX")]),
        ("Ingestion", "event", "service",
         [("Entity Producer", "extended", "captures bytes, hashes them, "
           "publishes one event")]),
        ("Knowledge\nprocessing", "trust", "service",
         [("Ingestion Preprocessor", "primary", "parses, cites, chunks"),
          ("Ingestion Loader", "primary", "embeds, converges projections")]),
        ("Specialised\nstorage", "store", "relational",
         [("PostgreSQL \u00b7 MinIO", "integrated", "canonical state, evidence"),
          ("Qdrant \u00b7 Neo4j", "integrated", "vectors, provision graph")]),
        ("Verification &\nreconciliation", "trust", "shield",
         [("14 gates", "primary", "in the preprocessor"),
          ("Health Service", "primary", "polls, verifies, reconciles")]),
        ("Trusted\ncorpus", "trust", "shield",
         [("what may be served", "concept", "four separate trust answers, "
           "never one badge")]),
        ("Retrieval &\napplication", "ai", "brain",
         [("hybrid search", "primary", "BGE-M3 dense + sparse, RRF"),
          ("Legal Chatbot", "integrated", "grounded answers")]),
    ]

    n = len(STAGES)
    gap = 16
    cw = (c.width - 2 * T.SAFE - (n - 1) * gap) / n
    top = y0 + 46

    # ---- stage band: the dominant visual. Big number, big name.
    band_h = 96
    for i, (stage, role, icon, _comps) in enumerate(STAGES):
        x = T.SAFE + i * (cw + gap)
        accent = T.ROLE[role]
        c.add(
            f'<rect x="{x}" y="{top}" width="{cw}" height="{band_h}" rx="12" '
            f'fill="{T.tint(role, 0.14)}" stroke="{T.border(role, 0.55)}" '
            f'stroke-width="1.2"/>'
        )
        c.add(
            f'<text x="{x + 14}" y="{top + 26}" font-size="12" '
            f'font-weight="700" fill="{T.rgba(accent, 0.85)}" '
            f'letter-spacing="1.2">{i + 1}</text>'
        )
        for j, ln in enumerate(stage.split("\n")):
            c.add(text_el(ln, x + 14, top + 52 + j * 22,
                          dict(size=18.0, weight=600, track=-0.2, lh=1.2,
                               font=T.SANS), T.INK))
        if i < n - 1:
            ax = x + cw
            c.add(
                f'<path d="M{ax + 2} {top + band_h / 2} '
                f'L{ax + gap - 3} {top + band_h / 2}" '
                f'stroke="{T.rail(role, 0.8)}" stroke-width="2" '
                f'marker-end="url(#ah-{role}-solid)"/>'
            )
            from svg_kit import _arrowhead
            _arrowhead(c, role, "solid")

    # ---- components under each stage, carrying the authorship encoding
    cy = top + band_h + 20
    bottoms = []
    for i, (_stage, role, icon, comps) in enumerate(STAGES):
        x = T.SAFE + i * (cw + gap)
        y = cy
        for name, level, line in comps:
            if level == "concept":
                b = note(c, x, y, cw, [line], accent=role, title=name)
            else:
                b = card(c, Box(x, y, cw), name, role=role, level=level,
                         subtitle=line)
            y = b.bottom + 10
        bottoms.append(y)

    # ---- the authorship key, made unmissable
    ky = max(bottoms) + 26
    c.add(text_el("WHAT IS MINE, AND WHAT IS NOT", T.SAFE, ky, "lane",
                  T.ROLE["trust"]))
    ky += 16
    keys = [
        ("primary", "Implemented by me",
         "Preprocessor \u00b7 Loader \u00b7 Health Service \u00b7 Dashboard "
         "\u2014 four of the system's five services"),
        ("extended", "Significant contribution",
         "Entity Producer \u2014 it predates legal ingestion; I added EU/CELLAR "
         "capture and broker-confirmed publication"),
        ("integrated", "Existing platform",
         "PostgreSQL, Qdrant, Neo4j, MinIO, Kafka, the legal chatbot "
         "\u2014 integrated and configured, not authored"),
        ("external", "External / upstream",
         "The publishers themselves. Outside the system entirely."),
    ]
    kw = (c.width - 2 * T.SAFE - 3 * 18) / 4
    kb = []
    for i, (level, label, detail) in enumerate(keys):
        x = T.SAFE + i * (kw + 18)
        kb.append(card(c, Box(x, ky, kw), label,
                       role="trust" if level == "primary" else "neutral",
                       level=level, subtitle=detail))

    c.fit(max(b.bottom for b in kb) + 14, footnote=dict(
        lines=["This was not a chatbot over documents. The engineering problem "
               "was turning changing, heterogeneous authoritative information "
               "into structured, searchable, verifiable machine knowledge while "
               "preserving provenance \u2014 and giving operators control over "
               "ingestion, validation and lifecycle state. Most of the "
               "difficulty was in the second half of that sentence.",
               "One rule makes it debuggable: four stores, one writer each. "
               "That is why \u2018which service made this row wrong?\u2019 "
               "always has exactly one answer."],
        accent="trust", title="What the work actually was"),
        legend_spec=dict(levels=["primary", "extended", "integrated",
                                 "external"]))
    write(c, f"{OUT}/13-interview-system-overview.svg")


# ===========================================================================
# 14 - Failure, recovery and trust
# ===========================================================================
def d14_failure() -> None:
    c = Canvas(1920, 1320,
               eyebrow="Failure and recovery",
               title="What actually goes wrong, and what happens next",
               subtitle="Every row is a failure the repositories document, with "
                        "the recovery that exists — or the honest statement "
                        "that none does.")
    c.background()
    y0 = c.header()
    c.byline()

    rows = [
        ["Source download fails", "Health service cannot reach the publisher, or "
         "CELLAR negotiation fails", "Nothing published, nothing written",
         "Operator retries. Re-ingest is idempotent at this stage.", "recovered"],
        ["MinIO upload fails on a download-mode capture",
         "originUrl path, where MinIO is mandatory", "502; nothing published",
         "Operator retries", "recovered"],
        ["MinIO upload fails on an upload-mode capture",
         "file path, where MinIO is best-effort",
         "Tolerated: publication continues with the inline copy, and the event "
         "has no MinIO url", "Degraded but consistent", "degraded"],
        ["Kafka ack times out", "Producer cannot confirm publication",
         "503 — and the send may already have reached the broker",
         "A retry mints a new eventId, so the same bytes land under a second "
         "prefix. No compensation exists.", "accepted"],
        ["Orphaned capture", "MinIO is written before Kafka; publication then "
         "fails", "An object exists that no event references",
         "Nothing removes it. Recorded as a known consequence.", "accepted"],
        ["Pre-flight detects unknown structure",
         "A law whose markup the model does not represent",
         "BLOCKED before ingestion",
         "Stop and report the gap. Never weaken the gate or special-case the "
         "law.", "by design"],
        ["Embedding would be truncated",
         "A chunk exceeds the model's 8192-token window",
         "The whole law is refused rather than storing a vector that "
         "misrepresents its text",
         "Fix the chunking, then replay", "by design"],
        ["Qdrant converges, Neo4j fails", "Partial projection",
         "No law.embedded, offset uncommitted, consume loop ends",
         "Redelivery re-runs both stores from a fresh snapshot and converges "
         "identically", "recovered"],
        ["Crash between publish and commit", "Offset not yet committed",
         "law.embedded may be published twice",
         "The unique index on capture_id absorbs the duplicate", "recovered"],
        ["Stores disagree at rest", "Drift between canonical and derived state",
         "Reconciliation reports DRIFT_DETECTED",
         "Operator decides: re-ingest, or investigate. Nothing self-heals.",
         "operator"],
        ["A store is unreachable during a check", "Qdrant or Neo4j down",
         "CHECK_UNAVAILABLE — a first-class answer, distinct from "
         "disagreement", "Retry the sweep", "recovered"],
        ["Publisher has moved on", "The source file changed since capture",
         "currency.source_state reports SOURCE_CHANGED_REINGEST_REQUIRED",
         "Operator re-ingests. The old generation stays queryable until the new "
         "one completes.", "operator"],
        ["Ruleset changed since a generation was stored",
         "A byte changed in the parser, extractor or registry",
         "The recorded digest no longer matches the installed one; the corpus "
         "baseline fails and no law gets a verdict",
         "Re-extract from the held capture. If output is unchanged, revalidate; "
         "if it differs, replay.", "by design"],
        ["Withdrawal half-completes", "Canonical state committed, projection "
         "cleanup failed", "RECONCILIATION_REQUIRED 409 — the law is "
         "withdrawn and not served",
         "Retry re-runs cleanup. Evidence is never touched by any step.",
         "recovered"],
        ["A law is permanently unprocessable", "Parse or gate failure that "
         "redelivery cannot fix",
         "No dead-letter topic exists. It is redelivered for ever and blocks its "
         "partition.",
         "Manual intervention. This is the clearest gap in the pipeline.",
         "gap"],
    ]
    accent_for = {"recovered": "trust", "degraded": "store", "accepted": "warn",
                  "by design": "ui", "operator": "ui", "gap": "warn"}
    tm = matrix(c, T.SAFE, y0 + 30,
                ["Failure", "Where", "Immediate effect", "Recovery", "Class"],
                rows, widths=[330, 300, 400, 420, 158], rowh=54,
                accents=[accent_for[r[4]] for r in rows],
                label="matrix:failures")

    c.fit(tm.bottom + 12, footnote=dict(
        lines=["Three of these are labelled accepted and one is labelled gap. "
               "That is the point of the diagram: a pipeline with no "
               "dead-letter topic, no bounded retry and no automatic repair is a "
               "deliberate position for a legal corpus — an automatic "
               "self-heal that silently re-derives knowledge is, after the fact, "
               "indistinguishable from one that silently corrupted it — but "
               "it is a position with a real cost, and the cost is that one bad "
               "law can stall a partition until a human intervenes."],
        accent="warn", title="Accepted, not unnoticed"),
        legend_spec=dict(roles=["store", "trust", "ui", "warn"]))
    write(c, f"{OUT}/14-failure-recovery-and-trust.svg")


# ===========================================================================
# 15 - Document state machine
# ===========================================================================
def d15_doc_states() -> None:
    c = Canvas(1920, 1080,
               eyebrow="State model",
               title="The states a law actually occupies",
               subtitle="Reconstructed from the technical states, event "
                        "boundaries, gate verdicts and lifecycle columns that "
                        "exist in code — not from a generic lifecycle "
                        "template.")
    c.background()
    y0 = c.header()
    c.byline()

    sw, sg = 250, 74
    row1 = y0 + 56
    a = state(c, Box(T.SAFE, row1, sw), "REGISTERED", role="source",
              detail="in law_registry.yaml; may be ingestible: false")
    b = state(c, Box(T.SAFE + sw + sg, row1, sw), "CAPTURED", role="event",
              detail="bytes in MinIO, SHA-256 recorded")
    d = state(c, Box(T.SAFE + 2 * (sw + sg), row1, sw), "STRUCTURED",
              role="store", detail="canonical PostgreSQL committed")
    e = state(c, Box(T.SAFE + 3 * (sw + sg), row1, sw), "EMBEDDED", role="ai",
              detail="Qdrant and Neo4j converged, fences passed")
    f = state(c, Box(T.SAFE + 4 * (sw + sg), row1, sw), "MEASURED", role="ui",
              detail="every applicable gate has a verdict")

    # Row 2 sits directly under the state that produces it, so no transition has
    # to travel sideways across an unrelated node.
    row2 = max(x.bottom for x in (a, b, d, e, f)) + 96
    j = state(c, Box(T.SAFE, row2, sw), "BLOCKED", role="warn",
              detail="pre-flight refused it; never ingested", terminal=True)
    i = state(c, Box(T.SAFE + 2 * (sw + sg), row2, sw), "INTEGRITY FAILED",
              role="warn", detail="a required gate failed")
    h = state(c, Box(T.SAFE + 3 * (sw + sg), row2, sw), "SOURCE CHANGED",
              role="warn", detail="the publisher has moved on")
    g = state(c, Box(T.SAFE + 4 * (sw + sg), row2, sw), "VERIFIED", role="trust",
              detail="all required gates pass; currency valid", terminal=True)

    row3 = max(g.bottom, h.bottom, i.bottom, j.bottom) + 44
    k = state(c, Box(T.SAFE + 4 * (sw + sg), row3, sw), "WITHDRAWN",
              role="neutral", detail="withdrawn_at set; evidence retained",
              terminal=True)

    edge(c, a, b, kind="sync", role="event", gap=5, label="capture")
    edge(c, b, d, kind="async", role="event", gap=5, label="events.inbound",
         mono=True)
    edge(c, d, e, kind="async", role="event", gap=5, label="law.structured",
         mono=True)
    edge(c, e, f, kind="async", role="trust", gap=5, label="law.embedded",
         mono=True)
    edge(c, a, j, kind="blocked", role="warn", side_a="s", side_b="n", gap=5,
         label="pre-flight")
    edge(c, f, g, kind="sync", role="trust", side_a="s", side_b="n", gap=5,
         label="all pass")
    edge(c, f, h, kind="sync", role="warn", side_a="s", side_b="n", ta=0.35,
         tb=0.6, gap=5, bend=row2 - 30)
    edge(c, f, i, kind="sync", role="warn", side_a="s", side_b="n", ta=0.2,
         tb=0.55, gap=5, bend=row2 - 48)
    edge(c, g, k, kind="sync", role="neutral", side_a="s", side_b="n", gap=5,
         label="withdraw")
    edge(c, h, b, kind="sync", role="ui", side_a="n", side_b="s", ta=0.15,
         tb=0.72, gap=5, label="re-ingest", bend=row2 - 66)
    edge(c, i, b, kind="sync", role="ui", side_a="n", side_b="s", ta=0.15,
         tb=0.4, gap=5, bend=row2 - 80)

    ny = max(g.bottom, h.bottom, i.bottom, j.bottom, k.bottom) + 40
    n1 = note(c, T.SAFE, ny, (c.width - 2 * T.SAFE) / 2 - 18,
              ["Two of these are not derived from a status column, and that is "
               "the interesting part. EMBEDDED exists because the loader "
               "publishes an event only after both count fences pass, and "
               "MEASURED exists because the preprocessor consumes that event and "
               "runs the gates unasked.",
               "So the state model is enforced by the event contract rather than "
               "by a field somebody has to remember to set."],
              accent="trust", title="Where these states live")
    note(c, c.width / 2 + 10, ny, (c.width - 2 * T.SAFE) / 2 - 18,
         ["WITHDRAWN is not deletion. The laws row survives, withdrawn_at is "
          "set, and every piece of evidence — MinIO objects, raw documents, "
          "publisher captures, currency observations, verification checks — "
          "is untouched.",
          "A law leaving the corpus does not make the record of what its "
          "publisher served untrue. That sentence is in the source, and it is "
          "why withdrawal and deletion are different operations."],
         accent="neutral", title="Withdrawn is not deleted")

    c.fit(n1.bottom + 14, legend_spec=dict(
        roles=["source", "event", "ai", "store", "trust", "ui", "warn"],
        flows=["sync", "async", "blocked"]))
    write(c, f"{OUT}/15-document-state-machine.svg")


# ===========================================================================
# 16 - Executive overview (Level 1)
# ===========================================================================
def d16_executive() -> None:
    c = Canvas(1920, 720,
               eyebrow="Level 1 · Executive",
               title="Authoritative information, made trustworthy and machine-readable",
               subtitle="No technology names. Four capabilities and the promise "
                        "each one makes.")
    c.background()
    y0 = c.header()
    c.byline()

    bw = (c.width - 2 * T.SAFE - 3 * 44) / 4
    blocks = [
        ("Authoritative information", "source", "globe",
         "Published law and business documents, taken from the body that issues "
         "them",
         "We can always show which file we used, and when."),
        ("A knowledge platform", "ai", "brain",
         "Extraction, structure, citation resolution and semantic indexing",
         "Content becomes queryable without losing what it came from."),
        ("Verified knowledge", "trust", "shield",
         "Independent measurement of what was stored against what was served",
         "We can state what is trustworthy, and what is merely present."),
        ("Applications", "ui", "ui",
         "Grounded search and answering, with operator control of the lifecycle",
         "Answers cite provisions, and a person decides what enters the corpus."),
    ]
    boxes = []
    for i, (name, role, icon, what, promise) in enumerate(blocks):
        x = T.SAFE + i * (bw + 44)
        b = card(c, Box(x, y0 + 52, bw), name, role=role, level="primary",
                 icon=icon, subtitle=what)
        boxes.append(b)
    maxb = max(b.bottom for b in boxes)
    for i, (name, role, icon, what, promise) in enumerate(blocks):
        note(c, boxes[i].x, maxb + 20, bw, [promise], accent=role,
             title="The promise")
    for i in range(len(boxes) - 1):
        edge(c, boxes[i], boxes[i + 1], kind="sync", role=blocks[i + 1][1], gap=6)

    c.fit(maxb + 116, footnote=dict(
        lines=["The distinction that matters at this level: the platform does not "
               "only make information searchable, it makes claims about that "
               "information falsifiable. Every stored item can be re-derived from "
               "the publisher's own bytes under a recorded set of rules, and if it "
               "cannot be, the system says so rather than serving it quietly."],
        accent="trust", title="Why this is different from search"),
        legend_spec=dict(roles=["source", "ai", "trust", "ui"]))
    write(c, f"{OUT}/16-executive-overview.svg")


# ===========================================================================
# 17 - Verification, in six elements (the slide-grade and ten-second version)
# ===========================================================================
def d17_verification_essence() -> None:
    """A deliberately sparse companion to diagram 06.

    Diagram 06 is the full gate inventory and is the right artefact for a
    reader who can zoom. Projected at slide size its 14-row table becomes
    texture rather than content, so this version carries the same argument in
    six elements at a size that survives a screen share.
    """
    c = Canvas(1920, 900,
               eyebrow="Verification · the short version",
               title="Why the verdict is worth believing",
               subtitle="Six mechanisms. Each one exists to stop the "
                        "verification layer from confirming itself.")
    c.background()
    y0 = c.header()
    c.byline()

    cw = (c.width - 2 * T.SAFE - 2 * 26) / 3
    r1 = y0 + 48
    a = card(c, Box(T.SAFE, r1, cw), "1 · The bytes are hashed first",
             role="source", level="primary", icon="globe",
             subtitle="SHA-256 over the publisher's own file, before any parser "
                      "reads it. A claim about a law is only as good as the "
                      "bytes it came from.")
    b = card(c, Box(T.SAFE + cw + 26, r1, cw),
             "2 · A second, independent reading",
             role="trust", level="primary", icon="shield",
             subtitle="The structural denominator comes from a different XML "
                      "stack that imports no parser code, so a defect cannot "
                      "be common to both.")
    d = card(c, Box(T.SAFE + 2 * (cw + 26), r1, cw),
             "3 · The rules are hashed too",
             role="trust", level="primary", icon="shield",
             subtitle="Every generation records digests over the parser, the "
                      "reference extractor and the registry. A byte change is "
                      "a rule change.")

    r2 = max(a.bottom, b.bottom, d.bottom) + 30
    e = card(c, Box(T.SAFE, r2, cw), "4 · The prover proves itself",
             role="trust", level="primary", icon="shield",
             subtitle="If any already-certified law stops reproducing under "
                      "today's rules, no law gets a verdict — including "
                      "the one being certified.")
    f = card(c, Box(T.SAFE + cw + 26, r2, cw),
             "5 · Fourteen gates, none hidden",
             role="trust", level="primary", icon="shield",
             subtitle="Seven are required for the badge; all fourteen are "
                      "recorded and displayed. A measurement nobody can see is "
                      "not a measurement.")
    g = card(c, Box(T.SAFE + 2 * (cw + 26), r2, cw),
             "6 · Four answers, never one badge",
             role="ui", level="primary", icon="ui",
             subtitle="Verification status, verdict freshness, source currency "
                      "and live store integrity stay separate, so a green "
                      "summary cannot hide which one failed.")

    for x, y in ((a, b), (b, d), (e, f), (f, g)):
        edge(c, x, y, kind="sync", role="trust", gap=5)
    edge(c, d, e, kind="sync", role="trust", side_a="s", side_b="n",
         ta=0.5, tb=0.5, bend=r2 - 15)

    c.fit(max(e.bottom, f.bottom, g.bottom) + 12, footnote=dict(
        lines=["And the two limits that travel with it: a count matching is "
               "not proof — a citation misread onto a provision that does "
               "exist moves no count and fails no gate — and COMPLETE is "
               "machine structural assurance, not legal review. No law in the "
               "corpus is human-certified.",
               "The full gate inventory, the verdict pipeline and the three "
               "operations are in diagram 06."],
        accent="warn", title="What this does not claim"),
        legend_spec=dict(roles=["source", "trust", "ui"], flows=["sync"],
                         levels=["primary"]))
    write(c, f"{OUT}/17-verification-essence.svg")


ALL = [d10_insurance, d11_events, d12_contributions, d13_interview,
       d14_failure, d15_doc_states, d16_executive, d17_verification_essence]
