"""Diagrams 06-09: verification, RAG query path, control plane, state machine.

Gate ids come verbatim from
the knowledge-db-ingestion-preprocessor at app/verification/gates.py:65-78.
Badge/DE/EU applicability is reconciled against families/formex.py -- see
private/audit/07-evidence-matrix.md rows VER-2, VER-2b, VER-2c.
"""

from __future__ import annotations

import design_tokens as T
from svg_kit import (Box, Canvas, card, edge, lane_around, legend, line_height,
                     matrix, note, pill, state, step, store, text_el, wrap,
                     write)

OUT = "assets/architecture"

# The fourteen gates, with the family each applies to.
GATES = [
    ("fidelity.raw_integrity", "is the archived file still the file we captured?",
     "required", "yes", "yes"),
    ("currency.source_state", "has the publisher's file changed?",
     "required", "yes", "yes"),
    ("provenance.pipeline_profile", "which declared pipeline produced this?",
     "required", "yes", "yes"),
    ("structure.section_inventory", "is every source unit present?",
     "required", "yes", "yes"),
    ("fidelity.qdrant_payload", "does search match the database?",
     "required", "yes", "yes"),
    ("fidelity.neo4j_graph", "does the graph match the database?",
     "required", "yes", "yes"),
    ("fidelity.xml_byte_partition", "does the stored text reconstruct the source?",
     "required", "yes", "not applicable"),
    ("fidelity.served_text", "is served text what the declared pipeline makes of it?",
     "recorded", "yes", "yes"),
    ("fidelity.reference_extraction", "does every stored reference reproduce?",
     "recorded", "yes", "yes"),
    ("fidelity.source_structure", "is each served unit exactly one publisher unit?",
     "recorded", "yes", "yes"),
    ("fidelity.source_substructure", "is the evidence tree what the source contains?",
     "recorded", "yes", "yes"),
    ("fidelity.citation_completeness", "is any detected citation missing?",
     "recorded", "yes", "yes"),
    ("provenance.publisher_capture", "is this archive bound to a described fetch?",
     "recorded", "yes", "yes"),
    ("structure.source_profile", "is the source served now inside our profile?",
     "recorded", "yes", "not applicable"),
]


