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
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    args = parser.parse_args()

    runs_dir = ".agents/workflow/runs"
    archive_dir = ".agents/llm_wiki/archive"
    _ensure_dir(runs_dir)
    _ensure_dir(archive_dir)

    openspec_src = os.path.join(runs_dir, "openspec.md")
    focus_src = os.path.join(runs_dir, "focus_card.md")

    openspec_dst = os.path.join(archive_dir, f"{args.date}_{args.slug}_openspec.md")
    focus_dst = os.path.join(archive_dir, f"{args.date}_{args.slug}_focus_card.md")

    moved_openspec = _move_if_exists(openspec_src, openspec_dst)
    moved_focus = _move_if_exists(focus_src, focus_dst)

    if moved_openspec:
        _write_pointer(openspec_src, openspec_dst)
    if moved_focus:
        _write_pointer(focus_src, focus_dst)

    if not moved_openspec and not moved_focus:
        raise SystemExit("No session artifacts found under .agents/workflow/runs/")


if __name__ == "__main__":
    main()

