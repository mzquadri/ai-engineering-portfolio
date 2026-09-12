# Design System

One visual language across the microsite, the SVG pack, the Draw.io sources and
the deck. Every token below is defined once, in
[`tools/design_tokens.py`](tools/design_tokens.py), and consumed by the generator
and the site. Changing a colour means changing one line.

The aim is consulting-grade systems documentation: dense, quiet, and legible at
both 4K and phone width. The reference points are Stripe's architecture pages,
Linear's changelog diagrams and Vercel's docs — not slideware.

---

## 1. The one rule that shapes everything

**Colour encodes engineering role. Border and marker encode authorship.**

If colour carried both, a diagram could not show "a vector store I built" and "a
vector store I integrated" without inventing a second palette and doubling the
legend. So:

- **Hue** answers *what kind of thing is this?*
- **Border weight, glow and corner marker** answer *who built it?*

This separation is the reason the contribution diagram can be the same drawing as
the architecture diagram with one layer switched on.

---

## 2. Colour tokens

### Canvas and surfaces

| Token | Value | Use |
|---|---|---|
| `canvas` | `#070A0F` | page and diagram ground — near-black with a blue cast |
| `canvas_alt` | `#0A0F16` | alternating band, lane fill |
| `surface` | `#0E141C` | card fill |
| `surface_raised` | `#141C26` | hovered / emphasised card |
| `grid` | `#16202C` | 40px grid lines, drawn at low opacity |
| `hairline` | `#1C2736` | dividers, lane borders |

### Text

| Token | Value | Use |
|---|---|---|
| `ink` | `#E8EEF6` | primary text |
| `ink_muted` | `#9FB0C3` | secondary text, card subtitles |
| `ink_faint` | `#667B91` | meta text, captions, axis labels |
| `ink_inverse` | `#070A0F` | text on an accent fill |

Minimum contrast held: `ink` on `canvas` ≈ 15:1, `ink_muted` on `surface` ≈ 7.5:1,
`ink_faint` on `canvas` ≈ 4.8:1. Nothing lighter than `ink_faint` is used for text
at any size.

### Semantic accents

Restrained, desaturated, all tested against `canvas` and `surface`.

| Role | Token | Value | Applies to |
|---|---|---|---|
| External / authoritative source | `source` | `#A78BFA` | GII, CELLAR, publishers — things outside the system |
| Event / transport | `event` | `#22D3EE` | Kafka topics, event flow, message movement |
| AI / ML | `ai` | `#818CF8` | embedding, LLM, OCR, classification |
| Persistence | `store` | `#F0B429` | PostgreSQL, Qdrant, Neo4j, MinIO |
| Verification / trust | `trust` | `#34D399` | gates, provers, oracles, verified state |
| Operator / UI | `ui` | `#60A5FA` | dashboard, API surfaces, control plane |
| Failure / warning | `warn` | `#F87171` | error paths, blocked states, drift |
| Neutral / existing | `neutral` | `#7D8B9C` | existing platform components |

**Colour is never decorative.** A node's fill tint is `accent @ 10%` over
`surface`, its border is `accent @ 55%`, and its title sits in `ink`. A card with
no semantic role gets `neutral`, not a fifth hue.

### Derived values

```
tint(accent)    = accent at 10% alpha over surface
border(accent)  = accent at 55% alpha
glow(accent)    = accent at 22% alpha, 6px blur
rail(accent)    = accent at 38% alpha — connector strokes
```

---

## 3. Authorship encoding

Five levels. The legend appears on every diagram that uses more than one.

| Level key | Treatment | Reads as |
|---|---|---|
| `primary` | 2.0px border in the role accent, outer glow, filled corner wedge top-right | **Primary implementation** |
| `extended` | 1.6px border in the role accent, no glow, hollow corner wedge | **Significant contribution** |
| `shared` | 1.3px border in the role accent, corner dot | **Integration / shared** |
| `integrated` | 1.0px `hairline` border, role accent used only on the icon | **Existing platform** |
| `external` | 1.0px `neutral` border, 3·3 dash, no fill tint | **External / upstream** |

