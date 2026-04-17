#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focus Card Gate

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

REQUIRED_SECTIONS = [
    "## Goal",
    "## Non-Goals",
    "## Allowed Scope",
    "## Budgets",
    "## Stop Rules",
]

REQUIRED_NON_EMPTY_SECTIONS = [
    "## Goal",
    "## Non-Goals",
    "## Allowed Scope",
]

PLACEHOLDER_TOKENS = ["- ", "TODO", "TBD", "to be filled", "待补充", "待定"]


def _section_body(content: str, section: str) -> str:
    lines = content.splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip() == section:
            start = i + 1
            break
    if start < 0:
        return ""
    buf = []
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith("## "):
            break
        buf.append(line)
    return "\n".join(buf).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"FAIL: focus card not found: {args.file}")
        return EXIT_FAIL

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing:
        print("FAIL: focus card missing required sections")
        for s in missing:
            print(f"- {s}")
        return EXIT_FAIL

    empty_like = []
    for sec in REQUIRED_NON_EMPTY_SECTIONS:
        body = _section_body(content, sec)
        normalized = body.replace("\n", " ").strip()
        if not normalized:
            empty_like.append(f"{sec}: empty")
            continue
        if normalized in ("-", "*"):
            empty_like.append(f"{sec}: placeholder bullet only")
            continue
        if any(token.lower() in normalized.lower() for token in PLACEHOLDER_TOKENS):
            # allow regular bullet lists; reject obvious placeholder forms
            if normalized in ("- ", "* "):
                empty_like.append(f"{sec}: placeholder token")

    if empty_like:
        print("FAIL: focus card has empty/placeholder key sections")
        for x in empty_like:
            print(f"- {x}")
        return EXIT_FAIL

    print("OK: focus card gate pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
