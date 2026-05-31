#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook for Edit|Write.

Claude Code passes the hook payload as JSON on stdin (NOT via env var).
We extract tool_input.file_path and fan out to:

  1. secrets_linter  — always, silent on PASS (defense in depth)
  2. scenario gates  — path-based dispatch (silent on PASS, prints on WARN/FAIL):
       *.sql      → migration_gate.py
       pom.xml    → dependency_gate.py
  3. skill_hint     — anti-pattern reminder, silent on no match
  4. incident_hint  — past-incident reminder, silent on no match
  5. session_stats  — edit counter (silent)

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


def _scenario_gates(file_path: str) -> list[tuple[str, list[str]]]:
    """Build (gate_name, argv) tuples for path-based gates.

    Empty list = no path-based gate applies. Each tuple is run in order;
    non-zero exits print stdout under a `[<gate_name>]` prefix.
    """
    cmds: list[tuple[str, list[str]]] = []
    name = os.path.basename(file_path)

    # SQL migration files → check for unsafe DDL patterns (DROP/TRUNCATE/etc).
    if file_path.endswith(".sql"):
        parent = os.path.dirname(file_path) or "."
        cmds.append(("migration_gate", [
            sys.executable, MIGRATION_GATE,
            "--sql-dir", parent,
            "--glob", name,
        ]))

    # pom.xml → diff vs git HEAD for adds/removes/major version bumps.
    if name == "pom.xml":
        cmds.append(("dependency_gate", [
            sys.executable, DEPENDENCY_GATE,
            "--pom", file_path,
        ]))

    return cmds


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path:
        return 0

    try:
        subprocess.run(
            [sys.executable, SECRETS_LINTER, "--paths", file_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except Exception:
        pass

    # Path-based scenario gates (migration / dependency). Silent on PASS,
    # prints findings on WARN/FAIL under a [<gate>] header so the agent
    # sees the diagnostic without the hook ever blocking the edit.
    for gate_name, argv in _scenario_gates(file_path):
        try:
            proc = subprocess.run(
                argv, check=False, capture_output=True, text=True, timeout=15,
            )
            if proc.returncode != 0:
                body = (proc.stdout or "").rstrip()
                if body:
                    print(f"[{gate_name}] non-PASS (exit {proc.returncode}):")
                    print(body)
        except Exception:
            pass

    # Symptom-driven skill hint: non-blocking, silent on no match. The hint
    # routes the agent to the relevant SKILL.md only when the just-edited file
    # shows an anti-pattern — not before Implement, not on every Java edit.
    try:
        proc = subprocess.run(
            [sys.executable, SKILL_HINT, file_path],
            check=False, capture_output=True, text=True,
            timeout=10,
        )
        out = (proc.stdout or "").rstrip()
        if out:
            print(out)
    except Exception:
        pass

    # Past-incident reverse lookup: if a recent incident touched this file,
    # remind the LLM. Non-blocking, silent on no match.
    try:
        proc = subprocess.run(
            [sys.executable, INCIDENT_HINT, file_path],
            check=False, capture_output=True, text=True,
            timeout=10,
        )
        out = (proc.stdout or "").rstrip()
        if out:
            print(out)
    except Exception:
        pass

    # Bump session edit counter for the reflect-threshold heuristic
    # (T1.1). Pure sink — silent stdout, never blocks.
    try:
        subprocess.run(
            [sys.executable, SESSION_STATS, "bump", "edit", file_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
