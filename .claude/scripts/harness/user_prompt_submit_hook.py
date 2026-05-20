#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook.

Injects up to three compact context blocks into the user prompt when applicable:

  1. Recurring failures from the last 30 days (failure_memory summary).
  2. Wiki distillation nudge when growth thresholds are tripped.
  3. Ambiguity nudge when the prompt has no action / object / success signals
     and no explicit @shortcut overrides triage.

Each block is silent when there is nothing to surface. Total token budget is
well below the prompt-cache window.
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
FAILURE_MEMORY = str(_SCRIPTS_DIR / "local_intel" / "failure_memory.py")
DISTILL_THRESHOLD = str(_SCRIPTS_DIR / "wiki" / "distill_threshold.py")
AMBIGUITY_GATE = str(_SCRIPTS_DIR / "gates" / "ambiguity_gate.py")
TRIAGE_PROBE = str(_SCRIPTS_DIR / "local_intel" / "triage_probe.py")

# Shortcuts that override the default triage — when present, the user has
# already declared intent and we do not need to nudge them.
SHORTCUT_OVERRIDES = (
    "@vibe", "@patch", "@learn", "@read", "@quickfix", "@standard",
    "@gc", "@librarian", "@distill", "@wiki-update", "@milestone",
    "@capabilities", "@cap",
)

# Below this prompt length we assume the input is a confirmation, a quick
# follow-up, or a yes/no — running the ambiguity gate would only produce noise.
MIN_PROMPT_LEN_FOR_AMBIGUITY_CHECK = 10


def _read_prompt_from_stdin() -> str:
    """Read user prompt from stdin. Supports both raw text and a JSON envelope."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return ""
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                for key in ("prompt", "user_prompt", "input", "text"):
                    value = obj.get(key)
                    if isinstance(value, str):
                        return value
        except json.JSONDecodeError:
            pass
    return raw


def _emit_failure_memory() -> None:
    if os.environ.get("CLAUDE_FAILURE_MEMORY_QUIET") == "1":
        return
    proc = subprocess.run(
        [sys.executable, FAILURE_MEMORY, "summary",
         "--days", "30", "--min-count", "2", "--top", "5",
         "--include-incidents"],
        check=False, capture_output=True, text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print("[failure-memory] Recent failures and incidents — keep in mind while planning:")
    print(out)


def _emit_distill_nudge() -> None:
    if os.environ.get("CLAUDE_DISTILL_QUIET") == "1":
        return
    proc = subprocess.run(
        [sys.executable, DISTILL_THRESHOLD],
        check=False, capture_output=True, text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print(out)


def _emit_triage_probe(prompt_text: str) -> None:
    """Inject [triage] block when probe suggests a profile above VIBE.

    Silent when probe heuristic-skips (short input, pure question) or when the
    suggested profile is VIBE with no red signals. Subprocess is bounded by the
    probe's internal 3s-per-tool timeouts.
    """
    if os.environ.get("CLAUDE_TRIAGE_QUIET") == "1":
        return
    text = (prompt_text or "").strip()
    if not text:
        return
    proc = subprocess.run(
        [sys.executable, TRIAGE_PROBE, "--quiet-on-skip"],
        input=text, check=False, capture_output=True, text=True,
    )
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print(out)


def _emit_ambiguity_check(prompt_text: str) -> None:
    if os.environ.get("CLAUDE_AMBIGUITY_QUIET") == "1":
        return
    text = (prompt_text or "").strip()
    if len(text) < MIN_PROMPT_LEN_FOR_AMBIGUITY_CHECK:
        return
    lowered = text.lower()
    if any(marker in lowered for marker in SHORTCUT_OVERRIDES):
        return
    proc = subprocess.run(
        [sys.executable, AMBIGUITY_GATE, "--intent", text[:500]],
        check=False, capture_output=True, text=True,
    )
    # 0 = PASS (silent). 1 = WARN, 2 = FAIL — both surface as a soft nudge.
    if proc.returncode == 0:
        return
    out = (proc.stdout or "").rstrip()
    if not out:
        return
    print("[ambiguity] input may be underspecified — consider clarifying via AskUserQuestion before acting:")
    print(out)


def main() -> int:
    prompt_text = _read_prompt_from_stdin()
    _emit_failure_memory()
    _emit_distill_nudge()
    _emit_ambiguity_check(prompt_text)
    _emit_triage_probe(prompt_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
