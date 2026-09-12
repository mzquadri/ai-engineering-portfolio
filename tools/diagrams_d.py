"""Diagrams 18-19: the AI Radiologist, and the AI Compliance product.

Both are evidenced workstreams that earlier revisions of this portfolio
under-reported. Every figure below was read from source on 2026-09-12:

  AI Radiologist   ai-prediction-service/src/ai_prediction/
                   ai-utils/bp_itcs_ibp_ai_utils/constants.py
                   ai-utils/bp_itcs_ibp_ai_utils/events/ai_prediction.py
  AI Compliance    local-env/ibp/ai-compliance{,-backend}/*.yaml
                   knowledge-db-ingestion-loader/docs/questionnaire-ingestion.md
                   knowledge-db-ingestion-loader/app/service/
                       questionnaire_loading_service.py

Authorship is stated per component. The questionnaire ingestion path runs
inside a service I implemented but the feature itself was written by a
colleague -- it is classed Integration / shared, not mine.
"""

from __future__ import annotations

import design_tokens as T
from svg_kit import (Box, Canvas, card, edge, lane_around, line_height, matrix,
                     note, pill, store, text_el, wrap, write)

OUT = "assets/architecture"

# Verbatim from ai-utils/bp_itcs_ibp_ai_utils/constants.py and
# events/ai_prediction.py. Threshold = Youden's J on the CheXpert validation
# set; ICD-10 and the baseline urgency ship with the clinical metadata.
FINDINGS = [
    ("Atelectasis", "0.329", "J98.11", "Partial lung collapse"),
    ("Cardiomegaly", "0.130", "I51.7", "Enlarged heart"),
    ("Consolidation", "0.234", "R91.8", "Airspace filled with fluid"),
    ("Edema", "0.233", "J81.0", "Fluid in the lungs"),
    ("Effusion", "0.424", "J90", "Fluid in the pleural space"),
]


