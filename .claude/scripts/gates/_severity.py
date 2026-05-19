#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared severity helper for gate scripts.

Codifies the FAIL/WARN/OK contract from `.claude/skills/linter-severity-standard/SKILL.md`.

Usage in a gate script:

    from _severity import Severity, Result, emit

    if some_problem:
        return emit(Result(Severity.FAIL, "my_gate", "what went wrong",
                           details=["line 1", "line 2"]), as_json=args.as_json)

Conventions enforced:
- Exit codes: OK=0, WARN=1, FAIL=2
- First line of stdout starts with `OK:` / `WARN:` / `FAIL:` (text mode)
- `--json` mode emits one JSON object: {"severity","gate","message","details"}

Gates may keep their existing inline `EXIT_WARN = 1; EXIT_FAIL = 2` style;
this helper is opt-in and additive, not required.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    OK = 0
    WARN = 1
    FAIL = 2


@dataclass
class Result:
    severity: Severity
    gate: str
    message: str = ""
    details: list[str] = field(default_factory=list)


def emit(result: Result, as_json: bool = False) -> int:
    """Print the result in either text or JSON format. Returns the exit code."""
    if as_json:
        print(json.dumps({
            "severity": result.severity.name,
            "gate": result.gate,
            "message": result.message,
            "details": result.details,
        }))
    else:
        head = f"{result.severity.name}: {result.gate}"
        if result.message:
            head = f"{head} — {result.message}"
        print(head)
        for d in result.details:
            print(f"- {d}")
    return int(result.severity)
