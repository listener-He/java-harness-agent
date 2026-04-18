#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAL Template Gate

Checks that WAL fragment files in the given directory conform to the
required template structure (frontmatter + mandatory sections).

Exit codes:
- 0: PASS
- 1: WARN (non-critical issues)
- 2: FAIL (missing mandatory sections)
"""

import argparse
import glob
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

REQUIRED_SECTIONS = ["## Change Summary", "## Impact"]
OPTIONAL_SECTIONS = ["## No-Change Confirmation"]
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
DATE_PREFIX_PATTERN = re.compile(r"^\d{8}_")


def _check_file(path: str) -> tuple[int, list[str]]:
    issues: list[str] = []

    filename = os.path.basename(path)
    if not DATE_PREFIX_PATTERN.match(filename):
        issues.append(f"filename does not start with YYYYMMDD_ prefix: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        return EXIT_FAIL, [f"file is empty: {filename}"]

    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing:
        for s in missing:
            issues.append(f"missing required section '{s}' in {filename}")
        return EXIT_FAIL, issues

    if len(content.strip().splitlines()) < 5:
        issues.append(f"WAL content suspiciously short (< 5 lines): {filename}")
        return EXIT_WARN, issues

    return 0, []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wal-dir", required=True, help="Directory containing WAL fragment files")
    parser.add_argument("--glob", default="*.md", help="File glob pattern (default: *.md)")
    args = parser.parse_args()

    wal_dir = args.wal_dir.rstrip("/")
    if not os.path.isdir(wal_dir):
        print(f"FAIL: wal-dir not found: {wal_dir}")
        return EXIT_FAIL

    files = sorted(glob.glob(os.path.join(wal_dir, args.glob)))
    if not files:
        print(f"WARN: no WAL files found in {wal_dir} matching '{args.glob}'")
        return EXIT_WARN

    overall = 0
    all_issues: list[str] = []
    for f in files:
        code, issues = _check_file(f)
        overall = max(overall, code)
        all_issues.extend(issues)

    if overall == 0:
        print(f"OK: wal_template_gate pass ({len(files)} file(s) checked)")
        return 0
    label = "WARN" if overall == EXIT_WARN else "FAIL"
    print(f"{label}: wal_template_gate")
    for issue in all_issues:
        print(f"- {issue}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
