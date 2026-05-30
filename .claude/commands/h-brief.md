---
description: TRIGGER at Phase 2 Propose start after risk classified OR user says 'create task brief' / '起草任务'. NOT FOR: PRD/EPIC decomposition (use /h-decompose); ticket ingestion (use /h-from-ticket); research report (use /h-research). Returns: schema-compliant task_brief + launch_spec binding.
argument-hint: <slug> [--risk low|medium|high] [--slim]
---

Generate a schema-compliant task_brief at the start of Phase 2 (Propose), then bind it into the active launch_spec. Substantive content lives in conversation memory — this command's job is to **lock in the contract structure** and the bidirectional binding, not to invent ACs.

## Step 1 — Parse `$ARGUMENTS`

Extract:

- `<slug>` (required, kebab-or-snake-case) — STOP and ask user if missing.
- `--risk low|medium|high` (optional) — explicit risk tier.
- `--slim` (optional) — **alias for `--risk low`**; identical effect, kept as ergonomic shorthand.

**Conflict rule:** `--slim` together with `--risk medium|high` is contradictory → STOP and ask user to pick one. `--slim` alone or `--risk low` alone are both fine.

If neither flag is provided: look for the `[triage]` block earlier in this conversation. Use `suggested_profile` to set risk (VIBE → reject this command; PATCH → LOW; STANDARD-MEDIUM → MEDIUM; STANDARD-HIGH → HIGH). If no `[triage]` found and conversation has no risk discussion → ask user via `AskUserQuestion` before proceeding. Do not silently default.

`spec_mode` is derived automatically from risk — no separate flag needed: LOW → SLIM, MEDIUM/HIGH → STANDARD.

## Step 2 — Compute paths

- Brief path: `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` (use today's date)
- If file already exists → invoke `AskUserQuestion` "slug collision" block below. Do NOT silently overwrite.

**Slug collision** AskUserQuestion:

```
Q: Brief already exists at <path> (created <ISO timestamp from file mtime>). How to proceed?
- Pick new slug (recommended) — provide alternate slug via Other; re-enter Step 2 with the new slug
- Resume prior brief — STOP /h-brief; use the resume command to continue prior work
- Delete prior + retry — main agent deletes prior file in-place, then re-renders Step 4
```

User picks "Delete prior + retry" → main agent `rm` the prior file, then proceeds to Step 3. Other choices → STOP with no state change.

## Step 3 — Decide `dimensions:` (STANDARD only; skip for SLIM)

Infer from Allowed Scope already discussed in this conversation. Default mapping:

| Path signature in Allowed Scope | dimension to add |
|---|---|
| `controller/`, `web/`, `*.controller.*`, `api/` | `api` |
| `mapper/`, `dao/`, `entity/`, `repository/`, migration SQL | `data` |
| `service/`, `*Service.java`, `usecase/`, `application/` | `domain` |
| `event/`, `*Event.java`, `*Listener.java`, `outbox/` | `domain` + `patterns` |
| `saga/`, `state-machine/`, `*Saga.java`, `*StateMachine.java` | `domain` + `patterns` |
| new bounded context / state machine / aggregate root | `domain` |
| new component, deployment topology change, new 3rd-party dep | `tech_arch` |
| explicit Strategy/Factory/Saga/Outbox/ACL discussion | `patterns` |

Allowed dimension keywords are exactly: `domain`, `api`, `data`, `tech_arch`, `patterns`. Do not invent new ones — `task_brief_gate.py` will reject anything else.

Empty `dimensions: []` is legal for pure internal refactor / harness tooling — use it deliberately, not as a fallback for laziness.

## Step 4 — Write the task_brief

Render the file at the path from Step 2. Schema source of truth: `.claude/wiki/schema/task_brief_schema.md`.

**For SLIM (LOW risk)**: include all 5 sections (Change Summary / Scope of Change / Risk & Rollback / Verification & Evidence) with the `spec_mode: SLIM` marker.

**For STANDARD**: emit the frontmatter (spec_mode + risk + dimensions) plus:
- **Always**: §1 Context, §5 Business Logic, §6 Non-Functional Constraints, §7 Acceptance Criteria (spec-floor; bodies MUST be substantive — no `None`/`N/A` placeholders)
- **Dimension-gated**: include §2/§3/§4/§8/§9 if and only if the corresponding dimension was added in Step 3. Omit the entire section header otherwise.

Fill in what conversation memory already established (slug context, ACs from Explorer phase, Allowed Scope, Hard Constraints). For sections without conversation evidence, write a **specific actionable placeholder** like:

```
<!-- TODO(h-brief): fill from Explorer findings. Required before Review phase. -->
```

NOT generic phrases like "to be filled". Placeholders MUST name what input is missing so the next session can complete it. Spec-floor sections (§1/§5/§6/§7) require substantive content — if conversation lacks the input, STOP after Step 4 and ask user to provide it, then re-run.

## Step 5 — Validate structure

Run:

```
python3 .claude/scripts/gates/task_brief_gate.py --require <brief path>
```

- exit 0 → continue
- exit 1 (WARN) → surface warning to user; continue
- exit 2 (FAIL) → revise the brief once based on the failure message; re-run. Second FAIL → STOP and ask user.

## Step 6 — Bidirectional bind to launch_spec

Locate the launch_spec to update:

- If `.claude/runs/launch-specs/launch_spec_*.md` files exist → use the latest (lexicographic last).
- Else → create `.claude/runs/launch-specs/launch_spec_<YYYY-MM-DD>.md` with this skeleton:

```markdown
# Launch Spec — <YYYY-MM-DD>

| Slug | Risk | Phase | Status | Depends On | Artifact |
|---|---|---|---|---|---|
```

Append a new row:

```
| <slug> | <LOW|MEDIUM|HIGH> | Propose | PENDING | <comma-separated upstream slugs, or "none"> | <brief path> |
```

**Bidirectional binding** means: the brief is written FIRST, then the row references it. Do not write the row before the brief exists on disk (lifecycle.md Phase 2 contract).

Do not mark the row `IN_PROGRESS` automatically — that transition belongs to the next phase (Review→Implement). Leave it `PENDING`.

## Step 7 — Report

Output exactly this block:

```
[Brief Status]: CREATED | INCOMPLETE
[Slug]: <slug>
[spec_mode]: SLIM | STANDARD
[Risk]: LOW | MEDIUM | HIGH
[Dimensions]: <comma-separated, or "n/a (SLIM)" or "[]">
[Brief Path]: <path>
[Launch Spec]: <path> (row appended)
[task_brief_gate]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Open Placeholders]: <count, with section numbers — e.g. "3 in §3 §4 §8">
[Next Action]: Run /h-design <slug> (MEDIUM/HIGH with `tech_arch` or `patterns` dimension), OR begin Implement directly (LOW, or no architectural dimension declared). If placeholders remain in spec-floor sections §1/§5/§6/§7: fill via conversation BEFORE /h-design.
```

## Hard constraints

- **Allowed edits**: only the new brief file + the target launch_spec. Nothing else.
- **No source-code edits**. If user wants to start coding, tell them to enter Implement phase via `/h-resume` after Approval Gate (HIGH) or after Review (MEDIUM).
- **No silent risk defaulting** — risk MUST come from `--risk` arg, `[triage]` block, or explicit user answer.
- **Refuse to overwrite** existing task_brief at the computed path.
- Anti-loop: max 2 retries on `task_brief_gate.py` revisions, then STOP.
