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
from pathlib import Path

# Resolve sibling scripts relative to this file so the hook works regardless
# of the harness's current working directory.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SECRETS_LINTER = str(_SCRIPTS_DIR / "gates" / "secrets_linter.py")
SKILL_HINT = str(_SCRIPTS_DIR / "local_intel" / "skill_hint.py")


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
            [sys.executable, SECRETS_LINTER, "--paths", file_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    # Symptom-driven skill hint: non-blocking, silent on no match. The hint
    # routes the agent to the relevant SKILL.md only when the just-edited file
    # shows an anti-pattern — not before Implement, not on every Java edit.
    try:
        proc = subprocess.run(
            [sys.executable, SKILL_HINT, file_path],
            check=False, capture_output=True, text=True,
        )
        out = (proc.stdout or "").rstrip()
        if out:
            print(out)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
