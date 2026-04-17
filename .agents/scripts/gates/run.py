#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate Runner (Role-aware)

This tool mounts roles dynamically by (intent, profile, phase) using:
- .agents/workflow/role_matrix.json

It runs deterministic gates and writes a markdown report to:
- .agents/workflow/runs/gates_report_<timestamp>.md

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import json
import os
import subprocess
import sys
import signal
from datetime import datetime

EXIT_WARN = 1
EXIT_FAIL = 2


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _render_arg(token: str, ctx: dict) -> str:
    for k, v in ctx.items():
        token = token.replace("{" + k + "}", str(v))
    return token


def _run_script(script: str, args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, script] + args
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return 0, out
    except subprocess.CalledProcessError as e:
        code = e.returncode
        out = e.output or ""
        if code not in (0, 1, 2):
            code = EXIT_FAIL
        return code, out


def _resolve_roles(matrix: dict, intent: str, profile: str, phase: str) -> list[str]:
    roles: list[str] = []
    for m in matrix.get("mounts", []):
        if m.get("intent") != intent:
            continue
        if m.get("profile") != profile:
            continue
        if m.get("phase") != phase:
            continue
        roles.extend(m.get("roles", []))
    return roles


def _safe_key(text: str) -> str:
    return (text or "").replace("\\", "/")


