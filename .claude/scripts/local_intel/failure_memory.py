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
import re
import sys
from datetime import datetime
from pathlib import Path

# Resolve repo-relative paths against this file's location so the script
# works regardless of the caller's CWD (UserPromptSubmit and PostToolUse
# hooks invoke us through subprocess from various directories).
_REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_PATH = str(_REPO_ROOT / ".claude" / "runs" / "local_intel" / "failure_memory.json")
MAX_RECORDS = 500
INCIDENTS_DIR = str(_REPO_ROOT / ".claude" / "wiki" / "incidents")


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


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_REMINDER_RE = re.compile(
    r"##\s*提醒未来\s*LLM\s*\n(.*?)(?=\n##\s|\Z)",
    re.DOTALL,
)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a minimal subset of YAML frontmatter (key: value lines)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def incidents_summary(days: int = 30, top: int = 5) -> list[dict]:
    """Read .claude/wiki/incidents/*.md, return recent entries.

    Returns list of dicts with: date, slug, severity, status, reminder.
    Includes:
      - All files whose frontmatter date is within `days`
      - All files with status == "watch" (permanent)
    Sorted by date desc, capped at top.
    """
    d = Path(INCIDENTS_DIR)
    if not d.is_dir():
        return []
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).date()

    entries: list[dict] = []
    for p in d.glob("*.md"):
        # Skip docs: README, TEMPLATE, anything not following <date>_<slug>.md
        name = p.name
        if not re.match(r"^\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*\.md$", name):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        if not fm:
            continue
        try:
            d_obj = datetime.fromisoformat(fm.get("date", "")).date()
        except ValueError:
            continue
        status = fm.get("status", "").lower()
        if d_obj < cutoff and status != "watch":
            continue
        m = _REMINDER_RE.search(text)
        reminder = (m.group(1).strip() if m else "").splitlines()
        reminder_line = next((ln.strip() for ln in reminder if ln.strip()), "")
        # Strip leading markdown emphasis like **下次改这片代码时考虑：**
        reminder_line = re.sub(r"^\*\*[^*]+\*\*\s*[:：]?\s*", "", reminder_line)
        entries.append({
            "date": fm.get("date", ""),
            "slug": fm.get("slug", p.stem.split("_", 1)[-1]),
            "severity": fm.get("severity", "").upper() or "?",
            "status": status or "?",
            "reminder": reminder_line or "(no '提醒未来 LLM' line in record)",
            "path": str(p),
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries[:top]


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
    sm.add_argument("--include-incidents", action="store_true",
                    help="append a second section listing recent incidents from "
                         ".claude/wiki/incidents/")
    sm.add_argument("--json", action="store_true", dest="as_json")

    inc = sub.add_parser("incidents",
                         help="Standalone list of recent incidents (for tooling)")
    inc.add_argument("--days", type=int, default=30)
    inc.add_argument("--top", type=int, default=5)
    inc.add_argument("--json", action="store_true", dest="as_json")

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
        incidents = (incidents_summary(args.days, args.top)
                     if args.include_incidents else [])
        if args.as_json:
            payload = {"recurring": items, "incidents": incidents} \
                if args.include_incidents else items
            print(json.dumps(payload, ensure_ascii=False))
            return 0 if (items or incidents) else 1
        if not items and not incidents:
            return 1
        if items:
            print("recurring gate failures (last %dd):" % args.days)
            for it in items:
                gate_part = f"/{it['gate']}" if it['gate'] else ""
                print(f"- ×{it['count']} {it['phase']}{gate_part}: "
                      f"{it['pattern']} (last {it['last_ts']})")
        if incidents:
            if items:
                print()
            print("incidents (last %dd + status:watch):" % args.days)
            for it in incidents:
                print(f"- {it['date']} {it['severity']} {it['slug']} — "
                      f"{it['reminder']}")
        return 0

    if args.cmd == "incidents":
        items = incidents_summary(args.days, args.top)
        if args.as_json:
            print(json.dumps(items, ensure_ascii=False))
            return 0 if items else 1
        if not items:
            return 1
        for it in items:
            print(f"- {it['date']} {it['severity']} {it['slug']} — "
                  f"{it['reminder']}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
