---
description: TRIGGER after external team replied to a /h-collab deliverable OR user says '外部团队反馈了' / 'frontend signed off'. NOT FOR: initial deliverable draft (use /h-collab). Returns: updated collab state + open items log + optional sign-off lifting WAITING_APPROVAL.
argument-hint: <slug> [--signoff] [--reviewer <name>]
---

Update the collab state for a task after receiving external team feedback. Works across sessions — finds the collab state file by slug without needing conversation context. Use `--signoff` when the external team has confirmed the deliverable and implementation can proceed.

## Step 1 — Parse `$ARGUMENTS`

- `<slug>` (required): collab slug (same as task slug). STOP if missing.
- `--signoff` (optional): mark this collab as signed off. Removes COLLAB marker from launch_spec.
- `--reviewer <name>` (optional): name/team who reviewed (e.g. `frontend-team`, `payment-vendor`). Stored in collab state.

## Step 2 — Locate collab state file

```bash
find .claude/runs/collabs -name "*_<slug>_collab.md" | sort | tail -1
```

If not found → STOP: `No collab found for slug <slug>. Run /h-collab <slug> first.`

Read the collab state file. Capture: `status`, `type`, `deliverable`, `task_brief`, `open_questions`, `feedback_log`.

Also read the deliverable file at the `deliverable` path — needed to show context when asking for feedback.

**Pre-flight: handle already-signed-off collab.** If `status: SIGNED_OFF` and `--signoff` was NOT passed, invoke `AskUserQuestion`:

```
Q: This collab is already signed off (signed_off_by: <name>, date: <date>).
   How do you want to re-engage with it?
- Add follow-up note only (recommended) — append to feedback_log without changing status; launch_spec untouched
- Re-open for amendments — flip status back to PENDING_REVIEW; re-append `| COLLAB:<date>-<slug>` marker to launch_spec Artifact column; then proceed to Step 3
- Cancel — STOP with no changes
```

Branch on selection:
- **Add follow-up** → ask the user for the note text (plain follow-up question in chat), append a `feedback_log` entry with `summary: <note>`, `changes_applied: no`, `questions_added: 0`, `blockers: none`. Status STAYS `SIGNED_OFF`. Skip Steps 3–6; jump to Step 7 Report with `[Collab Update Status]: UPDATED` and `[Collab Status]: SIGNED_OFF`.
- **Re-open** → in the collab state file, change `status: SIGNED_OFF` → `status: PENDING_REVIEW`, clear `signed_off_by` and `signed_off_date`, leave `feedback_log` intact. In the launch_spec, locate the slug's row and append `| COLLAB:<YYYYMMDD>-<slug>` back to the Artifact column. Then continue to Step 3.
- **Cancel** → STOP, zero writes.

If `--signoff` IS passed on an already-signed-off collab, treat as idempotent: skip to Step 7 with `[Collab Update Status]: UPDATED` and a note that status was already SIGNED_OFF.

## Step 3 — Collect feedback

If `--signoff` is NOT set → collect feedback via `AskUserQuestion`:

First question: "What did the external team say? Select all that apply."
- They approved the deliverable as-is
- They have questions / requested clarifications
- They requested changes to the deliverable
- They raised a blocker (something prevents sign-off)

Based on selection:

**Approved as-is** → skip to Step 4 with `--signoff` implied. Ask: "Who signed off?" → capture reviewer name.

**Questions / clarifications** → ask: "Paste or describe their questions (one per line)." Capture as list. For each question, ask: "Do you have an answer to provide now, or leave open?" If answered → capture as Q&A pair. If left open → add to `open_questions`.

**Requested changes** → ask: "Describe the changes requested." Then ask: "Do you want to update the deliverable now?" If yes → open the deliverable file content inline, apply the described changes, save. If no → record as open change request.

**Blocker** → ask: "Describe the blocker." Record in `feedback_log` with severity `BLOCKER`. Report: `[Collab Blocked] — Implement should NOT proceed until blocker is resolved.`

## Step 4 — Update deliverable (if changes were requested and user said yes)

Apply the described changes to the deliverable file. Only edit the deliverable — do not touch the task_brief or source code.

Update the `## Open Questions` section of the deliverable with any newly added open questions.

## Step 5 — Update collab state file

Append to `feedback_log`:
```yaml
- date: <YYYY-MM-DD>
  reviewer: <name or "unknown">
  summary: <one-line summary of what was received>
  questions_added: <N>
  changes_applied: yes | no
  blockers: <description or "none">
```

Update `open_questions` list (add new, remove resolved ones).

If `--signoff` or "Approved as-is" → update:
```yaml
status: SIGNED_OFF
signed_off_by: <reviewer>
signed_off_date: <YYYY-MM-DD>
open_questions: []
```

## Step 6 — Update launch_spec (signoff only)

If status is now `SIGNED_OFF`:

In the latest `launch_spec_*.md`, find the row for `<slug>`. Remove the `| COLLAB:<date>-<slug>` suffix from the Artifact column. Status remains `IN_PROGRESS` (task continues to Implement).

## Step 7 — Report

Output exactly this block:

```
[Collab Update Status]: UPDATED | SIGNED_OFF | BLOCKED
[Slug]: <slug>
[Reviewer]: <name or "not specified">
[Feedback Rounds]: <total count in feedback_log>
[Open Questions]: <N remaining>
[Deliverable Changes]: applied | none
[Collab Status]: PENDING_REVIEW | SIGNED_OFF | BLOCKED

[If SIGNED_OFF]:
  COLLAB marker removed from launch_spec. Ready to proceed with Implement.
  Next Action: Resume implementation — run /h-resume or continue directly.

[If PENDING_REVIEW]:
  <N> open questions remain. Share updated deliverable with external team.
  Next Action: Run /h-collab-update <slug> again after receiving answers.

[If BLOCKED]:
  Blocker: <description>
  Next Action: Resolve blocker with external team before proceeding to Implement.
```

## Hard constraints

- **Allowed edits**: collab state file, deliverable file (if changes requested), target `launch_spec_*.md` Artifact column (signoff only). No source-code edits. No task_brief edits.
- **Signoff removes the COLLAB marker** — it does NOT change launch_spec status from `IN_PROGRESS`. The task continues normally.
- **BLOCKED state does NOT change launch_spec** — it only records the blocker. Whether to pause Implement is a human decision, surfaced clearly in the report.
- **Do NOT auto-edit deliverable without user confirmation** — always ask before making changes to the deliverable content.
- Anti-loop: no retry logic needed — this is a data-entry command, not a gate runner.
