#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook for Edit|Write.

Claude Code passes the hook payload as JSON on stdin (NOT via env var).
We extract tool_input.file_path and fan out to up to 6 sibling scripts:

  1. secrets_linter  — always, silent on PASS (defense in depth)
  2. scenario gates  — path-based dispatch (silent on PASS, prints on WARN/FAIL):
       *.sql      → migration_gate.py
       pom.xml    → dependency_gate.py
  3. skill_hint     — anti-pattern reminder, silent on no match
  4. incident_hint  — past-incident reminder, silent on no match
  5. session_stats  — edit counter (silent)

All subprocesses are spawned concurrently via Popen, then we wait on them in
output order. Wall-clock is dominated by the slowest single subprocess
(Python boot ~80-100ms) rather than the sequential sum. Output is collected
and printed in deterministic order at the end so the agent sees a stable
context block.

Failures are silent — hooks must not abort tool execution. Exit 0 always.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Resolve sibling scripts relative to this file so the hook works regardless
# of the harness's current working directory.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_GATES_DIR = _SCRIPTS_DIR / "gates"
SECRETS_LINTER = str(_GATES_DIR / "secrets_linter.py")
MIGRATION_GATE = str(_GATES_DIR / "migration_gate.py")
DEPENDENCY_GATE = str(_GATES_DIR / "dependency_gate.py")
SKILL_HINT = str(_SCRIPTS_DIR / "local_intel" / "skill_hint.py")
INCIDENT_HINT = str(_SCRIPTS_DIR / "local_intel" / "incident_hint.py")
SESSION_STATS = str(_SCRIPTS_DIR / "local_intel" / "session_stats.py")

# Job output modes:
#   SILENT          — never print anything; swallow stdout. (secrets, stats)
#   EMIT_ON_NONPASS — print only on non-zero exit, with [name] header.
#                     (scenario gates)
#   EMIT_ANY_STDOUT — print whatever stdout is non-empty, as-is.
#                     (hints — they own their own format)
SILENT = "silent"
EMIT_ON_NONPASS = "emit_on_nonpass"
EMIT_ANY_STDOUT = "emit_any_stdout"


def _scenario_gates(file_path: str) -> list[tuple[str, list[str], str]]:
    """(name, argv, mode) for path-based scenario gates. Empty list = none."""
    jobs: list[tuple[str, list[str], str]] = []
    name = os.path.basename(file_path)

    if file_path.endswith(".sql"):
        parent = os.path.dirname(file_path) or "."
        jobs.append(("migration_gate", [
            sys.executable, MIGRATION_GATE,
            "--sql-dir", parent,
            "--glob", name,
        ], EMIT_ON_NONPASS))

    if name == "pom.xml":
        jobs.append(("dependency_gate", [
            sys.executable, DEPENDENCY_GATE,
            "--pom", file_path,
        ], EMIT_ON_NONPASS))

    return jobs


def _build_jobs(file_path: str) -> list[tuple[str, list[str], str]]:
    """Static job list for this file_path. Order = output order."""
    jobs: list[tuple[str, list[str], str]] = []
    # secrets first — defense in depth; silent regardless.
    jobs.append(("secrets_linter",
                 [sys.executable, SECRETS_LINTER, "--paths", file_path],
                 SILENT))
    # scenario gates (may emit findings).
    jobs.extend(_scenario_gates(file_path))
    # hints (may emit context).
    jobs.append(("skill_hint",
                 [sys.executable, SKILL_HINT, file_path],
                 EMIT_ANY_STDOUT))
    jobs.append(("incident_hint",
                 [sys.executable, INCIDENT_HINT, file_path],
                 EMIT_ANY_STDOUT))
    # session_stats last — pure counter, silent.
    jobs.append(("session_stats",
                 [sys.executable, SESSION_STATS, "bump", "edit", file_path],
                 SILENT))
    return jobs


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0

    jobs = _build_jobs(file_path)

    # Phase 1: spawn all subprocesses concurrently. Each Popen starts a
    # Python interpreter in parallel; the kernel handles scheduling. This
    # is the win — sequential would be sum(boots), concurrent is max(boot).
    procs: list[tuple[str, str, subprocess.Popen | None]] = []
    for name, argv, mode in jobs:
        try:
            p = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            procs.append((name, mode, p))
        except Exception:
            procs.append((name, mode, None))

    # Phase 2: collect output in deterministic order. communicate() blocks on
    # the current proc but later ones are likely already done by then.
    for name, mode, p in procs:
        if p is None:
            continue
        try:
            stdout, _ = p.communicate(timeout=15)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass
            continue
        except Exception:
            continue

        stdout = (stdout or "").rstrip()
        if mode == SILENT:
            continue
        if mode == EMIT_ON_NONPASS:
            if rc != 0 and stdout:
                print(f"[{name}] non-PASS (exit {rc}):")
                print(stdout)
        elif mode == EMIT_ANY_STDOUT:
            if stdout:
                print(stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
