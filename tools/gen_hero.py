"""Build the hero image: portfolio/assets/png/ai-engineering-architecture-4k.png

Authored as a 1920x1080 SVG and rasterised at 2x, so the delivered PNG is
3840x2160 true vector output rather than an upscale.

The composition is deliberately not a shrunken architecture diagram. It carries
the spine of the system as six labelled stages, the four stores beneath it, and
one piece of evidence -- because the characteristic artefact of this system is a
record you can check, not a box-and-arrow chart.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import design_tokens as T                                   # noqa: E402
from export_png import find_chrome, png_size                # noqa: E402
from svg_kit import Canvas, measure, text_el                # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SVG = ROOT / "assets" / "architecture" / "hero.svg"
PNG = (ROOT / "assets" / "png" /
       "ai-engineering-architecture-4k.png")

STAGES = [
    ("Acquire", "source", "the publisher's own bytes"),
    ("Structure", "trust", "parsed against the source, not the parser"),
    ("Persist", "store", "canonical, with the rules that made it"),
    ("Project", "ai", "vectors and a provision graph"),
    ("Verify", "trust", "fourteen gates, recorded per generation"),
    ("Operate", "ui", "one narrow control plane"),
]

STORES = [
    ("PostgreSQL", "canonical record"),
    ("Qdrant", "semantic retrieval"),
    ("Neo4j", "reference traversal"),
    ("MinIO", "immutable evidence"),
]


def build() -> str:
    c = Canvas(1920, 1080)
    c.background()

    # ---- one wide soft band behind the spine, the only decoration
    c.define(
        "bandgrad",
        '<linearGradient id="bandgrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{T.rgba(T.ROLE["source"], 0.16)}"/>'
        f'<stop offset="34%" stop-color="{T.rgba(T.ROLE["trust"], 0.16)}"/>'
        f'<stop offset="62%" stop-color="{T.rgba(T.ROLE["ai"], 0.16)}"/>'
        f'<stop offset="100%" stop-color="{T.rgba(T.ROLE["ui"], 0.16)}"/>'
        "</linearGradient>",
    )

    # ---- title block
    x = 120
    c.add(text_el("Mohd Zamin Quadri", x, 150, "subtitle", T.INK_MUTED))
    c.add(text_el("AI Engineer", x + measure("Mohd Zamin Quadri", "subtitle") + 26,
                  150, "subtitle", T.INK_FAINT))

    serif = ('"Iowan Old Style","Palatino Linotype",Palatino,Georgia,'
             '"Times New Roman",serif')
    c.add(
        f'<text x="{x}" y="266" font-family=\'{serif}\' font-size="92" '
        f'font-weight="500" fill="{T.INK}" letter-spacing="-1.6">'
        f'AI Engineering Systems</text>'
    )
    c.add(
        f'<text x="{x}" y="332" font-family=\'{T.SANS}\' font-size="25" '
        f'fill="{T.INK_MUTED}">Legal knowledge · document intelligence '
        f'· retrieval · verification · event-driven architecture'
        f'</text>'
    )

    # ---- the spine
    sy = 470
    band_x0, band_x1 = x, 1800
    c.add(
        f'<rect x="{band_x0}" y="{sy - 46}" width="{band_x1 - band_x0}" '
        f'height="150" rx="18" fill="url(#bandgrad)" opacity="0.5"/>'
    )
    step_w = (band_x1 - band_x0) / len(STAGES)
    for i, (name, role, sub) in enumerate(STAGES):
        cx = band_x0 + step_w * i + step_w / 2
        accent = T.ROLE[role]
        c.add(
            f'<circle cx="{cx}" cy="{sy}" r="13" fill="{T.CANVAS}" '
            f'stroke="{accent}" stroke-width="2.4"/>'
            f'<circle cx="{cx}" cy="{sy}" r="4.6" fill="{accent}"/>'
        )
        c.add(
            f'<text x="{cx}" y="{sy + 46}" font-family=\'{T.SANS}\' '
            f'font-size="25" font-weight="600" fill="{T.INK}" '
            f'text-anchor="middle">{name}</text>'
        )
        # wrap the sub-label to the column
        words, line, lines = sub.split(), "", []
        for w in words:
            trial = f"{line} {w}".strip()
            if measure(trial, "meta", size=15) <= step_w - 46:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
        for j, ln in enumerate(lines):
            c.add(
                f'<text x="{cx}" y="{sy + 72 + j * 21}" '
                f'font-family=\'{T.SANS}\' font-size="15" '
                f'fill="{T.INK_FAINT}" text-anchor="middle">{ln}</text>'
            )
        if i < len(STAGES) - 1:
            nx = band_x0 + step_w * (i + 1) + step_w / 2
            c.add(
                f'<line x1="{cx + 17}" y1="{sy}" x2="{nx - 19}" y2="{sy}" '
                f'stroke="{T.rgba(accent, 0.45)}" stroke-width="2"/>'
            )

    # ---- stores
    ty = 730
    sw = (band_x1 - band_x0 - 3 * 26) / 4
    for i, (name, role_txt) in enumerate(STORES):
        bx = band_x0 + i * (sw + 26)
        c.add(
            f'<rect x="{bx}" y="{ty}" width="{sw}" height="96" rx="12" '
            f'fill="{T.tint("store", 0.09)}" '
            f'stroke="{T.border("store", 0.5)}" stroke-width="1.4"/>'
            f'<rect x="{bx + 3}" y="{ty + 3}" width="{sw - 6}" height="90" '
            f'rx="9" fill="none" stroke="{T.border("store", 0.24)}" '
            f'stroke-width="1"/>'
        )
        c.add(
            f'<text x="{bx + 24}" y="{ty + 42}" font-family=\'{T.SANS}\' '
            f'font-size="23" font-weight="600" fill="{T.INK}">{name}</text>'
            f'<text x="{bx + 24}" y="{ty + 70}" font-family=\'{T.SANS}\' '
            f'font-size="15" fill="{T.INK_FAINT}">{role_txt}</text>'
        )
    c.add(
        f'<text x="{band_x0}" y="{ty - 22}" font-family=\'{T.SANS}\' '
        f'font-size="14" font-weight="600" fill="{T.INK_FAINT}" '
        f'letter-spacing="1.6">ONE WRITER EACH</text>'
    )

    # ---- the claim
    cy = 930
    c.add(
        f'<rect x="{band_x0}" y="{cy - 26}" width="3" height="72" rx="1.5" '
        f'fill="{T.rgba(T.ROLE["trust"], 0.85)}"/>'
    )
    c.add(
        f'<text x="{band_x0 + 22}" y="{cy}" font-family=\'{T.SANS}\' '
        f'font-size="21" fill="{T.INK_MUTED}">Every stored item re-derivable '
        f'from the publisher’s own bytes, under a recorded set of rules.'
        f'</text>'
        f'<text x="{band_x0 + 22}" y="{cy + 32}" font-family=\'{T.SANS}\' '
        f'font-size="21" fill="{T.INK_MUTED}">When it cannot be, the system '
        f'says so rather than serving it quietly.</text>'
    )
    return c.render()


if __name__ == "__main__":
    SVG.parent.mkdir(parents=True, exist_ok=True)
    SVG.write_text(build(), encoding="utf-8")
    print(f"wrote {SVG.relative_to(ROOT)}")
    chrome = find_chrome()
    PNG.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--force-device-scale-factor=2",
         "--window-size=1920,1080", f"--screenshot={PNG.resolve()}",
         SVG.resolve().as_uri()],
        check=True, capture_output=True,
    )
    w, h = png_size(PNG)
    print(f"wrote {PNG.relative_to(ROOT)}  {w}x{h}")
    assert (w, h) == (3840, 2160), f"expected 3840x2160, got {w}x{h}"
