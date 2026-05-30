---
description: TRIGGER at session start when prior work is in flight OR user says '继续上次' / 'where were we'. NOT FOR: queue overview (use /h-status); starting fresh (use /h-brief or /h-from-ticket). Returns: active task_brief path + Machine Section loaded into context + phase for resumption.
---

Implement CLAUDE.md "Session Start step 2" / lifecycle.md "Resume protocol". You are recovering context after a session interruption.

## Step 1 — Locate the latest launch_spec

Run `python3 .claude/scripts/harness/find_active_task_brief.py`. Stdout is either an active task_brief path or empty.

**Branch on the result:**

- **Empty stdout** → either no launch_spec exists, no IN_PROGRESS row, or the pointed task_brief is missing. Fall through to Step 2 (diagnose) before reporting.
- **Non-empty stdout** → that path is the active task_brief. Skip to Step 3.

## Step 2 — Diagnose when no active task_brief

List `.claude/runs/launch-specs/launch_spec_*.md`. Then:

| State observed | Report and stop |
|---|---|
| Directory missing or no launch_spec files | `No resumable state — clean slate. Ready for a fresh task.` |
| launch_spec exists, only `DONE`/`FAILED` rows | `Queue complete (N DONE / M FAILED). No active work to resume.` Surface FAILED rows if any. |
| launch_spec has `WAITING_APPROVAL` rows | `Task <slug> is WAITING_APPROVAL — surface its task_brief Human Section, ask user to approve/reject before resuming.` Read that brief's Human Section and present it. |
| `IN_PROGRESS` row Artifact column contains `\| COLLAB:<collab-slug>` | Read `.claude/runs/collabs/*_<collab-slug>_collab.md`. Surface `status`, `open_questions`, and `deliverable_path`. Report: `Task is IN_PROGRESS but pending external collab review. Run /h-collab-update <collab-slug> to log feedback or sign off before continuing implementation.` |
| launch_spec has only `PENDING` rows | `N pending tasks. Suggest starting <first-pending-slug> next.` List dependencies if any row has unmet `Depends On`. |
| `IN_PROGRESS` row exists but Artifact path is broken (file missing or already in `.claude/wiki/archive/`) | INCONSISTENT — invoke `AskUserQuestion` per block below; do NOT auto-fix without explicit selection. |

When INCONSISTENT, invoke `AskUserQuestion`:

```
Q: IN_PROGRESS row points to <Artifact path> which is missing or already archived. How to resolve?
- Mark DONE (recommended) — prior /h-archive likely succeeded but didn't update launch_spec; flip row to DONE
- Restore IN_PROGRESS pointer — recover artifact from archive if path is in wiki/archive/; manual editing required
- Investigate manually — STOP, surface diagnostic dump, await user instruction
```

User selection drives the action; do NOT execute any state change before the answer. After the chosen action completes (or "Investigate manually" → diagnostic dump), STOP.

## Step 3 — Load task_brief Machine Section

Read the resolved task_brief in full. From it, capture:

- **spec_mode** (`SLIM` or `STANDARD`) and **risk** (LOW/MEDIUM/HIGH) from frontmatter
- **Dimensions** declared (STANDARD only)
- **Allowed Scope** — exhaustive file list / path prefixes
- **Acceptance Criteria** (§7) — copy verbatim with AC-id assignments
- **Hard Constraints** (§6)
- **Plan Deviation Reflection** — if present, this task is partially or fully through Archive; warn user.

## Step 4 — Determine current Phase

Inspect the launch_spec row for this task. Look for a Phase column (typical values: `Explore`, `Propose`, `Review`, `Approval`, `Implement`, `QA`, `Archive`).

- **Phase column present** → that is the resume point.
- **Phase column absent** → infer from task_brief state:
  - No §7 Acceptance Criteria → still in Explore/Propose
  - §7 present, no code edits visible via `git log --oneline --since="7 days ago"` touching Allowed Scope → at Review/Approval boundary
  - Code edits exist + no QA evidence in `## Plan Deviation Reflection` → mid-Implement
  - QA evidence present, no archive pointer → ready for Archive (suggest `/h-archive`)
- **Phase HIGH-risk + Approval not yet given** → present Human Section, do not proceed past Approval Gate.

## Step 5 — Restore context summary

Output exactly this block, nothing else:

```
[Resume Status]: READY | BLOCKED | INCONSISTENT
[launch_spec]: <path>
[Task]: <slug> (risk=<LOW|MEDIUM|HIGH>, spec_mode=<SLIM|STANDARD>)
[task_brief]: <path>
[Current Phase]: <phase>
[Allowed Scope]: <comma-separated paths/prefixes>
[Acceptance Criteria]:
  - AC-1: <Given/When/Then>
  - AC-2: ...
[Hard Constraints]: <one-line summary>
[Pending Approvals]: <list or "none">
[Failed Gates (last 7d)]: <from failure_memory.py summary, or "none">
[Next Action]: <one specific sentence — e.g. "run /h-archive", "write failing test for AC-2", "request Approval Gate review on Human Section">
```

Optionally append: `[Notes]: <anything anomalous worth flagging>`.

## Hard constraints

- **Read-only by default** — Steps 1, 3, 4, 5 MUST NOT edit any file. Auto-recovery is FORBIDDEN.
- **Single user-authorized write exception**: Step 2 INCONSISTENT branch + user selects "Mark DONE" → flip the broken IN_PROGRESS row to DONE in the target `launch_spec_*.md`. NO other writes permitted.
- **No code execution** beyond the listed probe scripts (`find_active_task_brief.py`, optional `failure_memory.py summary`).
- **No sub-agent dispatch** — this is a synchronous probe.
- Anti-loop: if any probe script fails twice, STOP and report the script error verbatim.
