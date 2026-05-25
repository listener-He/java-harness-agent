#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impact Analysis Gate
Uses the local code index to detect files impacted by a change but absent
from the task_brief's Allowed Scope. Prevents silent blast-radius under-estimation.

Requires: code_index.py --build has been run at least once.

Exit codes:
  0 = PASS  (all impacted files are in scope, or no index exists)
  1 = WARN  (out-of-scope impacts found, non-blocking for LOW/TRIVIAL)
  2 = FAIL  (out-of-scope impacts found, blocking for MEDIUM/HIGH)

Integration:
  - Called by run.py when artifact-tag 'impact' is present
  - Also useful to run manually before finalizing a focus card
  - PreToolUse `scope_guard.py` is the live enforcement gate; this script is
    a manual / orchestration-time impact checker
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EXIT_WARN = 1
EXIT_FAIL = 2

INDEX_PATH = ".claude/runs/local_intel/code_index.json"
CODE_INDEX_SCRIPT = ".claude/scripts/local_intel/code_index.py"


def _load_index() -> dict | None:
    if not os.path.exists(INDEX_PATH):
        return None
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_focus_scope(task_brief: str) -> list[str]:
    try:
        with open(task_brief, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []
    in_section = False
    prefixes: list[str] = []
    for line in content.splitlines():
        if line.strip() == "## Allowed Scope":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("-"):
            v = line.strip().lstrip("-").strip()
            if v:
                prefixes.append(v.rstrip("/"))
    return prefixes


def _in_scope(file_path: str, prefixes: list[str]) -> bool:
    norm = file_path.replace("\\", "/")
    return any(norm.startswith(p) for p in prefixes)


def _impact_of(file_path: str, index: dict) -> list[str]:
    """Inline copy of code_index.impact_of to avoid import path issues."""
    norm = file_path.replace("\\", "/")
    owned = index["file_symbols"].get(norm, [])
    class_names = {q.split(".")[0] for q in owned if "." in q}
    method_names = {q.split(".")[-1] for q in owned if "." in q}

    if not class_names:
        class_names = {Path(norm).stem}

    importers: set[str] = set()
    for cls in class_names:
        importers.update(index["reverse_imports"].get(cls, []))

    callers: set[str] = set()
    for m in method_names:
        callers.update(index["reverse_calls"].get(m, []))

    return sorted((importers | callers) - {norm})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Impact analysis gate: detect out-of-scope blast radius"
    )
    parser.add_argument("--task-brief", required=True)
    parser.add_argument("--changed-files", default="",
                        help="comma-separated list of changed files")
    parser.add_argument("--risk", default="LOW",
                        choices=["TRIVIAL", "LOW", "MEDIUM", "HIGH"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if not os.path.exists(args.task_brief):
        print(f"FAIL: task_brief not found: {args.task_brief}")
        return EXIT_FAIL

    index = _load_index()
    if index is None:
        print("WARN: code index not found — run code_index.py --build to enable impact analysis")
        print("      Skipping impact gate (non-blocking).")
        return EXIT_WARN

    scope = _read_focus_scope(args.task_brief)
    if not scope:
        print("WARN: task_brief has no Allowed Scope entries — cannot enforce impact boundary")
        return EXIT_WARN

    changed = [
        f.strip().replace("\\", "/")
        for f in args.changed_files.split(",")
        if f.strip()
    ]
    if not changed:
        print("OK: no changed files provided — skipping impact analysis")
        return 0

    all_impacted: set[str] = set()
    for cf in changed:
        all_impacted.update(_impact_of(cf, index))

    out_of_scope = sorted(f for f in all_impacted if not _in_scope(f, scope))

    result = {
        "changed": changed,
        "total_impacted": len(all_impacted),
        "out_of_scope": out_of_scope,
        "risk": args.risk,
    }

    if args.as_json:
        print(json.dumps(result))

    if not out_of_scope:
        if not args.as_json:
            print(f"OK: impact gate pass — {len(all_impacted)} impacted files, all in scope")
        return 0

    if not args.as_json:
        print(f"Impact gate: {len(out_of_scope)} potentially impacted files outside task_brief scope:")
        for f in out_of_scope[:10]:
            print(f"  {f}")
        if len(out_of_scope) > 10:
            print(f"  ... and {len(out_of_scope) - 10} more")
        print(f"  Scope prefixes: {scope[:3]}")

    if args.risk in ("HIGH", "MEDIUM"):
        if not args.as_json:
            print("FAIL: MEDIUM/HIGH risk — expand task_brief scope or file a [Boundary Exception Request]")
        return EXIT_FAIL

    if not args.as_json:
        print("WARN: LOW/TRIVIAL risk — review whether these callers need updates (non-blocking)")
    return EXIT_WARN


if __name__ == "__main__":
    raise SystemExit(main())
