#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triage Probe — synthesize four signals into a suggested workflow profile.

Signals composed:
  - blast_radius: code_index.py --impact-of for each file hint extracted from prompt
  - failure_history: failure_memory.py summary --days 30 --min-count 2
  - ambiguity: ambiguity_gate.py --intent
  - danger_keywords: static scan against HIGH / MEDIUM tier word lists

Output:
  - default (human): a [triage] block; silent if profile=VIBE and no red signals
  - --json: full structured result for downstream consumers

Designed to run inside UserPromptSubmit hook in well under 1s — upstream signals
(code_index, failure_memory, ambiguity_gate) are gathered via in-process imports
(no subprocess fan-out), total typically under 600ms.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Import sibling modules directly — subprocess fan-out cost a measured ~4s per
# hook invocation, which made the prompt-submit hook unusable. In-process
# imports drop the same workload to ~250ms.
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / ".claude" / "scripts" / "local_intel"))
sys.path.insert(0, str(_REPO_ROOT / ".claude" / "scripts" / "gates"))

import code_index  # noqa: E402
import failure_memory  # noqa: E402
import ambiguity_gate  # noqa: E402

PROFILE_RANK = {
    "VIBE": 0,
    "RESEARCH": 1,
    "PATCH": 2,
    "STANDARD-MEDIUM": 3,
    "STANDARD-HIGH": 4,
}

# Shortcuts where the user has already declared intent; probe must not override.
HARD_SKIP_SHORTCUTS = (
    "@learn", "@read", "@cap", "@capabilities",
    "@gc", "@librarian", "@distill", "@wiki-update", "@milestone",
)

# Below this length input is almost always a confirmation / yes-no / typo question.
MIN_LEN_FOR_PROBE = 15

# HIGH-tier keywords escalate straight to STANDARD-HIGH. Lifecycle/policy/routing
# names are included because edits to those framework files cascade to every
# downstream task — they are the routing table itself.
DANGER_HIGH = (
    "auth", "认证", "permission", "权限", "rbac",
    # Mutating DDL — touches existing live data. Additive `create table`
    # is intentionally NOT here; see Scenario B1 (PATCH).
    "alter table", "drop column", "drop table",
    "modify column", "rename column", "rename table",
    "migration", "迁移",
    "error code", "错误码", "errcode",
    "secret", "token", "credential", "凭证",
    "lifecycle", "lifecycle.md", "policy.md", "dispatch-template",
    "skill-precedence", "claude.md",
)

DANGER_MEDIUM = (
    "public api", "公共 api", "endpoint", "签名",
    "hook", "gate", "framework", "架构",
    # Additive / generic schema talk — often PATCH-able when isolated. The
    # synthesizer escalates to MEDIUM only if compounded with other signals.
    "create table", "create index", "ddl", "schema",
)

FILE_HINT_PAT = re.compile(
    r"""(
        src/[\w/-]+\.java
        | src/[\w/-]+\.xml
        | \.claude/[\w./-]+\.md
        | [A-Z][A-Za-z0-9]+\.java
        | [A-Z][A-Za-z0-9]*(?:Service|Mapper|Controller|Repository|Manager)
    )""",
    re.VERBOSE,
)


def _read_prompt() -> str:
    """Read raw prompt from stdin. Accepts plain text or a JSON envelope."""
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
                    v = obj.get(key)
                    if isinstance(v, str):
                        return v
        except json.JSONDecodeError:
            pass
    return raw


def _should_skip(prompt: str) -> bool:
    t = prompt.strip().lower()
    if len(t) < MIN_LEN_FOR_PROBE:
        return True
    if any(sc in t for sc in HARD_SKIP_SHORTCUTS):
        return True
    # Pure question without an action verb — almost always LEARN-class chat.
    if t.endswith("?") or t.endswith("？"):
        action_verbs = (
            "改", "加", "修", "删", "实现", "新增", "重构", "迁移",
            "fix", "add", "implement", "refactor", "remove", "delete",
            "migrate", "update", "change", "create", "build",
        )
        if not any(v in t for v in action_verbs):
            return True
    return False


def _extract_file_hints(prompt: str) -> list[str]:
    hints: list[str] = []
    for m in FILE_HINT_PAT.finditer(prompt):
        h = m.group(1)
        if h not in hints:
            hints.append(h)
    return hints[:5]


def _probe_blast_radius(hints: list[str]) -> dict:
    if not hints:
        return {"files": 0, "callers": 0, "hints_resolved": 0, "sample": []}

    idx = code_index.load()
    if idx is None:
        return {"files": 0, "callers": 0, "hints_resolved": 0, "sample": []}

    impacted: set[str] = set()
    callers_total = 0
    resolved = 0
    for hint in hints:
        try:
            data = code_index.impact_of(hint, idx)
        except (KeyError, ValueError):
            continue
        impacted_here = data.get("all_impacted") or []
        if impacted_here:
            resolved += 1
            impacted.update(impacted_here)
            callers_total += len(data.get("callers") or [])

    return {
        "files": len(impacted),
        "callers": callers_total,
        "hints_resolved": resolved,
        "sample": sorted(impacted)[:3],
    }


def _probe_failure_history() -> dict:
    try:
        items = failure_memory.summary(days=30, min_count=2, top=3)
    except Exception:
        items = []
    return {
        "recurring": len(items),
        "top_pattern": items[0].get("pattern", "") if items else "",
    }


def _probe_ambiguity(prompt: str) -> str:
    try:
        code, _ = ambiguity_gate._check_intent(prompt[:500])
    except Exception:
        return "OK"
    return {0: "OK", 1: "WARN", 2: "FAIL"}.get(code, "OK")


