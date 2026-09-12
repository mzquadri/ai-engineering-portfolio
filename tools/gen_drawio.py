"""Generate editable diagrams.net (.drawio) sources.

Every node is a real mxCell with its own geometry and style, and every edge is a
real mxCell edge with a source and a target. Nothing is a raster image, so
opening one of these in diagrams.net gives you movable boxes, editable labels
and re-routable arrows -- which is the whole point of shipping a .drawio
alongside an SVG.

    python tools/gen_drawio.py
"""

from __future__ import annotations

import pathlib
from xml.sax.saxutils import escape as _escape


def escape(s: str) -> str:
    """Escape for use inside an XML attribute -- quotes included.

    xml.sax.saxutils.escape does not touch quotes, which silently
    produced one malformed .drawio file the first time this ran.
    """
    return _escape(s, {'"': '&quot;', "'": '&apos;'})

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "drawio"

# Palette mirrors design-system.md, expressed as diagrams.net styles.
FILL = {
    "source": "#241B3D", "event": "#0B2D33", "ai": "#191C3D",
    "store": "#2B2208", "trust": "#0C2A1E", "ui": "#0F2340",
    "warn": "#2E1416", "neutral": "#161C24", "lane": "#0A0F16",
}
STROKE = {
    "source": "#A78BFA", "event": "#22D3EE", "ai": "#818CF8",
    "store": "#F0B429", "trust": "#34D399", "ui": "#60A5FA",
    "warn": "#F87171", "neutral": "#7D8B9C", "lane": "#1C2736",
}
INK = "#E8EEF6"

LEVEL_WEIGHT = {"primary": 2, "extended": 2, "integrated": 1, "external": 1}
LEVEL_DASH = {"external": 1}


def node_style(role: str, level: str = "integrated", *, store: bool = False,
               rounded: bool = True) -> str:
    s = [
        f"rounded={1 if rounded else 0}",
        "whiteSpace=wrap", "html=1", "arcSize=8",
        f"fillColor={FILL[role]}", f"strokeColor={STROKE[role]}",
        f"strokeWidth={LEVEL_WEIGHT.get(level, 1)}",
        f"fontColor={INK}", "fontSize=13", "align=left",
        "verticalAlign=top", "spacing=8", "spacingTop=4",
        "fontFamily=Helvetica",
    ]
    if level in LEVEL_DASH:
        s.append("dashed=1;dashPattern=3 3")
    if store:
        s.append("shape=note;size=0")  # double-edge feel; still a plain shape
        s.remove("shape=note;size=0")
        s.append("shadow=0")
    return ";".join(s) + ";"


def lane_style() -> str:
    return (f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;"
            f"fillColor={FILL['lane']};strokeColor={STROKE['lane']};"
            f"strokeWidth=1;fontColor=#9FB0C3;fontSize=11;align=left;"
            f"verticalAlign=top;spacing=8;spacingTop=4;"
            f"fontFamily=Helvetica;fontStyle=1;")


def edge_style(role: str, kind: str = "sync") -> str:
    s = [
        "edgeStyle=orthogonalEdgeStyle", "rounded=1", "html=1",
        f"strokeColor={STROKE[role]}", "strokeWidth=1.4",
        "fontColor=#9FB0C3", "fontSize=11", "fontFamily=Helvetica",
        "labelBackgroundColor=#070A0F", "jettySize=auto", "orthogonalLoop=1",
    ]
    if kind == "async":
        s.append("dashed=1;dashPattern=6 5")
    elif kind == "verify":
        s.append("dashed=1;dashPattern=2 4;endArrow=open")
    elif kind == "own":
        s[4] = "strokeWidth=2.2"
    return ";".join(s) + ";"


