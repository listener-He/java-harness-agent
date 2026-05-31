#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Notification hook — log Claude Code notification events.

Claude Code fires this hook when surfacing a UI notification — typically:
  - permission request (about to use a tool that needs approval)
  - idle alert (long-running operation has been waiting for the user)

Side effects:
  1. Append timestamped JSONL entry to
     `.claude/runs/local_intel/notifications.jsonl` for later analysis
     (attention-required patterns, idle-time distributions, etc.)
  2. If env CLAUDE_NOTIFY_SOUND=1, play macOS system bell (afplay Glass.aiff).
     Off by default — opt-in to avoid surprise.

Non-blocking: silent stdout, always exit 0.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

LOG_DIR = Path(".claude/runs/local_intel")
LOG_FILE = LOG_DIR / "notifications.jsonl"
SOUND_FILE = "/System/Library/Sounds/Glass.aiff"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    # Tolerate several possible field names — Claude Code payload shape may
    # vary between hook versions; capture whatever message-like field exists.
    message = (
        payload.get("notification")
        or payload.get("message")
        or payload.get("title")
        or ""
    )

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "message": message,
        "session_id": payload.get("session_id", ""),
        "type": payload.get("type", ""),
    }

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

    if os.environ.get("CLAUDE_NOTIFY_SOUND") == "1" and os.path.exists(SOUND_FILE):
        try:
            subprocess.run(
                ["afplay", SOUND_FILE],
                check=False, timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
