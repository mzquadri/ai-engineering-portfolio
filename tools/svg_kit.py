"""SVG primitives for the architecture pack.

Stdlib only. Produces true vector output with named groups, so every diagram
stays editable and diffable. Nothing here rasterises; PNG export is a separate
step (export_png.py) driven by headless Chromium.

The part that matters most is measure(): every string is measured against a
per-character advance-width table before it is placed, text is wrapped to the
available width, boxes grow to fit, and an unbreakable token that still does not
fit raises rather than silently clipping. A build that would clip fails.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

import design_tokens as T

# ---------------------------------------------------------------------------
# Text metrics
# ---------------------------------------------------------------------------
# Advance widths in 1/1000 em, approximating Inter / Segoe UI at weight 400.
# Accurate to a few percent, which is what matters: the wrap decision only has
# to be conservative, and every value here errs slightly wide.
_ADV = {
    " ": 260, "!": 280, '"': 380, "#": 600, "$": 560, "%": 760, "&": 640,
    "'": 210, "(": 320, ")": 320, "*": 440, "+": 560, ",": 270, "-": 330,
    ".": 270, "/": 400, ":": 270, ";": 270, "<": 560, "=": 560, ">": 560,
    "?": 480, "@": 900, "[": 320, "\\": 400, "]": 320, "^": 500, "_": 480,
    "`": 300, "{": 340, "|": 260, "}": 340, "~": 560,
    "A": 660, "B": 640, "C": 680, "D": 700, "E": 580, "F": 560, "G": 720,
    "H": 720, "I": 280, "J": 520, "K": 650, "L": 550, "M": 860, "N": 720,
    "O": 760, "P": 620, "Q": 770, "R": 640, "S": 610, "T": 600, "U": 710,
    "V": 650, "W": 960, "X": 640, "Y": 620, "Z": 590,
    "a": 550, "b": 580, "c": 510, "d": 580, "e": 550, "f": 340, "g": 580,
    "h": 570, "i": 250, "j": 250, "k": 540, "l": 250, "m": 870, "n": 570,
    "o": 580, "p": 580, "q": 580, "r": 380, "s": 500, "t": 370, "u": 570,
    "v": 520, "w": 790, "x": 520, "y": 520, "z": 490,
}
_DIGIT = 580
_FALLBACK = 600          # CJK, symbols, anything unmapped -- err wide
_MONO_ADV = 600          # JetBrains Mono / Consolas advance
_WEIGHT_SCALE = {400: 1.0, 500: 1.012, 600: 1.03, 700: 1.05}


def measure(text: str, style: str | dict, *, size: float | None = None) -> float:
    """Advance width of `text` in px for a TYPE style (or a style dict)."""
    st = T.TYPE[style] if isinstance(style, str) else style
    sz = size if size is not None else st["size"]
    mono = st["font"] is T.MONO or st.get("font") == T.MONO
    scale = _WEIGHT_SCALE.get(int(st.get("weight", 400)), 1.03)
    track = float(st.get("track", 0.0))
    total = 0.0
    for ch in text:
        if mono:
            adv = _MONO_ADV
        elif ch.isdigit():
            adv = _DIGIT
        else:
            adv = _ADV.get(ch, _FALLBACK)
        total += adv / 1000.0 * sz
    return total * scale + track * max(len(text) - 1, 0)


class TextTooWide(RuntimeError):
    """An unbreakable token does not fit its box. Fail rather than clip."""


def wrap(text: str, style: str | dict, width: float, *, where: str = "") -> list[str]:
    """Greedy word wrap to `width` px. Raises if a single word cannot fit."""
    if not text:
        return []
    words, lines, cur = text.split(), [], ""
    for w in words:
        if measure(w, style) > width:
            raise TextTooWide(
                f"token {w!r} needs {measure(w, style):.1f}px but only "
                f"{width:.1f}px is available{(' in ' + where) if where else ''}. "
                "Widen the box or shorten the label -- do not let it clip."
            )
        trial = f"{cur} {w}".strip()
        if measure(trial, style) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def line_height(style: str | dict) -> float:
    st = T.TYPE[style] if isinstance(style, str) else style
    return st["size"] * st["lh"]


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
@dataclass
class Canvas:
    width: int
    height: int
    title: str = ""
    subtitle: str = ""
    eyebrow: str = ""
    parts: list[str] = field(default_factory=list)
    back: list[str] = field(default_factory=list)
    defs: list[str] = field(default_factory=list)
    _defs_keys: set = field(default_factory=set)

    # -- low level ---------------------------------------------------------
    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def define(self, key: str, markup: str) -> None:
        if key not in self._defs_keys:
            self._defs_keys.add(key)
            self.defs.append(markup)

    def group(self, markup: str, *, label: str, under: bool = False,
              data: dict | None = None) -> None:
        """Wrap markup in a named group, so the SVG stays navigable when edited.

        under=True puts the group in the underlay, which renders beneath every
        later part. Lanes use it so a lane can be sized from the content it
        contains without being drawn over that content.
        """
        attrs = f' data-name="{escape(label)}"'
        for k, v in (data or {}).items():
            attrs += f' data-{k}="{escape(str(v))}"'
        (self.back if under else self.parts).append(f'<g{attrs}>{markup}</g>')

    # -- chrome ------------------------------------------------------------
    def background(self) -> None:
        self.define(
            "grid",
            '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M40 0H0V40" fill="none" stroke="{T.GRID}" stroke-width="1" '
            'stroke-opacity="0.5"/></pattern>',
        )
        self.define(
            "grid-coarse",
            '<pattern id="grid-coarse" width="200" height="200" '
            'patternUnits="userSpaceOnUse">'
            f'<path d="M200 0H0V200" fill="none" stroke="{T.GRID}" '
            'stroke-width="1.4" stroke-opacity="0.9"/></pattern>',
        )
        self.define(
            "vignette",
            '<radialGradient id="vignette" cx="50%" cy="120%" r="120%">'
            f'<stop offset="0%" stop-color="{T.rgba("#000000", 0.34)}"/>'
            f'<stop offset="55%" stop-color="{T.rgba("#000000", 0.10)}"/>'
            f'<stop offset="100%" stop-color="{T.rgba("#000000", 0.0)}"/>'
            "</radialGradient>",
        )
        self.define(
            "aurora-a",
            '<radialGradient id="aurora-a" cx="8%" cy="-6%" r="62%">'
            f'<stop offset="0%" stop-color="{T.rgba(T.ROLE["ui"], 0.13)}"/>'
            f'<stop offset="100%" stop-color="{T.rgba(T.ROLE["ui"], 0.0)}"/>'
            "</radialGradient>",
        )
        self.define(
            "aurora-b",
            '<radialGradient id="aurora-b" cx="96%" cy="4%" r="58%">'
            f'<stop offset="0%" stop-color="{T.rgba(T.ROLE["trust"], 0.10)}"/>'
            f'<stop offset="100%" stop-color="{T.rgba(T.ROLE["trust"], 0.0)}"/>'
            "</radialGradient>",
        )
        self.define(
            "topsheen",
            '<linearGradient id="topsheen" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{T.rgba(T.ROLE["ui"], 0.0)}"/>'
            f'<stop offset="22%" stop-color="{T.rgba(T.ROLE["ui"], 0.45)}"/>'
            f'<stop offset="52%" stop-color="{T.rgba(T.ROLE["trust"], 0.40)}"/>'
            f'<stop offset="78%" stop-color="{T.rgba(T.ROLE["ai"], 0.35)}"/>'
            f'<stop offset="100%" stop-color="{T.rgba(T.ROLE["ai"], 0.0)}"/>'
            "</linearGradient>",
        )
        # Goes in the underlay, ahead of the lanes, so lanes sit above the grid
        # and below every card. Regenerated by fit() if the height changes.
        self.back.insert(0, self._bg_markup())

    def _bg_markup(self) -> str:
        """Layered ground: deep base, a fine grid over a coarse one, two
        corner auroras and a faint top sheen.

        Each layer is cheap and none of it competes with the content -- the
        total added ink is under 8% opacity. The point is depth, so cards read
        as floating above a surface rather than pasted onto a flat fill."""
        w, h = self.width, self.height
        return (
            f'<g data-name="background">'
            f'<rect width="{w}" height="{h}" fill="{T.CANVAS}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#grid-coarse)" '
            f'opacity="0.5"/>'
            f'<rect width="{w}" height="{h}" fill="url(#grid)" opacity="0.38"/>'
            f'<rect width="{w}" height="{h}" fill="url(#aurora-a)"/>'
            f'<rect width="{w}" height="{h}" fill="url(#aurora-b)"/>'
            f'<rect width="{w}" height="{h}" fill="url(#vignette)"/>'
            f'<rect width="{w}" height="2" fill="url(#topsheen)"/>'
            f'</g>'
        )

    def fit(self, bottom: float, *, pad: float = 36.0,
            footnote: dict | None = None, legend_spec: dict | None = None) -> None:
        """Trim the canvas to its content, then place the footnote and legend.

        Diagrams are laid out top-down without knowing their final height. This
        sets the height from the real content bottom, so no diagram ships with a
        band of dead space -- the defect that made the first drafts look
        unfinished.
        """
        y = bottom + pad
        if footnote:
            nb = note(self, T.SAFE, y, self.width - 2 * T.SAFE, **footnote)
            y = nb.bottom + 26
        if legend_spec:
            rows = sum(1 for k in ("roles", "flows", "levels") if legend_spec.get(k))
            y += 14
            legend(self, T.SAFE, y, **legend_spec)
            y += rows * 22 + 2
        self.height = int(round(y + T.SAFE - 18))
        self.back[0] = self._bg_markup()

    def header(self) -> float:
        """Draw the title block. Returns the y where content may begin."""
        x, y = T.SAFE, T.SAFE
        out = []
        if self.eyebrow:
            out.append(
                text_el(self.eyebrow.upper(), x, y + 12, "lane", T.ROLE["ui"])
            )
            y += 26
        if self.title:
            out.append(text_el(self.title, x, y + 27, "title", T.INK))
            y += 44
        if self.subtitle:
            w = self.width - 2 * T.SAFE - 360
            for i, ln in enumerate(wrap(self.subtitle, "subtitle", w, where="subtitle")):
                out.append(
                    text_el(ln, x, y + 14 + i * line_height("subtitle"),
                            "subtitle", T.INK_MUTED)
                )
            y += line_height("subtitle") * len(
                wrap(self.subtitle, "subtitle", w, where="subtitle")
            ) + 6
        out.append(
            f'<line x1="{x}" y1="{y + 14}" x2="{self.width - T.SAFE}" y2="{y + 14}" '
            f'stroke="{T.HAIRLINE}" stroke-width="1"/>'
        )
        self.group("".join(out), label="header")
        return y + 14 + 30

    def byline(self, name: str = "Mohd Zamin Quadri",
               role: str = "AI Engineer · BP-ITCS") -> None:
        x = self.width - T.SAFE
        self.group(
            text_el(name, x, T.SAFE + 14, "legend", T.INK_MUTED, anchor="end")
            + text_el(role, x, T.SAFE + 32, "meta", T.INK_FAINT, anchor="end"),
            label="byline",
        )

    def footnote(self, lines: list[str], *, y: float | None = None,
                 accent: str = "neutral") -> None:
        yy = y if y is not None else self.height - T.SAFE - len(lines) * 17
        out = [
            f'<rect x="{T.SAFE}" y="{yy - 12}" width="2.5" '
            f'height="{len(lines) * 17 + 4}" rx="1.2" fill="{T.rail(accent, 0.8)}"/>'
        ]
        for i, ln in enumerate(lines):
            out.append(text_el(ln, T.SAFE + 14, yy + i * 17, "note", T.INK_MUTED))
        self.group("".join(out), label="footnote")

    # -- output ------------------------------------------------------------
    def render(self) -> str:
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" '
            f'role="img" aria-label="{escape(self.title or "architecture diagram")}" '
            f'font-family=\'{T.SANS}\'>'
            f"{defs}{''.join(self.back)}{''.join(self.parts)}</svg>"
        )


# ---------------------------------------------------------------------------
# Text element
# ---------------------------------------------------------------------------
def text_el(s: str, x: float, y: float, style: str | dict, fill: str, *,
            anchor: str = "start", opacity: float | None = None) -> str:
    st = T.TYPE[style] if isinstance(style, str) else style
    attrs = [
        f'x="{x:.1f}"', f'y="{y:.1f}"',
        f'font-size="{st["size"]}"', f'font-weight="{st["weight"]}"',
        f'fill="{fill}"',
    ]
    if st["font"] is T.MONO:
        attrs.append(f"font-family='{T.MONO}'")
    if st.get("track"):
        attrs.append(f'letter-spacing="{st["track"]}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if style == "lane" or (isinstance(style, dict) and style.get("upper")):
        s = s.upper()
    return f'<text {" ".join(attrs)}>{escape(s)}</text>'


# ---------------------------------------------------------------------------
# Box model
# ---------------------------------------------------------------------------
@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float = 0.0   # 0 means "grow to fit" -- card()/store() compute it

    @property
    def cx(self) -> float: return self.x + self.w / 2

    @property
    def cy(self) -> float: return self.y + self.h / 2

    @property
    def right(self) -> float: return self.x + self.w

    @property
    def bottom(self) -> float: return self.y + self.h

    def port(self, side: str, t: float = 0.5) -> tuple[float, float]:
        if side == "n": return (self.x + self.w * t, self.y)
        if side == "s": return (self.x + self.w * t, self.bottom)
        if side == "w": return (self.x, self.y + self.h * t)
        if side == "e": return (self.right, self.y + self.h * t)
        raise ValueError(side)


# ---------------------------------------------------------------------------
# Glyphs -- 16px, drawn at (x, y) top-left
# ---------------------------------------------------------------------------
def glyph(kind: str, x: float, y: float, colour: str) -> str:
    s, o = 16.0, 1.3
    if kind == "relational":
        return "".join(
            f'<ellipse cx="{x + 8}" cy="{y + 4 + i * 4}" rx="6.2" ry="2.4" '
            f'fill="none" stroke="{colour}" stroke-width="{o}"/>' for i in range(3)
        )
    if kind == "vector":
        pts = [(8, 3), (3, 7), (13, 6), (5, 12), (11, 12), (8, 8)]
        return "".join(
            f'<circle cx="{x + a}" cy="{y + b}" r="1.7" fill="{colour}"/>'
            for a, b in pts
        )
    if kind == "graph":
        nodes = [(8, 3), (3, 12), (13, 12), (8, 8)]
        edges = [(0, 3), (1, 3), (2, 3), (1, 2)]
        out = [
            f'<line x1="{x + nodes[a][0]}" y1="{y + nodes[a][1]}" '
            f'x2="{x + nodes[b][0]}" y2="{y + nodes[b][1]}" '
            f'stroke="{colour}" stroke-width="{o}" stroke-opacity="0.75"/>'
            for a, b in edges
        ]
        out += [
            f'<circle cx="{x + a}" cy="{y + b}" r="2.1" fill="{colour}"/>'
            for a, b in nodes
        ]
        return "".join(out)
    if kind == "bucket":
        return (
            f'<path d="M{x + 2} {y + 3}h12l-1.6 10.5a1.4 1.4 0 0 1-1.4 1.2H{x + 5} '
            f'a1.4 1.4 0 0 1-1.4-1.2Z" fill="none" stroke="{colour}" stroke-width="{o}"/>'
            f'<line x1="{x + 1}" y1="{y + 3}" x2="{x + 15}" y2="{y + 3}" '
            f'stroke="{colour}" stroke-width="{o}"/>'
        )
    if kind == "service":
        return (
            f'<rect x="{x + 2}" y="{y + 2.5}" width="12" height="11" rx="2.4" '
            f'fill="none" stroke="{colour}" stroke-width="{o}"/>'
            f'<line x1="{x + 2}" y1="{y + 6.5}" x2="{x + 14}" y2="{y + 6.5}" '
            f'stroke="{colour}" stroke-width="{o}"/>'
        )
    if kind == "brain":  # AI / model
        return (
            f'<path d="M{x + 8} {y + 2.5}c-3 0-5 1.9-5 4.2 0 1 .4 1.9 1 2.6'
            f'-.4.6-.6 1.2-.6 1.9 0 1.6 1.4 2.8 3.2 2.8 .9 0 1.7-.3 2.3-.8'
            f'.6.5 1.4.8 2.3.8 1.8 0 3.2-1.2 3.2-2.8 0-.7-.2-1.3-.6-1.9'
            f'.6-.7 1-1.6 1-2.6 0-2.3-2-4.2-5-4.2Z" fill="none" '
            f'stroke="{colour}" stroke-width="{o}"/>'
            f'<line x1="{x + 8}" y1="{y + 4}" x2="{x + 8}" y2="{y + 13.5}" '
            f'stroke="{colour}" stroke-width="{o}" stroke-opacity="0.7"/>'
        )
    if kind == "document":
        return (
            f'<path d="M{x + 3.5} {y + 2}h6.5l3.5 3.5v8.5h-10z" fill="none" '
            f'stroke="{colour}" stroke-width="{o}" stroke-linejoin="round"/>'
            f'<path d="M{x + 10} {y + 2}v3.5h3.5" fill="none" stroke="{colour}" '
            f'stroke-width="{o}"/>'
        )
    if kind == "shield":
        return (
            f'<path d="M{x + 8} {y + 2}l5 2v4.2c0 3.2-2.1 5.6-5 6.6'
            f'c-2.9-1-5-3.4-5-6.6v-4.2z" fill="none" stroke="{colour}" '
            f'stroke-width="{o}" stroke-linejoin="round"/>'
            f'<path d="M{x + 5.4} {y + 8}l2 2 3.4-3.6" fill="none" stroke="{colour}" '
            f'stroke-width="{o + 0.2}" stroke-linecap="round"/>'
        )
    if kind == "globe":
        return (
            f'<circle cx="{x + 8}" cy="{y + 8}" r="5.8" fill="none" stroke="{colour}" '
            f'stroke-width="{o}"/>'
            f'<ellipse cx="{x + 8}" cy="{y + 8}" rx="2.4" ry="5.8" fill="none" '
            f'stroke="{colour}" stroke-width="{o}" stroke-opacity="0.7"/>'
            f'<line x1="{x + 2.3}" y1="{y + 8}" x2="{x + 13.7}" y2="{y + 8}" '
            f'stroke="{colour}" stroke-width="{o}" stroke-opacity="0.7"/>'
        )
    if kind == "ui":
        return (
            f'<rect x="{x + 2}" y="{y + 3}" width="12" height="10" rx="1.8" '
            f'fill="none" stroke="{colour}" stroke-width="{o}"/>'
            f'<line x1="{x + 2}" y1="{y + 6}" x2="{x + 14}" y2="{y + 6}" '
            f'stroke="{colour}" stroke-width="{o}"/>'
            f'<circle cx="{x + 4.2}" cy="{y + 4.5}" r="0.8" fill="{colour}"/>'
        )
    if kind == "bolt":
        return (
            f'<path d="M{x + 9.5} {y + 2}L{x + 4} {y + 9}h3.4l-1 5 5.6-7.4h-3.4Z" '
            f'fill="none" stroke="{colour}" stroke-width="{o}" stroke-linejoin="round"/>'
        )
    if kind == "alert":
        return (
            f'<path d="M{x + 8} {y + 2.5}l6 11H{x + 2}Z" fill="none" stroke="{colour}" '
            f'stroke-width="{o}" stroke-linejoin="round"/>'
            f'<line x1="{x + 8}" y1="{y + 6.5}" x2="{x + 8}" y2="{y + 9.8}" '
            f'stroke="{colour}" stroke-width="{o + 0.2}" stroke-linecap="round"/>'
            f'<circle cx="{x + 8}" cy="{y + 11.6}" r="0.85" fill="{colour}"/>'
        )
    return ""


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
def card(c: Canvas, box: Box, title: str, *, role: str = "neutral",
         level: str = "integrated", subtitle: str = "", meta: list[str] | None = None,
         icon: str | None = None, code_meta: bool = True,
         autoheight: bool = True, label: str | None = None) -> Box:
    """Draw a service/component card. Height grows to fit wrapped content."""
    lv = T.LEVEL[level]
    accent = T.ROLE[role]
    inner_w = box.w - 2 * T.PAD_X - (22 if icon else 0)

    title_lines = wrap(title, "card", inner_w, where=f"card title {title!r}")
    sub_lines = wrap(subtitle, "cardsub", box.w - 2 * T.PAD_X,
                     where=f"card subtitle {title!r}") if subtitle else []
    meta = meta or []
    meta_style = "code" if code_meta else "meta"
    meta_lines: list[str] = []
    for m in meta:
        meta_lines += wrap(m, meta_style, box.w - 2 * T.PAD_X,
                           where=f"card meta {title!r}")

    if autoheight:
        h = T.PAD_Y
        h += len(title_lines) * line_height("card")
        if sub_lines:
            h += 3 + len(sub_lines) * line_height("cardsub")
        if meta_lines:
            h += 11 + len(meta_lines) * line_height(meta_style)
        h += T.PAD_Y
        box = Box(box.x, box.y, box.w, max(h, 52))

    out = []
    if lv["glow"]:
        c.define(
            f"glow-{role}",
            f'<filter id="glow-{role}" x="-25%" y="-25%" width="150%" height="150%">'
            f'<feDropShadow dx="0" dy="0" stdDeviation="6" '
            f'flood-color="{accent}" flood-opacity="0.26"/></filter>',
        )
        out.append(
            f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
            f'rx="{T.R_CARD}" fill="{T.SURFACE}" filter="url(#glow-{role})"/>'
        )
    dash = f' stroke-dasharray="{lv["dash"]}"' if lv["dash"] else ""
    stroke = (T.border(role, 0.62)
              if level in ("primary", "extended", "shared") else T.HAIRLINE)

    # Glass surface. A vertical gradient (brighter at the top) plus a 1px inner
    # highlight along the top edge is what makes a flat rect read as a panel
    # catching light, at a cost of two extra elements and no extra ink budget.
    if level != "external":
        c.define(
            f"glass-{role}",
            f'<linearGradient id="glass-{role}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="{T.tint(role, 0.20)}"/>'
            f'<stop offset="55%" stop-color="{T.tint(role, 0.105)}"/>'
            f'<stop offset="100%" stop-color="{T.tint(role, 0.055)}"/>'
            f"</linearGradient>",
        )
        fill = f"url(#glass-{role})"
    else:
        fill = T.rgba(T.SURFACE, 0.82)

    c.define(
        "cardshadow",
        '<filter id="cardshadow" x="-20%" y="-20%" width="140%" height="150%">'
        '<feDropShadow dx="0" dy="5" stdDeviation="9" flood-color="#000000" '
        'flood-opacity="0.40"/></filter>',
    )
    out.append(
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_CARD}" fill="{T.rgba(T.CANVAS, 0.72)}" '
        f'filter="url(#cardshadow)"/>'
    )
    out.append(
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_CARD}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{lv["stroke"]}"{dash}/>'
    )
    if level != "external":
        out.append(
            f'<path d="M{box.x + T.R_CARD} {box.y + 0.9}'
            f'H{box.right - T.R_CARD}" stroke="{T.rgba("#FFFFFF", 0.11)}" '
            f'stroke-width="1" fill="none"/>'
        )

    if lv["wedge"]:
        wx, wy, k = box.right, box.y, T.WEDGE
        pts = f"{wx - k},{wy} {wx},{wy} {wx},{wy + k}"
        if lv["wedge"] == "filled":
            out.append(f'<polygon points="{pts}" fill="{accent}" opacity="0.9"/>')
        elif lv["wedge"] == "dot":
            out.append(
                f'<circle cx="{wx - k / 2}" cy="{wy + k / 2}" r="2.6" '
                f'fill="{accent}" opacity="0.8"/>'
            )
        else:
            out.append(
                f'<polyline points="{wx - k},{wy + 0.8} {wx - 0.8},{wy + 0.8} '
                f'{wx - 0.8},{wy + k}" fill="none" stroke="{accent}" '
                f'stroke-width="1.6" opacity="0.85"/>'
            )

    tx = box.x + T.PAD_X
    ty = box.y + T.PAD_Y + T.TYPE["card"]["size"] * 0.82
    if icon:
        out.append(glyph(icon, box.x + T.PAD_X, box.y + T.PAD_Y - 1, accent))
        tx += 22
    for i, ln in enumerate(title_lines):
        out.append(text_el(ln, tx, ty + i * line_height("card"), "card", T.INK))
    y = ty + len(title_lines) * line_height("card")

    for i, ln in enumerate(sub_lines):
        out.append(text_el(ln, box.x + T.PAD_X, y + 3 + i * line_height("cardsub"),
                           "cardsub", T.INK_MUTED))
    if sub_lines:
        y += 3 + len(sub_lines) * line_height("cardsub")

    if meta_lines:
        out.append(
            f'<line x1="{box.x + T.PAD_X}" y1="{y + 5}" '
            f'x2="{box.right - T.PAD_X}" y2="{y + 5}" stroke="{T.HAIRLINE}" '
            f'stroke-width="1"/>'
        )
        for i, ln in enumerate(meta_lines):
            out.append(text_el(ln, box.x + T.PAD_X,
                               y + 19 + i * line_height(meta_style),
                               meta_style, T.INK_FAINT))

    c.group("".join(out), label=label or f"card:{title}",
            data={"role": role, "level": level})
    return box


def store(c: Canvas, box: Box, title: str, *, kind: str = "relational",
          subtitle: str = "", meta: list[str] | None = None,
          level: str = "integrated", label: str | None = None) -> Box:
    """A persistent store. The double border is reserved for this, and only this."""
    accent = T.ROLE["store"]
    lv = T.LEVEL[level]
    inner_w = box.w - 2 * T.PAD_X - 22
    title_lines = wrap(title, "card", inner_w, where=f"store {title!r}")
    sub_lines = wrap(subtitle, "cardsub", box.w - 2 * T.PAD_X,
                     where=f"store sub {title!r}") if subtitle else []
    meta = meta or []
    meta_lines: list[str] = []
    for m in meta:
        meta_lines += wrap(m, "code", box.w - 2 * T.PAD_X, where=f"store meta {title!r}")

    h = T.PAD_Y + len(title_lines) * line_height("card")
    if sub_lines:
        h += 3 + len(sub_lines) * line_height("cardsub")
    if meta_lines:
        h += 11 + len(meta_lines) * line_height("code")
    h += T.PAD_Y
    box = Box(box.x, box.y, box.w, max(h, 56))

    c.define(
        "glass-store",
        '<linearGradient id="glass-store" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{T.tint("store", 0.19)}"/>'
        f'<stop offset="55%" stop-color="{T.tint("store", 0.095)}"/>'
        f'<stop offset="100%" stop-color="{T.tint("store", 0.05)}"/>'
        "</linearGradient>",
    )
    c.define(
        "cardshadow",
        '<filter id="cardshadow" x="-20%" y="-20%" width="140%" height="150%">'
        '<feDropShadow dx="0" dy="5" stdDeviation="9" flood-color="#000000" '
        'flood-opacity="0.40"/></filter>',
    )
    out = [
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_STORE}" fill="{T.rgba(T.CANVAS, 0.72)}" '
        f'filter="url(#cardshadow)"/>',
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_STORE}" fill="url(#glass-store)" '
        f'stroke="{T.border("store", 0.66)}" '
        f'stroke-width="{max(lv["stroke"], 1.4)}"/>',
        # the double border is the reserved "this is persistent" convention
        f'<rect x="{box.x + 3}" y="{box.y + 3}" width="{box.w - 6}" '
        f'height="{box.h - 6}" rx="{T.R_STORE - 3}" fill="none" '
        f'stroke="{T.border("store", 0.32)}" stroke-width="1"/>',
        f'<path d="M{box.x + T.R_STORE} {box.y + 0.9}'
        f'H{box.right - T.R_STORE}" stroke="{T.rgba("#FFFFFF", 0.10)}" '
        f'stroke-width="1" fill="none"/>',
    ]
    if lv["wedge"]:
        wx, wy, k = box.right, box.y, T.WEDGE
        if lv["wedge"] == "filled":
            out.append(
                f'<polygon points="{wx - k},{wy} {wx},{wy} {wx},{wy + k}" '
                f'fill="{accent}" opacity="0.9"/>'
            )
        elif lv["wedge"] == "dot":
            out.append(
                f'<circle cx="{wx - k / 2}" cy="{wy + k / 2}" r="2.6" '
                f'fill="{accent}" opacity="0.8"/>'
            )
        else:
            out.append(
                f'<polyline points="{wx - k},{wy + 0.8} {wx - 0.8},{wy + 0.8} '
                f'{wx - 0.8},{wy + k}" fill="none" stroke="{accent}" '
                f'stroke-width="1.6" opacity="0.85"/>'
            )

    out.append(glyph(kind, box.x + T.PAD_X, box.y + T.PAD_Y - 1, accent))
    tx = box.x + T.PAD_X + 22
    ty = box.y + T.PAD_Y + T.TYPE["card"]["size"] * 0.82
    for i, ln in enumerate(title_lines):
        out.append(text_el(ln, tx, ty + i * line_height("card"), "card", T.INK))
    y = ty + len(title_lines) * line_height("card")
    for i, ln in enumerate(sub_lines):
        out.append(text_el(ln, box.x + T.PAD_X, y + 3 + i * line_height("cardsub"),
                           "cardsub", T.INK_MUTED))
    if sub_lines:
        y += 3 + len(sub_lines) * line_height("cardsub")
    if meta_lines:
        out.append(
            f'<line x1="{box.x + T.PAD_X}" y1="{y + 5}" x2="{box.right - T.PAD_X}" '
            f'y2="{y + 5}" stroke="{T.HAIRLINE}" stroke-width="1"/>'
        )
        for i, ln in enumerate(meta_lines):
            out.append(text_el(ln, box.x + T.PAD_X, y + 19 + i * line_height("code"),
                               "code", T.INK_FAINT))
    c.group("".join(out), label=label or f"store:{title}",
            data={"role": "store", "level": level})
    return box


def pill(c: Canvas, x: float, y: float, topic: str, *, role: str = "event",
         h: float = 26.0, label: str | None = None) -> Box:
    """A Kafka topic. Never used for anything that is not a topic."""
    w = measure(topic, "code") + 26
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" '
        f'fill="{T.tint(role, 0.14)}" stroke="{T.border(role, 0.60)}" '
        f'stroke-width="1.2"/>',
        text_el(topic, x + 13, y + h / 2 + 4.2, "code", T.ROLE[role]),
    ]
    c.group("".join(out), label=label or f"topic:{topic}")
    return Box(x, y, w, h)


def lane(c: Canvas, box: Box, title: str, *, caption: str = "",
         accent: str = "neutral", label: str | None = None) -> Box:
    """A responsibility container. Drawn as an underlay so it can never cover
    the content it holds, and the caption is dropped rather than allowed to
    collide with the title."""
    c.define(
        f"lanefill-{accent}",
        f'<linearGradient id="lanefill-{accent}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{T.rgba(T.ROLE[accent], 0.055)}"/>'
        f'<stop offset="100%" stop-color="{T.rgba(T.CANVAS_ALT, 0.62)}"/>'
        "</linearGradient>",
    )
    out = [
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_LANE}" fill="url(#lanefill-{accent})" '
        f'stroke="{T.rgba(T.ROLE[accent], 0.20)}" stroke-width="1"/>',
        f'<rect x="{box.x}" y="{box.y}" width="3.5" height="{box.h}" '
        f'rx="1.75" fill="{T.rail(accent, 0.75)}"/>',
        f'<rect x="{box.x}" y="{box.y}" width="3.5" height="54" '
        f'rx="1.75" fill="{T.ROLE[accent]}" opacity="0.55"/>',
        text_el(title, box.x + 16, box.y + 22, "lane", T.rgba(T.ROLE[accent], 0.92)),
    ]
    if caption:
        need = (measure(title.upper(), "lane") + measure(caption, "meta") + 60)
        if need <= box.w:
            out.append(text_el(caption, box.right - 16, box.y + 22, "meta",
                               T.INK_FAINT, anchor="end"))
        else:
            # Would collide with the lane title. Put it under the title instead.
            out.append(text_el(caption, box.x + 16, box.y + 38, "meta", T.INK_FAINT))
    c.group("".join(out), label=label or f"lane:{title}", under=True)
    return box


def lane_around(c: Canvas, boxes: list[Box], title: str, *, caption: str = "",
                accent: str = "neutral", pad: float = 20.0, top: float = 40.0,
                label: str | None = None) -> Box:
    """Draw a lane sized to enclose `boxes`. Never too short for its content."""
    x0 = min(b.x for b in boxes) - pad
    x1 = max(b.right for b in boxes) + pad
    y0 = min(b.y for b in boxes) - top
    y1 = max(b.bottom for b in boxes) + pad
    return lane(c, Box(x0, y0, x1 - x0, y1 - y0), title, caption=caption,
                accent=accent, label=label)


def note(c: Canvas, x: float, y: float, w: float, lines: list[str], *,
         accent: str = "warn", title: str = "", label: str | None = None) -> Box:
    body: list[str] = []
    for ln in lines:
        body += wrap(ln, "note", w - 18, where=f"note {title or lines[0][:24]!r}")
    h = (len(body) * line_height("note")) + (20 if title else 0) + 8
    out = [
        f'<rect x="{x}" y="{y}" width="2.5" height="{h}" rx="1.2" '
        f'fill="{T.rail(accent, 0.85)}"/>'
    ]
    yy = y + 12
    if title:
        out.append(text_el(title, x + 14, yy, "lane", T.rgba(T.ROLE[accent], 0.95)))
        yy += 20
    for i, ln in enumerate(body):
        out.append(text_el(ln, x + 14, yy + i * line_height("note"), "note", T.INK_MUTED))
    c.group("".join(out), label=label or "note")
    return Box(x, y, w, h)


def step(c: Canvas, x: float, y: float, n: int | str, *, accent: str = "ui",
         r: float = 11.0) -> None:
    c.group(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{T.tint(accent, 0.18)}" '
        f'stroke="{T.border(accent, 0.7)}" stroke-width="1.2"/>'
        + text_el(str(n), x, y + 4.3, "step", T.ROLE[accent], anchor="middle"),
        label=f"step:{n}",
    )


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
def _arrowhead(c: Canvas, role: str, kind: str) -> str:
    key = f"ah-{role}-{kind}"
    colour = T.rail(role, 0.95)
    if kind == "open":
        body = (
            f'<path d="M1 1 L{T.ARROW_L} {T.ARROW_W / 2} L1 {T.ARROW_W}" fill="none" '
            f'stroke="{colour}" stroke-width="1.4" stroke-linecap="round"/>'
        )
    elif kind == "bar":
        body = (
            f'<rect x="1" y="0.6" width="2.6" height="{T.ARROW_W - 1.2}" '
            f'fill="{colour}"/>'
        )
    else:
        body = f'<path d="M0 0 L{T.ARROW_L} {T.ARROW_W / 2} L0 {T.ARROW_W} Z" fill="{colour}"/>'
    c.define(
        key,
        f'<marker id="{key}" markerWidth="{T.ARROW_L + 2}" '
        f'markerHeight="{T.ARROW_W + 2}" refX="{T.ARROW_L}" refY="{T.ARROW_W / 2}" '
        f'orient="auto" markerUnits="userSpaceOnUse">{body}</marker>',
    )
    return key


_EDGE_KINDS = {
    "sync":   {"dash": None,          "w": T.STROKE_EDGE, "head": "solid"},
    "async":  {"dash": T.DASH_ASYNC,  "w": T.STROKE_EDGE, "head": "solid"},
    "verify": {"dash": T.DASH_VERIFY, "w": 1.2,           "head": "open"},
    "own":    {"dash": None,          "w": T.STROKE_OWN,  "head": "solid"},
    "blocked": {"dash": None,         "w": T.STROKE_EDGE, "head": "bar"},
}


def _ortho(p: tuple[float, float], q: tuple[float, float],
           side_a: str, side_b: str, bend: float | None) -> list[tuple[float, float]]:
    ax, ay = p
    bx, by = q
    if side_a in "ew" and side_b in "ew":
        mx = bend if bend is not None else (ax + bx) / 2
        return [(ax, ay), (mx, ay), (mx, by), (bx, by)]
    if side_a in "ns" and side_b in "ns":
        my = bend if bend is not None else (ay + by) / 2
        return [(ax, ay), (ax, my), (bx, my), (bx, by)]
    if side_a in "ew":
        return [(ax, ay), (bx, ay), (bx, by)]
    return [(ax, ay), (ax, by), (bx, by)]


def _round_path(pts: list[tuple[float, float]], r: float = 8.0) -> str:
    if len(pts) < 3:
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        d1 = math.hypot(x1 - x0, y1 - y0)
        d2 = math.hypot(x2 - x1, y2 - y1)
        rr = min(r, d1 / 2, d2 / 2)
        if rr < 1.2:
            d.append(f"L{x1:.1f} {y1:.1f}")
            continue
        ux, uy = (x1 - x0) / d1, (y1 - y0) / d1
        vx, vy = (x2 - x1) / d2, (y2 - y1) / d2
        d.append(f"L{x1 - ux * rr:.1f} {y1 - uy * rr:.1f}")
        d.append(f"Q{x1:.1f} {y1:.1f} {x1 + vx * rr:.1f} {y1 + vy * rr:.1f}")
    d.append(f"L{pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return " ".join(d)


def edge(c: Canvas, a: Box, b: Box, *, kind: str = "sync", role: str = "neutral",
         side_a: str = "e", side_b: str = "w", ta: float = 0.5, tb: float = 0.5,
         label: str = "", bend: float | None = None, gap: float = 4.0,
         label_at: float = 0.5, label_dy: float = 0.0, mono: bool = False) -> None:
    spec = _EDGE_KINDS[kind]
    head = _arrowhead(c, role, spec["head"])
    p = list(a.port(side_a, ta))
    q = list(b.port(side_b, tb))
    for pt, side, sign in ((p, side_a, 1), (q, side_b, -1)):
        off = gap * sign
        if side == "e": pt[0] += off
        elif side == "w": pt[0] -= off
        elif side == "s": pt[1] += off
        elif side == "n": pt[1] -= off
    pts = _ortho(tuple(p), tuple(q), side_a, side_b, bend)
    dash = f' stroke-dasharray="{spec["dash"]}"' if spec["dash"] else ""
    out = [
        f'<path d="{_round_path(pts)}" fill="none" stroke="{T.rail(role, 0.85)}" '
        f'stroke-width="{spec["w"]}"{dash} marker-end="url(#{head})" '
        f'stroke-linecap="round"/>'
    ]
    if label:
        total = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                    for i in range(len(pts) - 1))
        want, acc, lx, ly = total * label_at, 0.0, pts[-1][0], pts[-1][1]
        for i in range(len(pts) - 1):
            seg = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            if acc + seg >= want:
                f = (want - acc) / seg if seg else 0
                lx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
                ly = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
                break
            acc += seg
        style = "code" if mono else "edge"
        tw = measure(label, style)
        ly += label_dy
        out.append(
            f'<rect x="{lx - tw / 2 - 7:.1f}" y="{ly - 11:.1f}" width="{tw + 14:.1f}" '
            f'height="19" rx="5" fill="{T.CANVAS}" stroke="{T.HAIRLINE}" '
            f'stroke-width="0.8"/>'
        )
        out.append(text_el(label, lx, ly + 3.2, style,
                           T.rgba(T.ROLE[role], 0.95) if mono else T.INK_MUTED,
                           anchor="middle"))
    c.group("".join(out), label=f"edge:{kind}:{label or 'unlabelled'}")


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
def legend(c: Canvas, x: float, y: float, *, roles: list[str] | None = None,
           flows: list[str] | None = None, levels: list[str] | None = None,
           columns: bool = True) -> Box:
    out, yy = [], y
    rowh = 19.0

    def heading(s: str, yv: float) -> None:
        out.append(text_el(s, x, yv, "lane", T.INK_FAINT))

    if roles:
        heading("ROLE", yy)
        cx = x + 54
        for r in roles:
            out.append(f'<circle cx="{cx + 5}" cy="{yy - 4}" r="4.6" '
                       f'fill="{T.ROLE[r]}" opacity="0.92"/>')
            out.append(text_el(T.ROLE_LABEL[r], cx + 15, yy, "legend", T.INK_MUTED))
            cx += 15 + measure(T.ROLE_LABEL[r], "legend") + 26
        yy += rowh + 3

    if flows:
        heading("FLOW", yy)
        cx = x + 54
        names = {"sync": "synchronous request", "async": "asynchronous event",
                 "verify": "verification / read-only", "own": "exclusive write",
                 "blocked": "refused / blocked"}
        for f in flows:
            spec = _EDGE_KINDS[f]
            dash = f' stroke-dasharray="{spec["dash"]}"' if spec["dash"] else ""
            out.append(
                f'<line x1="{cx}" y1="{yy - 4}" x2="{cx + 26}" y2="{yy - 4}" '
                f'stroke="{T.INK_FAINT}" stroke-width="{spec["w"]}"{dash}/>'
            )
            out.append(text_el(names[f], cx + 34, yy, "legend", T.INK_MUTED))
            cx += 34 + measure(names[f], "legend") + 26
        yy += rowh + 3

    if levels:
        heading("AUTHORSHIP", yy)
        cx = x + 104
        for lvl in levels:
            lv = T.LEVEL[lvl]
            dash = f' stroke-dasharray="{lv["dash"]}"' if lv["dash"] else ""
            out.append(
                f'<rect x="{cx}" y="{yy - 11}" width="15" height="13" rx="3" '
                f'fill="{T.rgba(T.INK, 0.05)}" stroke="{T.INK_FAINT}" '
                f'stroke-width="{lv["stroke"]}"{dash}/>'
            )
            if lv["wedge"] == "filled":
                out.append(f'<polygon points="{cx + 8},{yy - 11} {cx + 15},{yy - 11} '
                           f'{cx + 15},{yy - 4} " fill="{T.INK_MUTED}"/>')
            elif lv["wedge"] == "dot":
                out.append(f'<circle cx="{cx + 11.5}" cy="{yy - 7.5}" r="2.2" '
                           f'fill="{T.INK_MUTED}"/>')
            elif lv["wedge"] == "hollow":
                out.append(f'<polyline points="{cx + 8},{yy - 10.2} {cx + 14.2},{yy - 10.2} '
                           f'{cx + 14.2},{yy - 4}" fill="none" stroke="{T.INK_MUTED}" '
                           f'stroke-width="1.4"/>')
            out.append(text_el(lv["label"], cx + 23, yy, "legend", T.INK_MUTED))
            cx += 23 + measure(lv["label"], "legend") + 26
        yy += rowh

    c.group("".join(out), label="legend")
    return Box(x, y, 0, yy - y)


def matrix(c: Canvas, x: float, y: float, headers: list[str], rows: list[list[str]],
           *, widths: list[float], accents: list[str] | None = None,
           mono_cols: set[int] | None = None, rowh: float = 30.0,
           label: str | None = None) -> Box:
    """A dense table. Used where a diagram's real content is a list of facts
    (the gate inventory, the operation comparison) and boxes-and-arrows would
    only decorate it."""
    mono_cols = mono_cols or set()
    total = sum(widths)
    out = [
        f'<rect x="{x}" y="{y}" width="{total}" height="{rowh - 4}" rx="6" '
        f'fill="{T.rgba(T.INK, 0.04)}"/>'
    ]
    cx = x
    for i, hdr in enumerate(headers):
        out.append(text_el(hdr, cx + 12, y + rowh - 15, "lane", T.INK_FAINT))
        cx += widths[i]
    yy = y + rowh
    for r, row in enumerate(rows):
        if r % 2 == 1:
            out.append(
                f'<rect x="{x}" y="{yy - 1}" width="{total}" height="{rowh}" '
                f'rx="4" fill="{T.rgba(T.INK, 0.022)}"/>'
            )
        cx = x
        acc = (accents[r] if accents else None)
        for i, cell in enumerate(row):
            style = "code" if i in mono_cols else "meta"
            colour = T.INK_MUTED
            if i == 0 and acc:
                colour = T.rgba(T.ROLE[acc], 0.95)
            elif cell in ("required", "pass", "yes", "✓"):
                colour = T.ROLE["trust"]
            elif cell in ("not applicable", "no", "—", "blocked"):
                colour = T.INK_FAINT
            avail = widths[i] - 18
            lines = wrap(cell, style, avail, where=f"matrix r{r}c{i} {cell!r}")
            for j, ln in enumerate(lines):
                out.append(text_el(ln, cx + 12, yy + 18 + j * 13, style, colour))
            cx += widths[i]
        yy += rowh
    out.append(
        f'<line x1="{x}" y1="{yy + 2}" x2="{x + total}" y2="{yy + 2}" '
        f'stroke="{T.HAIRLINE}" stroke-width="1"/>'
    )
    c.group("".join(out), label=label or "matrix")
    return Box(x, y, total, yy + 2 - y)


def state(c: Canvas, box: Box, name: str, *, role: str = "ui", detail: str = "",
          terminal: bool = False, label: str | None = None) -> Box:
    """A state-machine node. Terminal states get a double outer ring."""
    accent = T.ROLE[role]
    title_lines = wrap(name, "card", box.w - 24, where=f"state {name!r}")
    det = wrap(detail, "meta", box.w - 24, where=f"state detail {name!r}") if detail else []
    h = 16 + len(title_lines) * line_height("card") + \
        (4 + len(det) * line_height("meta") if det else 0) + 14
    box = Box(box.x, box.y, box.w, max(h, 46))
    out = []
    if terminal:
        out.append(
            f'<rect x="{box.x - 4}" y="{box.y - 4}" width="{box.w + 8}" '
            f'height="{box.h + 8}" rx="{T.R_CARD + 4}" fill="none" '
            f'stroke="{T.border(role, 0.30)}" stroke-width="1"/>'
        )
    out.append(
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="{T.R_CARD}" fill="{T.tint(role, 0.13)}" '
        f'stroke="{T.border(role, 0.65)}" stroke-width="1.6"/>'
    )
    ty = box.y + 16 + T.TYPE["card"]["size"] * 0.72
    for i, ln in enumerate(title_lines):
        out.append(text_el(ln, box.cx, ty + i * line_height("card"), "card",
                           T.INK, anchor="middle"))
    yy = ty + len(title_lines) * line_height("card")
    for i, ln in enumerate(det):
        out.append(text_el(ln, box.cx, yy + 4 + i * line_height("meta"), "meta",
                           T.INK_MUTED, anchor="middle"))
    c.group("".join(out), label=label or f"state:{name}",
            data={"role": role})
    return box


def write(c: Canvas, path: str) -> None:
    import pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(c.render(), encoding="utf-8")
    print(f"  wrote {p.name:46s} {c.width}x{c.height}  {len(c.render()):>7,} bytes")
