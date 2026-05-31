---
description: Turn a high-confidence insight into a concrete rule-change proposal. Pick insight → generate file/line edit suggestion → human approves → optional --apply. TRIGGER: agent or user wants to act on an active insight. NOT FOR: routine insight viewing (use /h-context-check).
argument-hint: [--insight-id <id>] [--auto-pick] [--apply]
---

Bridges Insight Layer (L2) and Enforce Layer (L4). Insight detector finds patterns, this command turns one into a concrete edit proposal. Human always approves before applying — `--apply` is two-step (proposal then AskUserQuestion).

## Step 1 — Parse args

| Arg | Effect |
|---|---|
| `--insight-id <id>` | Operate on specific insight (id from `insight_writer query` output) |
| `--auto-pick` | Pick highest-confidence active insight (status=new, confidence=high preferred) |
| `--apply` | After proposal AND user confirms via `AskUserQuestion`, apply the Edit + mark insight `acted_on`. WITHOUT `--apply`: proposal only, no file changes. |

Default (no args): list top 3 active insights, ask user to pick one via `AskUserQuestion`.

## Step 2 — Load the insight

Run:
```bash
python3 .claude/scripts/local_intel/insight_writer.py query --top 10 --min-confidence medium --json
```

Filter to `id == <insight-id>` (explicit) OR pick first result (`--auto-pick`).

If no matching insight → STOP with `[Evolve Status]: NO_INSIGHT` block (see Step 5) and exit.

## Step 3 — Generate proposal by insight kind

Each `kind` has its own proposal shape. Use the matching template below; do NOT mix.

### Step 3.1 — `recurring_failure_cluster` (gate predicate refinement)

Inputs from insight evidence: `gate`, `phase`, `pattern`, `count`.

Proposal template:
- Read script `.claude/scripts/gates/<gate>.py`
- Identify the predicate / regex causing repeat FAIL
- Pick ONE refinement strategy:
  - **Widen implicit allowlist** — if the pattern repeats on a clearly-benign category (e.g. test fixtures): add a path prefix / glob to the gate's `IMPLICIT_ALLOWED_PREFIXES` or equivalent
  - **Refine pattern specificity** — if a regex over-matches: narrow it (add word boundary / negative lookbehind / extend keyword)
  - **Downgrade severity** — if FAIL is too strict: change `EXIT_FAIL` → `EXIT_WARN` for this branch
- Output the exact file path + line range + replace string in the Step 4 block

### Step 3.2 — `co_edit_cluster` (wiki scope template)

Inputs: `paths` (list), `total_pair_count`, `member_count`.

Proposal template:
- Locate the most-relevant wiki domain index for the cluster (e.g. `.claude/wiki/wiki/api/index.md` if endpoints; `.claude/wiki/wiki/data/index.md` if DB; `.claude/wiki/wiki/architecture/index.md` if cross-cutting)
- Propose adding a "Common scope clusters" section with the file list:
  ```
  When editing one of these, list ALL in Allowed Scope upfront:
  - <file1>
  - <file2>
  - <file3>
  ```
- This is a reference update, not enforcement — agents read it when writing task_brief

### Step 3.3 — `decayed_knowledge` (archive or refresh)

Inputs: `path`, `age_days`, `last_read_days`.

Proposal template, choose ONE:
- **Archive** (if content still useful but rarely consulted):
  ```
  mv <path> .claude/wiki/archive/  # or wiki/archive/incidents/ for old incidents
  ```
- **Delete** (if content contradicted by current code or fully superseded):
  Show file `head -20` so user can decide; if delete chosen: `git rm <path>`
- **Refresh** (if claim might be stale but still relevant):
  Open file, propose a section to update; defer the actual rewrite to a separate /h-distill-from-code run

### Step 3.4 — `override_drift` (gate threshold or allowlist)

Inputs: `env_var`, `count_30d`, `top_files`.

Proposal template:
- Identify the gate the env var bypasses (`CLAUDE_SECRETS_BYPASS` → `secrets_linter`; `CLAUDE_SCOPE_GUARD_BYPASS` → `scope_guard`)
- Inspect `top_files` for a common pattern:
  - **Pattern detected** (e.g. all files match `test/*.yml`): propose adding that pattern to the gate's exemption list with comment "(systematic bypass → exempted via /h-evolve insight <id>)"
  - **No pattern** (top_files are diverse): propose lowering gate strictness for the relevant category, OR open a wiki doc explaining when the bypass is legitimate so future agents document context

