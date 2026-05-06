#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brake Check Gate — Cognitive Brake Structural Validator

Validates that the Agent persisted a structurally complete Cognitive Brake
snapshot at phase transitions.

Reads `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_brake_snapshot.md` and checks:
- `[Intent Check]` line present with all required fields
- `<Cognitive_Brake>` block present with all 4 required dimensions
- Budget counters are numeric

Exit codes:
- 0: PASS
- 1: WARN (partial — some dimensions incomplete)
- 2: FAIL (snapshot missing or critically malformed)
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _check_intent_check_line(text: str) -> tuple[bool, list[str]]:
    """Verify [Intent Check] line has required fields."""
    missing = []
    if "[Intent Check]" not in text:
        return False, ["missing [Intent Check] line"]
    # Extract the intent check line
    m = re.search(r"\[Intent Check\].*", text)
    if not m:
        return False, ["[Intent Check] line unparseable"]
    line = m.group(0)
    required_fields = {
        "intent=": "intent",
        "profile=@": "profile",
        "risk=": "risk",
        "scenario=": "scenario",
        "emergency=": "emergency",
    }
    for token, name in required_fields.items():
        if token not in line:
            missing.append(f"missing field: {name}")
    return len(missing) == 0, missing


def _check_cognitive_brake_block(text: str) -> tuple[bool, list[str]]:
    """Verify <Cognitive_Brake> block has all 4 dimensions."""
    missing = []

    if "<Cognitive_Brake>" not in text:
        return False, ["missing <Cognitive_Brake> block"]

    # Extract the block
    m = re.search(r"<Cognitive_Brake>(.*?)</Cognitive_Brake>", text, re.DOTALL)
    if not m:
        return False, ["<Cognitive_Brake> block unparseable"]
    block = m.group(1)

    dimensions = [
        (r"Role\s*[&]\s*Scope:", "Role & Scope"),
        (r"Budget\s*[&]\s*Context:", "Budget & Context"),
        (r"Architectural\s+Defense:", "Architectural Defense"),
        (r"Next\s+State:", "Next State"),
    ]
    for pattern, name in dimensions:
        if not re.search(pattern, block):
            missing.append(f"missing dimension: {name}")

    # Verify budget line has all three counters
    budget_match = re.search(r"Budget.*?Wiki:\s*\[?\d+\]?/\d+.*?Code:\s*\[?\d+\]?/\d+.*?Web:\s*\[?\d+\]?/\d+", block)
    if not budget_match:
        missing.append("Budget line missing or incomplete (expected Wiki/Code/Web counters)")

    return len(missing) == 0, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, help="Path to brake_snapshot.md")
    args = parser.parse_args()

    if not os.path.exists(args.snapshot):
        print(f"FAIL: snapshot not found: {args.snapshot}")
        return EXIT_FAIL

    with open(args.snapshot, "r", encoding="utf-8") as f:
        text = f.read()

    # Find the most recent phase entry
    phases = re.split(r"## Phase:", text)
    if len(phases) < 2:
        print("FAIL: snapshot has no phase entries")
        return EXIT_FAIL

    # Check the latest phase block
    latest = "## Phase:" + phases[-1]

    intent_ok, intent_missing = _check_intent_check_line(latest)
    brake_ok, brake_missing = _check_cognitive_brake_block(latest)

    all_missing = intent_missing + brake_missing

    if not all_missing:
        print("OK: Cognitive Brake snapshot structurally complete")
        return 0

    critical = [m for m in all_missing if "missing" in m and "block" in m.lower()]
    if critical or not intent_ok:
        print("FAIL: Cognitive Brake snapshot structural violations")
        for m in all_missing:
            print(f"- {m}")
        return EXIT_FAIL

    print("WARN: Cognitive Brake snapshot incomplete")
    for m in all_missing:
        print(f"- {m}")
    return EXIT_WARN


if __name__ == "__main__":
    raise SystemExit(main())
