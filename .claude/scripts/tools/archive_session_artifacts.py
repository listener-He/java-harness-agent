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

    runs_dir = ".claude/workflow/runs"
    archive_dir = ".claude/wiki/archive"
    _ensure_dir(runs_dir)
    _ensure_dir(archive_dir)

    task_brief_src = os.path.join(runs_dir, f"{args.date}_{args.slug}_task_brief.md")
    task_brief_dst = os.path.join(archive_dir, f"{args.date}_{args.slug}_task_brief.md")

    moved = _move_if_exists(task_brief_src, task_brief_dst)

    if moved:
        _write_pointer(task_brief_src, task_brief_dst)
    else:
        raise SystemExit(f"No task_brief found for {args.date}_{args.slug} under .claude/workflow/runs/")


if __name__ == "__main__":
    main()
