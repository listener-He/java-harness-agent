#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook for Edit|Write.

Mechanically blocks edits that fall outside the active task_brief's Allowed Scope.
- No active task_brief (no launch_spec or no IN_PROGRESS row) → silent skip.
- CLAUDE_SCOPE_GUARD_BYPASS=1 → silent skip (emergency bypass).
- scope_guard FAIL (exit 2) → block via non-zero exit + stderr message.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

EXIT_BLOCK = 2

SCOPE_GUARD = ".claude/scripts/gates/scope_guard.py"
FIND_ACTIVE = ".claude/scripts/harness/find_active_task_brief.py"


def _read_file_path() -> str:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return ""
    return (payload.get("tool_input") or {}).get("file_path") or ""


def _find_active_task_brief() -> str:
    try:
        proc = subprocess.run(
            [sys.executable, FIND_ACTIVE],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return ""
    return (proc.stdout or "").strip()


def _repo_root() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        return out.decode().strip()
    except Exception:
        return os.getcwd()


def _to_relative(file_path: str, repo_root: str) -> str:
    """Return repo-relative path, or empty string if outside repo root.

    Handles tilde (~/...), absolute, and relative inputs uniformly. The empty
    return is the signal to the caller that scope_guard has no jurisdiction:
    its Allowed Scope is repo-rooted, so any file under ~/.claude/ (memory,
    user-level CLAUDE.md, user-level agents/skills/settings), /tmp/, or any
    sibling repo cannot meaningfully be checked against a task_brief.
    """
    if not file_path:
        return ""
    expanded = os.path.expanduser(file_path)
    abs_path = os.path.abspath(expanded)
    try:
        common = os.path.commonpath([abs_path, repo_root])
    except ValueError:
        # Different drives on Windows, or other path incompatibility.
        return ""
    if common != repo_root:
        return ""
    return os.path.relpath(abs_path, repo_root)


def main() -> int:
    if os.environ.get("CLAUDE_SCOPE_GUARD_BYPASS") == "1":
        return 0

    file_path = _read_file_path()
    if not file_path:
        return 0

    task_brief = _find_active_task_brief()
    if not task_brief or not os.path.isfile(task_brief):
        return 0

    rel_file = _to_relative(file_path, _repo_root())

    # Empty result = file lives outside repo root. Covers ~/.claude/ memory,
    # user-level CLAUDE.md / agents / skills / settings, and any Claude Code
    # state stored outside the project tree. scope_guard's allowlist is
    # repo-rooted; it has no jurisdiction here. Silent skip.
    if not rel_file:
        return 0

    try:
        proc = subprocess.run(
            [sys.executable, SCOPE_GUARD,
             "--task-brief", task_brief,
             "--files", rel_file],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        # Fail-open: if scope_guard hangs, don't block the edit.
        return 0
    if proc.returncode == EXIT_BLOCK:
        sys.stderr.write(
            f"[scope_guard] BLOCKED: {rel_file} is outside Allowed Scope of {task_brief}\n"
        )
        if proc.stdout:
            sys.stderr.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stderr.write("\n")
        sys.stderr.write(
            "\nTo proceed, either add the file to the task_brief's '## Allowed Scope' section\n"
            "or set CLAUDE_SCOPE_GUARD_BYPASS=1 for one-shot emergency bypass.\n"
        )
        return EXIT_BLOCK

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
