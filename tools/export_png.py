"""Rasterise SVG (or HTML) to PNG with headless Chromium.

Usage
    python tools/export_png.py <outdir> <scale> <file> [file ...]
    python tools/export_png.py assets/png 2 assets/architecture/*.svg

The window size is read from the SVG's own width/height, so a diagram authored
at 1920x1080 exported at scale 2 lands at exactly 3840x2160. No image library
is required, and the renderer is the same engine that will display the
microsite, which is why what you inspect is what ships.
"""

from __future__ import annotations

import os
import pathlib
import re
import struct
import subprocess
import sys

CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    r"C:\Users\{}\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe".format(
        os.environ.get("USERNAME", "")),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and pathlib.Path(c).exists():
            return c
    # last resort: any playwright chromium on this machine
    root = pathlib.Path(os.path.expanduser("~")) / "AppData/Local/ms-playwright"
    if root.exists():
        for p in sorted(root.glob("chromium-*/chrome-win64/chrome.exe"), reverse=True):
            return str(p)
    raise SystemExit(
        "No Chromium found. Set CHROME=/path/to/chrome.exe and re-run.\n"
        "Any Chrome, Chromium or Edge binary works."
    )


def svg_size(path: pathlib.Path) -> tuple[int, int]:
    head = path.read_text(encoding="utf-8")[:4000]
    w = re.search(r'\bwidth="(\d+)"', head)
    h = re.search(r'\bheight="(\d+)"', head)
    return (int(w.group(1)) if w else 1920, int(h.group(1)) if h else 1080)


def png_size(path: pathlib.Path) -> tuple[int, int]:
    d = path.read_bytes()[16:24]
    return struct.unpack(">II", d)


def shoot(chrome: str, src: pathlib.Path, dst: pathlib.Path, scale: int,
          size: tuple[int, int] | None = None) -> None:
    w, h = size or (svg_size(src) if src.suffix == ".svg" else (1920, 1080))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst = dst.resolve()          # Chrome ignores a relative --screenshot path
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
         "--virtual-time-budget=4000",
         f"--screenshot={dst}", src.resolve().as_uri()],
        check=True, capture_output=True,
    )
    got = png_size(dst)
    want = (w * scale, h * scale)
    flag = "" if got == want else f"  !! expected {want[0]}x{want[1]}"
    print(f"  {dst.name:<52s} {got[0]}x{got[1]}{flag}")


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(2)
    outdir = pathlib.Path(sys.argv[1])
    scale = int(sys.argv[2])
    files = [pathlib.Path(f) for f in sys.argv[3:]]
    chrome = find_chrome()
    print(f"rasterising {len(files)} file(s) at {scale}x")
    for f in files:
        if not f.exists():
            print(f"  !! missing {f}")
            continue
        suffix = "" if scale == 1 else f"@{scale}x"
        shoot(chrome, f, outdir / f"{f.stem}{suffix}.png", scale)


if __name__ == "__main__":
    main()