class Doc:
    """One .drawio page under construction."""

    def __init__(self, name: str, w: int = 1600, h: int = 900) -> None:
        self.name, self.w, self.h = name, w, h
        self.cells: list[str] = []
        self.n = 1

    def _id(self) -> str:
        self.n += 1
        return f"n{self.n}"

    def box(self, label: str, x: int, y: int, w: int, h: int, *,
            role: str = "neutral", level: str = "integrated",
            store: bool = False, parent: str = "1") -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" '
            f'style="{node_style(role, level, store=store)}" vertex="1" '
            f'parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" '
            f'height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def lane(self, label: str, x: int, y: int, w: int, h: int) -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" style="{lane_style()}" '
            f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" '
            f'height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def pill(self, label: str, x: int, y: int, w: int = 250,
             h: int = 30) -> str:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" '
            f'style="rounded=1;arcSize=50;whiteSpace=wrap;html=1;'
            f'fillColor={FILL["event"]};strokeColor={STROKE["event"]};'
            f'fontColor={STROKE["event"]};fontSize=12;'
            f'fontFamily=Courier New;align=center;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
            f'as="geometry"/></mxCell>'
        )
        return cid

    def edge(self, a: str, b: str, label: str = "", *, role: str = "neutral",
             kind: str = "sync") -> None:
        cid = self._id()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" '
            f'style="{edge_style(role, kind)}" edge="1" parent="1" '
            f'source="{a}" target="{b}"><mxGeometry relative="1" '
            f'as="geometry"/></mxCell>'
        )

    def render(self) -> str:
        return (
            f'<mxfile host="app.diagrams.net" type="device">'
            f'<diagram name="{escape(self.name)}">'
            f'<mxGraphModel dx="{self.w}" dy="{self.h}" grid="1" gridSize="10" '
            f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
            f'page="1" pageScale="1" pageWidth="{self.w}" pageHeight="{self.h}" '
            f'background="#070A0F" math="0" shadow="0">'
            f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            f'{"".join(self.cells)}'
            f'</root></mxGraphModel></diagram></mxfile>'
        )

    def write(self, filename: str) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        p = OUT / filename
        p.write_text(self.render(), encoding="utf-8")
        print(f"  {filename:<38s} {self.n - 1:>3d} cells")


# ---------------------------------------------------------------------------
def legal_platform() -> None:
    d = Doc("Legal Knowledge Database", 1700, 1000)
    d.lane("1 · ACQUIRE AND PROVE THE SOURCE", 40, 40, 1620, 200)
    src = d.box("Official publishers\n\ngesetze-im-internet.de\npublications.europa.eu",
                70, 90, 280, 120, role="source", level="external")
    hsf = d.box("Health Service — fetch\n\nDownloads the source itself;\n"
                "resolves CELEX for EU acts\n\nPOST /laws/{key}/reingest",
                380, 90, 280, 120, role="ui", level="primary")
    ep = d.box("Entity Producer\n\nEnvelope, SHA-256, capture, publish.\n"
               "Parses nothing.\n\n:4675 · file ≤ 1 MiB · url ≤ 50 MiB",
               690, 90, 290, 120, role="event", level="extended")
    cap = d.box("MinIO · captures\n\n{eventId}/{filename}\n"
                "legal-knowledge-database-laws",
                1010, 90, 290, 120, role="store", level="extended", store=True)
    ev = d.box("MinIO · evidence\n\nObject lock enabled.\n"
               "Release is a compliance procedure.",
               1330, 90, 290, 120, role="store", level="extended", store=True)
    d.edge(src, hsf, "fetch", role="source")
    d.edge(hsf, ep, "POST /events", role="ui")
    d.edge(ep, cap, "PUT", role="store", kind="own")
    d.edge(cap, ev, "mirror", role="store", kind="verify")

    d.lane("2 · STRUCTURE, CITE AND PROVE WHAT WAS PRODUCED", 40, 270, 1620, 230)
    tin = d.pill("legal.knowledge.database.events.inbound", 70, 300, 380)
    pre = d.box("Ingestion Preprocessor\n\nRegistry → parser dispatch →\n"
                "references → chunks → one transaction\n\n"
                "gii_norm: 32 · formex_v4: 20\nfilter domain=LEGAL, IMPORTED",
                70, 350, 300, 130, role="trust", level="primary")
    pg = d.box("PostgreSQL\n\nCanonical state, source evidence,\n"
               "assurance, currency\n\n~35 tables · 9 views · 84 migrations",
               410, 350, 300, 130, role="store", level="primary", store=True)
    gates = d.box("14 verification gates\n\nStructural fidelity, citations,\n"
                  "store equality, currency\n\n7 badge-required · DE 14 · EU 12",
                  750, 350, 300, 130, role="trust", level="primary")
    prov = d.box("Ruleset provenance\n\nThree digests over parser, extractor\n"
                 "and registry bytes\n\nA byte change is a rule change",
                 1090, 350, 300, 130, role="trust", level="primary")
    d.edge(ep, tin, "", role="event", kind="async")
    d.edge(tin, pre, "", role="event", kind="async")
    d.edge(pre, pg, "exclusive write", role="store", kind="own")
    d.edge(pg, gates, "measure", role="trust", kind="verify")
    d.edge(gates, prov, "", role="trust", kind="verify")

    d.lane("3 · DERIVE SEARCHABLE PROJECTIONS, THEN CLOSE THE LOOP",
           40, 530, 1620, 240)
    tst = d.pill("legal.knowledge.database.law.structured", 70, 560, 340)
    lo = d.box("Ingestion Loader\n\nOne REPEATABLE READ snapshot →\n"
               "embed → converge → count fences\n\n"
               "BGE-M3 · 8192-token window\nrefuses the law rather than truncate",
               70, 610, 300, 140, role="ai", level="primary")
    qd = d.box("Qdrant\n\ndense 1024 cosine + sparse LEXICAL,\nRRF fusion\n\n"
               "legal-knowledge-database-german-law\npoint id = uuid5(ns, chunk_id)",
               410, 610, 300, 140, role="store", level="primary", store=True)
    ne = d.box("Neo4j\n\nProvision reference graph, MERGE by id\n\n"
               "(:LawSection) (:Law)\n[:REFERS_TO] [:CITES_LAW]",
               750, 610, 300, 140, role="store", level="primary", store=True)
    temb = d.pill("legal.knowledge.database.law.embedded", 1090, 660, 340)
    d.edge(pre, tst, "", role="event", kind="async")
    d.edge(tst, lo, "", role="event", kind="async")
    d.edge(pg, lo, "read-only snapshot", role="store", kind="verify")
    d.edge(lo, qd, "1st", role="store", kind="own")
    d.edge(qd, ne, "2nd", role="store", kind="own")
    d.edge(ne, temb, "", role="event", kind="async")
    d.edge(temb, gates, "triggers verification", role="trust", kind="async")

    note = d.box("law.structured means PostgreSQL committed only.\n"
                 "law.embedded is the completion boundary — published after both\n"
                 "count fences pass, and it is what makes the preprocessor verify\n"
                 "the law without anyone asking.",
                 40, 800, 700, 110, role="warn", level="integrated")
    own = d.box("ONE WRITER PER STORE\n"
                "Preprocessor → PostgreSQL + archive mirror\n"
                "Loader → Qdrant + Neo4j\n"
                "Health Service → currency, snapshots, audit log\n"
                "Dashboard → nothing, anywhere",
                770, 800, 890, 110, role="trust", level="primary")
    d.write("legal-knowledge-database.drawio")


