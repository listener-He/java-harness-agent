#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook — pure sensor.

Phase P2 of the Sensor/Policy/Enforce refactor. This script used to emit up
to four context blocks every prompt:
  - [failure-memory] — recurring failures push
  - [wiki-distill]   — growth threshold nudge
  - [ambiguity]      — definition-of-ready check
  - [triage-evidence] — signal collection + advisory profile_hint

All four were the canonical "push model" — hook decides, agent reads
whatever was injected. The new pull model: agent reads /h-context-check
when entering a new task or unsure. Hook just records the event.

What that buys:
  - Zero per-prompt token pollution (no automatic context injection)
  - Higher prompt-cache hit rate (input is just the user text)
  - Latency: ~310ms → ~30-50ms

What it loses (and where the replacement lives):
  - failure_memory surfacing → events_query --kind edit_post / failure_memory.py summary
  - ambiguity nudge          → agent self-checks via /h-context-check
  - triage evidence          → triage_probe.py still callable for explicit context
  - distill nudge            → distill threshold runs at /h-distill, not per-prompt

Failures: silent. Exit 0 always.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_LOCAL_INTEL_DIR = Path(__file__).resolve().parent.parent / "local_intel"
if str(_LOCAL_INTEL_DIR) not in sys.path:
    sys.path.insert(0, str(_LOCAL_INTEL_DIR))

PROMPT_TEXT_CAP = 2000  # truncate per schema doc to keep jsonl rows lean


def _read_prompt_text() -> tuple[str, str]:
    """Return (text, session_id). Both may be empty on parse failure."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return "", ""
    if not raw:
        return "", ""
    raw = raw.strip()
    if not raw.startswith("{"):
        # Plain text (older Claude Code envelopes)
        return raw, ""
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return raw, ""
    if not isinstance(obj, dict):
        return raw, ""
    text = ""
    for key in ("prompt", "user_prompt", "input", "text"):
        v = obj.get(key)
        if isinstance(v, str) and v:
            text = v
            break
    session_id = obj.get("session_id") or ""
    if not isinstance(session_id, str):
        session_id = ""
    return text, session_id


def main() -> int:
    text, session_id = _read_prompt_text()
    if not text:
        return 0

    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "prompt",
            text=text[:PROMPT_TEXT_CAP],
            session_id=session_id,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
