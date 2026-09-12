"""Single source of truth for the portfolio's visual language.

Every colour, size and stroke weight used by the SVG generator, the Draw.io
exporter, the deck builder and the microsite comes from here. See
../design-system.md for the reasoning behind each choice.

Colour encodes engineering role. Border weight and corner marker encode
authorship. Those two axes are deliberately independent -- see ROLE and LEVEL.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Canvas and surfaces
# --------------------------------------------------------------------------
CANVAS = "#070A0F"
CANVAS_ALT = "#0A0F16"
SURFACE = "#0E141C"
SURFACE_RAISED = "#141C26"
GRID = "#16202C"
HAIRLINE = "#1C2736"

# --------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------
INK = "#E8EEF6"
INK_MUTED = "#9FB0C3"
INK_FAINT = "#667B91"
INK_INVERSE = "#070A0F"

# --------------------------------------------------------------------------
# Semantic accents -- role, never decoration
# --------------------------------------------------------------------------
ROLE = {
    "source": "#A78BFA",   # external / authoritative publisher
    "event": "#22D3EE",    # Kafka topic, event movement
    "ai": "#818CF8",       # embedding, LLM, OCR, classification
    "store": "#F0B429",    # persistence
    "trust": "#34D399",    # verification, gates, proven state
    "ui": "#60A5FA",       # operator surface, API
    "warn": "#F87171",     # failure, blocked, drift
    "neutral": "#7D8B9C",  # existing platform component
}

ROLE_LABEL = {
    "source": "External source",
    "event": "Event / transport",
    "ai": "AI / ML",
    "store": "Persistence",
    "trust": "Verification / trust",
    "ui": "Operator / API",
    "warn": "Failure path",
    "neutral": "Existing component",
}

# --------------------------------------------------------------------------
# Authorship levels -- geometry, not hue
#   stroke: border width in px
#   glow:   whether an outer glow is drawn
#   wedge:  "filled" | "hollow" | None
#   dash:   stroke dash pattern or None
# --------------------------------------------------------------------------
#   shared: for a component I contributed to without owning -- a shared library,
#           an environment, a handful of commits in someone else's service. It
#           sits between "significant contribution" and "existing platform"
#           because collapsing it into either one misstates the work.
LEVEL = {
    "primary": {"stroke": 2.0, "glow": True, "wedge": "filled", "dash": None,
                "label": "Primary implementation"},
    "extended": {"stroke": 1.6, "glow": False, "wedge": "hollow", "dash": None,
                 "label": "Significant contribution"},
    "shared": {"stroke": 1.3, "glow": False, "wedge": "dot", "dash": None,
               "label": "Integration / shared"},
    "integrated": {"stroke": 1.0, "glow": False, "wedge": None, "dash": None,
                   "label": "Existing platform"},
    "external": {"stroke": 1.0, "glow": False, "wedge": None, "dash": "3 3",
                 "label": "External / upstream"},
}
LEVEL_ORDER = ("primary", "extended", "shared", "integrated", "external")

# --------------------------------------------------------------------------
# Typography
# --------------------------------------------------------------------------
SANS = 'Inter, "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'
MONO = '"JetBrains Mono", "Cascadia Code", Consolas, "SF Mono", Menlo, monospace'

TYPE = {
    "title":     {"size": 34.0, "weight": 600, "track": -0.4, "lh": 1.18, "font": SANS},
    "subtitle":  {"size": 17.0, "weight": 400, "track": 0.0,  "lh": 1.38, "font": SANS},
    "lane":      {"size": 12.0, "weight": 600, "track": 1.4,  "lh": 1.2,  "font": SANS},
    "card":      {"size": 16.0, "weight": 600, "track": -0.1, "lh": 1.22, "font": SANS},
    "cardsub":   {"size": 13.0, "weight": 400, "track": 0.0,  "lh": 1.35, "font": SANS},
    "meta":      {"size": 11.5, "weight": 400, "track": 0.0,  "lh": 1.34, "font": SANS},
    "code":      {"size": 12.0, "weight": 400, "track": 0.0,  "lh": 1.35, "font": MONO},
    "edge":      {"size": 11.5, "weight": 500, "track": 0.2,  "lh": 1.25, "font": SANS},
    "legend":    {"size": 12.0, "weight": 500, "track": 0.3,  "lh": 1.25, "font": SANS},
    "note":      {"size": 12.5, "weight": 400, "track": 0.0,  "lh": 1.42, "font": SANS},
    "step":      {"size": 12.0, "weight": 700, "track": 0.0,  "lh": 1.2,  "font": SANS},
}

# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------
SAFE = 56              # canvas margin nothing may enter
R_CARD = 10
R_LANE = 14
R_STORE = 10
PAD_X = 16
PAD_Y = 14
GAP_X = 28
GAP_Y = 24
WEDGE = 10

STROKE_HAIR = 1.0
STROKE_EDGE = 1.4
STROKE_EMPH = 1.8
STROKE_OWN = 2.0

ARROW_L = 9.0
ARROW_W = 7.0

DASH_ASYNC = "6 5"
DASH_VERIFY = "2 4"

# Canvas presets
W16x9 = (1920, 1080)
W16x10 = (1920, 1200)


def rgba(hex_colour: str, alpha: float) -> str:
    """#RRGGBB + alpha -> rgba() string, for fills that must sit over a known ground."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha:.3f})"


def tint(role: str, alpha: float = 0.10) -> str:
    return rgba(ROLE[role], alpha)


def border(role: str, alpha: float = 0.55) -> str:
    return rgba(ROLE[role], alpha)


def rail(role: str, alpha: float = 0.38) -> str:
    return rgba(ROLE[role], alpha)