def verification() -> None:
    d = Doc("Verification and reconciliation", 1600, 900)
    cap = d.box("Captured source, digest-proven\n\nThe publisher's own bytes,\n"
                "in MinIO, hashed at capture", 60, 60, 300, 100,
                role="source", level="primary")
    ora = d.box("An independent denominator\n\nInventory built with stdlib and\n"
                "defusedxml; imports no parser code\n\n"
                "tools/oracle_gii_structure.py", 60, 200, 300, 120,
                role="trust", level="primary")
    pf = d.box("Pre-flight\n\nIs this structure recognised?", 60, 360, 300, 80,
               role="trust", level="primary")
    stop = d.box("BLOCKED — no ingest\n\nStop and report the gap.\n"
                 "Never weaken the gate.", 60, 490, 300, 100,
                 role="warn", level="primary")
    ing = d.box("Ingest, then store\n\nPostgreSQL, then Qdrant + Neo4j", 430,
                360, 300, 80, role="store", level="primary")
    base = d.box("Corpus baseline\n\nDoes every already-certified law\n"
                 "still reproduce under today's rules?", 430, 200, 300, 100,
                 role="trust", level="primary")
    nov = d.box("No verdict for ANY law\n\nIncluding the one being certified",
                430, 60, 300, 90, role="warn", level="primary")
    gates = d.box("Run every applicable gate\n\n14 total · 7 badge-required\n"
                  "DE 14 apply · EU 12 apply\n\n"
                  "POST /internal/laws/{key}/verify", 800, 200, 320, 130,
                  role="trust", level="primary")
    vc = d.box("verification_checks\n\nOne row per gate per generation.\n"
               "The badge is a view over this table.\n\nlaw_verification_state",
               800, 380, 320, 120, role="store", level="primary", store=True)
    tp = d.box("Four separate answers, never one badge\n\n"
               "Verification status · verdict freshness ·\n"
               "source currency · live store integrity",
               1180, 200, 340, 130, role="ui", level="primary")

    d.edge(cap, ora, "", role="trust")
    d.edge(ora, pf, "", role="trust")
    d.edge(pf, stop, "unknown structure", role="warn")
    d.edge(pf, ing, "recognised", role="trust")
    d.edge(ing, base, "", role="trust")
    d.edge(base, nov, "baseline fails", role="warn")
    d.edge(base, gates, "baseline holds", role="trust")
    d.edge(gates, vc, "record", role="store", kind="own")
    d.edge(vc, tp, "read back", role="ui", kind="verify")

    rc = d.box("RECONCILIATION · changes nothing\n\n"
               "Read PostgreSQL identity tuples, compare Qdrant and Neo4j.\n"
               "LIVE_CONSISTENT · DRIFT_DETECTED · CHECK_UNAVAILABLE\n\n"
               "LIVE_CONSISTENT is the last sweep's answer, not a guarantee.",
               60, 640, 480, 130, role="ui", level="primary")
    vf = d.box("VERIFY · changes nothing\n\n"
               "Poll the publisher, write currency evidence,\n"
               "ask the preprocessor to run the gates.\n\n"
               "Changes no version, section, chunk, vector or edge.",
               570, 640, 480, 130, role="trust", level="primary")
    ri = d.box("RE-INGEST · changes the corpus\n\n"
               "Fetch, capture, rewrite canonical state, reconverge stores.\n\n"
               "Zero-downtime: nothing is purged first, so the old generation\n"
               "stays queryable and a failed ingest leaves it untouched.",
               1080, 640, 460, 130, role="warn", level="primary")
    d.write("verification-reconciliation.drawio")


