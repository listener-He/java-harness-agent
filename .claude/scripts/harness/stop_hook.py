#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook — pure sensor + 2 throttled push-back reminders.

Sensor: emit turn_end event (branch/head/dirty_files) to events.jsonl.

Push-back (T9+T10), both with same throttling philosophy "only emit when
the situation changes":

  - [insight-reminder]   (T9): unread HIGH-confidence insights await review.
                               Throttle: emit only when the SET of active
                               insight ids changes vs the last emit.
  - [scope-check-reminder] (T10/R2): dirty file count high AND no recent
                               /h-gates run. Throttle: emit only when dirty
                               count increased or last emit was >1 hour ago.

Both reminders are 1 line of stdout; they replace the discipline cost of
"agent must remember to pull". They throttle on a shared state file so they
don't spam every turn end.

Respects `stop_hook_active` to prevent recursion. Always exit 0.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

_LOCAL_INTEL_DIR = Path(__file__).resolve().parent.parent / "local_intel"
_REMINDER_STATE_FILE = (
    Path(__file__).resolve().parent.parent.parent / "runs"
    / "local_intel" / "last_reminders.json"
)
SCOPE_DIRTY_THRESHOLD = 5
SCOPE_REMINDER_AGE_HOURS = 1


def _git(args: list[str], timeout: int = 3) -> str:
    try:
        return subprocess.check_output(
            ["git"] + args, timeout=timeout, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def _load_reminder_state() -> dict:
    try:
        if _REMINDER_STATE_FILE.is_file():
            return json.loads(_REMINDER_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_reminder_state(state: dict) -> None:
    try:
        _REMINDER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _REMINDER_STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _maybe_emit_insight_reminder(state: dict) -> dict:
    """If active high-conf insights set CHANGED since last emit, emit + update state."""
    try:
        if str(_LOCAL_INTEL_DIR) not in sys.path:
            sys.path.insert(0, str(_LOCAL_INTEL_DIR))
        import insight_writer  # noqa: E402
        active = insight_writer.query_active(top=20, min_confidence="high")
    except Exception:
        return state

    current_ids = sorted(ins.get("id", "") for ins in active if ins.get("id"))
    if not current_ids:
        # nothing to remind about; clear state so next non-empty set re-fires
        if state.get("insight"):
            state.pop("insight", None)
        return state

    prev = state.get("insight", {})
    prev_ids = sorted(prev.get("insight_ids", []))
    if current_ids == prev_ids:
        return state  # already reminded about exactly this set; stay quiet

    n = len(current_ids)
    print(f"[insight-reminder] {n} high-confidence insight(s) await review "
          f"— run /h-context-check or /h-evolve --auto-pick")
    state["insight"] = {
        "insight_ids": current_ids,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    return state


def _maybe_emit_scope_reminder(state: dict, dirty_files: int) -> dict:
    """If dirty > threshold AND (count increased OR last emit aged out), emit."""
    if dirty_files <= SCOPE_DIRTY_THRESHOLD:
        # situation healthy — don't reset state (avoid re-emit on a small
        # commit followed by re-dirtying)
        return state

    prev = state.get("scope", {})
    prev_count = int(prev.get("dirty_count", 0))
    prev_ts_str = prev.get("ts", "")
    prev_ts = None
    try:
        prev_ts = datetime.fromisoformat(prev_ts_str)
    except (ValueError, TypeError):
        pass

    aged_out = (
        prev_ts is None
        or (datetime.now() - prev_ts) > timedelta(hours=SCOPE_REMINDER_AGE_HOURS)
    )
    increased = dirty_files > prev_count
    if not (aged_out or increased):
        return state

    print(f"[scope-check-reminder] dirty file count = {dirty_files} "
          f"(>{SCOPE_DIRTY_THRESHOLD}); consider /h-gates --phase implement "
          f"to audit scope, or commit/stash before continuing")
    state["scope"] = {
        "dirty_count": dirty_files,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    return state


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

    # Throttled push-back reminders. Shared state file ensures we don't spam
    # every turn end with the same nudge. Both functions update state in-place.
    state = _load_reminder_state()
    state = _maybe_emit_insight_reminder(state)
    state = _maybe_emit_scope_reminder(state, dirty_files)
    _save_reminder_state(state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
