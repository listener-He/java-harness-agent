#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Incident Hint — symptom-driven reverse-lookup from a just-edited file to
recent incident records that referenced it.

Triggered by PostToolUse hook after Edit/Write. When the edited file's path
or filename stem appears in a `<date>_<slug>.md`'s `## 受影响代码栈` section
(or anywhere in the body), emit a one-line `[incident-hint]` pointing at
that incident record.

Philosophy: this is a signal, not a gate. The LLM keeps the right to ignore
the hint. The hook makes ignoring visible.

Quiet env: CLAUDE_INCIDENT_HINT_QUIET=1
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Resolve repo root from this file: .../repo/.claude/scripts/local_intel/incident_hint.py
_REPO_ROOT = Path(__file__).resolve().parents[3]
INCIDENTS_DIR = _REPO_ROOT / ".claude" / "wiki" / "incidents"
DEFAULT_WINDOW_DAYS = 90
MAX_HITS = 2

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_FNAME_PAT = re.compile(r"^\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*\.md$")


def _parse_date(text: str) -> tuple[str, str]:
    """Return (date, status) from frontmatter, both possibly empty."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return "", ""
    date_val = ""
    status_val = ""
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("date:"):
            date_val = line.split(":", 1)[1].strip().strip("\"'")
        elif line.startswith("status:"):
            status_val = line.split(":", 1)[1].strip().strip("\"'").lower()
    return date_val, status_val


def _within_window(date_str: str, status: str, days: int) -> bool:
    if status == "watch":
        return True
    try:
        d = datetime.fromisoformat(date_str).date()
    except ValueError:
        return False
    return d >= (datetime.now() - timedelta(days=days)).date()


def _candidates(path: str) -> set[str]:
    """Strings that, if found in an incident body, count as a match.

    Includes:
      - the full relative path as given
      - the basename (e.g. UserService.java)
      - the stem without extension (e.g. UserService)
    """
    p = Path(path)
    cands = {path, p.name, p.stem}
    # Strip leading ./ or absolute root for path-as-string matches
    if path.startswith("./"):
        cands.add(path[2:])
    return {c for c in cands if c and len(c) >= 4}


def main() -> int:
    if os.environ.get("CLAUDE_INCIDENT_HINT_QUIET") == "1":
        return 0
    if len(sys.argv) < 2:
        return 0
    edited = sys.argv[1]
    if not edited:
        return 0
    if not INCIDENTS_DIR.is_dir():
        return 0

    cands = _candidates(edited)
    hits: list[tuple[str, str]] = []  # (incident path, one-line label)

    for p in sorted(INCIDENTS_DIR.glob("*.md"), reverse=True):
        if not _FNAME_PAT.match(p.name):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        date_val, status = _parse_date(text)
        if not _within_window(date_val, status, DEFAULT_WINDOW_DAYS):
            continue
        # Cheap body match against any candidate string.
        if not any(c in text for c in cands):
            continue
        slug = p.stem.split("_", 1)[-1]
        try:
            rel = p.relative_to(_REPO_ROOT)
            display_path = str(rel)
        except ValueError:
            display_path = str(p)
        hits.append((display_path, f"{date_val} {slug}"))
        if len(hits) >= MAX_HITS:
            break

    if not hits:
        return 0

    print("[incident-hint]")
    for incident_path, label in hits:
        print(f"  - past incident touched this file: {label} → see {incident_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
