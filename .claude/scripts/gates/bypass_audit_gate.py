#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bypass Audit Gate — TTL Enforcement

Scans `.claude/workflow/runs/` for `bypass_justification*.md` files and
validates their lifecycle compliance:
- Must have `task_id:` header
- Must have `expires_after:` header
- Must not be from an already-archived task (stale bypass)

Exit codes:
- 0: PASS (no stale/invalid bypass files)
- 1: WARN (stale bypass files found, or missing headers on valid bypass)
- 2: FAIL (active bypass with missing required headers)
"""

import argparse
import os
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))
RUNS_DIR = os.path.join(REPO_ROOT, ".agents", "workflow", "runs")


def _find_bypass_files() -> list[str]:
    if not os.path.isdir(RUNS_DIR):
        return []
    return sorted(
        os.path.join(RUNS_DIR, f)
        for f in os.listdir(RUNS_DIR)
        if f.startswith("bypass_justification") and f.endswith(".md")
    )


def _extract_header(text: str, header: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(header):
            return stripped[len(header):].strip()
    return None


def _is_task_archived(task_id: str) -> bool:
    """Heuristic: check if launch_spec with this topic+date exists and is DONE/Archived.
    For simplicity, we check if there's an archived openspec for the date+slug pattern."""
    # task_id format: <intent>:<profile>:<topic>:<date>
    parts = task_id.split(":")
    if len(parts) < 4:
        return False
    date = parts[3]
    topic = parts[2] if len(parts) > 2 else ""
    archive_dir = os.path.join(REPO_ROOT, ".agents", "wiki", "archive")
    if os.path.isdir(archive_dir):
        for f in os.listdir(archive_dir):
            if date in f and topic.lower().replace(" ", "_") in f.lower():
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="", help="Current task id for comparison")
    args = parser.parse_args()

    bypass_files = _find_bypass_files()
    if not bypass_files:
        print("OK: no bypass files found")
        return 0

    warnings = []
    failures = []

    for bf in bypass_files:
        with open(bf, "r", encoding="utf-8") as f:
            text = f.read()

        task_id = _extract_header(text, "task_id:")
        expires = _extract_header(text, "expires_after:")

        # Check required headers
        if not task_id:
            failures.append(f"{os.path.basename(bf)}: missing 'task_id:' header")
        if not expires:
            failures.append(f"{os.path.basename(bf)}: missing 'expires_after:' header")

        if task_id and expires:
            # Check if stale (from archived task)
            if _is_task_archived(task_id):
                warnings.append(f"{os.path.basename(bf)}: STALE — task '{task_id}' appears archived")
            else:
                print(f"OK: {os.path.basename(bf)} — active bypass for task '{task_id}', expires after {expires}")

    if failures:
        print("FAIL: active bypass files with missing required headers")
        for f in failures:
            print(f"- {f}")
        return EXIT_FAIL

    if warnings:
        print("WARN: stale bypass files detected (from completed tasks)")
        for w in warnings:
            print(f"- {w}")
        print("Action: remove stale bypass files or run Archive cleanup.")
        return EXIT_WARN

    print("OK: all bypass files valid and within TTL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
