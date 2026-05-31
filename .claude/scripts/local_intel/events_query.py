#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""events_query — read .claude/runs/local_intel/events.jsonl with filters.

Agent-facing introspection CLI. Replaces the push-model context blocks
(`[triage-evidence]` / `[failure-memory]` / `[ambiguity]`) that used to be
injected on every prompt; agent now pulls when it actually needs context.

Filters (all combinable):
  --kind <k>          only events with this kind
  --file <path>       only events whose file_path equals or contains <path>
  --since <duration>  only events with ts >= now - duration (e.g. 30m, 1h, 7d)
  --last <N>          keep only the N most recent matching events
  --json              output JSON array (default: human-readable text)

Aggregation (separate from filters):
  --aggregate-by-kind     count events grouped by kind
  --aggregate-by-file     count events grouped by file_path

Exit codes:
  0 — query ran (may produce empty output)
  1 — invalid args or read failure

Rotated event files (events.jsonl.YYYY-MM-DD) are NOT read by default —
use --include-rotated to span them (slower).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
EVENTS_DIR = _REPO_ROOT / ".claude" / "runs" / "local_intel"
EVENTS_FILE = EVENTS_DIR / "events.jsonl"

DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$")


def _parse_duration(s: str) -> timedelta:
    """Parse '30m' / '2h' / '7d' / '60s' → timedelta. Raises ValueError on bad input."""
    m = DURATION_RE.match(s.strip().lower())
    if not m:
        raise ValueError(f"bad duration {s!r}; use forms like 30m, 2h, 7d, 60s")
    n, unit = int(m.group(1)), m.group(2)
    return {
        "s": timedelta(seconds=n),
        "m": timedelta(minutes=n),
        "h": timedelta(hours=n),
        "d": timedelta(days=n),
    }[unit]


def _parse_ts(ts_str: str) -> datetime | None:
    """Lenient ISO 8601 parse; returns None on failure."""
    if not ts_str:
        return None
    try:
        # Python 3.11+ fromisoformat handles +08:00; older versions are stricter.
        return datetime.fromisoformat(ts_str)
    except (ValueError, AttributeError):
        # Fallback: strip timezone and parse naive
        try:
            return datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None


def _iter_events(files: list[Path]):
    for p in files:
        if not p.is_file():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict) and "kind" in obj:
                        yield obj
        except OSError:
            continue


def _match(event: dict, kind: str | None, file_substr: str | None,
           min_ts: datetime | None) -> bool:
    if kind and event.get("kind") != kind:
        return False
    if file_substr:
        fp = event.get("file_path") or ""
        if file_substr not in fp:
            return False
    if min_ts is not None:
        ts = _parse_ts(event.get("ts", ""))
        if ts is None:
            return False
        # Make timezone-aware compare safe: drop tz if any side is naive.
        if ts.tzinfo and not min_ts.tzinfo:
            ts = ts.replace(tzinfo=None)
        elif min_ts.tzinfo and not ts.tzinfo:
            min_ts = min_ts.replace(tzinfo=None)
        if ts < min_ts:
            return False
    return True


def _format_text(events: list[dict]) -> str:
    """One event per line: ts kind k1=v1 k2=v2 ..."""
    lines = []
    for e in events:
        ts = e.get("ts", "")
        kind = e.get("kind", "")
        extras = []
        for k, v in e.items():
            if k in ("ts", "kind"):
                continue
            # Truncate long string values for legibility
            if isinstance(v, str) and len(v) > 80:
                v_display = v[:77] + "..."
            else:
                v_display = v
            if isinstance(v_display, str) and " " in v_display:
                v_display = json.dumps(v_display, ensure_ascii=False)
            extras.append(f"{k}={v_display}")
        lines.append(f"{ts}  {kind}  " + " ".join(extras))
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Query events.jsonl")
    p.add_argument("--kind", help="filter by event kind")
    p.add_argument("--file", dest="file_substr",
                   help="filter by file_path substring match")
    p.add_argument("--since", help="filter by ts >= now - <duration> (30m / 2h / 7d / 60s)")
    p.add_argument("--last", type=int, default=0,
                   help="keep only N most recent matching events (0 = all)")
    p.add_argument("--include-rotated", action="store_true",
                   help="also read rotated files events.jsonl.YYYY-MM-DD")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="output JSON array instead of text")
    p.add_argument("--aggregate-by-kind", action="store_true",
                   help="count events grouped by kind (overrides default output)")
    p.add_argument("--aggregate-by-file", action="store_true",
                   help="count events grouped by file_path (overrides default output)")
    args = p.parse_args()

    min_ts: datetime | None = None
    if args.since:
        try:
            delta = _parse_duration(args.since)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        min_ts = datetime.now() - delta

    files: list[Path] = [EVENTS_FILE]
    if args.include_rotated:
        files.extend(sorted(EVENTS_DIR.glob("events.jsonl.*")))

    matched = [
        e for e in _iter_events(files)
        if _match(e, args.kind, args.file_substr, min_ts)
    ]

    if args.last and args.last > 0:
        matched = matched[-args.last:]

    # Aggregation modes — short-circuit normal output.
    if args.aggregate_by_kind:
        counts = Counter(e.get("kind", "") for e in matched)
        if args.as_json:
            print(json.dumps(dict(counts), ensure_ascii=False))
        else:
            for k, n in counts.most_common():
                print(f"{n:6d}  {k}")
        return 0

    if args.aggregate_by_file:
        counts = Counter(e.get("file_path", "") for e in matched if e.get("file_path"))
        if args.as_json:
            print(json.dumps(dict(counts), ensure_ascii=False))
        else:
            for f, n in counts.most_common():
                print(f"{n:6d}  {f}")
        return 0

    # Default output: list events.
    if args.as_json:
        print(json.dumps(matched, ensure_ascii=False, indent=2))
    else:
        if not matched:
            print("(no events matched)", file=sys.stderr)
            return 0
        print(_format_text(matched))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
