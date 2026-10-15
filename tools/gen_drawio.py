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


def local_environment() -> None:
    """Diagram 20 as an editable source -- the only deployment view in the set.

    Ports, languages and ownership come from architecture-notes.md sections 1
    and 2. The three dashed boxes at the bottom are recorded absences, not
    omissions: drawing them dashed is what stops a reader assuming the stack
    has a DLQ, a monitoring plane or an agentic retrieval graph.
    """
    d = Doc("Local environment", 1700, 1320)

    # ---- 1. repositories and the environment
    d.lane("1 · REPOSITORIES, AND THE ENVIRONMENT AS ONE OF THEM",
           40, 40, 1620, 200)
    env = d.box("local-env\n\nCompose files, service YAML and the\n"
                "pinned dependency set\n\n"
                "the environment is a versioned repo,\n"
                "not a document describing one",
                70, 90, 370, 130, role="event", level="shared")
    lib = d.box("ai-utils\n\nShared library imported by the\nPython services\n\n"
                "constants · event models ·\ncalibrated thresholds",
                470, 90, 370, 130, role="ai", level="extended")
    svc = d.box("Nine service repositories\n\nSeven names appear in the evidence\n"
                "pack; four are not published.\n\n"
                "A dash means not in evidence —\nnot that no repository exists.",
                870, 90, 370, 130, role="neutral", level="integrated")
    img = d.box("Images built in CI\n\nRun from Docker Compose on a lab\nhost.\n\n"
                "No production deployment is\nclaimed anywhere.",
                1270, 90, 360, 130, role="neutral", level="integrated")
    d.edge(env, img, "builds", role="event")
    d.edge(lib, svc, "imported by", role="ai", kind="verify")

    # ---- 2. container discipline
    d.lane("2 · HOW DEPENDENCIES REACH A CONTAINER — ADR-003, "
           "SUPERSEDED BY ADR-004", 40, 270, 1620, 200)
    adr3 = d.box("ADR-003 · rebuild discipline\n\n"
                 "Written after the local overlay images were found running\n"
                 "code that predated completed work — while the repository,\n"
                 "the docs and the tests all said otherwise.\n\n"
                 "the failure that looked like success",
                 70, 320, 770, 130, role="warn", level="integrated")
    adr4 = d.box("ADR-004 · editable install + boot-time check\n\n"
                 "Supersedes ADR-003. The package is installed editable and a\n"
                 "check runs at boot, so a drifted container fails at startup\n"
                 "instead of serving a route table nobody expected.\n\n"
                 "fail at boot, not at request time",
                 870, 320, 760, 130, role="trust", level="integrated")
    d.edge(img, adr3, "", role="neutral")
    d.edge(adr3, adr4, "superseded by", role="trust")

    # ---- 3. runtime
    d.lane("3 · RUNTIME — DOCKER COMPOSE, FIVE HOST PORTS",
           40, 500, 1620, 230)
    ep = d.box("Entity Producer\n\nPolls the publishers, captures\n"
               "the bytes, announces the capture\n\n:4675 · java · spring boot",
               70, 550, 280, 150, role="event", level="extended")
    pre = d.box("Ingestion Preprocessor\n\nParses GII-NORM and FORMEX,\n"
                "writes canonical state, then\nruns the gates\n\n"
                ":4698 · python · fastapi",
                380, 550, 280, 150, role="ai", level="primary")
    lo = d.box("Ingestion Loader\n\nEmbeds and projects into the\n"
               "vector and graph stores\n\n"
               ":4710-4711 · a port range,\nbecause it is built to scale",
               690, 550, 280, 150, role="ai", level="primary")
    hs = d.box("Health Service\n\nCurrency, snapshots, audit log.\n"
               "Judges freshness evidence;\nnever fetches it.\n\n"
               ":8000 · python · fastapi",
               1000, 550, 280, 150, role="ui", level="primary")
    dash = d.box("Operator Dashboard\n\nRe-ingest, verify, reconcile,\n"
                 "withdraw. Writes nothing, and\nships with no store client.\n\n"
                 ":3000 · typescript · next.js 16",
                 1310, 550, 320, 150, role="ui", level="primary")
    d.edge(ep, pre, "events.inbound", role="event", kind="async")
    d.edge(pre, lo, "law.structured", role="event", kind="async")
    d.edge(lo, pre, "law.embedded", role="event", kind="async")
    d.edge(dash, hs, "REST", role="ui")

    # ---- 4. persistence
    d.lane("4 · PERSISTENCE — THREE DATABASES AND ONE OBJECT STORE",
           40, 760, 1620, 240)
    pg = d.box("PostgreSQL\n\nCanonical legal state, source\n"
               "evidence, assurance, currency —\nfour concerns, one database\n\n"
               "cannot: search by meaning",
               70, 810, 360, 160, role="store", level="primary", store=True)
    qd = d.box("Qdrant\n\nDense 1024 + sparse vectors in one\n"
               "collection, fused server-side\n\n"
               "point id = uuid5(ns, chunk_id)\ncannot: follow a citation chain",
               470, 810, 360, 160, role="store", level="primary", store=True)
    ne = d.box("Neo4j\n\nThe provision reference graph —\n"
               "what each provision cites,\nacross statutes\n\n"
               "MERGE by id · REFERS_TO · CITES_LAW",
               870, 810, 360, 160, role="store", level="primary", store=True)
    mo = d.box("MinIO\n\nPublisher bytes, hashed before\n"
               "anything parses them, plus an\nobject-locked evidence bucket\n\n"
               "{eventId}/{filename} · SHA-256",
               1270, 810, 360, 160, role="store", level="extended", store=True)
    d.edge(pre, pg, "exclusive write", role="store", kind="own")
    d.edge(hs, pg, "currency · audit", role="store", kind="own")
    d.edge(lo, qd, "1st", role="store", kind="own")
    d.edge(lo, ne, "2nd", role="store", kind="own")
    d.edge(ep, mo, "captures", role="store", kind="own")
    d.edge(pre, mo, "archive mirror", role="store", kind="own")

    # ---- 5. recorded absences
    d.lane("5 · DRAWN BECAUSE IT IS ABSENT — RECORDED IN THE REPOSITORY",
           40, 1030, 1620, 190)
    d.box("No dead-letter topic · legal pipeline\n\n"
          "A permanently unprocessable law is redelivered\n"
          "for ever and blocks its partition until a human\n"
          "intervenes. The document pipeline has a DLQ;\n"
          "the legal one does not.",
          70, 1080, 500, 120, role="warn", level="external")
    d.box("No monitoring plane in the delivered stack\n\n"
          "Prometheus and Alertmanager rules were written\n"
          "and promtool-tested, then withdrawn. Nothing in\n"
          "the running stack scrapes or alerts.",
          600, 1080, 500, 120, role="warn", level="external")
    d.box("No agentic retrieval graph\n\n"
          "A ten-node design exists in the architecture\n"
          "material. langgraph is commented out and the\n"
          "retrieval package is empty.",
          1130, 1080, 500, 120, role="warn", level="external")

    d.write("local-environment.drawio")


