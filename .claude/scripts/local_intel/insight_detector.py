#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""insight_detector — derive insights from events + failure_memory + incidents.

The 4 detectors are pure functions over their respective data sources.
Each returns a list of insight-shaped dicts; main() optionally writes
them via insight_writer.append (which dedupes by kind+summary hash).

  recurring_failure_cluster  : failure_memory grouped by (gate, pattern)
  co_edit_cluster            : events.jsonl edit_post grouped by proximity
  decayed_knowledge          : incidents/ + usage_tracker — unread files
  override_drift             : events.jsonl env_bypass — usage trends

Usage:
  python3 insight_detector.py                       # run all, stdout
  python3 insight_detector.py --detector co_edit    # only one
  python3 insight_detector.py --write               # also persist to insights.jsonl
  python3 insight_detector.py --json                # JSON output for piping
  python3 insight_detector.py --since 7d            # restrict event scan window

Exit 0 always (detector is a sensor, not a gate).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
EVENTS_FILE = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "events.jsonl"
FAILURE_MEMORY = _REPO_ROOT / ".claude" / "runs" / "local_intel" / "failure_memory.json"
INCIDENTS_DIR = _REPO_ROOT / ".claude" / "wiki" / "incidents"
USAGE_DIR = _REPO_ROOT / ".claude" / "runs" / ".usage"

_DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$")


# ----- shared helpers ------------------------------------------------------

def _parse_duration(s: str) -> timedelta:
    m = _DURATION_RE.match(s.strip().lower())
    if not m:
        raise ValueError(f"bad duration {s!r}")
    n, unit = int(m.group(1)), m.group(2)
    return {"s": timedelta(seconds=n), "m": timedelta(minutes=n),
            "h": timedelta(hours=n), "d": timedelta(days=n)}[unit]


def _parse_ts(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None


def _now_naive() -> datetime:
    return datetime.now()


def _iter_events(min_ts: datetime | None = None):
    """Yield events from events.jsonl (no rotated files for speed)."""
    if not EVENTS_FILE.is_file():
        return
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict) or "kind" not in obj:
                    continue
                if min_ts is not None:
                    ts = _parse_ts(obj.get("ts", ""))
                    if ts is None:
                        continue
                    if ts.tzinfo:
                        ts = ts.replace(tzinfo=None)
                    if ts < min_ts:
                        continue
                yield obj
    except OSError:
        return


