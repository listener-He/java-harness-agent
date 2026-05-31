#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook for Edit|Write — secrets-only enforcement + event emit.

Phase P3 of the Sensor/Policy/Enforce refactor. This hook used to run TWO
checks:
  1. secrets_linter pre-check on content/new_string (block on HIGH)
  2. scope_guard against active task_brief (block on out-of-scope edit)

Check #2 (scope_guard) moved OUT of the hook to /h-gates --phase implement.
Rationale: per-edit scope blocking interrupts mid-implementation discovery
and is mismatched with the LEARN/PATCH-style flexibility most edits warrant.
Phase-boundary check catches drift before it ships without per-edit friction.

Check #1 (secrets) stays in the hook because secret leakage is the one
irreversible-on-write red line. Even VIBE/LEARN edits must not commit a
credential.

Bypass envs:
  CLAUDE_SECRETS_BYPASS=1       — skip secrets pre-check (emergency only)
  CLAUDE_SCOPE_GUARD_BYPASS=1   — legacy, still respected to skip the entire
                                   hook (mostly redundant now scope_guard left)

Sensor side-effect: emit edit_pre event with secrets_check outcome + blocked
flag so events_query consumers can analyze pre-check incidence.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

EXIT_BLOCK = 2

_HARNESS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HARNESS_DIR.parent
_LOCAL_INTEL_DIR = _SCRIPTS_DIR / "local_intel"
SECRETS_LINTER = str(_SCRIPTS_DIR / "gates" / "secrets_linter.py")


def _read_payload() -> tuple[str, str, str]:
    """Return (file_path, content_to_scan, tool_name)."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return "", "", ""
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    tool_name = payload.get("tool_name") or ""
    return file_path, content, tool_name


def _emit_event(file_path: str, tool_name: str, secrets_check: str, blocked: bool) -> None:
    if str(_LOCAL_INTEL_DIR) not in sys.path:
        sys.path.insert(0, str(_LOCAL_INTEL_DIR))
    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "edit_pre",
            file_path=file_path,
            tool=tool_name,
            secrets_check=secrets_check,
            blocked=blocked,
        )
    except Exception:
        pass


def _secrets_precheck(file_path: str, content: str) -> tuple[int, str]:
    """Returns (rc, gate_stdout). rc 0 OK / 1 WARN / 2 FAIL. fail-open on subprocess error."""
    if not content:
        return 0, ""
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
        return 0, ""
    return proc.returncode, (proc.stdout or "")


def _emit_bypass(env_var: str, file_path: str) -> None:
    """Record env-bypass usage for the override_drift insight detector."""
    if str(_LOCAL_INTEL_DIR) not in sys.path:
        sys.path.insert(0, str(_LOCAL_INTEL_DIR))
    try:
        import event_writer  # noqa: E402
        event_writer.append(
            "env_bypass",
            env_var=env_var,
            hook="pre_tool_use_hook",
            file_path=file_path,
        )
    except Exception:
        pass


def main() -> int:
    # Legacy bypass — kept for backward compat. Skips the entire hook.
    if os.environ.get("CLAUDE_SCOPE_GUARD_BYPASS") == "1":
        # Capture file_path even when fully bypassed so drift detector knows context.
        try:
            payload_fp = (json.load(sys.stdin).get("tool_input") or {}).get("file_path", "")
        except Exception:
            payload_fp = ""
        _emit_bypass("CLAUDE_SCOPE_GUARD_BYPASS", payload_fp)
        return 0

    file_path, content, tool_name = _read_payload()
    if not file_path:
        return 0

    # Secrets bypass — new emergency escape for the secrets gate specifically.
    if os.environ.get("CLAUDE_SECRETS_BYPASS") == "1":
        _emit_event(file_path, tool_name, secrets_check="SKIP_BYPASS", blocked=False)
        _emit_bypass("CLAUDE_SECRETS_BYPASS", file_path)
        return 0

    rc, gate_out = _secrets_precheck(file_path, content)
    secrets_check = {0: "PASS", 1: "WARN", 2: "FAIL"}.get(rc, "ERROR")

    if rc == EXIT_BLOCK:
        sys.stderr.write(f"[secrets_linter] BLOCKED: {file_path}\n")
        if gate_out:
            sys.stderr.write(gate_out)
            if not gate_out.endswith("\n"):
                sys.stderr.write("\n")
        sys.stderr.write(
            "\nA high-confidence secret pattern was detected in the content "
            "you are about to write. Remove the secret, move it to a secret "
            "manager, or — emergency only — re-run with "
            "CLAUDE_SECRETS_BYPASS=1 prefix.\n"
        )
        _emit_event(file_path, tool_name, secrets_check, blocked=True)
        return EXIT_BLOCK

    if rc == 1 and gate_out:
        sys.stderr.write(f"[secrets_linter] WARN: {file_path}\n")
        sys.stderr.write(gate_out)
        if not gate_out.endswith("\n"):
            sys.stderr.write("\n")

    _emit_event(file_path, tool_name, secrets_check, blocked=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