def legal_kb_pipelines() -> None:
    """Diagram 21 as an editable source -- the Legal Knowledge Database.

    Two pipelines over one corpus. Pipeline A writes every store; Pipeline B
    writes none. That separation is the reason a retrieval bug cannot corrupt
    the corpus and a question cannot start an ingest.

    CELLAR is the EU repository, FORMEX v4 the markup, CELEX the identifier an
    act is resolved by -- three different things, and the diagram keeps them
    apart deliberately.
    """
    d = Doc("Legal Knowledge Database — two pipelines", 1700, 1340)

    # ---- 1. pipeline A
    d.lane("1 · PIPELINE A — INGESTION · PUBLISHER'S BYTES TO A STORED, "
           "PROVABLE LAW", 40, 40, 1620, 280)
    sde = d.box("German federal publisher\n\ngesetze-im-internet.de\n"
                "The health service downloads\nthe publisher's own ZIP.\n\n"
                "gii_norm · 32 of 52 laws",
                70, 90, 300, 110, role="source", level="external")
    seu = d.box("EU · CELLAR\n\nA FORMEX v4 bundle fetched by\n"
                "content negotiation. CELLAR is the\n"
                "repository, FORMEX the markup,\n"
                "CELEX the identifier.\n\nformex_v4 · 20 of 52 laws",
                70, 210, 300, 100, role="source", level="external")
    a1 = d.box("1 · Acquire\n\nThe health service fetches the\n"
               "publisher's own file and resolves\n"
               "CELEX for EU acts. It observes and\n"
               "judges freshness; it never parses.\n\n"
               ":8000 · health service",
               410, 90, 280, 220, role="ui", level="primary")
    a2 = d.box("2 · Capture\n\nSHA-256 before anything interprets\n"
               "the bytes, written to object storage\n"
               "under a fresh prefix, then one event.\n"
               "Parses nothing — no ZIP, no XML.\n\n"
               ":4675 · entity producer",
               730, 90, 280, 220, role="event", level="extended")
    a3 = d.box("3 · Structure\n\nA registry decides the canonical key\n"
               "and the parser; GII-NORM or\n"
               "FORMEX v4 extracts citations to\n"
               "provision level and chunks the active\n"
               "sections — one transaction, three\n"
               "ruleset digests.\n\n:4698 · preprocessor",
               1050, 90, 280, 220, role="ai", level="primary")
    a4 = d.box("4 · Project\n\nOne REPEATABLE READ snapshot,\n"
               "embedded with BGE-M3 (dense 1024\n"
               "+ sparse, one pass), then Qdrant and\n"
               "Neo4j converged in order, each fenced\n"
               "on an exact count. Refuses the law\n"
               "rather than truncate a vector.\n\n:4710-4711 · loader",
               1370, 90, 280, 220, role="ai", level="primary")
    d.edge(sde, a1, "", role="source")
    d.edge(seu, a1, "", role="source")
    d.edge(a1, a2, "", role="event", kind="async")
    d.edge(a2, a3, "events.inbound", role="event", kind="async")
    d.edge(a3, a4, "law.structured", role="event", kind="async")

    # ---- 2. the corpus
    d.lane("2 · THE CORPUS — THREE DATABASES, AND THE EVIDENCE BEHIND THEM",
           40, 350, 1620, 240)
    pg = d.box("PostgreSQL · the laws\n\nCanonical legal state as tables, plus\n"
               "source evidence, assurance and\n"
               "currency — the evidence tables\nappend-only\n\n"
               "~35 tables · sole writer: preprocessor",
               70, 400, 370, 160, role="store", level="primary", store=True)
    qd = d.box("Qdrant · the vectors\n\nOne point per chunk, dense and\n"
               "sparse together in one collection,\n"
               "both law families side by side\n\n"
               "uuid5(ns, chunk_id)\nsole writer: loader",
               470, 400, 370, 160, role="store", level="primary", store=True)
    ne = d.box("Neo4j · the relations\n\nWhich provision cites which, across\n"
               "statutes — exactly what a vector hit\ncannot tell you\n\n"
               "REFERS_TO · CITES_LAW\nsole writer: loader",
               870, 400, 370, 160, role="store", level="primary", store=True)
    mo = d.box("MinIO · the source bytes\n\nWhat the publisher actually served,\n"
               "hashed on arrival and mirrored into\n"
               "an object-locked bucket\n\n"
               "{eventId}/{filename} · SHA-256\nsole writer: entity producer",
               1270, 400, 380, 160, role="store", level="extended", store=True)
    d.edge(a2, mo, "captures", role="store", kind="own")
    d.edge(a3, pg, "exclusive write", role="store", kind="own")
    d.edge(a4, qd, "1st", role="store", kind="own")
    d.edge(a4, ne, "2nd", role="store", kind="own")

    # ---- 3. verification
    d.lane("3 · VERIFICATION — ASKED AND ANSWERED AFTER EVERY INGEST",
           40, 620, 1620, 210)
    v1 = d.box("Fourteen gates, run by the ingest\n\n"
               "Publishing law.embedded is what runs them —\n"
               "nobody asks. Structural fidelity, citation\n"
               "correctness, cross-store equality and source\n"
               "currency, and the verdict is never one badge.\n\n"
               "7 badge-required · 7 recorded",
               70, 670, 500, 140, role="trust", level="primary")
    v2 = d.box("A denominator that cannot share the defect\n\n"
               "The structural inventory is read a second time on\n"
               "a different XML stack, importing no parser code.\n"
               "And the prover proves itself first: if a certified\n"
               "law stops reproducing, no law gets a verdict.\n\n"
               "lxml iterparse · zero application imports",
               600, 670, 500, 140, role="trust", level="primary")
    v3 = d.box("Reconciliation · a different question\n\n"
               "Verification asks whether this generation was\n"
               "extracted faithfully. Reconciliation asks whether\n"
               "the stores agree right now. Read-only, repairs\n"
               "nothing, and says when it cannot tell.\n\n"
               "LIVE_CONSISTENT | DRIFT_DETECTED | CHECK_UNAVAILABLE",
               1130, 670, 520, 140, role="trust", level="primary")
    d.edge(v1, pg, "measure", role="trust", kind="verify")
    d.edge(v3, ne, "compare", role="trust", kind="verify")
    d.edge(v2, v3, "", role="trust", kind="verify")

    # ---- 4. pipeline B
    d.lane("4 · PIPELINE B — QUERY · A QUESTION ANSWERED FROM THE STORED "
           "CORPUS", 40, 860, 1620, 270)
    b1 = d.box("Question\n\nAn operator search, or a\n"
               "question arriving as an\nevent\n\n"
               "GET /search\nibp.events.inbound",
               70, 910, 250, 200, role="ui", level="integrated")
    b2 = d.box("Embed the question\n\nBGE-M3 — the same model\n"
               "that embedded the corpus.\nA different model would\n"
               "make the comparison\nmeaningless.\n\ndense 1024 + sparse",
               340, 910, 250, 200, role="ai", level="primary")
    b3 = d.box("Hybrid retrieval\n\nDense and sparse prefetch,\n"
               "fused server-side by\nreciprocal rank fusion in\n"
               "one round trip\n\nprefetch = max(limit, 20)\n"
               "reads Qdrant · writes nothing",
               610, 910, 250, 200, role="ai", level="primary")
    b4 = d.box("Cited chunks + graph\n\nThe law key and section\n"
               "number travel in the payload.\nThe graph then finds what\n"
               "the matched provision\npoints at.\n\n"
               "reads Neo4j · writes nothing",
               880, 910, 250, 200, role="trust", level="primary")
    b5 = d.box("Legal Chatbot + LLM\n\nConsumes ibp.events.inbound,\n"
               "publishes ibp.events.ai.\nprocessed. Self-hosted,\n"
               "OpenAI-compatible endpoint.\n"
               "Repository not in this\nworkspace.\n\nHF_HUB_OFFLINE=1",
               1150, 910, 250, 200, role="ai", level="integrated")
    b6 = d.box("Grounded answer\n\nReturned with the\n"
               "provisions it was built\nfrom\n\n"
               "ibp.events.ai.processed",
               1420, 910, 230, 200, role="ui", level="integrated")
    d.edge(b1, b2, "", role="ai")
    d.edge(b2, b3, "", role="ai")
    d.edge(b3, b4, "", role="trust")
    d.edge(b4, b5, "", role="ai")
    d.edge(b5, b6, "", role="ai")
    d.edge(qd, b3, "query_points", role="store", kind="verify")
    d.edge(ne, b4, "expand", role="store", kind="verify")

    d.box("TWO PATHS, ONE CORPUS — the two pipelines share one corpus and nothing "
          "else. Every component in A writes exactly one store, and the exclusive-write\n"
          "arrows are the only writes that exist; every component in B reads and "
          "returns. That is why a retrieval bug cannot corrupt the corpus and why a\n"
          "question cannot start an ingest — and why B has no verification gate of its "
          "own and needs none: it trusts the corpus because A proved it first.\n"
          "Not solved: no dead-letter topic on this pipeline, so one unprocessable law "
          "blocks its partition until a human intervenes; and no EU law is certified,\n"
          "because the end-to-end assurance contract does not exist yet — a missing "
          "contract, not a missing parser.",
          40, 1160, 1620, 130, role="trust", level="integrated")

    d.write("legal-kb-pipelines.drawio")


if __name__ == "__main__":
    print("generating editable diagrams.net sources")
    legal_platform()
    verification()
    rag_flow()
    insurance_ai()
    event_pipelines()
    overview()
    local_environment()
    legal_kb_pipelines()
