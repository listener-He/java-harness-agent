#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Failure Pattern Memory
Cross-session, append-only failure history. Pure Python stdlib.

Accumulates gate failures, phase rollbacks, and LLM self-reported errors.
At session start, the pre_hook queries similar past failures to warn the agent
before it makes the same mistake.

Storage: .claude/runs/local_intel/failure_memory.json (gitignored via .claude/runs/)
Max records: 500 (FIFO eviction)

Usage:
  # Record a gate failure
  python3 failure_memory.py --record \
    --intent Change --profile STANDARD --phase QA \
    --gate linter.py --pattern "missing Javadoc on public method" \
    --task-id "Change:STANDARD:order_service:20260517"

  # Query before starting similar work
  python3 failure_memory.py --query --intent Change --phase Implement

  # Show statistics
  python3 failure_memory.py --stats

  # Record a success (to track what worked)
  python3 failure_memory.py --record-success \
    --intent Change --profile PATCH --phase QA \
    --note "Slim spec + 1 file change cleared all gates cleanly"

Exit codes: 0=ok, 1=no data, 2=error
"""

import argparse
import json
import os
import sys
from datetime import datetime

MEMORY_PATH = ".claude/runs/local_intel/failure_memory.json"
MAX_RECORDS = 500


def _load() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {"failures": [], "successes": []}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # Migrate old format
            data = {"failures": data, "successes": []}
        return data
    except (json.JSONDecodeError, OSError):
        return {"failures": [], "successes": []}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    # FIFO eviction per category
    for key in ("failures", "successes"):
        if len(data.get(key, [])) > MAX_RECORDS:
            data[key] = data[key][-MAX_RECORDS:]
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_failure(intent: str, profile: str, phase: str,
                   gate: str, pattern: str, task_id: str = "") -> None:
    data = _load()
    data["failures"].append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": "failure",
        "intent": intent,
        "profile": profile,
        "phase": phase,
        "gate": gate,
        "pattern": pattern,
        "task_id": task_id,
    })
    _save(data)


def record_success(intent: str, profile: str, phase: str, note: str) -> None:
    data = _load()
    data["successes"].append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": "success",
        "intent": intent,
        "profile": profile,
        "phase": phase,
        "note": note,
    })
    _save(data)


def _match_score(record: dict, intent: str, phase: str, profile: str) -> int:
    score = 0
    if record.get("intent") == intent:
        score += 3
    if record.get("phase") == phase:
        score += 2
    if profile and record.get("profile") == profile:
        score += 1
    return score


def query_failures(intent: str, phase: str, profile: str = "",
                   top_k: int = 5) -> list[dict]:
    data = _load()
    scored = [
        (r, _match_score(r, intent, phase, profile))
        for r in data["failures"]
        if _match_score(r, intent, phase, profile) > 0
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in scored[:top_k]]


def stats() -> dict:
    data = _load()
    failures = data["failures"]
    phase_counts: dict[str, int] = {}
    gate_counts: dict[str, int] = {}
    pattern_counts: dict[str, int] = {}

    for r in failures:
        ph = r.get("phase", "?")
        phase_counts[ph] = phase_counts.get(ph, 0) + 1
        gt = r.get("gate", "?")
        gate_counts[gt] = gate_counts.get(gt, 0) + 1
        pat = r.get("pattern", "?")
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1

    top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_gates = sorted(gate_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_failures": len(failures),
        "total_successes": len(data["successes"]),
        "by_phase": phase_counts,
        "top_gates": top_gates,
        "top_patterns": top_patterns,
    }


def summary(days: int = 30, min_count: int = 2, top: int = 5) -> list[dict]:
    """Aggregate recurring failures over the last `days` days.

    Returns entries with count >= min_count, sorted by count desc, capped at top.
    """
    from datetime import timedelta

    data = _load()
    cutoff = datetime.now() - timedelta(days=days)
    buckets: dict[tuple, dict] = {}

    for r in data["failures"]:
        try:
            ts = datetime.fromisoformat(r.get("ts", ""))
        except ValueError:
            continue
        if ts < cutoff:
            continue
        key = (r.get("phase", "?"), r.get("gate", ""), r.get("pattern", "?"))
        if key not in buckets:
            buckets[key] = {
                "phase": key[0],
                "gate": key[1],
                "pattern": key[2],
                "count": 0,
                "last_ts": ts,
            }
        buckets[key]["count"] += 1
        if ts > buckets[key]["last_ts"]:
            buckets[key]["last_ts"] = ts

    recurring = [b for b in buckets.values() if b["count"] >= min_count]
    recurring.sort(key=lambda b: (-b["count"], b["last_ts"].timestamp() * -1))
    for b in recurring:
        b["last_ts"] = b["last_ts"].strftime("%Y-%m-%d")
    return recurring[:top]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local cross-session failure pattern memory"
    )
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("record", help="Record a gate/phase failure")
    rec.add_argument("--intent", default="Change")
    rec.add_argument("--profile", default="")
    rec.add_argument("--phase", required=True)
    rec.add_argument("--gate", default="")
    rec.add_argument("--pattern", required=True)
    rec.add_argument("--task-id", default="")

    suc = sub.add_parser("record-success", help="Record a successful approach")
    suc.add_argument("--intent", default="Change")
    suc.add_argument("--profile", default="")
    suc.add_argument("--phase", required=True)
    suc.add_argument("--note", required=True)

    qry = sub.add_parser("query", help="Find similar past failures")
    qry.add_argument("--intent", default="Change")
    qry.add_argument("--phase", required=True)
    qry.add_argument("--profile", default="")
    qry.add_argument("--top", type=int, default=5)
    qry.add_argument("--json", action="store_true", dest="as_json")

    st = sub.add_parser("stats", help="Show failure statistics")
    st.add_argument("--json", action="store_true", dest="as_json")

    sm = sub.add_parser("summary",
                        help="Top recurring failures over last N days (for hook injection)")
    sm.add_argument("--days", type=int, default=30)
    sm.add_argument("--min-count", type=int, default=2,
                    help="only include patterns that recurred at least N times")
    sm.add_argument("--top", type=int, default=5)
    sm.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args()

    if args.cmd == "record":
        record_failure(args.intent, args.profile, args.phase,
                       args.gate, args.pattern, args.task_id)
        print(f"Recorded: [{args.phase}/{args.gate}] {args.pattern}")
        return 0

    if args.cmd == "record-success":
        record_success(args.intent, args.profile, args.phase, args.note)
        print(f"Recorded success: [{args.phase}] {args.note[:80]}")
        return 0

    if args.cmd == "query":
        results = query_failures(args.intent, args.phase, args.profile, args.top)
        if args.as_json:
            print(json.dumps(results))
            return 0 if results else 1
        if not results:
            print("No similar past failures found.")
            return 1
        print(f"Past failures similar to [{args.intent}/{args.phase}]:")
        for r in results:
            print(f"  [{r['ts'][:10]}] {r['phase']}/{r.get('gate','?')}: {r['pattern']}")
        return 0

    if args.cmd == "stats":
        s = stats()
        if args.as_json:
            print(json.dumps(s))
        else:
            print(f"Failures: {s['total_failures']} | Successes: {s['total_successes']}")
            print("By phase:", s["by_phase"])
            print("Top gates:", s["top_gates"])
            print("Top patterns:", s["top_patterns"])
        return 0

    if args.cmd == "summary":
        items = summary(args.days, args.min_count, args.top)
        if args.as_json:
            print(json.dumps(items))
            return 0 if items else 1
        if not items:
            return 1
        for it in items:
            gate_part = f"/{it['gate']}" if it['gate'] else ""
            print(f"- ×{it['count']} {it['phase']}{gate_part}: "
                  f"{it['pattern']} (last {it['last_ts']})")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
