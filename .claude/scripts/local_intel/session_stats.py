#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Stats — per-session counters feeding the reflect-threshold heuristic.

Tracks edit count, unique files touched, and recorded failures since the
last `reset`. The Stop hook reads these via `reflect_threshold.py` to
decide whether to nudge the user toward `/h-reflect`.

Storage: .claude/runs/local_intel/session_stats.json (gitignored via
.claude/runs/ per policy.md). Pure stdlib; atomic writes.

Usage:
  python3 session_stats.py bump edit <file-path>   # increment edits + add path to files set
  python3 session_stats.py bump failure             # increment failure counter (in-process call from failure_memory)
  python3 session_stats.py read [--json]            # show current counters
  python3 session_stats.py reset                    # zero counters; stamp last_reflect_ts=now

Concurrency: Claude Code hook invocations are sequential; no locking needed.
Atomic write (tmpfile + os.replace) guards against partial-state on Ctrl-C.

Quiet env: none — this script is purely a counter sink. Reads/output happen
only on explicit `read`. Hooks invoking `bump` see zero stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
STATS_PATH = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "session_stats.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _empty() -> dict:
    ts = _now()
    return {
        "edits": 0,
        "files": [],
        "failures": 0,
        "session_start": ts,
        "last_reflect_ts": ts,
    }


def _load() -> dict:
    if not STATS_PATH.exists():
        return _empty()
    try:
        return json.loads(STATS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty()


def _save(data: dict) -> None:
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(STATS_PATH.parent),
        prefix=".session_stats.", suffix=".tmp", delete=False,
    ) as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        tmpname = tf.name
    os.replace(tmpname, STATS_PATH)


def bump_edit(file_path: str) -> dict:
    data = _load()
    data["edits"] = int(data.get("edits", 0)) + 1
    files = list(data.get("files", []))
    if file_path and file_path not in files:
        files.append(file_path)
    data["files"] = files
    _save(data)
    return data


def bump_failure() -> dict:
    data = _load()
    data["failures"] = int(data.get("failures", 0)) + 1
    _save(data)
    return data


def reset() -> dict:
    data = _empty()
    _save(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-session counters for reflect-threshold")
    sub = parser.add_subparsers(dest="cmd")

    b = sub.add_parser("bump", help="Increment a counter")
    b.add_argument("metric", choices=["edit", "failure"])
    b.add_argument("file_path", nargs="?", default="",
                   help="for `bump edit`: the path that was edited")

    r = sub.add_parser("read", help="Print current stats")
    r.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("reset", help="Clear counters; stamp last_reflect_ts=now")

    args = parser.parse_args()

    if args.cmd == "bump":
        if args.metric == "edit":
            bump_edit(args.file_path)
        else:
            bump_failure()
        return 0

    if args.cmd == "read":
        data = _load()
        if args.as_json:
            print(json.dumps(data, ensure_ascii=False))
        else:
            print(f"edits={data.get('edits', 0)} "
                  f"files={len(data.get('files', []))} "
                  f"failures={data.get('failures', 0)} "
                  f"last_reflect={data.get('last_reflect_ts', '?')}")
        return 0

    if args.cmd == "reset":
        reset()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
