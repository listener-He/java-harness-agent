#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Index Linter

Ensures all skills under skills-dir are referenced by the central index.

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _list_skills(skills_dir: str) -> list[str]:
    out: list[str] = []
    for name in os.listdir(skills_dir):
        p = os.path.join(skills_dir, name)
        if not os.path.isdir(p):
            continue
        if os.path.exists(os.path.join(p, "SKILL.md")):
            out.append(name)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--skills-dir", required=True)
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.index):
        print(f"FAIL: index not found: {args.index}")
        return EXIT_FAIL
    if not os.path.isdir(args.skills_dir):
        print(f"FAIL: skills dir not found: {args.skills_dir}")
        return EXIT_FAIL

    skills = _list_skills(args.skills_dir)
    with open(args.index, "r", encoding="utf-8") as f:
        index_text = f.read()

    index_skill = os.path.basename(os.path.dirname(args.index))

    missing = []
    for s in skills:
        if s == index_skill:
            continue
        if f"../{s}/SKILL.md" not in index_text:
            missing.append(s)

    if not missing:
        print("OK: skill index linter pass")
        return 0

    print("WARN: skill index missing entries")
    for s in missing:
        print(f"- {s}")

    if args.fail_on_missing:
        print("FAIL: missing skills in index (fail-on-missing enabled)")
        return EXIT_FAIL

    return EXIT_WARN


if __name__ == "__main__":
    raise SystemExit(main())
