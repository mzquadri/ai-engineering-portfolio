"""Build the interview deck: PPTX, PDF, and one PNG per slide.

    python tools/gen_deck.py

The PPTX is generated with python-pptx and is fully editable -- real text
frames, real pictures, no flattened slide images. The PDF comes from an HTML
rendition printed by headless Chromium, so it matches the microsite's
typography rather than PowerPoint's.

Every slide answers one question, stated in the slide's own kicker.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from export_png import find_chrome                      # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PNG = ROOT / "assets" / "png"
PRES = ROOT / "presentation"
SLIDES = PRES / "slides"
NAME = "ai-engineering-portfolio"

BG = "070A0F"
INK = "E8EEF6"
MID = "9FB0C3"
LOW = "667B91"
TRUST = "34D399"
HAIR = "1C2736"

# (kicker question, title, diagram stem or None, at most three observations)
DECK: list[tuple[str, str, str | None, list[str]]] = [
    ("", "AI Engineering Systems",
     "ai-engineering-architecture-4k",
     ["Mohd Zamin Quadri \u2014 AI Engineer, BP-ITCS",
      "Legal knowledge infrastructure \u00b7 document intelligence \u00b7 "
      "retrieval \u00b7 verification",
      "Four of five services implemented; three more extended"]),

    ("What was actually hard about it?",
     "From legal source to trusted machine knowledge",
     None,
     ["Authoritative law changes without telling you, in two unrelated XML "
      "markup families",
      "Extract it for retrieval and you hold three representations that can "
      "each drift from the source",
      "So the problem was provenance and operational control \u2014 not "
      "retrieval"]),

    ("How does it fit together?",
     "End-to-end legal knowledge architecture",
     "02-legal-knowledge-database",
     ["Five services: a three-stage ingestion pipeline, plus a two-part "
      "control plane",
      "Three Kafka topics; one law maps to one partition, so generations "
      "cannot race",
      "Exactly one service writes each store \u2014 enforced by deleting the "
      "path that violated it"]),

    ("What happens to one law?",
     "Source \u2192 trusted corpus",
     "04-source-to-trusted-corpus",
     ["Bytes are hashed before anything interprets them",
      "The structural denominator is built independently of the parser",
      "law.structured means PostgreSQL only; law.embedded is the completion "
      "boundary"]),

    ("How do you know it is right?",
     "Verification and reconciliation",
     "17-verification-essence",
     ["14 gates; 7 required for the badge, all 14 recorded and shown",
      "The prover proves itself first, or issues no verdict for any law",
      "A count matching is not proof \u2014 and the diagram says so"]),

    ("How is a question answered?",
     "The query path",
     "07-rag-query-flow",
     ["BGE-M3 dense + sparse in one pass, fused server-side by RRF",
      "Citations travel as payload, not as generated prose",
      "The loader refuses a whole law rather than store a truncated embedding"]),

    ("What happens when it breaks?",
     "Failure, recovery and operational control",
     "15-document-state-machine",
     ["Fifteen documented failures, each with its recovery \u2014 or the "
      "statement that none exists",
      "Redelivery is safe because identity is derived, never generated",
      "No dead-letter topic on the legal pipeline: stated as a gap, not hidden"]),

    ("What else runs on the platform?",
     "Document intelligence",
     "10-insurance-document-ai",
     ["Docling conversion, then template-driven LLM field extraction with "
      "post-validation",
      "A template is the extraction contract, not the model \u2014 six "
      "document types",
      "Hardened against real documents: rebuilt regexes, umlaut repair, "
      "replacement-character detection"]),

    ("Is there computer vision too?",
     "Chest X-ray classification \u2014 a research prototype",
     "18-ai-radiologist",
     ["Internal project name \u201cAI Radiologist\u201d \u2014 not a medical device, not clinically deployed",
      "DenseNet-121 over five findings, sigmoid per class \u2014 a study can "
      "show several at once",
      "One calibrated threshold per finding (Youden's J), plus ICD-10 and an "
      "urgency band",
      "Grad-CAM++ attribution, with anatomical priors built and then "
      "deliberately switched off"]),

    ("What is all of it actually for?",
     "AI Compliance \u2014 the product the corpus serves",
     "19-ai-compliance",
     ["A questionnaire plus a headless-browser site scan become a grounded, "
      "cited compliance report",
      "A report that cites a drifted provision is confidently wrong \u2014 "
      "which is why the corpus is verified",
      "The product is a colleague's work; I built the corpus and the service "
      "the questionnaire path runs in"]),

    ("What did you personally build?",
     "What I built, and what I did not",
     "12-my-contributions",
     ["Primary: preprocessor, loader, health service, dashboard \u2014 four "
      "of the system's five services",
      "Significant: entity producer, document extractor, indexing service "
      "(which I created), ai-utils",
      "Not mine: the Java entity platform, the RAG service, the chatbot, "
      "every third-party store"]),

    ("What would you do differently?",
     "Engineering lessons and design principles",
     "13-interview-system-overview",
     ["Keep: one writer per store; derive identity; refuse rather than "
      "approximate",
      "Change: add a dead-letter path; generate the gate list once; "
      "content-address the captures",
      "The lesson: a measurement nobody can falsify is not a measurement"]),
]



# ---------------------------------------------------------------------------
# PPTX
# ---------------------------------------------------------------------------
def build_pptx() -> pathlib.Path:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    def rgb(h: str) -> RGBColor:
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    for i, (kicker, title, stem, bullets) in enumerate(DECK, start=1):
        s = prs.slides.add_slide(blank)

        bgfill = s.background.fill
        bgfill.solid()
        bgfill.fore_color.rgb = rgb(BG)

        # kicker -- the question this slide answers (absent on the hero)
        if kicker:
            kb = s.shapes.add_textbox(Inches(0.62), Inches(0.42),
                                      Inches(9.0), Inches(0.32))
            kp = kb.text_frame.paragraphs[0]
            kp.text = kicker
            kp.font.size = Pt(12)
            kp.font.color.rgb = rgb(TRUST)
            kp.font.name = "Segoe UI"

        tb = s.shapes.add_textbox(Inches(0.6), Inches(0.74),
                                  Inches(11.6), Inches(0.9))
        tp = tb.text_frame.paragraphs[0]
        tp.text = title
        tp.font.size = Pt(33)
        tp.font.bold = False
        tp.font.color.rgb = rgb(INK)
        tp.font.name = "Georgia"

        # slide number
        nb = s.shapes.add_textbox(Inches(12.3), Inches(6.95),
                                  Inches(0.6), Inches(0.3))
        np_ = nb.text_frame.paragraphs[0]
        np_.text = f"{i:02d}"
        np_.font.size = Pt(10)
        np_.font.color.rgb = rgb(LOW)
        np_.alignment = PP_ALIGN.RIGHT

        img = PNG / f"{stem}.png" if stem else None
        has_img = bool(img and img.exists())

        if has_img:
            box_w, box_h = Inches(8.35), Inches(5.0)
            left, top = Inches(0.6), Inches(1.75)
            # scale to fit the box, preserving aspect from the PNG header
            import struct
            raw = img.read_bytes()[16:24]
            iw, ih = struct.unpack(">II", raw)
            scale = min(box_w / iw, box_h / ih)
            w, h = Emu(int(iw * scale)), Emu(int(ih * scale))
            s.shapes.add_picture(str(img), left, top, width=w, height=h)
            bl, bw = Inches(9.2), Inches(3.55)
        else:
            bl, bw = Inches(0.62), Inches(9.6)

        bbox = s.shapes.add_textbox(bl, Inches(1.8), bw, Inches(4.9))
        tf = bbox.text_frame
        tf.word_wrap = True
        for j, b in enumerate(bullets):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.text = b
            p.font.size = Pt(16 if has_img else 20)
            p.font.color.rgb = rgb(MID)
            p.font.name = "Segoe UI"
            p.space_after = Pt(15 if has_img else 18)
            p.line_spacing = 1.28

        fb = s.shapes.add_textbox(Inches(0.62), Inches(6.92),
                                  Inches(9.0), Inches(0.3))
        fp = fb.text_frame.paragraphs[0]
        fp.text = ("Mohd Zamin Quadri  ·  AI Engineer  ·  BP-ITCS   "
                   "—   every claim traceable to a file")
        fp.font.size = Pt(9.5)
        fp.font.color.rgb = rgb(LOW)
        fp.font.name = "Segoe UI"

    PRES.mkdir(parents=True, exist_ok=True)
    out = PRES / f"{NAME}.pptx"
    prs.save(str(out))
    return out


# ---------------------------------------------------------------------------
# HTML rendition -> PDF + per-slide PNG
# ---------------------------------------------------------------------------
def deck_html(*, for_print: bool, start: int = 1) -> str:
    slides = []
    for i, (kicker, title, stem, bullets) in enumerate(DECK, start=start):
        img = ""
        if stem and (PNG / f"{stem}.png").exists():
            img = (f'<div class="shot"><img src="../assets/png/{stem}.png" '
                   f'alt="{title}"></div>')
        lis = "".join(f"<li>{b}</li>" for b in bullets)
        deep = (f' &nbsp;|&nbsp; full resolution: assets/png/{stem}.png'
                if stem and stem != "ai-engineering-architecture-4k"
                else "")
        # Built outside the f-string below. An escaped quote inside an f-string
        # expression is Python 3.12 syntax, and nothing in this repository says
        # it needs 3.12, so on 3.11 the whole module failed to parse before a
        # single generator could run.
        kicker_html = f'<p class="k">{kicker}</p>' if kicker else ""
        wide = " wide" if not img else ""
        slides.append(f"""<section class="slide{wide}">
  {kicker_html}
  <h2>{title}</h2>
  <div class="body">{img}<ul>{lis}</ul></div>
  <p class="foot">Mohd Zamin Quadri &middot; AI Engineer &middot; BP-ITCS
    &mdash; every claim traceable to a file{deep}<span class="no">{i:02d}</span></p>
