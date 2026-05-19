#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
from datetime import datetime


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _move_if_exists(src: str, dst: str) -> bool:
    if not os.path.exists(src):
        return False
    _ensure_dir(os.path.dirname(dst))
    shutil.move(src, dst)
    return True


def _write_pointer(path: str, archived_path: str):
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Archived\n\n")
        f.write("This file is archived. Do not use it as active working memory.\n\n")
        f.write(f"- Archived to: {archived_path}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="Feature slug, e.g. live_room_batch_schedule_query")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    # Canonical location for active task_briefs (per CLAUDE.md):
    # .claude/runs/task-briefs/. The legacy .claude/workflow/runs/ is kept as a
    # fallback to support stale clones that still write to the old path.
    runs_dir = ".claude/runs/task-briefs"
    legacy_runs_dir = ".claude/workflow/runs"
    archive_dir = ".claude/wiki/archive"
    _ensure_dir(runs_dir)
    _ensure_dir(archive_dir)

    filename = f"{args.date}_{args.slug}_task_brief.md"
    task_brief_dst = os.path.join(archive_dir, filename)

    # Try canonical path first, then legacy.
    candidates = [
        os.path.join(runs_dir, filename),
        os.path.join(legacy_runs_dir, filename),
    ]
    task_brief_src = next((p for p in candidates if os.path.exists(p)), None)

    if task_brief_src is None:
        searched = ", ".join(candidates)
        raise SystemExit(f"No task_brief found for {args.date}_{args.slug}. Searched: {searched}")

    _move_if_exists(task_brief_src, task_brief_dst)
    _write_pointer(task_brief_src, task_brief_dst)


if __name__ == "__main__":
    main()
