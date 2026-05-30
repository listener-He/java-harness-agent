#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook for Read (T4.1).

Tracks wiki / skill file accesses into the sidecar usage counter so
distill.py can identify referenced-but-unused fragments (the "ghost
fragment" case — file IS linked but nobody actually reads it).

Hot path: every Read tool call fires this hook. We MUST exit fast on
non-tracked paths. Single Python startup; in-process import of
usage_tracker (no second subprocess fork).

Path filter: only `.claude/wiki/**` and `.claude/skills/**`. Source code
reads, gate script reads, etc. all bail at the first if-statement.

Hook contract: payload is JSON on stdin with `tool_input.file_path`.
Failure is silent — never abort tool execution.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Fast filter substrings — must match exactly the path-segment form Claude
# Code passes (POSIX-style, absolute or repo-relative).
_TRACK_PREFIXES = ("/.claude/wiki/", "/.claude/skills/", ".claude/wiki/", ".claude/skills/")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0

    # Fast bail before any heavier work: ~99% of Reads are NOT wiki/skill.
    if not any(prefix in file_path for prefix in _TRACK_PREFIXES):
        return 0

    # In-process track via import — avoids a second Python startup that
    # would otherwise add ~200ms per qualifying Read.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "local_intel"))
    try:
        import usage_tracker  # type: ignore
        usage_tracker.track(file_path)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