`shared` exists because collapsing it into either neighbour misstates the work:
five commits in a 243-commit UI is not a significant contribution, and it is not
nothing either. The rule when a class is arguable is to take the conservative
one — the public artefact must never over-claim.

The corner wedge is 10px and sits inside the card, so it survives downscaling to
a thumbnail — which a glow does not.

---

## 4. Typography

| Role | Family | Size (at 1920×1080) | Weight | Tracking |
|---|---|---|---|---|
| Diagram title | Inter / Segoe UI | 34px | 600 | −0.4px |
| Diagram subtitle | Inter | 17px | 400 | 0 |
| Section / lane label | Inter | 12px | 600 | +1.4px, uppercase |
| Card title | Inter | 16px | 600 | −0.1px |
| Card subtitle | Inter | 13px | 400 | 0 |
| Card meta | Inter | 11.5px | 400 | 0 |
| Identifier (topic, path, gate id) | JetBrains Mono / Consolas | 12px | 400 | 0 |
| Edge label | Inter | 11.5px | 500 | +0.2px |
| Legend | Inter | 12px | 500 | +0.3px |
| Caption / note | Inter | 12.5px | 400 | 0 |

Font stacks always carry a real fallback:
`Inter, "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif`
and `"JetBrains Mono", "Cascadia Code", Consolas, "SF Mono", monospace`.

**Every literal identifier is set in mono.** A topic name, a gate id, a file path
and a route are data, and setting them in the body face invites paraphrase. If it
is mono in a diagram, it is copied verbatim from the source.

Line height is 1.35 for body, 1.2 for titles. Text never exceeds 62 characters per
line in a card; the generator measures and wraps (§8).

---

## 5. Spacing and geometry

An 8px base scale. Only multiples of 4 are used.

| Token | Value |
|---|---|
| `space_1` … `space_6` | 4, 8, 12, 16, 24, 32 |
| card padding | 16px horizontal, 14px vertical |
| card corner radius | 10px |
| store corner radius | 10px, with a 2px inner stroke for the double border |
| pill corner radius | full (height ÷ 2) |
| lane corner radius | 14px |
| minimum gap between cards | 28px horizontal, 24px vertical |
| minimum gap between lanes | 32px |
| arrowhead | 9px long, 7px wide |
| stroke weights | 1.0 hairline · 1.4 connector · 1.8 emphasis · 2.0 owned border |

Canvas sizes: every diagram is authored at **1920×1080** (16:9) except the
contribution and landscape diagrams, which are authored at **1920×1200** where
density requires it. All are `viewBox`-driven, so they scale losslessly to 4K.

Safe margin: 56px on all sides. Nothing but the background grid enters it.

---

## 6. Component specifications

### Service card

```
┌──────────────────────────────◤  ← authorship wedge
│ ▣  SERVICE NAME                 ← 16/600 ink, icon in role accent
│    what it does, one line       ← 13/400 ink_muted
│    ─────────────────────        ← hairline, full width minus padding
│    :4698 · python · fastapi     ← 11.5 mono ink_faint
└─────────────────────────────────┘
```

Width 260–340px, height driven by content, never fixed. Fill `tint(accent)`,
border per authorship level.

### Store

A rounded rectangle with a **double border** — the outer stroke in
`border(store)` and an inner 1px stroke inset by 3px. The double border is the
single visual convention that means *persistent*, and it is never used for
anything else.

Each store carries a 16px glyph: stacked discs (relational), a radial point
cluster (vector), a 4-node graph (graph), a bucket outline (object storage).

### Topic pill

Fully rounded, fill `tint(event)`, border `border(event)`, label in **mono**.
Always the exact topic name. A pill is never used for anything that is not a
Kafka topic.

### Gate / trust marker

A 14px shield outline in `trust`, with a check for a passing gate and a dash for
`not_run`. A failing gate uses the same shield in `warn` with a cross. Three
states, one shape — so the reader learns it once.

### Lane