def _load_failures() -> list[dict]:
    if not FAILURE_MEMORY.is_file():
        return []
    try:
        with open(FAILURE_MEMORY, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("failures", []) if isinstance(data, dict) else []
    except (OSError, json.JSONDecodeError):
        return []


def _confidence_by_count(count: int, h: int, m: int, l: int) -> str | None:
    """Return high/medium/low/None given count + 3 thresholds."""
    if count >= h:
        return "high"
    if count >= m:
        return "medium"
    if count >= l:
        return "low"
    return None


# ----- Detector 1: recurring_failure_cluster -------------------------------

def detect_recurring_failure_clusters(failures: list[dict] | None = None,
                                      window_days: int = 30) -> list[dict]:
    if failures is None:
        failures = _load_failures()
    cutoff = _now_naive() - timedelta(days=window_days)

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for f in failures:
        ts = _parse_ts(f.get("ts", ""))
        if ts is None:
            continue
        if ts.tzinfo:
            ts = ts.replace(tzinfo=None)
        if ts < cutoff:
            continue
        key = (f.get("gate", ""), f.get("phase", ""), f.get("pattern", ""))
        grouped[key].append(f)

    insights = []
    for (gate, phase, pattern), items in grouped.items():
        count = len(items)
        confidence = _confidence_by_count(count, h=10, m=5, l=3)
        if confidence is None:
            continue
        # Compute days-span
        timestamps = sorted(filter(None, (_parse_ts(it.get("ts", "")) for it in items)))
        span_days = (timestamps[-1] - timestamps[0]).days if len(timestamps) >= 2 else 0

        insights.append({
            "kind": "recurring_failure_cluster",
            "confidence": confidence,
            "summary": (
                f"{gate or '<unknown>'} FAIL ×{count} in last {window_days}d "
                f"(pattern: {pattern[:60]})"
            ),
            "suggested_action": (
                f"Inspect {gate} threshold / pattern; consider widening "
                f"allowlist or refining gate predicate"
            ),
            "evidence": [
                {"kind": "failure", "gate": gate, "phase": phase,
                 "pattern": pattern[:200], "count": count, "span_days": span_days}
            ],
            "detector": "recurring_failure_cluster",
        })
    return insights


# ----- Detector 2: co_edit_cluster -----------------------------------------

def detect_co_edit_clusters(window_days: int = 30,
                            proximity_minutes: int = 30) -> list[dict]:
    """Files frequently edited within `proximity_minutes` of each other.

    Heuristic: bucket edits into proximity windows (any 30min sliding-ish
    grouping); count co-occurrence of file pairs across buckets. Files that
    pair ≥3 times become a candidate cluster.
    """
    min_ts = _now_naive() - timedelta(days=window_days)
    # Collect (ts, file_path) for edit_post events
    edits: list[tuple[datetime, str]] = []
    for ev in _iter_events(min_ts):
        if ev.get("kind") != "edit_post":
            continue
        ts = _parse_ts(ev.get("ts", ""))
        fp = ev.get("file_path", "")
        if ts is None or not fp:
            continue
        if ts.tzinfo:
            ts = ts.replace(tzinfo=None)
        edits.append((ts, fp))

    if len(edits) < 2:
        return []

    edits.sort()
    proximity = timedelta(minutes=proximity_minutes)

    # Sliding window: for each edit, find others within proximity_minutes
    pair_counts: Counter = Counter()
    n = len(edits)
    for i in range(n):
        ts_i, fp_i = edits[i]
        # files in same bucket
        bucket = {fp_i}
        j = i + 1
        while j < n and edits[j][0] - ts_i <= proximity:
            bucket.add(edits[j][1])
            j += 1
        # all unordered pairs in this bucket
        for a, b in combinations(sorted(bucket), 2):
            pair_counts[(a, b)] += 1

    insights = []
    # Identify pair clusters with count ≥ 3 and de-duplicate file overlap into bigger clusters
    qualifying = [(pair, c) for pair, c in pair_counts.items() if c >= 3]
    qualifying.sort(key=lambda x: -x[1])
    # Take top 5 pairs to avoid noise
    for (a, b), c in qualifying[:5]:
        confidence = _confidence_by_count(c, h=10, m=5, l=3)
        if confidence is None:
            continue
        insights.append({
            "kind": "co_edit_cluster",
            "confidence": confidence,
            "summary": f"{Path(a).name} + {Path(b).name} co-edited ×{c} in {window_days}d",
            "suggested_action": (
                f"If a task brief touches one of these, list both in Allowed Scope "
                f"upfront to avoid mid-implementation [Plan Invalidation]"
            ),
            "evidence": [
                {"kind": "files", "paths": [a, b], "co_edit_count": c,
                 "window_days": window_days}
            ],
            "detector": "co_edit_cluster",
        })
    return insights


# ----- Detector 3: decayed_knowledge ---------------------------------------

def detect_decayed_knowledge(decay_days: int = 90) -> list[dict]:
    """Wiki/incident files older than decay_days and not recently read."""
    insights = []
    now = time.time()
    decay_seconds = decay_days * 86400

    # Scan incidents/
    if INCIDENTS_DIR.is_dir():
        for p in INCIDENTS_DIR.glob("*.md"):
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            age_days = (now - mtime) / 86400
            if age_days < decay_days:
                continue
            # Check usage_tracker for last read
            last_read_days = _last_read_days(p)
            if last_read_days is None or last_read_days >= decay_days:
                confidence = _confidence_by_count(
                    int(min(age_days, last_read_days or age_days)),
                    h=180, m=90, l=60
                )
                if confidence is None:
                    continue
                insights.append({
                    "kind": "decayed_knowledge",
                    "confidence": confidence,
                    "summary": (
                        f"{p.name} unread {int(last_read_days or age_days)}d "
                        f"(age {int(age_days)}d)"
                    ),
                    "suggested_action": (
                        f"Review {p}: still relevant? Move to wiki/archive/ "
                        f"or refresh content"
                    ),
                    "evidence": [
                        {"kind": "file", "path": str(p),
                         "age_days": int(age_days),
                         "last_read_days": int(last_read_days) if last_read_days else None}
                    ],
                    "detector": "decayed_knowledge",
                })
    return insights


def _last_read_days(path: Path) -> float | None:
    """Look up days-since-last-read from usage_tracker sidecar. None if not tracked."""
    if not USAGE_DIR.is_dir():
        return None
    # usage_tracker key is the relative path with / replaced by __
    rel = path.relative_to(_REPO_ROOT) if path.is_absolute() else path
    key = str(rel).replace("/", "__")
    counter_file = USAGE_DIR / f"{key}.json"
    if not counter_file.is_file():
        return None
    try:
        data = json.loads(counter_file.read_text(encoding="utf-8"))
        last_ts = data.get("last_read") or data.get("last_access") or ""
        if not last_ts:
            return None
        last = _parse_ts(last_ts)
        if last is None:
            return None
        if last.tzinfo:
            last = last.replace(tzinfo=None)
        return (datetime.now() - last).days
    except (OSError, json.JSONDecodeError):
        return None


# ----- Detector 4: override_drift ------------------------------------------

def detect_override_drift(window_days: int = 30) -> list[dict]:
    min_ts = _now_naive() - timedelta(days=window_days)
    counts: Counter = Counter()
    file_contexts: dict[str, Counter] = defaultdict(Counter)
    for ev in _iter_events(min_ts):
        if ev.get("kind") != "env_bypass":
            continue
        var = ev.get("env_var", "")
        if not var:
            continue
        counts[var] += 1
        fp = ev.get("file_path") or ""
        if fp:
            file_contexts[var][fp] += 1

    insights = []
    for var, c in counts.most_common():
        confidence = _confidence_by_count(c, h=10, m=5, l=3)
        if confidence is None:
            continue
        top_files = [f for f, _ in file_contexts[var].most_common(3)]
        ctx = f"; top contexts: {', '.join(Path(f).name for f in top_files)}" if top_files else ""
        insights.append({
            "kind": "override_drift",
            "confidence": confidence,
            "summary": f"{var} used ×{c} in last {window_days}d{ctx}",
            "suggested_action": (
                f"If usage is sustained, the gate {var} bypasses may be too strict "
                f"— review the underlying gate's predicate or scope"
            ),
            "evidence": [
                {"kind": "env_bypass", "env_var": var, "count": c,
                 "top_files": top_files, "window_days": window_days}
            ],
            "detector": "override_drift",
        })
    return insights


# ----- CLI orchestration ----------------------------------------------------

DETECTORS = {
    "recurring_failure_cluster": detect_recurring_failure_clusters,
    "co_edit_cluster": detect_co_edit_clusters,
    "decayed_knowledge": detect_decayed_knowledge,
    "override_drift": detect_override_drift,
}


def main() -> int:
    p = argparse.ArgumentParser(description="Run insight detectors")
    p.add_argument("--detector", choices=list(DETECTORS.keys()),
                   help="run only this detector (default: all)")
    p.add_argument("--since", help="window override (e.g. 7d, 30d); detector default if omitted")
    p.add_argument("--write", action="store_true",
                   help="append generated insights to insights.jsonl via insight_writer")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="emit JSON array instead of text")
    args = p.parse_args()

    selected = [args.detector] if args.detector else list(DETECTORS.keys())

    all_insights: list[dict] = []
    for name in selected:
        fn = DETECTORS[name]
        try:
            # Pass --since to detectors that take a window_days kwarg
            if args.since and name in ("co_edit_cluster", "override_drift",
                                       "recurring_failure_cluster"):
                days = _parse_duration(args.since).days or 1
                all_insights.extend(fn(window_days=days))
            elif args.since and name == "decayed_knowledge":
                days = _parse_duration(args.since).days or 1
                all_insights.extend(fn(decay_days=days))
            else:
                all_insights.extend(fn())
        except Exception as e:
            print(f"detector {name} failed: {e}", file=sys.stderr)

    if args.write:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import insight_writer  # noqa: E402
            for ins in all_insights:
                insight_writer.append(
                    kind=ins["kind"],
                    confidence=ins["confidence"],
                    summary=ins["summary"],
                    suggested_action=ins.get("suggested_action", ""),
                    evidence=ins.get("evidence", []),
                    detector=ins.get("detector", ""),
                )
        except Exception as e:
            print(f"write failed: {e}", file=sys.stderr)

    if args.as_json:
        print(json.dumps(all_insights, ensure_ascii=False, indent=2))
    else:
        if not all_insights:
            print("(no insights detected)", file=sys.stderr)
            return 0
        for ins in all_insights:
            print(f"[{ins['confidence']:6s}] {ins['kind']:30s} {ins['summary']}")
            if ins.get("suggested_action"):
                print(f"           → {ins['suggested_action']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