# ===========================================================================
# 18 - AI Radiologist
# ===========================================================================
def d18_radiologist() -> None:
    c = Canvas(1920, 1500,
               eyebrow="Computer vision · research prototype",
               title="Multi-label chest X-ray classification with "
                     "explainability",
               subtitle="Internal project name: “AI Radiologist”. A "
                         "research/prototype medical-imaging classification "
                         "pipeline — not a medical device and not clinically "
                         "deployed. Five findings, one calibrated threshold "
                         "each, and a Grad-CAM++ attribution map.")
    c.background()
    y0 = c.header()
    c.byline()

    # ---------------- the pipeline
    cw, gap = 292, 50
    cols = [T.SAFE + i * (cw + gap) for i in range(5)]
    ry = y0 + 46

    ing = card(c, Box(cols[0], ry, cw), "Study arrives",
               role="source", level="integrated", icon="document",
               subtitle="A medical image is uploaded and an event names it; "
                        "the bytes live in object storage",
               meta=["ibp.events.inbound",
                     "entityType: MEDICAL_IMAGE"])
    pre = card(c, Box(cols[1], ry, cw), "Preprocess",
               role="ai", level="extended", icon="bolt",
               subtitle="Decode, resize to the model's input geometry, "
                        "normalise",
               meta=["224 × 224 · IMAGE_SIZE",
                     "max dimension 800 on re-encode"])
    clf = card(c, Box(cols[2], ry, cw), "Classify",
               role="ai", level="extended", icon="brain",
               subtitle="DenseNet-121 with a dropout + linear head over five "
                        "findings. Sigmoid per class, not softmax — a "
                        "study can show several findings at once.",
               meta=["DenseNet121-v2.0.0",
                     "torchvision · CUDA or DirectML"])
    cam = card(c, Box(cols[3], ry, cw), "Attribute",
               role="trust", level="extended", icon="shield",
               subtitle="Grad-CAM++ over the final convolutional block, "
                        "showing which regions drove each positive finding",
               meta=["Chattopadhay et al., WACV 2018",
                     "keep 40% · floor 10%"])
    rep = card(c, Box(cols[4], ry, cw), "Report",
               role="ui", level="extended", icon="ui",
               subtitle="Per-finding probability, its threshold, the verdict, "
                        "an urgency band and an ICD-10 code; heatmap written "
                        "to object storage",
               meta=["ibp.events.ai.processed",
                     "jet colormap · alpha 0.40"])

    for a, b in ((ing, pre), (pre, clf), (clf, cam), (cam, rep)):
        edge(c, a, b, kind="sync", role="ai", gap=5)
    lane_around(c, [ing, pre, clf, cam, rep],
                "Inference path · one study",
                caption="event in, enriched event out", accent="ai")

    # ---------------- the decision table
    ty = max(b.bottom for b in (ing, pre, clf, cam, rep)) + 46
    c.add(text_el("FIVE FINDINGS, FIVE DECISION THRESHOLDS", T.SAFE, ty,
                  "lane", T.ROLE["trust"]))
    ty += 16
    mt = matrix(c, T.SAFE, ty,
                ["Finding", "Threshold", "ICD-10", "What it means"],
                [[f, th, icd, desc] for f, th, icd, desc in FINDINGS],
                widths=[260, 180, 160, 512], rowh=34, mono_cols={1, 2},
                accents=["ai"] * 5, label="matrix:findings")

    nx = T.SAFE + 1140
    nw = c.width - T.SAFE - nx
    n1 = note(c, nx, ty, nw,
              ["A single global cut-off would have been wrong for every class. "
               "Cardiomegaly is called positive at 0.130 and Effusion only at "
               "0.424 — the same raw score means different things per "
               "finding.",
               "The thresholds are Youden's J optima from a validation set, so "
               "each one maximises sensitivity plus specificity for its own "
               "class rather than for the average."],
              accent="trust", title="Why per-class thresholds")
    n2 = note(c, nx, n1.bottom + 18, nw,
              ["Presence and urgency are answered separately. Presence uses "
               "the calibrated per-class threshold; urgency uses fixed "
               "probability bands — HIGH at 0.70, MODERATE at 0.40, "
               "otherwise LOW.",
               "Collapsing the two would make a confident low-acuity finding "
               "look like an emergency, and a borderline high-acuity one look "
               "routine."],
              accent="ui", title="Presence is not urgency")

    # ---------------- the interesting decision
    dy = max(mt.bottom, n2.bottom) + 44
    c.add(text_el("A DESIGN DECISION \u00b7 FACT FROM CODE, THEN MY READING OF IT",
                  T.SAFE, dy, "lane", T.ROLE["warn"]))
    dy += 16
    dw = (c.width - 2 * T.SAFE - 2 * 26) / 3
    a1 = card(c, Box(T.SAFE, dy, dw), "Fact \u00b7 what exists in the code",
              role="ai", level="extended", icon="brain",
              subtitle="A per-finding anatomical prior: cardiomegaly centre-left, "
                       "effusion lower, edema perihilar, each with a boost "
                       "factor. It is boost-only \u2014 the mask never suppresses, "
                       "it only emphasises.")
    a2 = card(c, Box(T.SAFE + dw + 26, dy, dw),
              "Fact \u00b7 it is switched off",
              role="warn", level="extended", icon="alert",
              subtitle="USE_ANATOMICAL_HINTS = False, commented \u201cDISABLED \u2014 "
                       "trust Grad-CAM fully\u201d. The code states the model\u2019s "
                       "attention is the ground truth for localisation and the "
                       "hints are soft only.")
    a3 = card(c, Box(T.SAFE + 2 * (dw + 26), dy, dw),
              "My reading \u00b7 not documented in the code",
              role="ui", level="extended", icon="ui",
              subtitle="An engineering concern is that an anatomical prior could "
                       "bias localisation towards expected anatomy, so the "
                       "attribution would tend to agree with the label rather than "
                       "show what the model used. That rationale is my interpretation "
                       "of the decision, not a comment in the source.")
    for a, b in ((a1, a2), (a2, a3)):
        edge(c, a, b, kind="sync", role="warn", gap=5)

    c.fit(max(a1.bottom, a2.bottom, a3.bottom) + 14, footnote=dict(
        lines=["I read this as the same shape of decision as the legal corpus\u2019s "
               "structural oracle \u2014 a check that shares the assumption of the "
               "thing it checks cannot falsify it. That parallel is my own "
               "framing across two codebases, not a claim that either was built "
               "with the other in mind.",
               "Stated plainly: a research/prototype classification pipeline with "
               "explainability and calibrated thresholds. Not a medical device, "
               "not clinically validated or deployed, no regulatory clearance, "
               "and no accuracy figure is claimed anywhere in this portfolio."],
        accent="trust", title="Interpretation, and the limits"),
        legend_spec=dict(roles=["source", "ai", "store", "trust", "ui", "warn"],
                         flows=["sync"],
                         levels=["primary", "extended", "integrated"]))
    write(c, f"{OUT}/18-ai-radiologist.svg")


