#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sub-Agent Contract Gate (Deterministic)

Validates that delegated sub-agent prompts are persisted and follow the required
contract envelope defined in:
- .claude/wiki/schema/subagent_contract_schema.md

Expected artifact convention (recommended):
- .claude/workflow/runs/<YYYY-MM-DD>_<slug>_delegation_<id>.md

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import glob
import os
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


REQUIRED_MARKERS = [
    "# Sub-Agent Contract",
    "## 0) Task",
    "## 1) Scope (Hard Boundary)",
    "## 2) Non-negotiable Constraints",
    "## 3) Inputs Provided",
    "## 4) Output Format (MANDATORY)",
    "## Result",
    "## Details",
    "## Self-Check",
]


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _match_files(root_dir: str, topic: str, date: str) -> list[str]:
    root_dir = root_dir or ".claude/workflow/runs"
    pattern = os.path.join(root_dir, "**", "*.md")
    files = [os.path.normpath(p) for p in glob.glob(pattern, recursive=True)]
    files = [p for p in files if os.path.isfile(p)]
    files = [p for p in files if "_delegation_" in os.path.basename(p)]

    if topic:
        files = [p for p in files if topic in os.path.basename(p)]
    if date:
        files = [p for p in files if date in os.path.basename(p)]
    return sorted(files)


def _validate_contract(text: str) -> list[str]:
    missing = [m for m in REQUIRED_MARKERS if m not in (text or "")]
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".claude/workflow/runs", help="Directory to search for delegation artifacts")
    parser.add_argument("--topic", default="", help="topic slug (optional filter; already normalized)")
    parser.add_argument("--date", default="", help="YYYYMMDD (optional filter)")
    parser.add_argument("--fail-on-missing", action="store_true", help="FAIL if no delegation artifacts are found")
    args = parser.parse_args()

    files = _match_files(args.dir, args.topic, args.date)
    if not files:
        msg = "no delegation artifacts found (expected '*_delegation_*.md')"
        if args.fail_on_missing:
            print("FAIL: sub-agent contract gate")
            print(f"- {msg}")
            return EXIT_FAIL
        print("WARN: sub-agent contract gate")
        print(f"- {msg}")
        return EXIT_WARN

    failed: list[tuple[str, list[str]]] = []
    for p in files:
        missing = _validate_contract(_read_text(p))
        if missing:
            failed.append((p, missing))

    if not failed:
        print("OK: sub-agent contract gate pass")
        print(f"- checked: {len(files)} file(s)")
        return 0

    print("FAIL: sub-agent contract gate")
    for p, miss in failed:
        print(f"- file: {p}")
        for m in miss:
            print(f"  - missing: {m}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())

