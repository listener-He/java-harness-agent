#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the structured return block from a sub-agent dispatch.

Contract source: .claude/rules/dispatch-template.md (Expected Output section).

The main agent invokes this AFTER receiving a sub-agent's response. It checks:

  1. All six required line-prefixes are present.
  2. Cross-check 1 — PASS status but Files Changed = none on a code-writing task.
  3. Cross-check 2 — PASS status but Commands Run = none.
  4. Cross-check 3 — PASS status but ACs Mapped = none (task brief had ACs).
  5. Cross-check 4 — Status says PASS but an AC row says FAIL.

FAIL is emitted only for cross-check 4 (direct contradiction); the other three
are WARN (heuristic — might be a read-only or trivial task with no diff).

Exit codes per linter-severity-standard:
  0 = OK
  1 = WARN
  2 = FAIL

Usage:
  python3 subagent_return_gate.py --return-file <path>
  python3 subagent_return_gate.py --return-stdin              # read from stdin
  python3 subagent_return_gate.py --return-file <path> --task-kind review
    # task-kind=review|extract suppresses "no files changed" WARN
"""
from __future__ import annotations

import argparse
import re
import sys

# Local import — both files live in .claude/scripts/gates/
sys.path.insert(0, ".claude/scripts/gates")
from _severity import Result, Severity, emit  # type: ignore

REQUIRED_FIELDS = [
    "Status",
    "Files Changed",
    "Commands Run",
    "ACs Mapped",
    "Issues Found",
    "Next Step",
]

STATUS_VALUES = {"PASS", "PARTIAL", "FAIL", "ESCALATE", "BOUNDARY_EXCEPTION"}
AC_FAIL_TOKENS = {"FAIL", "FAILED", "FAILING"}
NONE_TOKENS = {"none", "n/a", "无", ""}

FIELD_LINE = re.compile(r"^\s*\[([^\]]+)\]\s*:\s*(.*)$")


def _parse(text: str) -> dict[str, str]:
    """Extract [Field]: value pairs. Multi-line values keep first line only
    for cross-checks (sufficient because checks examine the leading value)."""
    fields: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        m = FIELD_LINE.match(line)
        if m:
            if current is not None:
                fields[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = [m.group(2)]
        elif current is not None:
            buf.append(line)
    if current is not None:
        fields[current] = "\n".join(buf).strip()
    return fields


def _is_none(value: str) -> bool:
    first_line = value.strip().splitlines()[0].strip().lower() if value.strip() else ""
    return first_line.rstrip(".") in NONE_TOKENS


def _ac_has_fail(value: str) -> bool:
    """An AC row like 'AC-1 → test_foo → FAIL' contains a fail token."""
    for line in value.splitlines():
        tokens = re.split(r"[\s|→/\->,;:]+", line)
        for t in tokens:
            if t.strip().upper() in AC_FAIL_TOKENS:
                return True
    return False


def _status_value(raw: str) -> str:
    return raw.strip().splitlines()[0].strip().upper() if raw.strip() else ""


def validate(text: str, task_kind: str) -> Result:
    fields = _parse(text)
    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    details: list[str] = []
    sev = Severity.OK

    if missing:
        return Result(
            Severity.FAIL,
            "subagent_return_gate",
            f"missing required fields: {', '.join(missing)}",
            details=[
                "Sub-agent return must include all 6 line-prefixes from "
                ".claude/rules/dispatch-template.md (Expected Output).",
                "Re-dispatch the sub-agent with the template.",
            ],
        )

    status = _status_value(fields["Status"])
    if status not in STATUS_VALUES:
        return Result(
            Severity.FAIL,
            "subagent_return_gate",
            f"[Status] value '{status}' is not one of {sorted(STATUS_VALUES)}",
        )

    # Cross-check 4 (FAIL) — direct contradiction wins over heuristics
    if status == "PASS" and _ac_has_fail(fields["ACs Mapped"]):
        return Result(
            Severity.FAIL,
            "subagent_return_gate",
            "[Status]=PASS but at least one AC row reports FAIL — direct contradiction",
            details=[fields["ACs Mapped"][:200]],
        )

    # Cross-checks 1-3 (WARN) — only for PASS status; gated by task kind
    is_implement = task_kind not in {"review", "extract", "audit"}
    if status == "PASS":
        if is_implement and _is_none(fields["Files Changed"]):
            details.append(
                "[Status]=PASS but [Files Changed]=none — implement task with no diff is suspicious"
            )
            sev = Severity.WARN
        if _is_none(fields["Commands Run"]):
            details.append(
                "[Status]=PASS but [Commands Run]=none — no compile/test evidence recorded"
            )
            sev = Severity.WARN
        if _is_none(fields["ACs Mapped"]):
            details.append(
                "[Status]=PASS but [ACs Mapped]=none — no AC verification recorded"
            )
            sev = Severity.WARN

    if sev == Severity.OK:
        return Result(Severity.OK, "subagent_return_gate",
                      f"all 6 fields present, [Status]={status}, no internal contradiction")
    return Result(sev, "subagent_return_gate",
                  f"return passes structural check but has {len(details)} consistency warning(s)",
                  details=details)


def main() -> int:
    parser = argparse.ArgumentParser()
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--return-file", help="path to a file containing the sub-agent's return text")
    src.add_argument("--return-stdin", action="store_true", help="read return text from stdin")
    parser.add_argument(
        "--task-kind",
        default="implement",
        choices=["implement", "review", "extract", "audit"],
        help="suppresses 'no files changed' WARN for non-modifying task kinds",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.return_stdin:
        text = sys.stdin.read()
    else:
        with open(args.return_file, "r", encoding="utf-8") as f:
            text = f.read()

    result = validate(text, args.task_kind)
    return emit(result, as_json=args.as_json)


if __name__ == "__main__":
    raise SystemExit(main())
