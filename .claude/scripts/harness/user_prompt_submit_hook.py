#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook.

Injects two compact context blocks into the user prompt when applicable:

  1. Recurring failures from the last 30 days (failure_memory summary).
  2. Wiki distillation nudge when growth thresholds are tripped
     (single-line @distill suggestion).

Each block is silent when there is nothing to surface. Both stay well below
the prompt-cache token budget.
"""
from __future__ import annotations

import os
import subprocess
import sys

FAILURE_MEMORY = ".claude/scripts/local_intel/failure_memory.py"
DISTILL_THRESHOLD = ".claude/scripts/wiki/distill_threshold.py"


def _drain_stdin() -> None:
    try:
        sys.stdin.read()
    except Exception:
        pass


def _emit_failure_memory() -> None:
    if os.environ.get("CLAUDE_FAILURE_MEMORY_QUIET") == "1":
        return
    proc = subprocess.run(
        [sys.executable, FAILURE_MEMORY, "summary",
         "--days", "30", "--min-count", "2", "--top", "5"],
        check=False, capture_output=True, text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print("[failure-memory] Recurring issues in the last 30 days — keep in mind while planning:")
    print(out)


def _emit_distill_nudge() -> None:
    if os.environ.get("CLAUDE_DISTILL_QUIET") == "1":
        return
    proc = subprocess.run(
        [sys.executable, DISTILL_THRESHOLD],
        check=False, capture_output=True, text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print(out)


def main() -> int:
    _drain_stdin()
    _emit_failure_memory()
    _emit_distill_nudge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