def rag_flow() -> None:
    d = Doc("Retrieval and grounded answering", 1600, 620)
    d.lane("VERIFIED IN THIS WORKSPACE", 40, 40, 1520, 190)
    q = d.box("Query\n\nOperator search, or a question\narriving as an event\n\n"
              "GET /search", 70, 85, 260, 120, role="ui", level="integrated")
    em = d.box("Embed the query\n\nBGE-M3 — the same model that\nembedded the corpus\n\n"
               "dense 1024 + sparse", 360, 85, 260, 120, role="ai",
               level="primary")
    rt = d.box("Hybrid retrieval\n\nDense and sparse prefetch,\nfused server-side by RRF\n\n"
               "prefetch = max(limit, 20)", 650, 85, 260, 120, role="ai",
               level="primary")
    qd = d.box("Qdrant\n\nOne point per chunk; both law\nfamilies in one collection",
               940, 85, 260, 120, role="store", level="primary", store=True)
    ch = d.box("Cited chunks\n\nlaw and section_number travel\nwith every chunk, so a\n"
               "citation is data, not prose", 1230, 85, 300, 120,
               role="trust", level="primary")
    d.edge(q, em, "", role="ui")
    d.edge(em, rt, "", role="ai")
    d.edge(rt, qd, "query_points", role="store", kind="verify")
    d.edge(qd, ch, "", role="trust")

    d.lane("ANSWERING · EXISTING COMPONENT, NOT INSPECTABLE HERE",
           40, 270, 1520, 190)
    ne = d.box("Neo4j\n\nWhat each provision cites", 70, 315, 260, 110,
               role="store", level="integrated", store=True)
    cb = d.box("Legal Chatbot\n\nConsumes ibp.events.inbound,\n"
               "publishes ibp.events.ai.processed\n\nrepository not present here",
               360, 315, 260, 110, role="ai", level="integrated")
    llm = d.box("LLM\n\nSelf-hosted, OpenAI-compatible.\n"
                "Container runs offline for weights.\n\nHF_HUB_OFFLINE=1",
                650, 315, 260, 110, role="ai", level="integrated")
    ans = d.box("Grounded answer\n\nReturned with the provisions\nit was built from",
                940, 315, 260, 110, role="ui", level="integrated")
    cv = d.box("Citation validation\n\nCheck each cited section against\n"
               "the corpus. Zero LLM calls.\n\nDESIGNED, NOT IMPLEMENTED",
               1230, 315, 300, 110, role="warn", level="integrated")
    d.edge(ch, cb, "", role="ai")
    d.edge(ne, cb, "", role="store", kind="verify")
    d.edge(cb, llm, "", role="ai")
    d.edge(llm, ans, "", role="ai")
    d.edge(ans, cv, "", role="warn", kind="verify")

    d.box("Ingestion-time components write stores and are the only things that do.\n"
          "Query-time components read. The query path has no gate of its own: it\n"
          "trusts the corpus because the corpus was verified before it was served.",
          40, 490, 760, 90, role="trust", level="primary")
    d.box("The answer-level citation check is a design position, not delivered work.\n"
          "An LLM citing a section that does not exist is the specific failure that\n"
          "makes a legal assistant dangerous, and checking costs no model call.",
          830, 490, 730, 90, role="warn", level="integrated")
    d.write("rag-flow.drawio")


