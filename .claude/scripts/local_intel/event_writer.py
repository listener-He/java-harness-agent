#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""event_writer — JSONL append API for the unified event stream.

Schema lives at .claude/wiki/wiki/architecture/wal/20260531_events_jsonl_schema.md.

Design contract:
  - append(kind, **fields) → None, silent on all IO errors (hook safety)
  - File location: .claude/runs/local_intel/events.jsonl (relative to repo root)
  - Rotation: when file > 10MB pre-write, rename to events.jsonl.<YYYY-MM-DD>
    (with .1/.2/... if same-day rotation already happened); new empty file
    takes its place.
  - Schema not enforced — writer is dumb on purpose. Schema discipline lives
    in the doc + caller code review.

Why silent: this is called from PreToolUse / PostToolUse / UserPromptSubmit /
SubagentStop / Stop / Notification / PreCompact hooks. Any exception bubbling
out would abort the user's tool call or pollute their UI. Hooks must never
fail closed for analytics.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

# Resolve repo root from this script's location, not from cwd — hooks run
# with whatever cwd Claude Code chose, often the project root but not always.
_REPO_ROOT = Path(__file__).resolve().parents[3]
EVENTS_DIR = _REPO_ROOT / ".claude" / "runs" / "local_intel"
EVENTS_FILE = EVENTS_DIR / "events.jsonl"

# Rotation threshold. 10MB chosen to balance file scan cost vs rotation churn.
ROTATE_SIZE_BYTES = 10 * 1024 * 1024


def _ts() -> str:
    """ISO 8601 with local timezone. Always succeeds; uses fallback if %z empty."""
    s = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if not s.endswith(("+0000",)) and len(s) >= 5 and (s[-5] in "+-"):
        # Insert ':' to make ISO format strict (+0800 → +08:00)
        return s[:-2] + ":" + s[-2:]
    return s if s else time.strftime("%Y-%m-%dT%H:%M:%S")


def _rotate_if_needed() -> None:
    """If events.jsonl > 10MB, rename to dated suffix; new empty file takes over."""
    try:
        if not EVENTS_FILE.exists():
            return
        if EVENTS_FILE.stat().st_size <= ROTATE_SIZE_BYTES:
            return
    except OSError:
        return

    date_suffix = time.strftime("%Y-%m-%d")
    base_rotated = EVENTS_FILE.with_name(f"{EVENTS_FILE.name}.{date_suffix}")
    target = base_rotated
    n = 0
    # If today's rotated file already exists, append .1/.2/...
    while target.exists():
        n += 1
        target = EVENTS_FILE.with_name(f"{EVENTS_FILE.name}.{date_suffix}.{n}")
    try:
        EVENTS_FILE.rename(target)
    except OSError:
        # If rotation fails, fall through — caller will still try to append.
        return


def append(kind: str, **fields) -> None:
    """Append one event to events.jsonl. Silent on all IO failures.

    Args:
        kind: event type (required, free-form string per schema doc)
        **fields: arbitrary kwargs merged into the record. Caller is
                  responsible for keeping values JSON-serializable.

    The record gains `ts` (ISO 8601 with timezone) automatically; if `ts` is
    in fields, the caller's value wins (mostly for testing).
    """
    if not kind:
        return
    record = {"ts": _ts(), "kind": kind}
    record.update(fields)
    try:
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed()
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        # Silent: never propagate to caller.
        pass


# Optional convenience: invoke from CLI for ad-hoc testing/debug. Not the
# primary surface — hooks should import and call `append` directly.
def _cli() -> int:
    import argparse
    import sys
    p = argparse.ArgumentParser(description="Append an event for debugging.")
    p.add_argument("kind", help="event kind")
    p.add_argument("--field", action="append", default=[],
                   metavar="KEY=VALUE",
                   help="kwargs, repeat as needed (value parsed as JSON if possible)")
    args = p.parse_args()

    fields = {}
    for kv in args.field:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        try:
            fields[k] = json.loads(v)
        except json.JSONDecodeError:
            fields[k] = v
    append(args.kind, **fields)
    print(f"appended kind={args.kind} fields={fields}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
