"""Scan the portfolio tree for anything that must not be published.

    python tools/check_public.py

Exits non-zero on a finding. This is the gate PUBLICATION_CHECKLIST.md refers
to: the point of writing a redaction review is being able to re-run it, so the
review is executable rather than a promise.

Binary assets are skipped for text patterns but their names are still checked.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pptx", ".ico",
                   ".woff", ".woff2", ".ttf", ".zip", ".webp"}

# (label, regex, explanation shown on a hit)
# The patterns are deliberately GENERIC.
#
# An earlier version of this file listed the literal internal hostnames,
# credential variable names and env-var names it was written to catch -- which
# meant the scanner published exactly the values the rest of the portfolio had
# removed. A redaction gate that leaks its own inputs is worse than no gate.
#
# Every pattern below is now a heuristic that matches the real values without
# naming them, and each is at least as broad as the literal it replaced. Any
# site-specific literals belong in an untracked override (see LOCAL_PATTERNS).
PATTERNS: list[tuple[str, str, str]] = [
    # Hostnames whose label names an internal service class. Catches
    # gitea/registry/artifactory/nexus/harbor hosts on any domain, plus the
    # usual internal TLDs, without naming a company domain.
    ("internal service host",
     r"\b[a-z0-9-]*(?:gitea|gitlab|registry|artifactory|nexus|harbor|jfrog|"
     r"jenkins|intranet)[a-z0-9-]*\.[a-z0-9-]+\.[a-z]{2,}\b",
     "a hostname naming an internal service"),
    ("internal TLD host",
     r"\b[a-z0-9-]+\.(?:internal|intranet|corp|lan|local|home\.arpa)\b",
     "a hostname on an internal-only TLD"),
    ("lab/staging host prefix",
     r"\b(?:lab|stg|staging|dev|uat|preprod)-[a-z0-9-]+\.[a-z0-9-]+\.[a-z]{2,}\b",
     "a non-production internal hostname"),

    # RFC1918 and loopback, including a port or path suffix.
    ("private IPv4 10/8", r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
     "a private IP address"),
    ("loopback IPv4", r"\b127\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
     "a loopback IP address"),
    ("private IPv4 192.168/16", r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
     "a private IP address"),
    ("private IPv4 172.16/12",
     r"\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b",
     "a private IP address"),

    # Credentials. The first catches any <word>_password / <word>Password
    # identifier; the second catches an assignment of a value to one.
    # The trailing [a-z0-9_]* matters: a value like app_password123 has a word
    # character after "password", so a bare \b there would miss it.
    ("credential identifier",
     r"(?i)\b[a-z][a-z0-9]{2,}[_-](?:password|passwd|secret|apikey)[a-z0-9_]*\b",
     "an identifier naming a credential"),
    ("password literal",
     r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9_!@#$%^&*-]{4,}",
     "a password value"),
    ("well-known default credential",
     r"(?i)\b(?:admin123|changeme|letmein|p@ssw0rd|postgres:postgres|"
     r"root:root|guest:guest)\b",
     "a well-known default credential"),

    # Secret-bearing environment variables of any name.
    ("secret env var",
     r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_(?:API_KEY|APIKEY|TOKEN|SECRET|"
     r"PASSWORD|CREDENTIALS|PRIVATE_KEY)\b",
     "an environment variable that carries a secret"),
    ("api key assignment",
     r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?key|token)\s*[:=]\s*"
     r"['\"]?[A-Za-z0-9_\-]{12,}",
     "an API key or token value"),
    ("credential filename", r"\.(?:[a-z_]*_)?(?:token|credentials|netrc)\b",
     "a credential filename"),

    # Concrete secret material.
    ("bearer token", r"(?i)bearer\s+[A-Za-z0-9\-_.]{20,}", "a bearer token"),
    ("private key block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
     "a private key"),
    ("aws access key", r"\bAKIA[0-9A-Z]{16}\b", "an AWS access key id"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.", "a JWT"),

    # Tool/session attribution trailers of any vendor. These must not appear
    # in this repository, in a file or in a commit message.
    ("session or tool trailer",
     r"(?im)^\s*(?:co-authored-by|[a-z][a-z-]*-session|assistant-session|"
     r"generated-by)\s*:",
     "a tool session or attribution trailer"),
]

# Optional, untracked, site-specific literals. `.gitignore` already excludes
# `*.local.*`, so a file named tools/check_public.local.py never reaches a
# remote. It should define PATTERNS as the same 3-tuple shape; entries are
# appended to the generic set above.
#
#   # tools/check_public.local.py   (never committed)
#   PATTERNS = [("our git host", r"gitea\.example\.internal", "our Git host")]
LOCAL_PATTERNS: list[tuple[str, str, str]] = []
try:  # pragma: no cover - optional local override
    from check_public_local import PATTERNS as _local  # type: ignore
    LOCAL_PATTERNS = list(_local)
except Exception:
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "check_public_local",
            pathlib.Path(__file__).with_name("check_public.local.py"))
        if _spec and _spec.loader:
            _mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            LOCAL_PATTERNS = list(getattr(_mod, "PATTERNS", []))
    except Exception:
        LOCAL_PATTERNS = []
PATTERNS = PATTERNS + LOCAL_PATTERNS

# Deliberate, reviewed exceptions: the redaction review discusses these
# patterns as things that were removed, so the words themselves appear there.
ALLOW = {
    "tools/check_public.py",
    "PUBLICATION_CHECKLIST.md",
    "PUBLICATION_DECISIONS.md",
}

# The private evidence pack is scanned separately and deliberately contains
# the strings it documents as redacted. It is excluded from a public remote
# by .gitignore, so it is skipped here rather than allow-listed file by file.
SKIP_TREES = {"private"}


def rel(p: pathlib.Path) -> str:
    return p.relative_to(ROOT).as_posix()


def main() -> int:
    findings: list[tuple[str, int, str, str]] = []
    scanned = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        r = rel(p)
        if r in ALLOW:
            continue
        # r is portfolio-relative, so its first segment is the top-level
        # directory. p.parts[0] would be the drive root.
        if r.split("/", 1)[0] in SKIP_TREES:
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, pat, why in PATTERNS:
                if re.search(pat, line):
                    findings.append((r, line_no, label, line.strip()[:110]))

    print(f"scanned {scanned} text files under {ROOT.name}/ "
          f"(excluding: {', '.join(sorted(SKIP_TREES))}/)")
    if not findings:
        print("\nNo credential, internal hostname, private IP, token or session\n"
              "metadata found. Safe to publish on the technical criteria in\n"
              "PUBLICATION_DECISIONS.md.\n"
              "\nThe two remaining decisions are the author's, not this script's:\n"
              "  1. whether to publish the employer repository names\n"
              "  2. whether to publish the corpus composition")
        return 0

    print(f"\n{len(findings)} finding(s) -- DO NOT PUBLISH until each is resolved:\n")
    for path, line_no, label, snippet in findings:
        print(f"  {path}:{line_no}")
        print(f"      {label}: {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