def insurance_ai() -> None:
    d = Doc("Insurance document AI", 1600, 720)
    up = d.box("Document arrives\n\nStored in MinIO; an event names it\n\n"
               "ibp.events.inbound\nbucket: ibp-documents", 60, 70, 270, 120,
               role="source", level="integrated")
    dx = d.box("Document Extractor\n\nFilters by domain and entity type,\n"
               "downloads, converts, extracts fields\n\n"
               "accepted_domains: INSURANCE", 360, 70, 270, 120,
               role="ai", level="extended")
    dl = d.box("Docling Serve\n\nSidecar: PDF and image bytes → Markdown\n\n"
               "docling-serve-cpu :5001\ndo_ocr: \"false\"", 660, 70, 270, 120,
               role="ai", level="integrated")
    ea = d.box("Extraction agent\n\nDiscovery, guided extraction,\n"
               "re-extraction, post-validation\n\nmax 6000 chars per call",
               960, 70, 270, 120, role="ai", level="extended")
    ix = d.box("Indexing Service\n\nOptional LLM mapping, overlapping\n"
               "chunks, embeddings, vector upsert\n\ndomain-configured · DLQ",
               1260, 70, 280, 120, role="ai", level="extended")
    d.edge(up, dx, "event", role="event", kind="async")
    d.edge(dx, dl, "POST", role="ai")
    d.edge(dl, ea, "markdown", role="ai")
    d.edge(ea, ix, "ibp.events.document.extracted", role="event", kind="async")

    tpl = d.box("Templates — the extraction contract\n\n"
                "VERSICHERUNGSPOLICE · SCHADENMELDUNG ·\n"
                "VERSICHERUNGSVERTRAG · RECHNUNG ·\n"
                "ARZTBERICHT · AUSWEIS\n\n"
                "Each field carries an extraction_hint naming the\n"
                "German label variants to look for.",
                60, 250, 420, 170, role="trust", level="extended")
    er = d.box("entity-reader\n\nHolds the active templates\n\n:4680",
               520, 250, 250, 100, role="neutral", level="integrated")
    tt = d.pill("ibp.events.templates", 520, 380, 250)
    d.edge(er, tt, "", role="event", kind="async")
    d.edge(tt, ea, "", role="event", kind="async")
    d.edge(tpl, ea, "contract", role="trust", kind="verify")

    qd = d.box("Qdrant — per-domain collections\n\n"
               "ibp_documents_insurance\nibp_medical_images\n\n"
               "Routing is a declared filter on metadata.domain",
               820, 250, 340, 140, role="store", level="extended", store=True)
    rg = d.box("RAG Service\n\nRetrieval-only chat and query extraction\n\n"
               "/chat · /query · /stats", 1200, 250, 340, 140,
               role="ai", level="integrated")
    d.edge(ix, qd, "upsert", role="store", kind="own")
    d.edge(qd, rg, "", role="store", kind="verify")

    d.box("What is and is not modelled\n\n"
          "Modelled: customer, policy, coverage, claim, contract, invoice,\n"
          "identity, and a medical report.\n"
          "Not modelled: vehicle, property, health, beneficiary — no template\n"
          "or domain configuration for them exists, so none is drawn.",
          60, 470, 700, 130, role="warn", level="integrated")
    d.box("Why hints rather than fine-tuning\n\n"
          "\"Look for: Policennummer, VS-Nr., Vertragsnummer, Police Nr.\"\n"
          "is German insurance-document literacy encoded as data. It is\n"
          "reviewable by someone who knows insurance but not Python, and it\n"
          "moves between models without retraining.",
          800, 470, 740, 130, role="trust", level="extended")
    d.write("insurance-ai.drawio")


