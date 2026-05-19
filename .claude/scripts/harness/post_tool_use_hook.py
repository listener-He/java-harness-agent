#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook for Edit|Write.

Claude Code passes the hook payload as JSON on stdin (NOT via env var).
We extract tool_input.file_path and run the secrets linter on it.
Failures are silent — hooks must not abort tool execution.
"""
from __future__ import annotations

import json
import subprocess
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0

    try:
        subprocess.run(
            [sys.executable, ".claude/scripts/gates/secrets_linter.py",
             "--paths", file_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