# ===========================================================================
# 06 - Verification and reconciliation
# ===========================================================================
def d06_verification() -> None:
    c = Canvas(1920, 1400,
               eyebrow="Trust and verification",
               title="Can we trust the knowledge currently being served?",
               subtitle="Fourteen gates answer it, and the answer is never one "
                        "badge. Seven gates are required for the aggregate; the "
                        "other seven are recorded and shown, because a hidden "
                        "measurement is not a measurement.")
    c.background()
    y0 = c.header()
    c.byline()

    # ---- the gate inventory
    gw = [318, 430, 108, 74, 132]
    mt = matrix(c, T.SAFE, y0 + 34,
                ["Gate id", "Question it asks", "Badge", "DE", "EU"],
                [[g[0], g[1], g[2], g[3], g[4]] for g in GATES],
                widths=gw, mono_cols={0},
                accents=["trust"] * 6 + ["trust"] + ["ui"] * 7,
                rowh=31, label="matrix:gates")
    text_el("", 0, 0, "meta", T.INK)
    c.add(text_el("THE FOURTEEN GATES", T.SAFE, y0 + 20, "lane", T.ROLE["trust"]))

    # ---- how a verdict is produced
    px = T.SAFE + sum(gw) + 46
    pwid = c.width - T.SAFE - px
    c.add(text_el("HOW A VERDICT IS PRODUCED", px, y0 + 20, "lane", T.ROLE["trust"]))

    cap = card(c, Box(px, y0 + 34, pwid), "1 · Captured source, digest-proven",
               role="source", level="primary", icon="globe",
               subtitle="The publisher's own bytes, in MinIO, hashed at capture",
               meta=["fidelity.raw_integrity"])
    ora = card(c, Box(px, cap.bottom + 16, pwid),
               "2 · An independent denominator",
               role="trust", level="primary", icon="shield",
               subtitle="A second inventory of the same markup on a different "
                        "stack \u2014 lxml streaming events, where production "
                        "parses the whole tree \u2014 importing no parser code",
               meta=["tools/oracle_gii_structure.py"])
    base = card(c, Box(px, ora.bottom + 16, pwid),
                "3 · The prover proves itself first",
                role="trust", level="primary", icon="shield",
                subtitle="If any already-certified law no longer reproduces under "
                         "today's rules, no law gets a verdict — including "
                         "the one being certified",
                meta=["tools/prove_law.py"])
    ver = card(c, Box(px, base.bottom + 16, pwid), "4 · Run every applicable gate",
               role="trust", level="primary", icon="shield",
               subtitle="Triggered automatically by law.embedded, or on demand by "
                        "an operator. Observer only.",
               meta=["POST /internal/laws/{key}/verify"])
    rec = store(c, Box(px, ver.bottom + 16, pwid), "5 · verification_checks",
                kind="relational", level="primary",
                subtitle="One row per gate per generation. The dashboard badge is "
                         "read back from a view over this table.",
                meta=["law_verification_state"])

    for a, b in ((cap, ora), (ora, base), (base, ver), (ver, rec)):
        edge(c, a, b, kind="sync", role="trust", side_a="s", side_b="n", gap=3)

    nb = note(c, px, rec.bottom + 22, pwid,
              ["A count matching is not proof. A citation misread onto a "
               "provision that does exist produces no orphan, moves no count and "
               "fails no gate — which is why a separate human review of "
               "citation targets exists alongside the machine gates.",
               "COMPLETE is machine structural assurance. It is not legal review, "
               "and no law in the corpus claims to be human-certified."],
              accent="warn", title="What the gates cannot see")

    # ---- the four trust questions, in the space beside the verdict column
    fy = mt.bottom + 34
    c.add(text_el("FOUR QUESTIONS, FOUR ANSWERS · NEVER ONE BADGE",
                  T.SAFE, fy, "lane", T.ROLE["ui"]))
    fy += 16
    fw = (sum(gw) - 3 * 16) / 4
    fboxes = []
    for i, (q, a, role) in enumerate([
        ("Verification status", "VERIFIED · MEASURED · NOT_INGESTED "
         "· NOT_INGESTIBLE", "trust"),
        ("Verdict freshness", "how old the measurement itself is", "ui"),
        ("Source currency", "has the publisher moved since we captured?", "source"),
        ("Live store integrity", "do Qdrant and Neo4j still match PostgreSQL?",
         "store"),
    ]):
        fboxes.append(card(c, Box(T.SAFE + i * (fw + 16), fy, fw), q,
                           role=role, level="primary", subtitle=a))
    note(c, T.SAFE, max(b.bottom for b in fboxes) + 14, sum(gw),
         ["A single green summary would hide which of the four actually failed, "
          "so the dashboard keeps them apart. A law can be structurally perfect "
          "and out of date; it can be current and have drifted in one derived "
          "store. Those are different problems with different fixes, and one "
          "badge cannot say which you have."],
         accent="warn", title="Why they are not merged")

    # ---- three operations
    oy = max(mt.bottom, nb.bottom,
             max(b.bottom for b in fboxes) + 100) + 46
    c.add(text_el("THREE OPERATIONS TOUCH A LAW · ONLY ONE CHANGES IT",
                  T.SAFE, oy, "lane", T.ROLE["ui"]))
    ow = (c.width - 2 * T.SAFE - 2 * 30) / 3
    oy += 20

    ops = [
        ("Reconciliation", "ui", "changes nothing",
         ["Read PostgreSQL identity tuples",
          "Compare Qdrant and Neo4j",
          "Report LIVE_CONSISTENT, DRIFT_DETECTED or CHECK_UNAVAILABLE"],
         "LIVE_CONSISTENT is the last sweep's answer, not a standing guarantee.",
         "POST /reconciliation-sweep"),
        ("Verify", "trust", "changes nothing",
         ["Poll the publisher, write a currency observation",
          "Ask the preprocessor to run the gates",
          "Return one outcome plus every gate verdict"],
         "It changes no version, section, chunk, vector or edge. Observer only.",
         "POST /laws/{key}/verify"),
        ("Re-ingest", "warn", "changes the corpus",
         ["Fetch the source, submit a new capture",
          "Preprocessor rewrites canonical state",
          "Loader reconverges Qdrant and Neo4j"],
         "Zero-downtime: nothing is purged first, so the old generation stays "
         "queryable and a failed ingest leaves it untouched.",
         "POST /laws/{key}/reingest"),
    ]
    bottoms = []
    for i, (name, role, kind, steps, insight, route) in enumerate(ops):
        x = T.SAFE + i * (ow + 30)
        b = card(c, Box(x, oy, ow), f"{name} · {kind}",
                 role=role, level="primary",
                 icon={"ui": "ui", "trust": "shield", "warn": "alert"}[role],
                 meta=[route])
        yy = b.bottom + 18
        for j, s in enumerate(steps):
            lines = wrap(s, "meta", ow - 40, where=f"op step {s!r}")
            step(c, x + 13, yy + 2, j + 1, accent=role, r=9)
            for k, ln in enumerate(lines):
                c.add(text_el(ln, x + 30, yy + 6 + k * line_height("meta"),
                              "meta", T.INK_MUTED))
            yy += max(len(lines) * line_height("meta"), 16) + 10
        ib = note(c, x, yy + 4, ow, [insight], accent=role)
        bottoms.append(ib.bottom)

    c.fit(max(bottoms), footnote=dict(
        lines=["The distinction is the architecture. Two of the three operations "
               "are measurements and one is a mutation, and they are built so "
               "that an operator cannot reach for the mutation by accident: "
               "re-ingest requires DATA_SOURCE=live and LIFECYCLE_ACTIONS_ENABLED, "
               "while verify and reconcile need neither. A system that makes "
               "measuring as expensive as changing gets measured less often."],
        accent="trust", title="Why measurement and mutation are separated"),
        legend_spec=dict(roles=["source", "store", "trust", "ui", "warn"],
                         flows=["sync", "verify"], levels=["primary"]))
    write(c, f"{OUT}/06-verification-and-reconciliation.svg")


