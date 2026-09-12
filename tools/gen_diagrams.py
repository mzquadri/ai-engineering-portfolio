"""Regenerate every architecture SVG.

    python tools/gen_diagrams.py

Run from the portfolio root -- output paths are relative to it.

A diagram whose text would not fit its box raises TextTooWide rather than
rendering a clipped label, so a clean run is evidence that nothing is
truncated. That is the same principle as the system being documented: refuse
rather than produce something that looks fine and is wrong.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import diagrams_a  # noqa: E402
import diagrams_b  # noqa: E402
import diagrams_c  # noqa: E402
import diagrams_d  # noqa: E402
from svg_kit import TextTooWide  # noqa: E402


def main() -> int:
    out = pathlib.Path("assets/architecture")
    if not out.parent.exists():
        print("Run this from the portfolio root (assets/ must be reachable).",
              file=sys.stderr)
        return 2

    builders = (diagrams_a.ALL + diagrams_b.ALL + diagrams_c.ALL
                + diagrams_d.ALL)
    print(f"building {len(builders)} diagrams")
    failed = 0
    for fn in builders:
        try:
            fn()
        except TextTooWide as e:
            failed += 1
            print(f"  !! {fn.__name__}: {e}", file=sys.stderr)
        except Exception as e:                      # noqa: BLE001
            failed += 1
            print(f"  !! {fn.__name__}: {type(e).__name__}: {e}",
                  file=sys.stderr)

    if failed:
        print(f"\n{failed} diagram(s) failed. Nothing partial was shipped for "
              f"them.", file=sys.stderr)
        return 1

    svgs = sorted(out.glob("*.svg"))
    total = sum(p.stat().st_size for p in svgs)
    print(f"\n{len(svgs)} SVGs, {total / 1024:,.0f} KB total")

    # Keep the public docs/architecture copies in step. These were hand-copied
    # once and had silently drifted within a day -- which is precisely the
    # defect class this portfolio documents elsewhere. Doing it here makes
    # drift impossible rather than merely discouraged.
    public = {
        "01-ai-systems-landscape": "system-overview",
        "02-legal-knowledge-database": "legal-knowledge-flow",
        "07-rag-query-flow": "rag-flow",
        "06-verification-and-reconciliation": "verification-flow",
        "17-verification-essence": "verification-short",
        "13-interview-system-overview": "interview-overview",
    }
    dest = pathlib.Path("docs/architecture")
    if dest.exists():
        for src_stem, dst_stem in public.items():
            src = out / f"{src_stem}.svg"
            if src.exists():
                (dest / f"{dst_stem}.svg").write_bytes(src.read_bytes())
        print(f"synced {len(public)} public copies into {dest}/")

    print("next: python tools/gen_site.py   (inlines these into index.html)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
