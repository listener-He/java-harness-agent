#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render task_brief skeletons from a task-decomposition-guide output file.

Reads a `<YYYY-MM-DD>_<slug>_tasks.md` produced by the task-decomposition-guide
skill, splits it into per-task sections, and writes one task_brief skeleton
per subtask under `.claude/runs/task-briefs/<slug>_part_<i>_task_brief.md`.

The skeleton is intentionally INCOMPLETE — the main agent must still fill in
Context details, API contract, Data model, Business logic, etc. The script
pre-fills only what decomposition already knows:

  • Task ID + Name              → file slug + Section 1 Business goal
  • Goal / Type                 → Section 1 Context
  • Dependencies                → Section 1 Dependencies
  • Acceptance Criteria list    → Section 7 (Standard) / Verification (Slim)
  • Effort estimate             → spec_mode (Simple → SLIM, Medium/Complex → STANDARD)
  • Handoff Artifact            → Section 5 Business Logic notes

Refuses to overwrite existing files unless --force is set.

Usage:
  python3 brief_from_decomposition.py --tasks <YYYY-MM-DD>_<slug>_tasks.md
  python3 brief_from_decomposition.py --tasks <file> --out-dir <dir> [--force]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_OUT_DIR = Path(".claude/runs/task-briefs")

TASK_HEADER_RE = re.compile(
    r"^###\s+(?:[^\s]+\s+)?Task\s+(?P<id>[^:]+):\s*(?P<name>.+?)\s*$",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"^\s*-\s*\*\*(?P<key>[^:*]+):\*\*\s*(?P<value>.*)$")
AC_BULLET_RE = re.compile(r"^\s*-\s*\[\s*[xX ]?\s*\]\s*(?P<text>.+)$")


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w一-鿿]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "task"


def parse_tasks(content: str) -> list[dict]:
    """Split decomposition markdown into per-task structured records."""
    matches = list(TASK_HEADER_RE.finditer(content))
    if not matches:
        return []
    tasks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end]
        record = {
            "id": m.group("id").strip(),
            "name": m.group("name").strip(),
            "goal": "",
            "type": "",
            "effort": "",
            "dependencies": "",
            "handoff": "",
            "acs": [],
        }
        in_ac_section = False
        for line in body.splitlines():
            fm = FIELD_RE.match(line)
            if fm:
                key = fm.group("key").strip().lower()
                value = fm.group("value").strip()
                in_ac_section = False
                if key in {"goal"}:
                    record["goal"] = value
                elif key in {"type"}:
                    record["type"] = value
                elif key in {"effort"}:
                    record["effort"] = value
                elif key in {"dependencies"}:
                    record["dependencies"] = value
                elif "acceptance" in key:
                    in_ac_section = True
                elif "handoff" in key:
                    record["handoff"] = value
                continue
            if in_ac_section:
                am = AC_BULLET_RE.match(line)
                if am:
                    record["acs"].append(am.group("text").strip())
                elif line.strip().startswith("- **") or line.strip().startswith("#"):
                    in_ac_section = False
        tasks.append(record)
    return tasks


def _effort_to_spec_mode(effort: str) -> str:
    """Map decomposition effort hint to task_brief spec_mode."""
    e = (effort or "").lower()
    if "simple" in e or "2h" in e:
        return "SLIM"
    return "STANDARD"


def render_slim_brief(task: dict) -> str:
    acs_block = "\n".join(f"  - {ac}" for ac in task["acs"]) or "  - (fill from decomposition AC list)"
    return f"""spec_mode: SLIM

# Change Summary
- What changed: {task['name']} (Task {task['id']})
- Why: {task['goal'] or '(fill in business value)'}

# Scope of Change
- File/module list (paths only):
  - (fill in — main agent inspects code to populate)

# Risk & Rollback
- Why LOW: effort={task['effort']}, type={task['type']}
- Rollback steps: (one-line revert plan)

# Verification & Evidence
- Local verification: {task['handoff'] or '(test commands the agent will run)'}
- Acceptance criteria:
{acs_block}
- Evidence: (logs / test output / screenshots)
"""


def render_standard_brief(task: dict) -> str:
    acs_lines = "\n".join(f"  - {ac}" for ac in task["acs"]) or "  - (fill from decomposition AC list)"
    return f"""spec_mode: STANDARD

## 1. Context
- Business goal: {task['goal'] or '(one-sentence business value)'}
- Source: decomposition Task {task['id']} ({task['type']}, effort={task['effort']})
- Scope of change: (list modules/packages/key classes — main agent fills)
- Dependencies:
  - Upstream tasks: {task['dependencies'] or 'None'}
  - Wiki docs read: (relative links to wiki indexes consulted)

## 2. Domain Model
None (fill in if new terms / state machine changes)

## 3. API Contract (Handoff)
None (fill in if new/changed endpoint — use the strict format from task_brief_schema.md)

## 4. Data Model
None (fill in if schema change)

## 5. Business Logic
- Step-by-step behavior: (fill in)
- Error handling: (fill in)
- Handoff artifact for downstream task: {task['handoff'] or 'None'}

## 6. Non-Functional Constraints (Hard Constraints)
None (fill in: security / concurrency / forbidden patterns / rollback)

## 7. Acceptance Criteria (Testing)
- Happy path:
{acs_lines}
- Edge cases: (invalid params, concurrency, permission denied, etc.)
- Unit test requirements: (key branches and asserts)
"""


def render_brief(task: dict) -> str:
    mode = _effort_to_spec_mode(task["effort"])
    return render_slim_brief(task) if mode == "SLIM" else render_standard_brief(task)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render task_brief skeletons from a task-decomposition-guide output."
    )
    parser.add_argument("--tasks", required=True, help="Path to <date>_<slug>_tasks.md")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing skeletons")
    args = parser.parse_args()

    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        print(f"Tasks file not found: {tasks_path}", file=sys.stderr)
        return 2

    content = tasks_path.read_text(encoding="utf-8")
    records = parse_tasks(content)
    if not records:
        print("No `### Task N: ...` headers found in input.", file=sys.stderr)
        print("Expected format: see .claude/skills/task-decomposition-guide/SKILL.md", file=sys.stderr)
        return 1

    # Derive a slug for filenames from the input file basename.
    base_slug = re.sub(r"_tasks\.md$", "", tasks_path.name)
    base_slug = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", base_slug) or "tasks"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    for idx, task in enumerate(records, start=1):
        suffix = slugify(f"{task['id']}_{task['name']}")[:60]
        target = out_dir / f"{base_slug}_part_{idx:02d}_{suffix}_task_brief.md"
        if target.exists() and not args.force:
            print(f"[SKIP] exists: {target} (use --force to overwrite)")
            skipped += 1
            continue
        target.write_text(render_brief(task), encoding="utf-8")
        written += 1
        print(f"[WROTE] {target}")

    print(f"\nDone. {written} skeleton(s) written, {skipped} skipped, {len(records)} task(s) parsed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