# ===========================================================================
# 07 - RAG query flow
# ===========================================================================
def d07_rag() -> None:
    c = Canvas(1920, 1100,
               eyebrow="Query time",
               title="Retrieval and grounded answering",
               subtitle="The query path is deliberately separate from the "
                        "ingestion path. Nothing here writes a store, and "
                        "nothing here parses a law.")
    c.background()
    y0 = c.header()
    c.byline()

    # ---- the verified path
    c.add(text_el("VERIFIED IN THIS WORKSPACE", T.SAFE, y0 + 18, "lane",
                  T.ROLE["trust"]))
    cw = 250
    gap = 76
    ry = y0 + 34
    q = card(c, Box(T.SAFE, ry, cw), "Query",
             role="ui", level="integrated", icon="ui",
             subtitle="Operator search, or a question arriving as an event",
             meta=["GET /search · ibp.events.inbound"])
    emb = card(c, Box(T.SAFE + cw + gap, ry, cw), "Embed the query",
               role="ai", level="primary", icon="brain",
               subtitle="BGE-M3, the same model that embedded the corpus",
               meta=["dense 1024 + sparse"])
    ret = card(c, Box(T.SAFE + 2 * (cw + gap), ry, cw), "Hybrid retrieval",
               role="ai", level="primary", icon="bolt",
               subtitle="Dense and sparse prefetch, fused server-side by RRF",
               meta=["prefetch = max(limit, 20)"])
    qd = store(c, Box(T.SAFE + 3 * (cw + gap), ry, cw), "Qdrant",
               kind="vector", level="primary",
               subtitle="One point per chunk, both law families in one collection",
               meta=["payload: law, section_number,", "title, raw_text"])
    ctx = card(c, Box(T.SAFE + 4 * (cw + gap), ry, cw), "Cited chunks",
               role="trust", level="primary", icon="document",
               subtitle="Section number and law key travel with every chunk, so a "
                        "citation is data rather than generated text",
               meta=["section_number · law"])

    edge(c, q, emb, kind="sync", role="ui")
    edge(c, emb, ret, kind="sync", role="ai")
    edge(c, ret, qd, kind="verify", role="store", label="query_points")
    edge(c, qd, ctx, kind="sync", role="trust")

    # ---- the answering stage, not inspectable here
    ay = max(q.bottom, ctx.bottom) + 62
    c.add(text_el("ANSWERING · EXISTING COMPONENT, NOT INSPECTABLE IN THIS "
                  "WORKSPACE", T.SAFE, ay, "lane", T.ROLE["neutral"]))
    ay += 18
    g1 = card(c, Box(T.SAFE, ay, cw), "Graph expansion",
              role="store", level="integrated", icon="graph",
              subtitle="Neo4j holds what each provision cites; the chatbot has "
                       "access to it",
              meta=["needs verification"])
    g2 = card(c, Box(T.SAFE + cw + gap, ay, cw), "Legal Chatbot",
              role="ai", level="integrated", icon="brain",
              subtitle="Consumes ibp.events.inbound, publishes "
                       "ibp.events.ai.processed",
              meta=["repository not present here"])
    g3 = card(c, Box(T.SAFE + 2 * (cw + gap), ay, cw), "LLM",
              role="ai", level="integrated", icon="brain",
              subtitle="Self-hosted, OpenAI-compatible endpoint; the container "
                       "runs fully offline for weights",
              meta=["HF_HUB_OFFLINE=1"])
    g4 = card(c, Box(T.SAFE + 3 * (cw + gap), ay, cw), "Grounded answer",
              role="ui", level="integrated", icon="document",
              subtitle="Returned with the provisions it was built from",
              meta=["ibp.events.ai.processed"])
    g5 = card(c, Box(T.SAFE + 4 * (cw + gap), ay, cw), "Citation validation",
              role="warn", level="integrated", icon="alert",
              subtitle="Check each cited section against the corpus before the "
                       "answer is shown. Zero LLM calls.",
              meta=["DESIGNED, NOT IMPLEMENTED"])

    edge(c, ctx, g2, kind="sync", role="ai", side_a="s", side_b="n",
         ta=0.5, tb=0.5, bend=ay - 30)
    edge(c, g1, g2, kind="verify", role="store")
    edge(c, g2, g3, kind="sync", role="ai")
    edge(c, g3, g4, kind="sync", role="ai")
    edge(c, g4, g5, kind="verify", role="warn")

    nb = note(c, T.SAFE, max(g1.bottom, g5.bottom) + 26,
              (c.width - 2 * T.SAFE) / 2 - 20,
              ["Ingestion-time components write stores and are the only things "
               "that do. Query-time components read. The separation is why a "
               "retrieval bug cannot corrupt the corpus and why an ingestion "
               "replay cannot be triggered by a question.",
               "One consequence worth stating: the query path has no verification "
               "gate of its own. It trusts the corpus because the corpus was "
               "verified before it was served — which is exactly why the "
               "gates and the badge exist upstream."],
              accent="ai", title="Two paths, one corpus")
    note(c, c.width / 2 + 10, nb.y, (c.width - 2 * T.SAFE) / 2 - 20,
         ["The answer-level citation check is a design position, not delivered "
          "work. An LLM that cites a section which does not exist is the specific "
          "failure that makes a legal assistant dangerous, and validating cited "
          "section numbers against the corpus costs no model call.",
          "What does ship today is upstream of that: provenance on the source, "
          "structural fidelity gates on the extraction, and retrieval that "
          "carries the law key and section number as payload rather than as "
          "prose."],
         accent="warn", title="Where hallucinated citations are addressed — "
                              "and where they are not yet")

    c.fit(nb.bottom + 16, legend_spec=dict(
        roles=["ai", "store", "trust", "ui", "warn"],
        flows=["sync", "verify"],
        levels=["primary", "integrated"]))
    write(c, f"{OUT}/07-rag-query-flow.svg")


