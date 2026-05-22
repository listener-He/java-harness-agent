---
name: ai-pipeline
description: "Orchestrate the repo-aligned AI engineering pipeline (plan → decisions → eval → improve → cleanup → verify → archive) with explicit approval gates. TRIGGER when user asks to run the full pipeline or go from idea to delivery; DO NOT TRIGGER for small tasks or when user invokes a specific phase."
---

# AI Pipeline — Repo-Aligned Orchestration

Orchestrate the full “idea → delivery” pipeline while staying strictly compatible with this repository’s workflow gates and artifact conventions.

## Hard Compatibility Rules

- Follow `CLAUDE.md` lifecycle gates and roles (including Approval Gate and Archive/WAL).
- All runtime artifacts MUST be written under `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_*`.
- No external state directories, no implicit git/CI automation.
- No infinite loops. Any iterative improvement requires explicit user approval to continue.
- Only delegate to available agent types (e.g., search) and provide self-contained context.

## When to Use

- User asks to “run the pipeline / full pipeline”
- Work spans multiple phases: planning + decision records + evaluation + implementation + cleanup + verification

Do not use when the user requests a single phase explicitly (e.g., “just write the plan”).

## Pipeline (Repo Lifecycle Mapping)

0. **Intake**: `input-classifier` — classify and normalize the raw input before anything else. Emits `[Intake]` block with Intent/Profile/Scenario/AC-Candidates. Skip only for explicit @shortcuts or single-phase invocations.
1. **Design**: `brainstorming` (when creative) → `impl-plan` or `blueprint`
2. **Decisions**: `architecture-decision-records`
3. **Evaluation**: `eval-harness` (define pass/fail and verification commands)
4. **Approval Gate**: if risk is MEDIUM/HIGH, stop after spec and wait for approval
5. **Implement**: implement the plan in-scope only
6. **Improve (optional)**: `self-improve` (bounded iterations, user-approved)
6.1 **External Research (conditional)**: if `self-improve` score has plateaued for 2+ iterations, invoke `external-research` to find new approaches before continuing. External research can only be invoked once per plateau.
7. **Cleanup**: `ai-slop-cleaner` (regression-safe)
8. **Verify**: `ac-verify` (single pass) or `ultraqa` (bounded cycles)
9. **Archive**: write WAL fragments + archive the task_brief
10. **Remember (optional)**: invoke `remember` skill to extract lessons learned into long-term memory. Use when the task surfaced non-obvious project constraints, anti-patterns, or validated approaches.

## Orchestration Steps

### Step 0 — Intake + Scope

Run `input-classifier` on the raw input. Use its `[Intake]` block as the seed for Steps 1–2.

Capture:
- Objective (what changes, what must not)
- File boundary (explicit in-scope paths)
- Acceptance criteria (what evidence means “done”) — from `[Intake].AC-Candidates` if available

### Step 1 — Create Task Artifacts

Create:
- `<slug>_task_brief.md`
- `<slug>_current_task.md`

### Step 2 — Run Phases in Order

- Plan → Decisions → Eval → (Approval Gate) → Implement → Verify → Archive

### Step 3 — Iteration Policy (if not met)

If acceptance criteria are not met:
- Produce a short delta analysis (what failed, why)
- Propose one next iteration (plan change or fix)
- Ask the user to approve another iteration (no silent looping)

## Related Skills
- [eval-harness](../eval-harness/SKILL.md): MUST precede self-improve; defines the objective baseline
- [self-improve](../self-improve/SKILL.md): bounded improvement loop requiring eval-harness baseline
- [remember](../remember/SKILL.md): optional post-archive knowledge preservation
- [external-research](../external-research/SKILL.md): plateau-breaker for stalled self-improve cycles