### Step 3.5 — `user_correction` (agent behavior review)

Inputs: `phrase`, `count`, `recent_excerpts`, `bound_to_prior_action`.

Proposal template (this kind RARELY proposes a file edit — usually proposes a review action):
- Surface the 3 recent excerpts + window
- Suggest the user run:
  ```bash
  python3 .claude/scripts/local_intel/events_query.py --since 7d \
    | grep -B5 '<correction prompt text>'
  ```
  to manually correlate the corrections with what agent had just done
- If a clear pattern emerges (e.g. agent always over-classifies prompts mentioning "performance" as STANDARD-HIGH), propose a CLAUDE.md / lifecycle.md Risk Classification table refinement
- DO NOT propose an automated agent rule change from this insight kind — frustration patterns need human interpretation

## Step 4 — Output proposal block

Render exactly:

```
[evolve-proposal] insight=<id> kind=<kind>

Summary: <insight.summary>
Suggested action: <insight.suggested_action>

Proposed change:
  File: <relative path>
  Locate: <line range or grep pattern>
  Replace/Add:
    <new content snippet, full enough to apply unambiguously>

Rationale:
  Evidence:
    - <bullet from insight.evidence>
  Risk if applied:
    <one-line worst case>
  Risk if NOT applied:
    <one-line cost of leaving as-is>

To apply now:        /h-evolve --insight-id <id> --apply
To dismiss:          python3 .claude/scripts/local_intel/insight_writer.py mark-status --id <id> --status dismissed
To defer:            do nothing (status stays new/acknowledged)
```

## Step 5 — If `--apply` is set

1. Use `AskUserQuestion`: "Apply the proposed change to `<file>`? (Yes / No / Show diff first)"
2. On **Yes**: use `Edit` tool with the exact proposed snippet
3. On **success**: `python3 .claude/scripts/local_intel/insight_writer.py mark-status --id <id> --status acted_on`
4. On **error** during Edit: report + STOP, do NOT mark status; user investigates
5. On **No / dismiss**: `mark-status --status dismissed`
6. On **Show diff first**: re-render Step 4 block + ask again

## Step 6 — Final report

Emit the structured status block (greppable):

```
[Evolve Status]: PROPOSED | APPLIED | DISMISSED | NO_INSIGHT | ERROR
[Insight ID]: <id> | n/a
[Insight Kind]: <kind> | n/a
[File Touched]: <path> | none
[New Insight Status]: <new|acknowledged|acted_on|dismissed>
[Next Action]: <one-line — what user/agent should do next>
```

## Hard constraints

| Constraint | Rule |
|---|---|
| **Allowed edit set** | Step 4 (proposal): **none** — proposal block only. Step 5 (--apply): EXACTLY the file named in proposal, EXACTLY the snippet shown; nothing adjacent. |
| **Source-code edits FORBIDDEN** | Never propose a `src/**` edit from `/h-evolve`. Insight-driven evolution is for harness rules / wiki / gates / hooks, not application code. Application-code changes go through normal `/h-brief`. |
| **Anti-loop** | Max 1 insight per invocation. `--auto-pick` returns the top one only. To act on multiple, invoke /h-evolve multiple times. |
| **Skip-path semantics** | No insight matches → `[Evolve Status]: NO_INSIGHT` and exit 0. User explicit cancel → `[Evolve Status]: DISMISSED` + mark_status dismissed. |
| **Idempotency** | Re-invoking on same `--insight-id` after successful apply → `[Evolve Status]: NO_INSIGHT` (status is now acted_on, no longer active). |
| **Audit** | EVERY status change goes through `insight_writer.py mark-status` (append-only log). Never modify insights.jsonl directly. |
| **Sub-agent dispatch** | None — /h-evolve is a pure orchestrator; no Agent tool. |

## Out of scope

- Surfacing insights for routine review → `/h-context-check`
- Generating insights from scratch → `insight_detector.py` (auto-invoked by /h-context-check)
- Manually marking an insight dismissed without reading → use `insight_writer.py mark-status --status dismissed` directly; no need for /h-evolve ceremony
