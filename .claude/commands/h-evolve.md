---
description: Transform a high-confidence insight into a concrete rule-change proposal — pick insight, generate file/line edit suggestion, require human approval before applying. TRIGGER: agent or user wants to act on an active insight. NOT FOR: routine insight viewing (use /h-context-check).
argument-hint: [--insight-id <id>] [--auto-pick] [--apply]
---

The bridge between observation (Insight Layer) and modification (CLAUDE.md / rules / hooks). Insight detector finds patterns, this command turns one into a proposed edit. Human always approves before edit applies.

## Step 1 — Parse args

| Arg | Effect |
|---|---|
| `--insight-id <id>` | Operate on a specific insight (id from `insight_writer query` output) |
| `--auto-pick` | Pick highest-confidence active insight (status=new, confidence=high preferred) |
| `--apply` | After generating proposal AND user confirming, apply the edit + mark insight `acted_on`. WITHOUT `--apply`: proposal only, no file changes. |

Default (no args): list top 3 active insights, ask user to pick one via `AskUserQuestion`.

## Step 2 — Load the insight

```bash
python3 .claude/scripts/local_intel/insight_writer.py query --top 10 --min-confidence medium --json
```

Filter to `id == <insight-id>` or pick top result if `--auto-pick`.

If no matching insight → STOP with "no active insight with id <X>".

## Step 3 — Generate proposal by insight kind

Each insight kind maps to a different proposal shape. Pick the one that matches the loaded insight's `kind`:

### `recurring_failure_cluster` → propose gate predicate refinement

- Read the gate script (`evidence[0].gate` is the script name in `.claude/scripts/gates/`)
- Identify the predicate that's recurring-failing
- Propose ONE of:
  - **Widen allowlist** (if gate is too strict on a category): e.g. add `*.yml` to `_IS_IMPLICITLY_ALLOWED` in scope_guard
  - **Refine pattern** (if regex over-matches): make the false-positive pattern more specific
  - **Lower severity** (if WARN suffices): change exit 2 → 1 for this case
- Output the specific diff target.

### `co_edit_cluster` → propose task_brief scope template

- Read the co-edited files (`evidence[0].paths`)
- Propose adding a "common scope template" note to `.claude/wiki/wiki/api/index.md` or the relevant domain index:
  "When editing X, also include Y, Z in Allowed Scope (co-edited ≥N times in 30d)"
- This is a wiki update, not a rule change — agent reference, not enforcement

### `decayed_knowledge` → propose archive move

- Read `evidence[0].path`
- Propose `mv <path> .claude/wiki/archive/` or `git rm` if truly obsolete
- Show the file content (head -20) so user can decide

### `override_drift` → propose gate threshold loosening

- Read `evidence[0].env_var` and `top_files`
- If `top_files` show a common pattern (e.g. all `test_*.yml`):
  - Propose adding that pattern to the gate's exemption list
- Otherwise:
  - Propose lowering the gate's strictness (e.g. WARN instead of FAIL for the category)
- Show the gate script's predicate location

## Step 4 — Output proposal block

Render exactly:

```
[evolve-proposal] insight=<id>

Summary: <insight summary>
Suggested action: <insight suggested_action>

Proposed change:
  File: <relative path>
  Locate: <line range or grep pattern>
  Replace/Add:
    <new content snippet>

Rationale:
  Evidence:
    - <bullet from insight evidence>
  Risk if applied:
    <one-line worst case if change is wrong>
  Risk if not applied:
    <one-line cost of leaving as-is>

To apply: invoke /h-evolve --insight-id <id> --apply (will Edit + mark acted_on).
To dismiss: invoke insight_writer.py mark-status --id <id> --status dismissed
To leave for later: do nothing (status stays as new/acknowledged).
```

## Step 5 — If `--apply` is set

1. Re-confirm with user via `AskUserQuestion`: "Apply the proposed change to <file>? Yes / No / Show diff first"
2. On Yes: use `Edit` tool with the exact proposed change
3. On success: `python3 .claude/scripts/local_intel/insight_writer.py mark-status --id <id> --status acted_on`
4. On error: STOP, do not mark status; report the error

## Hard constraints

- **Never apply without explicit `--apply` AND explicit user Yes** — proposal-only is the default
- **Never auto-apply multiple insights in one invocation** — one insight per `/h-evolve` run, even with `--auto-pick`
- **Never invent evidence** — every claim in the proposal must trace back to the insight's `evidence` field
- **Never modify the insight in place** — status changes go through `insight_writer.py mark-status` (append-only audit)
- **Never propose changes to** `.claude/runs/` (runtime state, not policy)
- **Read-only by default** — Step 4 always runs; Step 5 only with `--apply`

## When NOT to use this command

- For surfacing insights → use `/h-context-check` (it queries automatically)
- For dismissing without proposal → use `insight_writer.py mark-status --status dismissed` directly
- For ad-hoc rule changes not tied to an insight → just edit the file directly (no insight ceremony needed)