# ===========================================================================
# 08 - Operator control plane
# ===========================================================================
def d08_control_plane() -> None:
    c = Canvas(1920, 1200,
               eyebrow="Operations",
               title="The operator control plane",
               subtitle="Four actions, and what each one actually triggers behind "
                        "the button. The dashboard decides nothing: every badge it "
                        "shows was decided by a gate and read back through one "
                        "backend.")
    c.background()
    y0 = c.header()
    c.byline()

    dash = card(c, Box(T.SAFE, y0 + 40, 300), "Legal KB Dashboard",
                role="ui", level="primary", icon="ui",
                subtitle="7 pages · 27 components · 9 route handlers. "
                         "Holds no database, queue or object-store client.",
                meta=["one env var: LEGAL_KB_API_URL", "server-side only"])
    hs = card(c, Box(T.SAFE, dash.bottom + 24, 300), "Health Service",
              role="ui", level="primary", icon="service",
              subtitle="The only backend. Owns currency, snapshots and the audit "
                       "log; inspects everything else.",
              meta=["23 routes under /api/v1"])
    edge(c, dash, hs, kind="sync", role="ui", side_a="s", side_b="n")
    lane_around(c, [dash, hs], "Operator surface", accent="ui")

    ax = T.SAFE + 340
    aw = c.width - T.SAFE - ax
    rows = [
        ("Ingest / Re-ingest", "warn", "POST /laws/{key}/reingest",
         ["Health service downloads the current source itself, or resolves the "
          "CELEX for an EU act",
          "Entity Producer captures the bytes, hashes them, writes MinIO, "
          "publishes events.inbound",
          "Preprocessor rewrites canonical state in one transaction and "
          "publishes law.structured",
          "Loader re-embeds and reconverges Qdrant and Neo4j, then publishes "
          "law.embedded",
          "That event triggers verification with nobody asking for it"],
         "Returns 202 immediately. The old generation stays queryable throughout "
         "and a failed ingest leaves it untouched."),
        ("Verify", "trust", "POST /laws/{key}/verify",
         ["Poll the publisher and bind the result to the capture id",
          "Write one currency_observations row — evidence, not a verdict",
          "Ask the preprocessor to run every applicable gate",
          "Return one outcome plus the per-gate verdicts"],
         "Takes minutes legitimately, so the route sets no-store and a 300-second "
         "timeout. A default fetch timeout would have reported a failure that "
         "never happened."),
        ("Reconcile", "ui", "POST /reconciliation-sweep",
         ["Read the identity tuples PostgreSQL holds",
          "Count and compare what Qdrant and Neo4j actually hold now",
          "Report LIVE_CONSISTENT, DRIFT_DETECTED or CHECK_UNAVAILABLE"],
         "CHECK_UNAVAILABLE is a first-class answer. A store that cannot be "
         "reached is not the same as a store that disagrees."),
        ("Withdraw from active corpus", "warn", "DELETE /laws/{key}",
         ["Take a per-law lifecycle lock",
          "Preprocessor withdraws canonical state in one transaction: sections "
          "and cascades deleted, inbound references deleted, version superseded, "
          "withdrawn_at set",
          "Loader clears the law's Qdrant points and Neo4j graph, verifying zero",
          "Report REMOVED, ALREADY_REMOVED, NOT_FOUND, RECONCILIATION_REQUIRED "
          "or ERROR"],
         "The order is not interchangeable: canonical first, because that is the "
         "step that can be refused. No MinIO object, raw document, publisher "
         "capture, currency observation or verification check is ever touched."),
    ]

    y = y0 + 40
    bottoms = []
    for name, role, route, steps, insight in rows:
        b = card(c, Box(ax, y, aw), name, role=role, level="primary",
                 icon={"warn": "alert", "trust": "shield", "ui": "ui"}[role],
                 meta=[route])
        yy = b.bottom + 14
        for j, s in enumerate(steps):
            lines = wrap(s, "meta", aw - 300, where=f"cp step {s!r}")
            step(c, ax + 14, yy + 3, j + 1, accent=role, r=9)
            for k, ln in enumerate(lines):
                c.add(text_el(ln, ax + 32, yy + 7 + k * line_height("meta"),
                              "meta", T.INK_MUTED))
            yy += max(len(lines) * line_height("meta"), 15) + 6
        note(c, ax + aw - 276, b.bottom + 14, 276, [insight], accent=role)
        y = max(yy, b.bottom + 14 + 90) + 26
        bottoms.append(y)

    c.fit(max(bottoms) - 12, footnote=dict(
        lines=["Every one of these is reachable only through the health service, "
               "and the two that change the corpus are double-gated behind "
               "DATA_SOURCE=live and LIFECYCLE_ACTIONS_ENABLED. The dashboard "
               "cannot reach the preprocessor, the loader, Kafka or any store "
               "directly — not by convention, but because it ships with no "
               "client for any of them and exactly one configurable URL."],
        accent="ui", title="Why the operator surface is this narrow"),
        legend_spec=dict(roles=["trust", "ui", "warn"], flows=["sync"],
                         levels=["primary"]))
    write(c, f"{OUT}/08-operator-control-plane.svg")