def _load_retry_state(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_retry_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _clear_task_state(path: str, state: dict, task_id: str) -> None:
    if task_id in state:
        state.pop(task_id, None)
        _save_retry_state(path, state)


def _build_escalation_card(
        out_path: str,
        task_id: str,
        args,
        blocked: list[str],
        task_state: dict,
        report_path: str
) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Card - {datetime.now().strftime('%Y%m%d_%H%M%S')}\n\n")
        f.write(f"- task-id: {task_id}\n")
        f.write(f"- intent: {args.intent}\n")
        f.write(f"- profile: {args.profile}\n")
        f.write(f"- phase: {args.phase}\n")
        f.write(f"- topic: {args.topic}\n")
        f.write(f"- date: {args.date}\n")
        f.write(f"- verify-level: {args.verify_level}\n")
        f.write(f"- report: `{report_path}`\n\n")
        f.write("## Goal\n")
        f.write("- Complete gate validation and proceed to next lifecycle phase.\n\n")
        f.write("## Current blockers\n")
        f.write("- Per-script failure cap exceeded (>3) in this task.\n")
        for s in blocked:
            f.write(f"- `{s}`: {task_state.get(s)} failures\n")
        f.write("\n## What I tried (with evidence)\n")
        f.write(f"- Re-ran mounted gates; latest evidence in `{report_path}`.\n")
        f.write(f"- Retry state snapshot: `.agents/workflow/runs/gate_retry_state.json`.\n\n")
        f.write("## What I need from human\n")
        f.write("- Clarify scope/intent ambiguities or adjust constraints for blocked scripts.\n")
        f.write("- Confirm whether to reset retry counter for this task after intervention.\n")


def _parse_artifact_tags(raw: str) -> set[str]:
    if not raw:
        return set()
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _should_run_gate(script: str, rendered_args: list[str], verify_level: str, artifact_tags: set[str], ctx: dict) -> tuple[bool, str]:
    base = os.path.basename(script or "")

    # 1) Intensity-based filtering
    if verify_level == "quick" and base in {"wiki_linter.py", "secrets_linter.py", "comment_linter_java.py"}:
        return False, "skip by verify-level=quick"

    # 2) Artifact-based filtering
    if base == "delivery_capsule_gate.py" and not ctx.get("delivery_file"):
        return False, "skip: delivery file not provided"

    if base == "writeback_gate.py" and artifact_tags:
        req_types = []
        for i, x in enumerate(rendered_args):
            if x == "--require" and i + 1 < len(rendered_args):
                req_types.append(rendered_args[i + 1].strip().lower())
        if req_types:
            if not any(rt in artifact_tags for rt in req_types):
                return False, f"skip by artifact-tags={sorted(artifact_tags)}"

    # 3) Strict mode runs mounted gates as-is (plus we can append global gates later if needed)
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", default="Change")
    parser.add_argument("--profile", required=True, choices=["PATCH", "STANDARD"])
    parser.add_argument("--phase", required=True, choices=["Explorer", "Propose", "Review", "Implement", "QA", "Archive"])
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--intent-text", default="")
    parser.add_argument("--anchors-file", default="")
    parser.add_argument("--delivery-file", default="")
    parser.add_argument("--changed-files", default="", help="comma-separated changed files for scope guard")
    parser.add_argument("--artifact-tags", default="", help="comma-separated tags: domain,api,rules,data,architecture,skill,workflow")
    parser.add_argument("--verify-level", default="standard", choices=["quick", "standard", "strict"])
    parser.add_argument("--task-id", default="", help="stable task id for retry counting; default=intent:profile:topic:date")
    parser.add_argument("--max-failures-per-script", type=int, default=3, help="per task/script failure cap")
    parser.add_argument("--end-task", action="store_true", help="clear retry state for this task after run (success/fail)")
    parser.add_argument("--matrix", default=".agents/workflow/role_matrix.json")
    args = parser.parse_args()

    matrix = _load_json(args.matrix)
    task_id = args.task_id.strip() or f"{args.intent}:{args.profile}:{args.topic}:{args.date}"
    retry_state_file = ".agents/workflow/runs/gate_retry_state.json"
    retry_state = _load_retry_state(retry_state_file)
    task_state = retry_state.get(task_id, {})

    def _handle_signal(signum, frame):
        _clear_task_state(retry_state_file, retry_state, task_id)
        print(f"INTERRUPTED: task state cleared for {task_id}")
        raise SystemExit(130)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    ctx = {
        "intent_text": args.intent_text,
        "anchors_file": args.anchors_file,
        "topic": args.topic.strip().lower().replace(" ", "_"),
        "date": args.date,
        "delivery_file": args.delivery_file,
        "changed_files": args.changed_files,
    }
    artifact_tags = _parse_artifact_tags(args.artifact_tags)

    roles = _resolve_roles(matrix, args.intent, args.profile, args.phase)
    if not roles:
        print("WARN: no roles mounted for this phase")
        return EXIT_WARN

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f".agents/workflow/runs/gates_report_{timestamp}.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    overall = 0
    with open(report_path, "w", encoding="utf-8") as rep:
        rep.write(f"# Gates Report - {timestamp}\n\n")
        rep.write(f"- intent: {args.intent}\n")
        rep.write(f"- profile: {args.profile}\n")
        rep.write(f"- phase: {args.phase}\n")
        rep.write(f"- topic: {ctx['topic']}\n")
        rep.write(f"- date: {ctx['date']}\n\n")
        rep.write(f"- task-id: {task_id}\n")
        rep.write(f"- max-failures-per-script: {args.max_failures_per_script}\n")
        rep.write(f"- verify-level: {args.verify_level}\n")
        rep.write(f"- artifact-tags: {sorted(artifact_tags)}\n\n")
        rep.write("## Mounted Roles\n")
        for r in roles:
            rep.write(f"- {r}\n")
        rep.write("\n## Gate Results\n")

        for role in roles:
            role_def = matrix.get("roles", {}).get(role, {})
            for gate in role_def.get("gates", []):
                script = gate.get("script")
                raw_args = gate.get("args", [])
                rendered_args = []
                for a in raw_args:
                    if a is None:
                        continue
                    rendered = _render_arg(a, ctx).strip()
                    if rendered == "":
                        continue
                    rendered_args.append(rendered)
                run_it, reason = _should_run_gate(script, rendered_args, args.verify_level, artifact_tags, ctx)
                if not run_it:
                    rep.write(f"### {role}: {script}\n")
                    rep.write(f"- exit: SKIP\n")
                    rep.write(f"- reason: {reason}\n\n")
                    continue

                script_key = _safe_key(script)
                current_failures = int(task_state.get(script_key, 0))
                if current_failures > args.max_failures_per_script:
                    overall = EXIT_FAIL
                    rep.write(f"### {role}: {script}\n")
                    rep.write("- exit: BLOCKED\n")
                    rep.write(
                        f"- reason: failure count exceeded {args.max_failures_per_script}; human help required\n\n"
                    )
                    continue

                code, out = _run_script(script, rendered_args)
                overall = max(overall, code)
                if code == EXIT_FAIL:
                    task_state[script_key] = current_failures + 1
                rep.write(f"### {role}: {script}\n")
                rep.write(f"- exit: {code}\n")
                rep.write(f"- failure-count: {task_state.get(script_key, current_failures)}\n")
                rep.write("\n```text\n")
                rep.write(out.strip() + "\n")
                rep.write("```\n\n")

    retry_state[task_id] = task_state
    _save_retry_state(retry_state_file, retry_state)

    print(f"Report: {report_path}")
    # Auto clear when task naturally ends (Archive phase), or explicitly requested.
    if args.phase == "Archive" or args.end_task:
        _clear_task_state(retry_state_file, retry_state, task_id)
        print(f"TASK_STATE_CLEARED: {task_id}")

    if overall == 0:
        print("OK: all gates pass")
        return 0
    if overall == EXIT_WARN:
        print("WARN: gates produced warnings")
        return EXIT_WARN
    print("FAIL: gates failed")
    blocked = [k for k, v in task_state.items() if int(v) > args.max_failures_per_script]
    if blocked:
        escalation_path = f".agents/workflow/runs/escalation_card_{timestamp}.md"
        _build_escalation_card(escalation_path, task_id, args, blocked, task_state, report_path)
        print("HUMAN_HELP_REQUIRED: some scripts exceeded failure cap")
        for b in blocked:
            print(f"- {b}: {task_state.get(b)} failures")
        print(f"ESCALATION_CARD: {escalation_path}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
