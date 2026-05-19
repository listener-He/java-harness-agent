#!/usr/bin/env python3
"""Find the active task_brief path from launch_spec_*.md.

Prints the task_brief path on stdout if an IN_PROGRESS row exists, else empty.
Exit 0 always (this is a probe, not a gate).
"""
import glob
import os
import re
import sys

LAUNCH_DIR = ".claude/runs/launch-specs"


def find() -> str:
    if not os.path.isdir(LAUNCH_DIR):
        return ""
    specs = sorted(glob.glob(os.path.join(LAUNCH_DIR, "launch_spec_*.md")))
    if not specs:
        return ""
    latest = specs[-1]
    try:
        with open(latest, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return ""

    for line in text.splitlines():
        if "IN_PROGRESS" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        for cell in cells:
            m = re.search(r"(\.claude/runs/task-briefs/[^\s|`)]+\.md)", cell)
            if m and os.path.isfile(m.group(1)):
                return m.group(1)
    return ""


if __name__ == "__main__":
    print(find())
    sys.exit(0)