# ===========================================================================
# 09 - Re-ingestion state machine
# ===========================================================================
def d09_reingest_states() -> None:
    c = Canvas(1920, 1040,
               eyebrow="Lifecycle",
               title="Re-ingestion, and what it does to system state",
               subtitle="A re-ingest does not clear the law first. Each store's "
                        "own write path replaces it safely, which is what makes "
                        "the operation survivable at any point.")
    c.background()
    y0 = c.header()
    c.byline()

    sw, sg = 236, 66
    ry = y0 + 54
    sts = [
        ("SERVED", "trust", "the current generation,\nverified", False),
        ("CAPTURE SUBMITTED", "event", "new eventId, new prefix\nold capture intact", False),
        ("CANONICAL REPLACED", "store", "one transaction\nversion superseded", False),
        ("PROJECTIONS CONVERGING", "ai", "Qdrant upsert then\ndelete stale", False),
        ("MEASURED", "ui", "gates have run,\nverdicts recorded", False),
        ("SERVED", "trust", "the new generation,\nverified", True),
    ]
    boxes = []
    for i, (name, role, det, term) in enumerate(sts):
        x = T.SAFE + i * (sw + sg)
        b = state(c, Box(x, ry, sw), name, role=role,
                  detail=det.replace("\n", " "), terminal=term)
        boxes.append(b)
        step(c, x + 12, ry - 14, i + 1, accent=role, r=11)
    for i in range(len(boxes) - 1):
        edge(c, boxes[i], boxes[i + 1], kind="sync",
             role=sts[i + 1][1], gap=5)

    # what stays queryable
    qy = max(b.bottom for b in boxes) + 40
    c.add(text_el("WHAT A READER SEES AT EACH STATE", T.SAFE, qy, "lane",
                  T.ROLE["trust"]))
    qy += 16
    rowh = 34
    mt = matrix(c, T.SAFE, qy,
                ["State", "PostgreSQL serves", "Qdrant serves", "Neo4j serves",
                 "Badge shows"],
                [["1 SERVED", "old generation", "old vectors", "old graph",
                  "VERIFIED"],
                 ["2 CAPTURE SUBMITTED", "old generation", "old vectors",
                  "old graph", "VERIFIED, ingest in progress"],
                 ["3 CANONICAL REPLACED", "new generation", "old vectors",
                  "old graph", "stale — drift is real here"],
                 ["4 PROJECTIONS CONVERGING", "new generation",
                  "new vectors after the fence", "new graph after the fence",
                  "ingest in progress"],
                 ["5 MEASURED", "new generation", "new vectors", "new graph",
                  "verdict per gate"],
                 ["6 SERVED", "new generation", "new vectors", "new graph",
                  "VERIFIED"]],
                widths=[330, 330, 350, 350, 360], rowh=rowh,
                accents=["trust", "event", "warn", "ai", "ui", "trust"],
                label="matrix:reingest-states")

    nb = note(c, T.SAFE, mt.bottom + 26, (c.width - 2 * T.SAFE) / 2 - 18,
              ["State 3 is the honest part of this diagram. Between the canonical "
               "commit and the projection fences, PostgreSQL holds the new "
               "generation while Qdrant and Neo4j still hold the old one. That "
               "window is real, it is short, and reconciliation will report it as "
               "DRIFT_DETECTED if it is sampled inside it.",
               "It is accepted rather than eliminated, because the alternative — "
               "a distributed transaction across a relational store, a vector "
               "store and a graph store — buys consistency at a cost the "
               "corpus does not need. Nothing serves a partial law: the old "
               "generation answers until the new one is complete."],
              accent="warn", title="The window that is not hidden")
    note(c, c.width / 2 + 12, nb.y, (c.width - 2 * T.SAFE) / 2 - 18,
         ["No state here is entered by a timer, a retry policy or a repair "
          "daemon. A re-ingest is an operator action, every transition is driven "
          "by an event the previous stage published, and if a stage fails the "
          "machine stops in place rather than advancing.",
          "That is a deliberate choice about a legal corpus: an automatic "
          "self-heal that silently re-derives knowledge is indistinguishable, "
          "afterwards, from an automatic self-heal that silently corrupted it."],
         accent="ui", title="Nothing advances on its own")

    c.fit(nb.bottom + 14, legend_spec=dict(
        roles=["event", "ai", "store", "trust", "ui", "warn"], flows=["sync"]))
    write(c, f"{OUT}/09-reingestion-state-machine.svg")


ALL = [d06_verification, d07_rag, d08_control_plane, d09_reingest_states]
