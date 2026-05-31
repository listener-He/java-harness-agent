#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook for Edit|Write.

Runs two pre-flight checks in order; either can block the tool call.

  1. secrets_linter (content-stdin mode) — scans the about-to-be-written
     bytes for high-confidence secret patterns. FAIL → block. Runs on EVERY
     Edit/Write regardless of repo jurisdiction (a secret in user-home
     memory is as bad as one in the repo).
  2. scope_guard — blocks edits outside the active task_brief's Allowed
     Scope. Skipped when there is no active task, when the file lives
     outside the repo, or when CLAUDE_SCOPE_GUARD_BYPASS=1.

Either exit 2 = block (stderr carries the reason). Defense in depth:
PostToolUse still re-runs secrets_linter on the resulting file for any
multi-line / future pattern Pre might have missed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

EXIT_BLOCK = 2

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SCOPE_GUARD = str(_SCRIPTS_DIR / "gates" / "scope_guard.py")
SECRETS_LINTER = str(_SCRIPTS_DIR / "gates" / "secrets_linter.py")
FIND_ACTIVE = str(_SCRIPTS_DIR / "harness" / "find_active_task_brief.py")


def _read_payload() -> tuple[str, str]:
    """Return (file_path, content_to_scan).

    content_to_scan is:
      - tool_input.content for Write (full file body)
      - tool_input.new_string for Edit (only the addition)
      - empty string if neither present
    """
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return "", ""
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    return file_path, content


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


def _secrets_precheck(file_path: str, content: str) -> int:
    """Run secrets_linter in content-stdin mode. Returns the gate exit code
    (0 OK / 1 WARN / 2 FAIL). On any subprocess error, returns 0 (fail-open
    — never block due to harness failure)."""
    if not content:
        return 0
    try:
        proc = subprocess.run(
            [sys.executable, SECRETS_LINTER,
             "--content-stdin", "--target-path", file_path or "<unknown>"],
            input=content,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return 0
    if proc.returncode == EXIT_BLOCK:
        sys.stderr.write(f"[secrets_linter] BLOCKED: {file_path}\n")
        if proc.stdout:
            sys.stderr.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stderr.write("\n")
        sys.stderr.write(
            "\nA high-confidence secret pattern was detected in the content "
            "you are about to write. Remove or move the secret out-of-band "
            "(env var, secret manager, .env file in .gitignore) and retry.\n"
        )
    elif proc.returncode == 1 and proc.stdout:
        # WARN: surface but don't block.
        sys.stderr.write(f"[secrets_linter] WARN: {file_path}\n")
        sys.stderr.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stderr.write("\n")
    return proc.returncode


def main() -> int:
    if os.environ.get("CLAUDE_SCOPE_GUARD_BYPASS") == "1":
        return 0

    file_path, content = _read_payload()
    if not file_path:
        return 0

    # Check 1: secrets — runs first because secret leaks are worse than scope
    # drift, and applies to ALL writes including out-of-repo paths (memory,
    # user-level configs).
    if _secrets_precheck(file_path, content) == EXIT_BLOCK:
        return EXIT_BLOCK

    # Check 2: scope_guard — only meaningful when there is an active
    # task_brief AND the file lives inside the repo.
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
