#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook.

Injects a compact summary of recurring failures (last 30 days, count >= 2)
into the conversation context. The goal is compounding cross-session learning
without flooding the prompt with one-off issues.

Stdout is appended to the user prompt as additional context.
Silent (no output, exit 0) when:
  - failure memory file missing
  - no patterns recurred >= 2 times in the window
  - CLAUDE_FAILURE_MEMORY_QUIET=1 set
"""
from __future__ import annotations

import os
import subprocess
import sys

FAILURE_MEMORY = ".claude/scripts/local_intel/failure_memory.py"


def main() -> int:
    if os.environ.get("CLAUDE_FAILURE_MEMORY_QUIET") == "1":
        return 0

    # Drain stdin so the caller does not block on SIGPIPE.
    try:
        sys.stdin.read()
    except Exception:
        pass

    proc = subprocess.run(
        [sys.executable, FAILURE_MEMORY, "summary",
         "--days", "30", "--min-count", "2", "--top", "5"],
        check=False,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return 0

    print("[failure-memory] Recurring issues in the last 30 days — keep in mind while planning:")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
