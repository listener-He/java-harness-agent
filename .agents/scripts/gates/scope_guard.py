#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scope Guard (Anti-drift)

This gate prevents the change set from drifting outside allowed scope.
It reads Allowed Scope prefixes from a focus card and compares them against changed files.

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import re
import subprocess
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _read_allowed_prefixes(focus_card_path: str) -> list[str]:
    with open(focus_card_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_section = False
    prefixes: list[str] = []
    for line in lines:
        if line.strip() == "## Allowed Scope":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            s = line.strip()
            if s.startswith("-"):
                v = s.lstrip("-").strip()
                if v:
                    prefixes.append(v)
    return prefixes


def _git_changed_files() -> list[str]:
    try:
        out = subprocess.check_output(["git", "diff", "--name-only"], text=True).strip()
        if out:
            return [x.strip() for x in out.splitlines() if x.strip()]
    except Exception:
        pass
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "--cached"], text=True).strip()
        if out:
            return [x.strip() for x in out.splitlines() if x.strip()]
    except Exception:
        return []
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus-card", required=True)
    parser.add_argument("--files", nargs="*", default=None, help="explicit file list; if omitted, uses git diff")
    parser.add_argument("--allow-prefix", action="append", default=[], help="additional allowed prefixes")
    args = parser.parse_args()

    if not os.path.exists(args.focus_card):
        print(f"FAIL: focus card not found: {args.focus_card}")
        return EXIT_FAIL

    raw_allowed = _read_allowed_prefixes(args.focus_card) + args.allow_prefix
    allowed_prefixes: list[str] = []
    allowed_exact: set[str] = set()
    for a in raw_allowed:
        a = a.strip()
        if not a:
            continue
        if a.endswith("/"):
            allowed_prefixes.append(a)
            continue
        if "/" in a:
            allowed_prefixes.append(a.rstrip("/") + "/")
            continue
        allowed_exact.add(a)

    if not allowed_prefixes and not allowed_exact:
        print("WARN: no allowed scope prefixes found; cannot enforce scope")
        return EXIT_WARN

    files = args.files if args.files is not None and len(args.files) > 0 else _git_changed_files()
    normalized_files: list[str] = []
    for item in files:
        if item is None:
            continue
        parts = [p.strip() for p in item.split(",")] if "," in item else [item.strip()]
        for p in parts:
            if p:
                normalized_files.append(p.replace("\\", "/"))
    files = normalized_files
    if not files:
        print("OK: no changed files detected")
        return 0

    violations = []
    for f in files:
        if f in allowed_exact:
            continue
        if any(f.startswith(p) for p in allowed_prefixes):
            continue
        violations.append(f)

    if violations:
        print("FAIL: scope guard detected out-of-scope changes")
        print("Allowed exact:")
        for p in sorted(allowed_exact):
            print(f"- {p}")
        print("Allowed prefixes:")
        for p in allowed_prefixes:
            print(f"- {p}")
        print("Violations:")
        for v in violations:
            print(f"- {v}")
        return EXIT_FAIL

    print("OK: scope guard pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
