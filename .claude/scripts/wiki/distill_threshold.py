#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight wiki distillation threshold check.

Called by the UserPromptSubmit hook to nudge users toward running @distill
once the wiki has grown enough to warrant cleanup. Performs only fast
filesystem-level checks (no git, no content scan) so it stays cheap on
every prompt.

Exits 0=OK (silent), 1=WARN (one-line stdout for hook injection).

Thresholds (any match → WARN; OR semantics):
  - Any domain index.md exceeds 200 lines
  - Any domain has more than 15 detail .md files (excluding index/wal/archive)
  - Total wal/archive/ fragments across all domains exceed 50
"""
from __future__ import annotations

import sys
from pathlib import Path

WIKI_DOMAIN_ROOT = Path(".claude/wiki/wiki")
INDEX_LINE_THRESHOLD = 200
DETAIL_FILE_THRESHOLD = 15
ARCHIVE_TOTAL_THRESHOLD = 50


def _count_lines(p: Path) -> int:
    try:
        with p.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _domain_details(domain: Path) -> list[Path]:
    """Detail markdown files in a domain root (excludes index/wal/archive subdirs)."""
    return [
        p for p in domain.iterdir()
        if p.is_file() and p.suffix == ".md" and p.name != "index.md"
    ]


def _archive_fragments(domain: Path) -> int:
    archive = domain / "wal" / "archive"
    if not archive.exists():
        return 0
    return sum(1 for p in archive.iterdir() if p.is_file() and p.suffix == ".md")


def main() -> int:
    if not WIKI_DOMAIN_ROOT.exists():
        return 0
    domains = [p for p in WIKI_DOMAIN_ROOT.iterdir() if p.is_dir()]
    if not domains:
        return 0

    over_index = []
    over_detail = []
    archive_total = 0

    for d in domains:
        idx = d / "index.md"
        if idx.exists():
            n = _count_lines(idx)
            if n > INDEX_LINE_THRESHOLD:
                over_index.append(f"{d.name}/index.md ({n} lines)")

        details = _domain_details(d)
        if len(details) > DETAIL_FILE_THRESHOLD:
            over_detail.append(f"{d.name}/ ({len(details)} files)")

        archive_total += _archive_fragments(d)

    reasons = []
    if over_index:
        reasons.append(f"oversize index: {', '.join(over_index)}")
    if over_detail:
        reasons.append(f"detail overflow: {', '.join(over_detail)}")
    if archive_total > ARCHIVE_TOTAL_THRESHOLD:
        reasons.append(f"archive total {archive_total} > {ARCHIVE_TOTAL_THRESHOLD}")

    if not reasons:
        return 0

    print(f"[wiki-distill] threshold hit — run @distill to extract & clean: {'; '.join(reasons)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
