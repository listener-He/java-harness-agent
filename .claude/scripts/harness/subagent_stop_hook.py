#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SubagentStop hook — pure sensor.

Phase P2 of the Sensor/Policy/Enforce refactor. Previously this hook ran
subagent_return_gate.py inline and injected WARN/FAIL findings into the
main agent's context. New model: emit the return text as an event; agent
runs the gate via /h-gates --phase ... when it decides validation is due.

We keep the (3-shape-aware) text extraction logic — that's the hard part,
and other consumers (notably /h-gates) need it. Just import it instead of
duplicating.

Failures: silent. Exit 0 always.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_LOCAL_INTEL_DIR = _HARNESS_DIR.parent / "local_intel"
_REPO_ROOT = _HARNESS_DIR.parent.parent.parent
DEBUG_DUMP = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "last_subagent_payload.json"

# Common payload field names — kept here (not events_query) because the
# extraction is part of the hook contract with Claude Code, not the agent
# query surface.
TEXT_FIELDS = ("response", "output", "text", "content", "message",
               "final_message", "subagent_output", "result")
TRANSCRIPT_FIELDS = ("transcript_path", "transcript", "transcript_file")

# Truncation cap per events.jsonl schema doc.
RETURN_TEXT_CAP = 4000


def _read_last_assistant_from_transcript(path: Path) -> str:
    """Best-effort extract of the last assistant message from a JSONL transcript.

    Supports 3 known shapes (locked by test_subagent_stop_hook.py):
      A: {role: assistant, content: "..."}                — flat
      B: {type: assistant, message: {content: [...]}}     — Claude Code current
      C: {message: {role: assistant, content: ...}}       — outer wrapper only
    """
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        outer_role = obj.get("role") or obj.get("type") or ""
        inner = obj.get("message") if isinstance(obj.get("message"), dict) else None

        if "assistant" in str(outer_role).lower():
            target = inner if (inner is not None and inner.get("content") is not None) else obj
        else:
            if inner is None:
                continue
            inner_role = inner.get("role") or inner.get("type") or ""
            if "assistant" not in str(inner_role).lower():
                continue
            target = inner

        content = target.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, dict):
                    t = p.get("text") or p.get("content") or ""
                    if isinstance(t, str):
                        parts.append(t)
                elif isinstance(p, str):
                    parts.append(p)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    return ""


def _extract_return_text(payload: dict) -> tuple[str, str]:
    """Return (text, transcript_path). Either may be empty.

    Returning transcript_path too so the event preserves it (agent can re-read
    later for full context beyond the 4000-char cap)."""
    for k in TRANSCRIPT_FIELDS:
        v = payload.get(k)
        if isinstance(v, str) and v:
            p = Path(v)
            if p.exists():
                text = _read_last_assistant_from_transcript(p)
                if text:
                    return text, str(v)
    for k in TEXT_FIELDS:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v, ""
    for outer in ("subagent", "agent", "tool_result"):
        inner = payload.get(outer)
        if isinstance(inner, dict):
            for k in TEXT_FIELDS:
                v = inner.get(k)
                if isinstance(v, str) and v.strip():
                    return v, ""
    return "", ""


def main() -> int:
    if os.environ.get("CLAUDE_SUBAGENT_RETURN_QUIET") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    text, transcript_path = _extract_return_text(payload)
    if not text:
        # Preserve the unknown payload shape for future debugging — same
        # mechanism as before, this is how we noticed shape B was broken.
        try:
            DEBUG_DUMP.parent.mkdir(parents=True, exist_ok=True)
            with open(DEBUG_DUMP, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        return 0

    # Sensor write: capture truncated text + transcript_path for agent
    # consumption via events_query.
    if str(_LOCAL_INTEL_DIR) not in sys.path:
        sys.path.insert(0, str(_LOCAL_INTEL_DIR))
    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "subagent_return",
            text=text[:RETURN_TEXT_CAP],
            transcript_path=transcript_path,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
