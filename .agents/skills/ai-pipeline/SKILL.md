---
name: ai-pipeline
description: "Orchestrate the repo-aligned AI engineering pipeline (plan → decisions → eval → improve → cleanup → verify → archive) with explicit approval gates. TRIGGER when user asks to run the full pipeline or go from idea to delivery; DO NOT TRIGGER for small tasks or when user invokes a specific phase."
---

# AI Pipeline — Repo-Aligned Orchestration

Orchestrate the full “idea → delivery” pipeline while staying strictly compatible with this repository’s workflow gates and artifact conventions.

## Hard Compatibility Rules

- Follow `AGENTS.md` lifecycle gates and roles (including Approval Gate and Archive/WAL).
- All runtime artifacts MUST be written under `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_*`.
- No external state directories, no implicit git/CI automation.
- No infinite loops. Any iterative improvement requires explicit user approval to continue.
- Only delegate to available agent types (e.g., search) and provide self-contained context.

## When to Use

- User asks to “run the pipeline / full pipeline”
- Work spans multiple phases: planning + decision records + evaluation + implementation + cleanup + verification

Do not use when the user requests a single phase explicitly (e.g., “just write the plan”).

## Pipeline (Repo Lifecycle Mapping)

1. **Design**: `brainstorming` (when creative) → `writing-plans` or `blueprint`
2. **Decisions**: `architecture-decision-records`
3. **Evaluation**: `eval-harness` (define pass/fail and verification commands)
4. **Approval Gate**: if risk is MEDIUM/HIGH, stop after spec and wait for approval
5. **Implement**: implement the plan in-scope only
6. **Improve (optional)**: `self-improve` (bounded iterations, user-approved)
7. **Cleanup**: `ai-slop-cleaner` (regression-safe)
8. **Verify**: `verify` (single pass) or `ultraqa` (bounded cycles)
9. **Archive**: write WAL fragments + archive the OpenSpec

## Orchestration Steps

### Step 0 — Establish Goal + Scope

Capture:
- Objective (what changes, what must not)
- File boundary (explicit in-scope paths)
- Acceptance criteria (what evidence means “done”)

### Step 1 — Create Task Artifacts

Create:
- `<slug>_focus_card.md`
- `<slug>_openspec.md`
- `<slug>_current_task.md`

### Step 2 — Run Phases in Order

- Plan → Decisions → Eval → (Approval Gate) → Implement → Verify → Archive

### Step 3 — Iteration Policy (if not met)

If acceptance criteria are not met:
- Produce a short delta analysis (what failed, why)
- Propose one next iteration (plan change or fix)
- Ask the user to approve another iteration (no silent looping)