A rounded container with `canvas_alt` fill at 60% and a `hairline` border, with an
uppercase label in the top-left and an optional right-aligned caption. Lanes carry
the *engineering responsibility*, not the technology.

### Note

Left-edge rule 2px in the relevant accent, no fill, text in `ink_muted`. Notes
state limitations and are deliberately quiet — they are there to be read second.

---

## 7. Arrow conventions

| Meaning | Stroke | Head |
|---|---|---|
| Synchronous request / data flow | solid, 1.4px | filled triangle |
| Asynchronous event | dashed `6 5`, 1.4px | filled triangle |
| Verification / observation (read-only) | dotted `2 4`, 1.2px | open chevron |
| Ownership / write | solid, 2.0px | filled triangle |
| Blocked / refused path | solid, 1.4px `warn` | flat bar terminator |

Routing is orthogonal with 8px corner radii. Edges never cross a card. Where two
edges must share a channel they are offset by 10px, never overlapped. Edge labels
sit on a `canvas`-filled rounded rect so they are legible over a rail.

---

## 8. Text fitting — how clipping is prevented

The generator does not trust eyeballing. `tools/svg_kit.py` carries a per-character
advance-width table for the Inter/Segoe UI metrics at weight 400/500/600 and for
the mono stack, measures every string before it is placed, and:

1. wraps to the available width on word boundaries;
2. grows the card height to fit the wrapped result;
3. **raises** if a single unbreakable token (a long topic name, a file path) still
   exceeds the box.

A build that would clip text fails instead of shipping. That is the same principle
as the gates in the system being documented, applied to its documentation.

---

## 9. Legend

Every diagram with more than one role or authorship level carries a legend in the
bottom-left. Order is fixed so it is recognisable across the set:

```
ROLE      ● external  ● event  ● ai  ● store  ● trust  ● ui  ● failure
FLOW      ── sync   ┄┄ async   ⋯⋯ verify
AUTHORSHIP ▣ primary  ▢ extended  ▫ integrated  ◌ external
```

Only the entries actually used on that diagram are drawn.

---

## 10. Abstraction levels

Three, never mixed on one canvas.

| Level | Audience | Contains | Max nodes |
|---|---|---|---|
| **L1 — Executive** | non-specialist | 4–6 capability blocks, no technology names | 8 |
| **L2 — Interview** | engineering interviewer | responsibilities, stores, the trust loop | 16 |
| **L3 — Engineering** | implementer | exact services, topics, routes, gate ids, failure paths | 32 |

If a diagram needs more than its level's node budget, it is the wrong diagram and
gets split. This is the rule that keeps the set readable.

---

## 11. Microsite specifics

- Single static `index.html`, no build step, no framework, no CDN dependency.
  It opens from the filesystem and deploys to any static host unchanged.
- Dark by default, matching the diagram canvas. A light theme is offered and the
  tokens invert through CSS custom properties on `:root`.
- Diagrams are inlined as `<svg>` so they inherit the page's theme and remain
  selectable and zoomable; the standalone `.svg` files are the same markup.
- Interaction is restricted to: section navigation, diagram zoom/pan, node hover
  detail, the authorship overlay toggle, and Interview Mode. No animation that
  cannot be paused; no motion on `prefers-reduced-motion: reduce`.
- Breakpoints: 1440+ (two-column), 1024 (stacked with sticky nav), 640 (single
  column, nav collapses, diagrams become horizontally scrollable inside their own
  container — the page body never scrolls sideways).
- Focus is always visible: 2px `ui` outline at 2px offset.

---

## 12. What this system forbids

Worth stating, since most of the work was removing things.

- No gradients as decoration. One vignette on the canvas, nothing else.
- No drop shadows except the authorship glow.
- No more than 8 accents, ever.
- No icon larger than 20px in a diagram.
- No 3D, no isometric, no skeuomorphism, no cartoon clouds.
- No logo-driven layout. Technologies are annotations on responsibilities.
- No diagram where an arrow crosses a node.
- No red used for anything except failure.
- No green used for anything except verified state.
- No claim in a diagram that is not in the evidence matrix.