def _scan_danger_keywords(prompt: str) -> tuple[list[str], list[str]]:
    t = prompt.lower()
    high = [k for k in DANGER_HIGH if k in t]
    medium = [k for k in DANGER_MEDIUM if k in t]
    return high, medium


def _synthesize(blast: dict, failure: dict, ambiguity: str,
                high_kw: list[str], medium_kw: list[str],
                intent_class: str) -> tuple[str, list[str], list[str]]:
    """Combine signals → (profile, signals_red, signals_yellow).

    Conservative thresholds: a single soft signal lands at PATCH, never MEDIUM.
    MEDIUM requires either large blast radius (≥7), high-recurrence failures
    (≥3), or a soft signal that compounds. HIGH is reserved for HIGH-tier
    danger keywords (auth, schema, framework routing files).

    RESEARCH short-circuits Change-side escalation: when intent_class=RESEARCH,
    danger keywords and large blast radius become signals_yellow (heightened
    evidence rigor) rather than signals_red (profile escalation). The user's
    declared intent is "produce a report", not "change code" — even when the
    research touches sensitive areas.
    """
    signals_yellow: list[str] = []

    if intent_class == "RESEARCH":
        profile = "RESEARCH"
        signals: list[str] = []
        if high_kw:
            signals_yellow.append(
                f"research touches sensitive area ({', '.join(high_kw[:2])}) — "
                "require ≥ 10 evidence entries"
            )
        if blast["files"] >= 7:
            signals_yellow.append(
                f"research spans {blast['files']} files — keep §1 Question scoped"
            )
        if failure["recurring"] >= 2:
            signals_yellow.append(
                f"failure history: {failure['recurring']} recurring patterns — "
                "factor into Findings"
            )
        return profile, signals, signals_yellow

    profile = "VIBE"
    signals: list[str] = []

    def upgrade(target: str, reason: str) -> None:
        nonlocal profile
        if PROFILE_RANK[target] > PROFILE_RANK[profile]:
            profile = target
        signals.append(reason)

    # HIGH-tier danger keywords are non-negotiable.
    if high_kw:
        upgrade("STANDARD-HIGH", f"danger keywords: {', '.join(high_kw[:3])}")

    # Blast radius — code_index based.
    if blast["files"] >= 7:
        upgrade("STANDARD-MEDIUM",
                f"blast: impacts {blast['files']} files ({blast['callers']} callers)")
    elif blast["files"] >= 3:
        upgrade("PATCH", f"blast: impacts {blast['files']} files")

    # Failure recurrence — soft signal, requires multiple hits to escalate.
    if failure["recurring"] >= 3:
        upgrade("STANDARD-MEDIUM",
                f"failure: {failure['recurring']} recurring patterns in last 30d")
    elif failure["recurring"] >= 2:
        upgrade("PATCH",
                f"failure: {failure['recurring']} recurring patterns in last 30d")

    # Ambiguity — FAIL is common for short imperative prompts, so cap at PATCH.
    # WARN is too noisy to record at all.
    if ambiguity == "FAIL":
        upgrade("PATCH", "ambiguity: FAIL (missing action/object signal)")

    # MEDIUM-tier keywords — only escalate if no higher signal already landed.
    if medium_kw and profile == "VIBE":
        upgrade("PATCH", f"keywords: {', '.join(medium_kw[:3])}")
    elif medium_kw:
        signals.append(f"keywords: {', '.join(medium_kw[:3])}")

    return profile, signals, signals_yellow


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Triage probe — synthesize signals into a suggested profile"
    )
    parser.add_argument("--prompt-file",
                        help="read prompt from file (default: stdin)")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--quiet-on-skip", action="store_true",
                        help="silent exit when heuristic skip triggers")
    args = parser.parse_args()

    if os.environ.get("CLAUDE_TRIAGE_QUIET") == "1":
        return 0

    if args.prompt_file:
        try:
            with open(args.prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
        except OSError:
            print("(triage: prompt file not found)", file=sys.stderr)
            return 1
    else:
        prompt = _read_prompt()

    if _should_skip(prompt):
        if args.as_json and not args.quiet_on_skip:
            print(json.dumps({"skipped": True}))
        return 0

    hints = _extract_file_hints(prompt)
    blast = _probe_blast_radius(hints)
    failure = _probe_failure_history()
    ambiguity = _probe_ambiguity(prompt)
    high_kw, medium_kw = _scan_danger_keywords(prompt)
    intent_class = ambiguity_gate.classify_intent(prompt[:500])
    profile, signals, signals_yellow = _synthesize(
        blast, failure, ambiguity, high_kw, medium_kw, intent_class
    )

    result = {
        "suggested_profile": profile,
        "intent_class": intent_class,
        "signals_red": signals,
        "signals_yellow": signals_yellow,
        "blast_radius": blast,
        "failure_history": failure,
        "ambiguity": ambiguity,
        "danger_keywords": {"high": high_kw, "medium": medium_kw},
        "file_hints": hints,
    }

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # Human-readable: silent when probe sees nothing worth flagging.
    if profile == "VIBE" and not signals and not signals_yellow:
        return 0

    print("[triage]")
    print(f"suggested: {profile}")
    if signals:
        print("signals_red:")
        for s in signals:
            print(f"  - {s}")
    if signals_yellow:
        print("signals_yellow:")
        for s in signals_yellow:
            print(f"  - {s}")
    if high_kw or medium_kw:
        print(f"keywords: {', '.join(high_kw + medium_kw)}")
    if blast["sample"]:
        print(f"impacted_sample: {', '.join(blast['sample'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