def event_pipelines() -> None:
    """The event-driven architecture that actually exists.

    The portfolio brief asked for a "gdms-kafka" diagram. No GDMS Rule Mapper
    exists anywhere in the inspected workspace -- see assets/mermaid/gdms.mmd,
    which documents the absence rather than inventing a diagram. This is the
    real event-driven work, under a filename that describes its contents.
    """
    d = Doc("Event-driven pipelines", 1600, 760)
    d.lane("LEGAL PIPELINE · three topics, two boundaries", 40, 40, 1520, 250)
    ep = d.box("Entity Producer", 70, 90, 240, 70, role="event", level="extended")
    t1 = d.pill("legal.knowledge.database.events.inbound", 340, 95, 380)
    pre = d.box("Ingestion Preprocessor", 750, 90, 240, 70, role="trust",
                level="primary")
    t2 = d.pill("legal.knowledge.database.law.structured", 1020, 95, 360)
    lo = d.box("Ingestion Loader", 70, 195, 240, 70, role="ai", level="primary")
    t3 = d.pill("legal.knowledge.database.law.embedded", 340, 200, 360)
    hs = d.box("Health Service\ncompletion consumer", 750, 195, 240, 70,
               role="ui", level="primary")
    ver = d.box("Verification\n14 gates", 1020, 195, 240, 70, role="trust",
                level="primary")
    d.edge(ep, t1, "", role="event", kind="async")
    d.edge(t1, pre, "", role="event", kind="async")
    d.edge(pre, t2, "", role="event", kind="async")
    d.edge(t2, lo, "PostgreSQL committed only", role="event", kind="async")
    d.edge(lo, t3, "both fences passed", role="event", kind="async")
    d.edge(t3, hs, "", role="event", kind="async")
    d.edge(t3, ver, "", role="trust", kind="async")

    d.lane("DOCUMENT PIPELINE · five topics, with a dead-letter path",
           40, 320, 1520, 190)
    ui = d.box("Platform UI / backend", 70, 370, 240, 70, role="neutral",
               level="integrated")
    d1 = d.pill("ibp.events.inbound", 340, 375, 240)
    dx = d.box("Document Extractor", 610, 370, 240, 70, role="ai",
               level="extended")
    d2 = d.pill("ibp.events.document.extracted", 880, 375, 300)
    ixs = d.box("Indexing Service", 1210, 370, 240, 70, role="ai",
                level="extended")
    d3 = d.pill("ibp.events.document.indexed", 610, 450, 280)
    dlq = d.box("ibp.events.document.indexed.dlq", 920, 445, 300, 50,
                role="warn", level="integrated")
    d.edge(ui, d1, "", role="event", kind="async")
    d.edge(d1, dx, "", role="event", kind="async")
    d.edge(dx, d2, "", role="event", kind="async")
    d.edge(d2, ixs, "", role="event", kind="async")
    d.edge(ixs, d3, "", role="event", kind="async")
    d.edge(ixs, dlq, "failure", role="warn", kind="async")

    d.box("Delivery properties that were designed, not inherited\n\n"
          "• The Kafka key is law_key, so one law maps to one partition and two\n"
          "  generations can never be processed concurrently.\n"
          "• Publish, then commit: the offset is committed last of all.\n"
          "• A redelivery may publish law.embedded twice; a unique index on\n"
          "  capture_id absorbs it.\n"
          "• A non-matching event has its offset committed and is skipped, so a\n"
          "  foreign event cannot wedge the consumer.",
          40, 540, 760, 180, role="trust", level="primary")
    d.box("What is missing, stated as missing\n\n"
          "The legal pipeline has no dead-letter topic, no bounded retry and no\n"
          "backoff. A permanently unprocessable law is redelivered for ever and\n"
          "blocks its partition; the loop ends and waits for a human.\n\n"
          "The document pipeline does have a DLQ. That difference is real, and it\n"
          "is the clearest piece of outstanding work in the legal workstream.",
          830, 540, 730, 180, role="warn", level="primary")
    d.write("event-driven-pipelines.drawio")


