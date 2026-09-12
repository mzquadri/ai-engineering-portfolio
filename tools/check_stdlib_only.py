"""Fail if anything under tools/ takes an undeclared third-party dependency.

    python tools/check_stdlib_only.py

Almost every generator here draws its own SVG, writes its own drawio XML and
renders its own site, so the tree runs on a bare Python install. That is a claim
worth keeping true: one convenient `import requests` in a diagram script turns a
repository that runs anywhere into one that needs a setup step nobody wrote down.

There are two exceptions, and they are listed rather than hidden:

  `pptx`, imported inside `gen_deck.build_pptx`, is genuinely needed to write the
  PowerPoint file and is declared in requirements.txt. It is imported inside the
  function so that every other tool still runs without it.

  `check_public_local` is an optional override that is deliberately never
  committed. It holds the literal internal hostnames the publication gate looks
  for, which are exactly the strings this repository exists to keep out, so the
  import is wrapped in try/except and its absence is the normal case.

Anything else fails. Imports are read from the parsed syntax tree rather than
matched with a regular expression, so a name in a comment cannot trigger it and
an import nested inside a function cannot hide from it. The earlier version of
this check used grep and missed both exceptions above for that reason.
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

#: Modules that live in this directory and are imported by their bare name.
LOCAL = {path.stem for path in TOOLS.glob("*.py")}

#: name -> why it is allowed. Adding a row here is a deliberate act, which is
#: the point: the cost of a new dependency should be a decision, not a reflex.
ALLOWED = {
    "pptx": "writes the PowerPoint deck; declared in requirements.txt",
    "check_public_local": "optional, never committed; holds the literal internal "
                          "patterns the publication gate must not publish",
}


def imported_roots(source: str) -> set[str]:
    """Every top-level module name a file imports, at any nesting depth."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # A relative import has no module root to check.
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def main() -> int:
    offenders: dict[str, set[str]] = {}
    declared_seen: set[str] = set()
    checked = 0

    for path in sorted(TOOLS.glob("*.py")):
        checked += 1
        names = imported_roots(path.read_text(encoding="utf-8"))
        for name in names:
            if name in LOCAL or name == "__future__":
                continue
            if name in sys.stdlib_module_names:
                continue
            if name in ALLOWED:
                declared_seen.add(name)
                continue
            offenders.setdefault(path.name, set()).add(name)

    if offenders:
        print("Undeclared third-party imports under tools/:\n")
        for name, names in sorted(offenders.items()):
            print(f"  {name}: {', '.join(sorted(names))}")
        print(
            "\nThe tooling is documented as running on a bare Python install apart"
            "\nfrom the exceptions listed in this file. Either drop the dependency,"
            "\nor add it to requirements.txt and to ALLOWED here with the reason."
        )
        return 1

    print(f"{checked} tools checked, no undeclared dependency.")
    for name in sorted(declared_seen):
        print(f"  allowed: {name} - {ALLOWED[name]}")
    unused = set(ALLOWED) - declared_seen
    if unused:
        # A stale exemption is a small lie about what the tree needs.
        print(f"\n  note: no longer imported, so the exemption can go: "
              f"{', '.join(sorted(unused))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
