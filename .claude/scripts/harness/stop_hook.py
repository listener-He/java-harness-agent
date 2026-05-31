#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook — pure sensor; fires when main agent ends a turn.

Phase P2 of the Sensor/Policy/Enforce refactor. Previously this script ran
turn_health_check.py + reflect_threshold.py inline and printed their findings
to stdout for next-turn injection. Both are now agent-on-demand:

  - turn_health_check  → agent runs via /h-context-check (T6.3) or
                         /h-gates --phase qa when ending Implement
  - reflect_threshold  → agent reads session_stats counters when deciding
                         whether to invoke /h-reflect

The Stop hook just records "turn ended at HEAD=X branch=Y dirty=N" into
events.jsonl. That's enough for events_query consumers to detect long-
running sessions, frequent dirty-without-commit, etc.

Respects `stop_hook_active` to prevent recursion. Always exit 0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_LOCAL_INTEL_DIR = Path(__file__).resolve().parent.parent / "local_intel"


def _git(args: list[str], timeout: int = 3) -> str:
    try:
        return subprocess.check_output(
            ["git"] + args, timeout=timeout, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        return 0

    branch = _git(["branch", "--show-current"])
    head = _git(["rev-parse", "--short", "HEAD"])
    dirty_files = len(_git(["diff", "--name-only"]).splitlines())

    if str(_LOCAL_INTEL_DIR) not in sys.path:
        sys.path.insert(0, str(_LOCAL_INTEL_DIR))
    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "turn_end",
            branch=branch,
            head=head,
            dirty_files=dirty_files,
        )
    except Exception:
        pass

    # Minimal push-back (T9): if any HIGH-confidence insight awaits review,
    # emit a single-line reminder. This is the ONLY non-event side effect of
    # the sensor-tier hook layer; rationale: pull model risks agent never
    # invoking /h-context-check. Turn-end is the lowest-frequency injection
    # point + only fires when something actionable exists.
    try:
        import insight_writer  # noqa: E402
        unread_high = insight_writer.query_active(top=10, min_confidence="high")
        if unread_high:
            n = len(unread_high)
            print(f"[insight-reminder] {n} high-confidence insight(s) await review "
                  f"— run /h-context-check or /h-evolve --auto-pick")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
