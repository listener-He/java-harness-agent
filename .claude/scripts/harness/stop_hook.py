#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook — fires when the main agent finishes a turn.

Runs turn_health_check.py to surface observable inconsistencies (uncompiled
Java, large uncommitted change set, launch_spec drift). Non-blocking: always
exits 0, only injects context via stdout.

Respects `stop_hook_active` to prevent recursion if the health check ever
needs to trigger downstream behavior that re-fires Stop.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
TURN_HEALTH = str(_HARNESS_DIR.parent / "local_intel" / "turn_health_check.py")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        return 0

    try:
        proc = subprocess.run(
            [sys.executable, TURN_HEALTH],
            check=False, capture_output=True, text=True, timeout=3,
        )
    except Exception:
        return 0

    out = (proc.stdout or "").rstrip()
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
