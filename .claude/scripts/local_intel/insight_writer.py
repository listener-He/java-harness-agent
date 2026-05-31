#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""insight_writer — append API for insights.jsonl.

Schema: .claude/wiki/wiki/architecture/insights_layer_schema.md.

Append-only JSONL; status updates use a separate `status_change` record
rather than rewriting the original (preserves auditability).

Mirror of event_writer.py — silent on all IO errors so detectors can fire
without ever blocking the calling /h-context-check or /h-evolve flow.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
INSIGHTS_DIR = _REPO_ROOT / ".claude" / "runs" / "local_intel"
INSIGHTS_FILE = INSIGHTS_DIR / "insights.jsonl"

ROTATE_SIZE_BYTES = 5 * 1024 * 1024

VALID_KINDS = (
    "recurring_failure_cluster",
    "co_edit_cluster",
    "decayed_knowledge",
    "override_drift",
    "user_correction",
    "status_change",  # internal — produced by mark_status, not by detectors
)
VALID_CONFIDENCE = ("high", "medium", "low")
VALID_STATUS = ("new", "acknowledged", "acted_on", "published", "dismissed")


def _ts() -> str:
    s = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if len(s) >= 5 and s[-5] in "+-":
        return s[:-2] + ":" + s[-2:]
    return s if s else time.strftime("%Y-%m-%dT%H:%M:%S")


def _gen_id(kind: str, summary: str) -> str:
    """Deterministic short id from kind + summary — same insight = same id,
    so re-running a detector doesn't create duplicates."""
    h = hashlib.sha256(f"{kind}::{summary}".encode("utf-8")).hexdigest()
    return h[:10]


def _rotate_if_needed() -> None:
    try:
        if not INSIGHTS_FILE.exists():
            return
        if INSIGHTS_FILE.stat().st_size <= ROTATE_SIZE_BYTES:
            return
    except OSError:
        return
    date_suffix = time.strftime("%Y-%m-%d")
    target = INSIGHTS_FILE.with_name(f"{INSIGHTS_FILE.name}.{date_suffix}")
    n = 0
    while target.exists():
        n += 1
        target = INSIGHTS_FILE.with_name(f"{INSIGHTS_FILE.name}.{date_suffix}.{n}")
    try:
        INSIGHTS_FILE.rename(target)
    except OSError:
        pass


def _existing_ids() -> set[str]:
    """Return all insight ids currently in the file (excluding status_change rows).
    Used by append() to deduplicate: same kind+summary → same id → skip re-emit."""
    ids: set[str] = set()
    try:
        if not INSIGHTS_FILE.exists():
            return ids
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("kind") == "status_change":
                    continue
                rid = obj.get("id")
                if rid:
                    ids.add(rid)
    except OSError:
        pass
    return ids


def _write_record(record: dict) -> None:
    try:
        INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed()
        with open(INSIGHTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def append(kind: str, confidence: str, summary: str,
           suggested_action: str = "",
           evidence: list | None = None,
           detector: str = "",
           tags: list[str] | None = None,
           dedupe: bool = True,
           **extras) -> str:
    """Append an insight. Returns the assigned id (empty string on validation fail).

    dedupe=True (default): if same kind+summary already exists, skip write
    and return the existing id. This keeps detectors idempotent — running
    them N times produces 1 insight, not N.
    """
    if kind not in VALID_KINDS:
        return ""
    if confidence not in VALID_CONFIDENCE:
        return ""
    if not summary:
        return ""

    iid = _gen_id(kind, summary)
    if dedupe and iid in _existing_ids():
        return iid

    record = {
        "id": iid,
        "ts": _ts(),
        "kind": kind,
        "confidence": confidence,
        "summary": summary,
        "suggested_action": suggested_action,
        "evidence": evidence or [],
        "status": "new",
    }
    if detector:
        record["detector"] = detector
    if tags:
        record["tags"] = tags
    record.update(extras)
    _write_record(record)
    return iid


def mark_status(insight_id: str, new_status: str) -> bool:
    """Append a status_change record. Returns True iff a valid update queued.
    Caller is responsible for verifying the new status reflects in subsequent
    queries (status resolution merges last-wins per id)."""
    if not insight_id or new_status not in VALID_STATUS:
        return False
    record = {
        "id": insight_id,
        "ts": _ts(),
        "kind": "status_change",
        "status": new_status,
    }
    _write_record(record)
    return True


_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def query_active(top: int = 5, min_confidence: str = "medium") -> list[dict]:
    """Return active insights (status ∈ {new, acknowledged}) with confidence
    ≥ min_confidence, sorted by ts desc, capped at `top`.

    Resolves status by replaying status_change records: latest status per id wins.
    """
    min_rank = _CONFIDENCE_RANK.get(min_confidence, 1)
    insights: dict[str, dict] = {}
    status_overrides: dict[str, str] = {}
    if not INSIGHTS_FILE.is_file():
        return []
    try:
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                iid = obj.get("id")
                if not iid:
                    continue
                if obj.get("kind") == "status_change":
                    status_overrides[iid] = obj.get("status", "")
                else:
                    insights[iid] = obj
    except OSError:
        return []

    result = []
    for iid, ins in insights.items():
        status = status_overrides.get(iid, ins.get("status", "new"))
        # Active = not terminal. Terminal statuses: acted_on, published, dismissed.
        if status not in ("new", "acknowledged"):
            continue
        if _CONFIDENCE_RANK.get(ins.get("confidence", ""), -1) < min_rank:
            continue
        ins_out = dict(ins)
        ins_out["status"] = status  # apply resolved status
        result.append(ins_out)

    result.sort(key=lambda i: i.get("ts", ""), reverse=True)
    return result[:top]


def _cli() -> int:
    """Debug CLI — mostly for inspecting append / mark_status / query from terminal."""
    import argparse
    import sys
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append")
    a.add_argument("--kind", required=True)
    a.add_argument("--confidence", required=True)
    a.add_argument("--summary", required=True)
    a.add_argument("--suggested-action", default="")
    a.add_argument("--detector", default="")

    m = sub.add_parser("mark-status")
    m.add_argument("--id", required=True)
    m.add_argument("--status", required=True)

    q = sub.add_parser("query")
    q.add_argument("--top", type=int, default=5)
    q.add_argument("--min-confidence", default="medium",
                   choices=["low", "medium", "high"])
    q.add_argument("--json", action="store_true", dest="as_json")

    args = p.parse_args()
    if args.cmd == "append":
        iid = append(args.kind, args.confidence, args.summary,
                     suggested_action=args.suggested_action,
                     detector=args.detector)
        print(iid or "REJECTED", file=sys.stderr)
        return 0 if iid else 1
    if args.cmd == "mark-status":
        ok = mark_status(args.id, args.status)
        print("OK" if ok else "REJECTED", file=sys.stderr)
        return 0 if ok else 1
    if args.cmd == "query":
        results = query_active(top=args.top, min_confidence=args.min_confidence)
        if args.as_json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            if not results:
                print("(no active insights)", file=sys.stderr)
                return 0
            for ins in results:
                print(f"[{ins['confidence']:6s}] id={ins['id']} status={ins['status']}")
                print(f"  {ins['summary']}")
                if ins.get("suggested_action"):
                    print(f"  → {ins['suggested_action']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
