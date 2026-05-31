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
whatever was injected. The new pull model: agent runs /h-context-check
when entering a new task or unsure; hook just records the event for
downstream queries.

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

# Phrases that, when appearing at the START of a prompt, signal the user is
# correcting / disagreeing / frustrated-with the agent's prior action. Pure
# string match (no LLM) — false-positive tolerance: "actually" used in
# "let me actually add this" will fire; user_correction insight only surfaces
# on RECURRING phrases (count ≥3 in 30d, AND ideally with prior_actions_5min>0
# binding), so a single false fire is noise-floor.
# Match is case-insensitive, on the first 50 chars (stripped).
CORRECTION_PHRASES = (
    # --- Chinese: explicit correction ---
    "不对", "不是", "错了", "应该是", "实际上", "我意思是", "我的意思是",
    "不该", "不该是", "搞错了", "搞错",
    # --- Chinese: frustration / sarcasm (人类气急败坏 / 阴阳怪气) ---
    "你认真的", "你认真吗", "认真的吗", "你确定", "你不懂", "懂不懂",
    "胡说", "胡扯", "扯淡", "瞎扯", "瞎搞", "搞什么", "搞毛",
    "妈的", "tmd", "我擦", "卧槽",
    "停一下", "停", "等等", "打住",
    # --- English: explicit correction ---
    "no,", "no ", "wrong", "actually", "i meant", "i mean", "that's not",
    "thats not", "incorrect", "but no", "no it", "actually no",
    # --- English: frustration / sarcasm ---
    "wtf", "wth", "what the", "ffs", "seriously?", "really?",
    "are you serious", "are you kidding", "you don't get it",
    "you don't understand", "stop", "wait", "hold on",
    "no no no", "ugh",
)
CORRECTION_PREFIX_SCAN = 50  # chars from start

# Sub-second tail read of events.jsonl to determine whether agent was
# active in the last 5 minutes — used to BIND user_correction to a real
# prior decision instead of correcting nothing. Only edit_post +
# subagent_return events count as "agent did something visible".
PRIOR_ACTION_WINDOW_MINUTES = 5
PRIOR_ACTION_KINDS = ("edit_post", "subagent_return")
# Tail this many lines max — keeps the hook bounded.
PRIOR_ACTION_TAIL_LINES = 100


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


def _match_correction_phrase(text: str) -> str:
    """Return the FIRST CORRECTION_PHRASES match found in the prompt's first
    CORRECTION_PREFIX_SCAN chars (lowercased compare). Empty string = no match."""
    prefix = text[:CORRECTION_PREFIX_SCAN].lower().lstrip()
    for phrase in CORRECTION_PHRASES:
        if prefix.startswith(phrase):
            return phrase
    return ""


def _count_prior_actions() -> int:
    """Count edit_post / subagent_return events in last PRIOR_ACTION_WINDOW_MINUTES.

    Reads only the tail of events.jsonl (~100 lines) so cost is bounded.
    Returns 0 on any IO error (fail-open — false-negative beats hook hang).
    """
    events_file = _LOCAL_INTEL_DIR.parent.parent / "runs" / "local_intel" / "events.jsonl"
    if not events_file.is_file():
        return 0
    import time
    try:
        # Tail read: open + seek to last ~30KB (covers ~100 typical lines)
        with open(events_file, "rb") as f:
            f.seek(0, 2)
            end = f.tell()
            start = max(0, end - 30 * 1024)
            f.seek(start)
            raw = f.read().decode("utf-8", errors="ignore")
        lines = raw.splitlines()[-PRIOR_ACTION_TAIL_LINES:]
    except Exception:
        return 0
    cutoff_epoch = time.time() - PRIOR_ACTION_WINDOW_MINUTES * 60
    count = 0
    for line in lines:
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if obj.get("kind") not in PRIOR_ACTION_KINDS:
            continue
        ts_str = obj.get("ts", "")
        if not ts_str:
            continue
        # Lenient ISO 8601 parse; fall back to skipping line
        try:
            from datetime import datetime
            ts = datetime.fromisoformat(ts_str)
            if ts.timestamp() >= cutoff_epoch:
                count += 1
        except (ValueError, AttributeError):
            continue
    return count


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
        # If prompt opens with a correction phrase, emit additional event
        # for the user_correction insight detector. Bind to prior_actions
        # so detector can filter: a correction with prior_actions=0 likely
        # means "fresh conversation, user is just being curt", not "agent
        # screwed up".
        correction = _match_correction_phrase(text)
        if correction:
            event_writer.append(
                "user_correction",
                correction_phrase=correction,
                prompt_excerpt=text[:100],
                session_id=session_id,
                prior_actions_5min=_count_prior_actions(),
            )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
