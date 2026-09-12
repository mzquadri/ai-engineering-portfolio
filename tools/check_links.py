"""Validate every internal reference in the portfolio.

    python tools/check_links.py

Checks, in order:
  1. every relative link and image path in every Markdown file resolves
  2. every image/href/figure path referenced by index.html resolves
  3. every diagram stem the deck references has a PNG
  4. every .drawio parses as XML and contains real shapes, not an image
  5. every .svg parses as XML and declares a viewBox
  6. the public docs/architecture copies match their canonical SVGs

Exits non-zero on any failure. This is the gate the QA report cites.
"""

from __future__ import annotations

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
fails: list[str] = []
checked = {"md_links": 0, "html_refs": 0, "deck": 0, "drawio": 0, "svg": 0}


def rel(p: pathlib.Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


# ---------------------------------------------------------------- 1. markdown
MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
for md in sorted(ROOT.rglob("*.md")):
    if "__pycache__" in md.parts:
        continue
    text = md.read_text(encoding="utf-8")
    for target in MD_LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        checked["md_links"] += 1
        path = (md.parent / target.split("#")[0]).resolve()
        if not path.exists():
            fails.append(f"{rel(md)} -> missing {target}")

# ---------------------------------------------------------------- 2. index.html
index = ROOT / "index.html"
if not index.exists():
    fails.append("index.html is missing")
else:
    html = index.read_text(encoding="utf-8")
    refs = set(re.findall(r'(?:href|src)="([^"#:]+)"', html))
    for target in sorted(refs):
        if target.startswith(("http", "//", "data:", "mailto:")):
            continue
        checked["html_refs"] += 1
        if not (ROOT / target).exists():
            fails.append(f"index.html -> missing {target}")
    if "<svg" not in html:
        fails.append("index.html contains no inline <svg> -- diagrams did not inline")

# ---------------------------------------------------------------- 3. deck stems
# Import the deck rather than pattern-matching its source: a regex over the
# literal matched bullet text that happened to sit alone on a line.
sys.path.insert(0, str(ROOT / "tools"))
try:
    from gen_deck import DECK  # noqa: E402
except Exception as e:                                      # noqa: BLE001
    fails.append(f"cannot import tools/gen_deck.py: {type(e).__name__}: {e}")
    DECK = []
for _kicker, title, stem, _bullets in DECK:
    if not stem:
        continue
    checked["deck"] += 1
    if not (ROOT / "assets" / "png" / f"{stem}.png").exists():
        fails.append(f"deck slide {title!r} references assets/png/{stem}.png "
                     f"which is missing")

# ---------------------------------------------------------------- 4. drawio
for dio in sorted((ROOT / "assets" / "drawio").glob("*.drawio")):
    checked["drawio"] += 1
    try:
        root = ET.parse(dio).getroot()
    except ET.ParseError as e:
        fails.append(f"{rel(dio)} is not well-formed XML: {e}")
        continue
    cells = root.findall(".//mxCell")
    verts = [c for c in cells if c.get("vertex") == "1"]
    edges = [c for c in cells if c.get("edge") == "1"]
    imgs = [c for c in cells if "image=" in (c.get("style") or "")]
    if len(verts) < 5:
        fails.append(f"{rel(dio)} has only {len(verts)} shapes -- suspiciously few")
    if not edges:
        fails.append(f"{rel(dio)} has no edges -- shapes are not connected")
    if imgs:
        fails.append(f"{rel(dio)} embeds {len(imgs)} image(s) -- must be real shapes")

# ---------------------------------------------------------------- 5. svg
for svg in sorted((ROOT / "assets" / "architecture").glob("*.svg")):
    checked["svg"] += 1
    try:
        root = ET.parse(svg).getroot()
    except ET.ParseError as e:
        fails.append(f"{rel(svg)} is not well-formed XML: {e}")
        continue
    if not root.get("viewBox"):
        fails.append(f"{rel(svg)} has no viewBox -- will not scale")

# ---------------------------------------------------------------- 6. public copies
PUBLIC = {
    "system-overview": "01-ai-systems-landscape",
    "legal-knowledge-flow": "02-legal-knowledge-database",
    "rag-flow": "07-rag-query-flow",
    "verification-flow": "06-verification-and-reconciliation",
    "verification-short": "17-verification-essence",
    "interview-overview": "13-interview-system-overview",
}
for dst, src in PUBLIC.items():
    a = ROOT / "docs" / "architecture" / f"{dst}.svg"
    b = ROOT / "assets" / "architecture" / f"{src}.svg"
    if not a.exists():
        fails.append(f"public copy docs/architecture/{dst}.svg is missing")
    elif not b.exists():
        fails.append(f"canonical assets/architecture/{src}.svg is missing")
    elif a.read_bytes() != b.read_bytes():
        fails.append(f"docs/architecture/{dst}.svg has drifted from {src}.svg "
                     f"-- re-run tools/gen_diagrams.py")

# ---------------------------------------------------------------- report
print("checked: " + " · ".join(f"{k}={v}" for k, v in checked.items()))
if fails:
    print(f"\n{len(fails)} failure(s):\n")
    for f in fails:
        print(f"  {f}")
    sys.exit(1)
print("\nAll internal references resolve. No drift, no embedded images, "
      "every SVG scalable.")