def overview() -> None:
    d = Doc("BP-ITCS AI landscape", 1600, 760)
    d.lane("SOURCES", 40, 50, 300, 330)
    gii = d.box("gesetze-im-internet.de\n\nGerman federal law, GII-NORM XML",
                65, 95, 250, 90, role="source", level="external")
    cel = d.box("EUR-Lex / CELLAR\n\nEU acts, FORMEX v4", 65, 200, 250, 80,
                role="source", level="external")
    doc = d.box("Insurance documents\n\nPDF, PNG, JPEG, TIFF, BMP, WEBP",
                65, 295, 250, 70, role="source", level="external")

    d.lane("A · LEGAL KNOWLEDGE DATABASE — five services, four implemented by me",
           370, 50, 740, 330)
    ep = d.box("Entity Producer\n\nCaptures source bytes\nas evidence\n\n:4675",
               400, 95, 210, 110, role="event", level="extended")
    pre = d.box("Ingestion Preprocessor\n\nStructures, cites,\nowns 14 gates\n\n:4698",
                660, 95, 210, 110, role="trust", level="primary")
    lo = d.box("Ingestion Loader\n\nEmbeds, converges\nderived stores\n\n:4697",
               890, 95, 200, 110, role="ai", level="primary")
    dash = d.box("Legal KB Dashboard\n\nOperator interface.\nDecides nothing.\n\n:3000",
                 400, 250, 210, 110, role="ui", level="primary")
    hs = d.box("Health Service\n\nControl and verification\nboundary\n\n:8000",
               660, 250, 210, 110, role="ui", level="primary")
    bot = d.box("Legal Chatbot\n\nGrounded answers\nover the corpus\n\nexisting",
                890, 250, 200, 110, role="ai", level="integrated")

    d.lane("B · DOCUMENT INTELLIGENCE — extended by me", 1140, 50, 420, 330)
    dx = d.box("Document Extractor\n\nDocling Serve → Markdown, then\n"
               "template-driven LLM field extraction", 1165, 95, 370, 75,
               role="ai", level="extended")
    ix = d.box("Indexing Service\n\nChunks, embeds and upserts vectors per domain",
               1165, 180, 370, 70, role="ai", level="extended")
    rg = d.box("RAG Service\n\nRetrieval-only chat and query extraction",
               1165, 260, 370, 60, role="ai", level="integrated")
    pd = d.box("AI Prediction Service — DenseNet-121, Grad-CAM++ (medical)",
               1165, 330, 370, 40, role="ai", level="extended")

    d.lane("SHARED PLATFORM — one writer per store", 40, 420, 1520, 170)
    pg = d.box("PostgreSQL\n\ncanonical state + evidence\nwriter: preprocessor",
               70, 465, 280, 95, role="store", level="integrated", store=True)
    qd = d.box("Qdrant\n\ndense 1024 + sparse\nwriter: loader",
               370, 465, 280, 95, role="store", level="integrated", store=True)
    ne = d.box("Neo4j\n\nprovision reference graph\nwriter: loader",
               670, 465, 280, 95, role="store", level="integrated", store=True)
    mo = d.box("MinIO\n\ncaptures, evidence, documents\nwriter: producer",
               970, 465, 280, 95, role="store", level="integrated", store=True)
    kf = d.box("Apache Kafka\n\nKRaft · 10 topics\nboth workstreams",
               1270, 465, 260, 95, role="event", level="integrated")

    d.edge(gii, ep, "", role="source")
    d.edge(cel, ep, "", role="source")
    d.edge(doc, dx, "", role="source")
    d.edge(ep, pre, "events.inbound", role="event", kind="async")
    d.edge(pre, lo, "law.structured", role="event", kind="async")
    d.edge(lo, pre, "law.embedded", role="event", kind="async")
    d.edge(dash, hs, "REST", role="ui")
    d.edge(hs, ep, "re-ingest", role="ui")
    d.edge(dx, ix, "", role="event", kind="async")
    d.edge(ix, rg, "", role="store", kind="verify")
    d.edge(pre, pg, "", role="store", kind="own")
    d.edge(lo, qd, "", role="store", kind="own")
    d.edge(lo, ne, "", role="store", kind="own")
    d.edge(ep, mo, "", role="store", kind="own")

    d.box("Legend — colour is engineering role; border weight is authorship.\n"
          "2px border = implemented by me · 2px = extended by me ·\n"
          "1px = existing platform component · dashed = external source",
          40, 620, 700, 90, role="neutral", level="integrated")
    d.write("systems-overview.drawio")


if __name__ == "__main__":
    print("generating editable diagrams.net sources")
    legal_platform()
    verification()
    rag_flow()
    insurance_ai()
    event_pipelines()
    overview()
