#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reflect Threshold — emit `[reflect-hint]` when session_stats indicates
accumulated work without a recent reflection.

Called from `stop_hook.py` after `turn_health_check.py`. Pure read; never
modifies state. Non-blocking — always exits 0; emits to stdout for hook
injection only when at least one threshold is tripped.

Thresholds (any match → hint; OR semantics):
  - edits      >= 12   (sustained tool activity in one session)
  - files      >= 6    (broad blast radius)
  - failures   >= 3    (repeated gate / lint refusal — likely patterns to capture)
  - hours      > 24    (long stretch since last `/h-reflect` or `/h-archive`)

The hint suggests `/h-reflect`, which then runs Session Review and resets
the counters. Counters are also reset by `/h-archive` to avoid hinting
right after the user already captured at task close.

Quiet env: CLAUDE_REFLECT_THRESHOLD_QUIET=1
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
STATS_PATH = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "session_stats.json"

EDIT_THRESHOLD = 12
FILE_THRESHOLD = 6
FAILURE_THRESHOLD = 3
HOURS_THRESHOLD = 24.0


def _hours_since(ts_str: str) -> float:
    """Hours elapsed since ISO-format timestamp. 0.0 if unparseable."""
    try:
        ts = datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return 0.0
    return (datetime.now() - ts).total_seconds() / 3600.0


def main() -> int:
    if os.environ.get("CLAUDE_REFLECT_THRESHOLD_QUIET") == "1":
        return 0
    if not STATS_PATH.exists():
        return 0
    try:
        data = json.loads(STATS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0

    edits = int(data.get("edits", 0))
    files = len(data.get("files", []))
    failures = int(data.get("failures", 0))
    hours = _hours_since(data.get("last_reflect_ts", ""))

    reasons: list[str] = []
    if edits >= EDIT_THRESHOLD:
        reasons.append(f"{edits} edits")
    if files >= FILE_THRESHOLD:
        reasons.append(f"{files} files touched")
    if failures >= FAILURE_THRESHOLD:
        reasons.append(f"{failures} failures recorded")
    if hours > HOURS_THRESHOLD:
        reasons.append(f"{hours:.0f}h since last reset")

    if not reasons:
        return 0

    print(
        f"[reflect-hint] {' / '.join(reasons)} — consider /h-reflect to "
        f"capture lessons (incidents / wiki patches / failure patterns / "
        f"success / auto-memory) before continuing."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
