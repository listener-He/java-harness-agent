#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage Tracker — sidecar usage statistics for wiki / skill files.

Records access events to `.claude/runs/.usage/<sha1>.jsonl` (one file per
tracked target, append-only JSONL). Feeds `distill.py` scan_domain so the
librarian can DELETE wiki fragments that are *referenced* (refs > 0) but
not *used* (0 reads in 30 days) — the missing signal in T2's trust-tier
filter, which only catches dead-reference fragments.

Storage:
  .claude/runs/.usage/<sha1>.jsonl       per-file event log
  Each line:   {"ts": "2026-05-30T...", "action": "read"}
  sha1 = sha1(absolute-resolved-path)

Usage (CLI — typically invoked from post_read_hook.py):
  python3 usage_tracker.py track <path>          # append a read event
  python3 usage_tracker.py score <path>          # print read count in last 30d
  python3 usage_tracker.py score <path> --days 7
  python3 usage_tracker.py purge --days 180      # drop event files inactive >180d

Import (preferred for hook integration to skip a Python startup):
  import usage_tracker
  usage_tracker.track(path)
  count = usage_tracker.score(path, days=30)

Concurrency: append-only line writes are atomic on POSIX for small writes;
no locking needed for typical hook fire rates.

Quiet env: none — pure sink (track is silent; score prints int to stdout).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
USAGE_DIR = _REPO_ROOT / ".claude" / "runs" / ".usage"


def _key(path: str) -> str:
    """Stable sha1 over the resolved absolute path."""
    try:
        resolved = str(Path(path).resolve())
    except (OSError, ValueError):
        resolved = path
    return hashlib.sha1(resolved.encode("utf-8")).hexdigest()


def _jsonl_for(path: str) -> Path:
    return USAGE_DIR / f"{_key(path)}.jsonl"


def track(path: str, action: str = "read") -> bool:
    """Append a usage event for `path`. Returns True on success, False on error.

    Best-effort: silent on any IO failure (callers are hooks that must not
    fail tool execution).
    """
    if not path:
        return False
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    jsonl = _jsonl_for(path)
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "action": action,
    }
    try:
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def score(path: str, days: int = 30) -> int:
    """Count usage events for `path` in the last `days` days. 0 if no jsonl."""
    if not path:
        return 0
    jsonl = _jsonl_for(path)
    if not jsonl.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    count = 0
    try:
        with jsonl.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts = datetime.fromisoformat(obj.get("ts", ""))
                    if ts >= cutoff:
                        count += 1
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return 0
    return count


def purge(days: int = 180) -> int:
    """Delete jsonl files whose most recent event is older than `days` days.
    Returns number of files removed.
    """
    if not USAGE_DIR.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    for jsonl in USAGE_DIR.glob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            if mtime < cutoff:
                jsonl.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sidecar usage tracker for wiki / skills")
    sub = parser.add_subparsers(dest="cmd")

    t = sub.add_parser("track", help="Append a usage event")
    t.add_argument("path")
    t.add_argument("--action", default="read")

    s = sub.add_parser("score", help="Print usage count over last N days")
    s.add_argument("path")
    s.add_argument("--days", type=int, default=30)

    p = sub.add_parser("purge", help="Drop jsonl files inactive for N+ days")
    p.add_argument("--days", type=int, default=180)

    args = parser.parse_args()

    if args.cmd == "track":
        return 0 if track(args.path, args.action) else 1

    if args.cmd == "score":
        print(score(args.path, args.days))
        return 0

    if args.cmd == "purge":
        n = purge(args.days)
        print(f"Removed {n} inactive usage files (>{args.days}d)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
