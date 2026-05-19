#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit gate scripts for compliance with the linter-severity-standard contract.

Checks every `.claude/scripts/gates/*.py` (excluding underscore-prefixed helpers)
for two requirements from the standard:

  1. Declares both `EXIT_WARN = 1` and `EXIT_FAIL = 2` constants — OR
     imports them from the shared `_severity` helper.
  2. Produces at least one stdout line starting with `OK:` / `WARN:` / `FAIL:`
     (verified via static grep — runtime invocation is out of scope).

Exit codes:
  0 = all gates compliant
  1 = warnings (gate lacks structured output, but exit codes look right)
  2 = failures (gate missing severity constants entirely)
"""
from __future__ import annotations

import glob
import os
import re
import sys

GATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_PREFIX = "_"

HAS_WARN = re.compile(r"^EXIT_WARN\s*=\s*1", re.MULTILINE)
HAS_FAIL = re.compile(r"^EXIT_FAIL\s*=\s*2", re.MULTILINE)
HAS_IMPORT = re.compile(r"from\s+_severity\s+import|import\s+_severity", re.MULTILINE)
HAS_OUTPUT_PREFIX = re.compile(r"""print\(\s*[fr]?["']\s*(OK|WARN|FAIL)\s*:""", re.MULTILINE)
USES_EMIT = re.compile(r"\bemit\s*\(", re.MULTILINE)


def audit_one(path: str) -> tuple[int, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    issues: list[str] = []
    severity = 0

    has_constants = bool(HAS_WARN.search(text) and HAS_FAIL.search(text))
    uses_helper = bool(HAS_IMPORT.search(text))
    if not (has_constants or uses_helper):
        issues.append("missing EXIT_WARN=1 / EXIT_FAIL=2 constants and does not import _severity helper")
        severity = max(severity, 2)

    # Output-prefix is satisfied EITHER by a literal print("OK:|WARN:|FAIL:...")
    # OR by importing _severity and calling its emit() helper (which guarantees the prefix).
    helper_chain = uses_helper and bool(USES_EMIT.search(text))
    if not (HAS_OUTPUT_PREFIX.search(text) or helper_chain):
        issues.append("no stdout line starts with 'OK:' / 'WARN:' / 'FAIL:' — agent cannot classify")
        severity = max(severity, 1)

    return severity, issues


def main() -> int:
    targets = sorted(glob.glob(os.path.join(GATES_DIR, "*.py")))
    targets = [
        t for t in targets
        if not os.path.basename(t).startswith(EXCLUDE_PREFIX)
        and os.path.basename(t) != os.path.basename(__file__)
    ]

    overall = 0
    nonconforming: list[tuple[str, int, list[str]]] = []

    for t in targets:
        sev, issues = audit_one(t)
        if sev > 0:
            nonconforming.append((os.path.basename(t), sev, issues))
            overall = max(overall, sev)

    if overall == 0:
        print(f"OK: severity audit — {len(targets)} gates conform to linter-severity-standard")
        return 0

    label = "FAIL" if overall == 2 else "WARN"
    print(f"{label}: severity audit — {len(nonconforming)}/{len(targets)} gates non-conformant")
    for name, sev, issues in nonconforming:
        marker = "FAIL" if sev == 2 else "WARN"
        print(f"- [{marker}] {name}")
        for i in issues:
            print(f"    · {i}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