# ===========================================================================
# 19 - AI Compliance
# ===========================================================================
def d19_compliance() -> None:
    c = Canvas(1920, 1480,
               eyebrow="Product · insurance AI compliance",
               title="AI Compliance — what the legal corpus is actually for",
               subtitle="The customer-facing assessment product. It is the "
                        "reason the Legal Knowledge Database has to be "
                        "verifiable: its answers become a compliance report "
                        "somebody relies on.")
    c.background()
    y0 = c.header()
    c.byline()

    cw, gap = 300, 48
    cols = [T.SAFE + i * (cw + gap) for i in range(5)]
    ry = y0 + 46

    ui = card(c, Box(cols[0], ry, cw), "Assessment UI",
              role="ui", level="integrated", icon="ui",
              subtitle="Next.js app on Bun. Customer works through a "
                       "structured questionnaire; password, magic-link or SSO",
              meta=[":4000 · auth: local | keycloak"])
    be = card(c, Box(cols[1], ry, cw), "Compliance backend",
              role="ui", level="integrated", icon="service",
              subtitle="Spring Boot on JDK 25. Owns assessments, publishes "
                       "work, consumes results, renders the report",
              meta=[":4010 · PostgreSQL ai_compliance"])
    scan = card(c, Box(cols[2], ry, cw), "Website scan",
                role="ai", level="integrated", icon="globe",
                subtitle="Drives a headless browser over the customer's site "
                         "to gather evidence the questionnaire cannot ask for",
                meta=["Playwright over websocket"])
    kb = card(c, Box(cols[3], ry, cw), "Knowledge processor",
              role="ai", level="integrated", icon="brain",
              subtitle="Reads questions, answers and flags with their "
                       "embeddings from the graph, retrieves the relevant "
                       "provisions, and produces a grounded assessment",
              meta=["consumes ibp.events.inbound"])
    rpt = card(c, Box(cols[4], ry, cw), "Report",
               role="trust", level="integrated", icon="document",
               subtitle="Rendered to PDF by a headless browser behind a "
                        "short-lived render token",
               meta=["token TTL 120s",
                     "evidence bucket: assessment-evidence"])

    edge(c, ui, be, kind="sync", role="ui", label="REST")
    edge(c, be, scan, kind="sync", role="ai", label="scan")
    edge(c, be, kb, kind="async", role="event", side_a="s", side_b="s",
         ta=0.75, tb=0.25, label="ibp.events.inbound", mono=True,
         bend=ry + 210)
    edge(c, kb, rpt, kind="sync", role="trust")
    lane_around(c, [ui, be, scan, kb, rpt], "The product",
                caption="existing platform · not my code", accent="ui")

    ty = max(b.bottom for b in (ui, be, scan, kb, rpt)) + 74
    t1 = pill(c, cols[1], ty, "ibp.events.inbound")
    t2 = pill(c, cols[2] + 20, ty, "ibp.events.ai.processed")
    t3 = pill(c, cols[3] + 60, ty + 42,
              "ibp.events.ai-compliance.results.dlt", role="warn")
    edge(c, t2, be, kind="async", role="event", side_a="n", side_b="s",
         ta=0.5, tb=0.35, label="results")
    edge(c, t2, t3, kind="async", role="warn", side_a="s", side_b="w",
         label="undeliverable")

    # ---------------- the bridge into the legal corpus
    by = t3.bottom + 46
    c.add(text_el("WHERE IT MEETS THE LEGAL KNOWLEDGE DATABASE",
                  T.SAFE, by, "lane", T.ROLE["trust"]))
    by += 16
    bw = (c.width - 2 * T.SAFE - 3 * 22) / 4
    q1 = card(c, Box(T.SAFE, by, bw), "Questionnaire published",
              role="event", level="integrated", icon="document",
              subtitle="A new questionnaire version lands in object storage "
                       "and an event announces it",
              meta=["domain: AI_COMPLIANCE",
                    "entityType: QUESTIONNAIRE"])
    q2 = card(c, Box(T.SAFE + bw + 22, by, bw), "Loader ingests it",
              role="ai", level="shared", icon="service",
              subtitle="A second consumer path inside the ingestion loader: "
                       "fetch, skip if the content hash is unchanged, embed, "
                       "store",
              meta=["questionnaire_loading_service.py",
                    "BGE-M3 · 1024-dim"])
    q3 = store(c, Box(T.SAFE + 2 * (bw + 22), by, bw),
               "Neo4j · questionnaire graph", kind="graph",
               level="shared",
               subtitle="Questions, answers and compliance flags as nodes, "
                        "each carrying its own embedding",
               meta=["HAS_QUESTION · HAS_OPTION",
                     "TRIGGERS_FLAG"])
    q4 = card(c, Box(T.SAFE + 3 * (bw + 22), by, bw),
              "Processor reads the graph",
              role="ai", level="integrated", icon="brain",
              subtitle="Takes questions, answers, flags and embeddings "
                       "straight from the graph, so it needs no embedding "
                       "model of its own",
              meta=["no local BGE-M3"])
    for a, b in ((q1, q2), (q2, q3), (q3, q4)):
        edge(c, a, b, kind="sync", role="trust", gap=5)
    lane_around(c, [q1, q2, q3, q4],
                "The questionnaire bridge",
                caption="a colleague's feature, inside a service I built",
                accent="trust")

    ny = max(q1.bottom, q2.bottom, q3.bottom, q4.bottom) + 44
    half = (c.width - 2 * T.SAFE) / 2 - 18
    n1 = note(c, T.SAFE, ny, half,
              ["This is the answer to ‘why build a verification layer at "
               "all?’. A compliance report tells an insurance customer "
               "whether they meet an obligation, and cites the provision it "
               "relied on. If the corpus behind that citation has drifted from "
               "what the publisher actually served, the report is confidently "
               "wrong — and nobody downstream can tell.",
               "So the gates, the provenance digests and the four separate "
               "trust answers are not engineering decoration. They are what "
               "makes this product's output defensible."],
              accent="trust", title="Why the corpus has to be verifiable")
    note(c, T.SAFE + half + 36, ny, half,
         ["The product itself is not my work. The assessment UI, the backend, "
          "the website scan and the knowledge processor were built by "
          "colleagues, and their repositories are not in the workspace this "
          "portfolio was audited from — so no internal detail is drawn.",
          "The questionnaire ingestion path is a colleague's feature living "
          "inside a service I implemented: I implemented the loader, its Kafka "
          "handling and its embedding and graph-write layers; the "
          "questionnaire service on top of them is not mine to claim. It is "
          "marked Integration / shared, and its author is credited in the "
          "private evidence pack."],
         accent="neutral", title="Whose work this is")

    c.fit(n1.bottom + 14, legend_spec=dict(
        roles=["event", "ai", "store", "trust", "ui", "warn"],
        flows=["sync", "async"],
        levels=["shared", "integrated"]))
    write(c, f"{OUT}/19-ai-compliance.svg")


ALL = [d18_radiologist, d19_compliance]
