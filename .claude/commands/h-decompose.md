---
description: Decompose a PRD/EPIC into INVEST subtasks + scaffold per-subtask briefs + bind to launch_spec
argument-hint: <slug> <prd-path | --from-paste> [--input-type prd|epic] [--no-scaffold]
---

Pipeline that takes a monolithic PRD or EPIC and produces: (1) a structured `<date>_<slug>_tasks.md`, (2) per-subtask task_brief skeletons via `brief_from_decomposition.py`, (3) launch_spec rows linking everything. Without this command, the LLM has to remember to chain three steps and easily forgets the launch_spec binding.

## Step 1 — Parse `$ARGUMENTS`

Extract:
- `<slug>` (required, kebab-or-snake-case) — the EPIC/PRD identifier. STOP if missing.
- `<prd-path>` OR `--from-paste` (required, mutually exclusive).
  - File path: must exist, must be a readable `.md` or `.txt`.
  - `--from-paste`: invoke `AskUserQuestion` asking user to paste the PRD/EPIC content in the next message; write it to `.claude/runs/decompositions/<date>_<slug>_input.md` before continuing.
- `--input-type prd|epic` (optional). If omitted, infer:
  - Multi-section markdown with explicit "Requirements" / "User Stories" / "需求列表" headings → PRD
  - Single coherent feature description without enumerated requirements → EPIC
- `--no-scaffold` (optional): produce only the `_tasks.md`, skip `brief_from_decomposition.py` and launch_spec binding.

If `.claude/runs/task-briefs/*_<slug>_*.md` already exists → STOP and report collision. Pick a new slug or remove the prior artifacts explicitly.

## Step 2 — Pre-decomposition validation (mandatory, per task-decomposition-guide §0)

Branch on input-type:

**PRD path** — invoke `product-manager-expert` skill Mode A (Ingestion) on the input.
- Read its output: validated requirement list, conflicts flagged (if any).
- If CRITICAL conflicts → STOP and surface them. Do not proceed to decomposition with embedded conflicts.

**EPIC path** — invoke `adversarial-review` skill with Category C, EPIC frame:
> "Assume the task decomposition has a hidden sequential dependency that makes parallel execution impossible. Which two tasks, and what shared state forces the ordering?"
- CRITICAL → resolve before decomposing.
- MINOR → continue; annotate affected subtasks with `[Dep-Risk]` in Step 3 output.

One round only.

## Step 3 — Invoke task-decomposition-guide skill

Call the skill explicitly with the validated input. The skill enforces INVEST and Vertical Slicing.

Required output file: `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_tasks.md` (use today's date).

The `_tasks.md` MUST follow the format `brief_from_decomposition.py` expects:
- `### Task <id>: <name>` headers per subtask
- Per-subtask fields: `Goal`, `Type`, `Dependencies`, `Effort` (Simple|Medium|Complex), `Handoff Artifact`
- Per-subtask `Acceptance Criteria` as `- [ ] <text>` checkbox list

If `brief_from_decomposition.py --tasks <file>` (dry-run via `--help` is not available; just attempt parse and check) rejects the format, revise once, then STOP.

## Step 4 — INVEST quality gate (inline self-check)

Before scaffolding briefs, audit each subtask in the `_tasks.md`:

| Letter | Check |
|---|---|
| **I**ndependent | Does any subtask have >2 `Dependencies`? → flag for re-slice |
| **N**egotiable | Does the task description prescribe implementation (`how`)? → rewrite as `what + why` |
| **V**aluable | Can you state the business or technical outcome in one sentence? |
| **E**stimable | Is `Effort` filled with `Simple`/`Medium`/`Complex`? Missing → reject |
| **S**mall | Any `Complex` task with >15 file impact? → recommend further slicing |
| **T**estable | Each subtask has ≥1 AC checkbox? Missing → reject |

If any reject criterion fires, revise the `_tasks.md` once. Second revision-required signal → STOP and ask user.

## Step 5 — Scaffold per-subtask briefs (skip if `--no-scaffold`)

Run:

```
python3 .claude/scripts/tools/brief_from_decomposition.py --tasks .claude/runs/task-briefs/<date>_<slug>_tasks.md
```

The script writes one skeleton per subtask under `.claude/runs/task-briefs/<slug>_part_<i>_task_brief.md`. It pre-fills only what decomposition already knows; substantive content stays as placeholders to be filled at each subtask's own Propose phase.

If the script exits non-zero, surface stderr verbatim and STOP. Do not proceed to launch_spec binding with partial scaffolds.

## Step 6 — Bind all subtasks to launch_spec

For each scaffolded brief from Step 5:

- Resolve or create the latest `.claude/runs/launch-specs/launch_spec_<YYYY-MM-DD>.md` (same logic as `/h-brief` Step 6: use latest if exists, create with table header otherwise).
- Append one row per subtask:
  ```
  | <slug>_part_<i> | <risk inferred from Effort: Simple→LOW, Medium→MEDIUM, Complex→HIGH> | Propose | PENDING | <Depends On from _tasks.md, mapped to other part_<j> slugs, or "none"> | <brief path> |
  ```

All rows start as `PENDING`. Dependencies form a DAG — if you detect a cycle, STOP and report; cycles must be resolved at the decomposition layer (Step 3), not by editing launch_spec rows.

## Step 7 — Report

Output exactly this block:

```
[Decompose Status]: COMPLETE | PARTIAL | FAILED
[Slug]: <slug>
[Input Type]: prd | epic
[Subtasks]: <N>
[Tasks File]: .claude/runs/task-briefs/<date>_<slug>_tasks.md
[Briefs Scaffolded]: <list of part_<i> paths, or "skipped (--no-scaffold)">
[Launch Spec]: <path> (rows appended: <N>)
[Dependency Graph]:
  part_1 → (none)
  part_2 → part_1
  part_3 → part_1
  ...
[Parallelizable Now]: <list of subtasks with no unmet deps>
[Dep-Risk Flags]: <list from Step 2, or "none">
[Next Action]: <one specific sentence — typically "Start with /h-resume to pick up <first-parallelizable> via its part_<i> brief">
```

## Hard constraints

- **Allowed edits**: `.claude/runs/decompositions/*` (for paste input), `.claude/runs/task-briefs/<date>_<slug>_tasks.md`, scaffolded brief skeletons, and the target `launch_spec_*.md`. Nothing else.
- **No source-code edits** — decomposition is planning, not implementation.
- **Pre-decomposition validation is non-skippable** (Step 2). Skipping it embeds hidden conflicts/dependencies into the task graph — the entire reason `task-decomposition-guide` mandates §0.
- **Refuse to bind partial scaffolds** to launch_spec — all-or-nothing in Step 6 to keep the DAG consistent.
- **Cycle detection in Step 6 is mandatory** — a cyclic launch_spec is worse than no launch_spec.
- Anti-loop: max 1 revision per step (decomposition, INVEST audit, scaffold). Second failure → STOP and ask user.
