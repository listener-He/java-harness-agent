#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SubagentStop hook.

When a sub-agent finishes, automatically run subagent_return_gate.py on its
final output and inject WARN/FAIL findings into the main agent's context.

Why this exists: dispatch-template.md mandates the gate run after every
sub-agent return, but relies on the main agent to invoke it. Honest take —
agents skip the gate when busy. This hook makes the check enforceable while
remaining non-blocking (exit 0 always, only injects context).

Payload discovery (Claude Code SubagentStop hook):
  We don't hardcode field names. Try transcript_path first (most reliable),
  then a list of common payload fields. If none yield text, dump the payload
  to .claude/runs/local_intel/last_subagent_payload.json for debugging so the
  hook author can adjust the field list on the next pass — silent failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _HARNESS_DIR.parent.parent.parent
RETURN_GATE = str(_HARNESS_DIR.parent / "gates" / "subagent_return_gate.py")
DEBUG_DUMP = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "last_subagent_payload.json"

# Common payload field names we'll try in order.
TEXT_FIELDS = ("response", "output", "text", "content", "message",
               "final_message", "subagent_output", "result")

# transcript_path is a JSONL file; read the last assistant message.
TRANSCRIPT_FIELDS = ("transcript_path", "transcript", "transcript_file")


def _read_last_assistant_from_transcript(path: Path) -> str:
    """Best-effort extract of the last assistant message from a JSONL transcript."""
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
        # Try common shapes: {role: assistant, content: "..."} or
        # {type: assistant, message: {content: [...]}} or {message: {role: ..., content: ...}}.
        role = obj.get("role") or obj.get("type") or ""
        if "assistant" not in str(role).lower():
            # Some formats nest inside "message"
            inner = obj.get("message") or {}
            if isinstance(inner, dict):
                role = inner.get("role") or inner.get("type") or ""
                if "assistant" not in str(role).lower():
                    continue
                obj = inner
            else:
                continue
        # Content might be a string or a list of {type: "text", text: "..."} parts.
        content = obj.get("content")
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


def _extract_return_text(payload: dict) -> str:
    for k in TRANSCRIPT_FIELDS:
        v = payload.get(k)
        if isinstance(v, str) and v:
            p = Path(v)
            if p.exists():
                text = _read_last_assistant_from_transcript(p)
                if text:
                    return text
    for k in TEXT_FIELDS:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # Some payloads nest under "subagent" or "agent"
    for outer in ("subagent", "agent", "tool_result"):
        inner = payload.get(outer)
        if isinstance(inner, dict):
            for k in TEXT_FIELDS:
                v = inner.get(k)
                if isinstance(v, str) and v.strip():
                    return v
    return ""


def main() -> int:
    if os.environ.get("CLAUDE_SUBAGENT_RETURN_QUIET") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    text = _extract_return_text(payload)
    if not text:
        try:
            DEBUG_DUMP.parent.mkdir(parents=True, exist_ok=True)
            with open(DEBUG_DUMP, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        return 0

    try:
        proc = subprocess.run(
            [sys.executable, RETURN_GATE, "--return-stdin"],
            input=text, check=False, capture_output=True, text=True,
        )
    except Exception:
        return 0

    # 0 = OK silent. 1 = WARN. 2 = FAIL. We always exit 0 (non-blocking).
    if proc.returncode == 0:
        return 0
    severity = "WARN" if proc.returncode == 1 else "FAIL"
    print(f"[subagent-return] {severity} — sub-agent return failed validation:")
    out = (proc.stdout or proc.stderr or "").rstrip()
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
