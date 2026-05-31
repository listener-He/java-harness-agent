#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook for Edit|Write — pure sensor.

Phase P2 of the Sensor/Policy/Enforce refactor: hooks become event emitters,
not policy executors. This script previously ran 5-6 subprocesses (secrets
linter / migration / dependency / skill_hint / incident_hint / session_stats)
and printed findings to stdout. All of that moved:

  - secrets post-scan         → /h-gates --phase qa (Implement→QA boundary)
  - migration / dependency    → /h-gates --phase archive (file-based dispatch)
  - skill_hint / incident_hint → agent reads via events_query when it cares
  - session_stats edit count  → still useful for /h-reflect threshold;
                                kept as a single inline call here

Net effect: one synchronous JSONL append + one fire-and-forget counter bump.
Wall-clock dropped from ~160ms (5 parallel subprocesses) to ~30ms (in-process
imports only).

Failures: silent. Exit 0 always.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_LOCAL_INTEL_DIR = _SCRIPTS_DIR / "local_intel"
if str(_LOCAL_INTEL_DIR) not in sys.path:
    sys.path.insert(0, str(_LOCAL_INTEL_DIR))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0

    # Best-effort tool name (Edit / Write). Claude Code may pass tool_name
    # at top level; if absent, leave empty — events_query users don't need it.
    tool_name = payload.get("tool_name") or ""

    # Sensor write — silent on any error.
    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "edit_post",
            file_path=file_path,
            tool=tool_name,
            success=True,
        )
    except Exception:
        pass

    # Keep session edit counter — /h-reflect threshold consumes it.
    # Single in-process import; no subprocess.
    try:
        import session_stats  # noqa: E402
        session_stats.bump_edit(file_path)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
