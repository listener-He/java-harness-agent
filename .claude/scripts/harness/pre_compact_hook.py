#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreCompact hook — snapshot harness state before context compression.

Fires when Claude Code is about to compact the conversation. Captures
"what's in flight" external state so the post-compact agent can recover
via /h-status or /h-resume without losing track of the active task.

Snapshot fields:
  - ts: ISO timestamp
  - branch: current git branch
  - head: short HEAD commit
  - dirty_files: count of uncommitted modifications
  - active_task_brief: path from find_active_task_brief.py (may be empty)
  - launch_spec_rows: every row of the latest launch_spec (slug/risk/phase/status)
  - recent_commits: last 5 commits (short hash + subject)

Side effects:
  - Per-timestamp file at .claude/runs/local_intel/compact_snapshots/snapshot_<ts>.json
  - Convenience "latest" pointer at .claude/runs/local_intel/last_compact_snapshot.json
  - Stdout: one-line [pre-compact-snapshot] hint for the post-compact agent

Non-blocking: never aborts compaction. Stdout failures are silently swallowed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SNAPSHOT_DIR = Path(".claude/runs/local_intel/compact_snapshots")
LATEST = Path(".claude/runs/local_intel/last_compact_snapshot.json")
LAUNCH_DIR = Path(".claude/runs/launch-specs")
FIND_ACTIVE = ".claude/scripts/harness/find_active_task_brief.py"


def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        return subprocess.check_output(
            cmd, timeout=timeout, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def _find_active_brief() -> str:
    if not os.path.isfile(FIND_ACTIVE):
        return ""
    return _run([sys.executable, FIND_ACTIVE])


def _launch_spec_rows() -> list[dict]:
    """Parse latest launch_spec into a list of dict rows."""
    if not LAUNCH_DIR.is_dir():
        return []
    specs = sorted(LAUNCH_DIR.glob("launch_spec_*.md"), reverse=True)
    if not specs:
        return []
    try:
        text = specs[0].read_text(encoding="utf-8")
    except Exception:
        return []

    rows: list[dict] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        # Skip header + separator.
        if line.startswith("|---") or "Slug" in line.split("|")[1]:
            continue
        cells = [c.strip() for c in line.split("|")]
        # Drop leading/trailing empties from outer pipes.
        cells = [c for i, c in enumerate(cells) if not (i in (0, len(cells) - 1) and c == "")]
        if len(cells) < 4 or not cells[0]:
            continue
        rows.append({
            "slug": cells[0],
            "risk": cells[1] if len(cells) > 1 else "",
            "phase": cells[2] if len(cells) > 2 else "",
            "status": cells[3] if len(cells) > 3 else "",
            "artifact": cells[5] if len(cells) > 5 else "",
        })
    return rows


def main() -> int:
    try:
        # Drain stdin to be polite, but don't require any specific shape.
        _ = sys.stdin.read()
    except Exception:
        pass

    ts = time.strftime("%Y-%m-%dT%H-%M-%S")
    snapshot = {
        "ts": ts,
        "branch": _run(["git", "branch", "--show-current"]),
        "head": _run(["git", "rev-parse", "--short", "HEAD"]),
        "dirty_files": len(_run(["git", "diff", "--name-only"]).splitlines()),
        "active_task_brief": _find_active_brief(),
        "launch_spec_rows": _launch_spec_rows(),
        "recent_commits": _run(["git", "log", "--oneline", "-5"]).splitlines(),
    }

    try:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        (SNAPSHOT_DIR / f"snapshot_{ts}.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        LATEST.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

    # Inject a single-line hint so the post-compact agent knows a snapshot
    # exists. Recovery flow: read LATEST file → infer active task → resume.
    try:
        hint_parts = [f"[pre-compact-snapshot] branch={snapshot['branch']} head={snapshot['head']}"]
        if snapshot["active_task_brief"]:
            hint_parts.append(f"active_brief={snapshot['active_task_brief']}")
        in_progress = [r["slug"] for r in snapshot["launch_spec_rows"] if r["status"] == "IN_PROGRESS"]
        if in_progress:
            hint_parts.append(f"in_progress=[{','.join(in_progress)}]")
        hint_parts.append(f"recover_via={LATEST}")
        print(" ".join(hint_parts))
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