</section>""")
    page = "@page { size: 1280px 720px; margin: 0; }" if for_print else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{NAME}</title>
<style>
{page}
:root {{
  --bg:#{BG}; --ink:#{INK}; --mid:#{MID}; --low:#{LOW};
  --trust:#{TRUST}; --hair:#{HAIR};
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans:Inter,"Segoe UI",system-ui,-apple-system,Arial,sans-serif;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#05070b; color:var(--ink);
  font-family:var(--sans); }}
.slide {{ width:1280px; height:720px; padding:48px 64px 40px;
  background:var(--bg); position:relative; overflow:hidden;
  page-break-after:always; break-after:page;
  page-break-inside:avoid; break-inside:avoid;
  background-image:linear-gradient(#0f1720 1px,transparent 1px),
                   linear-gradient(90deg,#0f1720 1px,transparent 1px);
  background-size:40px 40px; }}
.slide + .slide {{ margin-top:{0 if for_print else 26}px; }}
.slide:last-child {{ page-break-after:auto; break-after:auto; }}
.k {{ margin:0 0 6px; font-size:13px; color:var(--trust); }}
h2 {{ font-family:var(--serif); font-weight:500; font-size:41px;
  line-height:1.08; letter-spacing:-.01em; margin:0 0 22px; max-width:22ch; }}
.slide.wide h2 {{ max-width:34ch; }}
.body {{ display:grid; grid-template-columns:1fr 330px; gap:32px;
  align-items:start; }}
.slide.wide .body {{ grid-template-columns:1fr; }}
.shot {{ border:1px solid var(--hair); border-radius:9px; overflow:hidden;
  background:#070A0F; }}
.shot img {{ display:block; width:100%; height:auto;
  max-height:440px; object-fit:contain; object-position:top left; }}
ul {{ margin:0; padding-left:1.1em; }}
li {{ color:var(--mid); font-size:16.5px; line-height:1.46;
  margin-bottom:17px; }}
.slide.wide li {{ font-size:19px; line-height:1.46; margin-bottom:16px;
  max-width:62ch; }}
.foot {{ position:absolute; left:64px; right:64px; bottom:30px; margin:0;
  padding-top:12px; border-top:1px solid var(--hair);
  font-size:11px; color:var(--low); display:flex; }}
.no {{ margin-left:auto; font-variant-numeric:tabular-nums; }}
</style></head><body>
{"".join(slides)}
</body></html>"""


