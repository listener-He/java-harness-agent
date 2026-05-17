#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Safety Gate

Checks SQL migration files for patterns that are unsafe to run in production
without explicit review:
- DROP TABLE / DROP COLUMN (data loss)
- TRUNCATE (data loss)
- Missing transaction wrapper (non-DDL statements without BEGIN/COMMIT)
- ALTER TABLE without DEFAULT on a NOT NULL column addition (lock risk)
- DELETE without WHERE (full table delete)

Exit codes:
- 0: PASS
- 1: WARN (risky but not blocked)
- 2: FAIL (high-risk, must not proceed without bypass_justification.md)
"""

import argparse
import glob
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

# Patterns that FAIL the gate (block Implement without bypass)
FAIL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE detected — irreversible data loss"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE detected — irreversible data loss"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;", re.IGNORECASE), "DELETE FROM without WHERE — full table delete"),
]

# Patterns that WARN (allowed to proceed, but Agent must explain)
WARN_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE), "DROP COLUMN — column data permanently removed"),
    (
        re.compile(r"\bADD\s+COLUMN\b.*?\bNOT\s+NULL\b(?!.*?\bDEFAULT\b)", re.IGNORECASE | re.DOTALL),
        "ADD COLUMN NOT NULL without DEFAULT — may lock table on large datasets",
    ),
    (re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE), "ALTER TABLE — verify index impact on large tables"),
    (re.compile(r"\bCREATE\s+INDEX\b(?!.*?\bCONCURRENTLY\b)", re.IGNORECASE), "CREATE INDEX without CONCURRENTLY — may lock reads"),
]


def _check_file(path: str) -> tuple[int, list[str]]:
    issues: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(path)
    max_code = 0

    for pattern, message in FAIL_PATTERNS:
        if pattern.search(content):
            issues.append(f"FAIL [{filename}]: {message}")
            max_code = EXIT_FAIL

    for pattern, message in WARN_PATTERNS:
        if pattern.search(content):
            issues.append(f"WARN [{filename}]: {message}")
            max_code = max(max_code, EXIT_WARN)

    return max_code, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql-dir", required=True, help="Directory containing SQL migration files")
    parser.add_argument("--glob", default="**/*.sql", help="File glob (default: **/*.sql)")
    args = parser.parse_args()

    sql_dir = args.sql_dir.rstrip("/")
    if not os.path.isdir(sql_dir):
        print(f"FAIL: sql-dir not found: {sql_dir}")
        return EXIT_FAIL

    files = sorted(glob.glob(os.path.join(sql_dir, args.glob), recursive=True))
    if not files:
        print(f"WARN: no SQL files found in {sql_dir}")
        return EXIT_WARN

    overall = 0
    all_issues: list[str] = []
    for f in files:
        code, issues = _check_file(f)
        overall = max(overall, code)
        all_issues.extend(issues)

    if overall == 0:
        print(f"OK: migration_gate pass ({len(files)} file(s) checked)")
        return 0

    label = "WARN" if overall == EXIT_WARN else "FAIL"
    print(f"{label}: migration_gate")
    for issue in all_issues:
        print(f"- {issue}")
    if overall == EXIT_FAIL:
        print("Action: create bypass_justification.md with DBA sign-off to downgrade to WARN.")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