def build_pdf_and_slides() -> tuple[pathlib.Path, int]:
    chrome = find_chrome()
    PRES.mkdir(parents=True, exist_ok=True)
    SLIDES.mkdir(parents=True, exist_ok=True)

    printable = PRES / "_deck.print.html"
    printable.write_text(deck_html(for_print=True), encoding="utf-8")
    pdf = PRES / f"{NAME}.pdf"
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=6000",
         f"--print-to-pdf={pdf.resolve()}", printable.resolve().as_uri()],
        check=True, capture_output=True,
    )

    # one PNG per slide, by rendering a single-slide page for each
    count = 0
    for i, entry in enumerate(DECK, start=1):
        one = PRES / "_slide.html"
        saved = list(DECK)
        DECK.clear()
        DECK.append(entry)
        one.write_text(deck_html(for_print=True, start=i), encoding="utf-8")
        DECK.clear()
        DECK.extend(saved)
        out = SLIDES / f"slide-{i:02d}.png"
        subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             "--hide-scrollbars", "--force-device-scale-factor=2",
             "--window-size=1280,720", "--virtual-time-budget=4000",
             f"--screenshot={out.resolve()}", one.resolve().as_uri()],
            check=True, capture_output=True,
        )
        count += 1
        one.unlink(missing_ok=True)
    printable.unlink(missing_ok=True)
    return pdf, count


if __name__ == "__main__":
    p = build_pptx()
    print(f"wrote {p.relative_to(ROOT)}  {len(DECK)} slides  "
          f"{p.stat().st_size / 1024:,.0f} KB")
    pdf, n = build_pdf_and_slides()
    print(f"wrote {pdf.relative_to(ROOT)}  {pdf.stat().st_size / 1024:,.0f} KB")
    print(f"wrote {n} slide PNGs at 2560x1440 into "
          f"{SLIDES.relative_to(ROOT)}")
