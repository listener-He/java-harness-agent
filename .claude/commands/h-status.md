---
description: List all launch_spec tasks at a glance — global queue view (PENDING / IN_PROGRESS / WAITING_APPROVAL / DONE / FAILED) with parallelizable next steps
argument-hint: [--all] [--days <N>] [--slug <prefix>]
---

Read-only global queue view. Complements `/h-resume` (which only loads the IN_PROGRESS task). Use when you forget what's in flight, when triaging a backlog, or before `/h-release` (which requires all rows DONE/FAILED).

## Step 1 — Parse `$ARGUMENTS`

- `--all` (optional): show every row regardless of age. Default: hide DONE rows older than 7d and FAILED rows older than 30d.
- `--days <N>` (optional): override the recency cutoff for DONE/FAILED rows.
- `--slug <prefix>` (optional): filter rows whose slug starts with this prefix (e.g. `--slug ci-` to list only CI-derived tasks).

## Step 2 — Locate launch_specs

```bash
ls -1 .claude/runs/launch-specs/launch_spec_*.md 2>/dev/null | sort
```

- 0 files → STOP: `No launch_spec found. Start work with /h-brief, /h-from-ticket, /h-decompose, or /h-research.`
- 1+ files → read the **latest** (lexicographic last) by default. With `--all`, read every spec and merge rows.

## Step 3 — Parse rows

Each launch_spec is a markdown table with columns: `Slug | Risk | Phase | Status | Depends On | Artifact`.

Parse all rows, applying `--slug` filter if provided. For DONE/FAILED rows, apply the recency cutoff (from filesystem mtime of the linked artifact, or fall back to today if no artifact).

Detect Artifact column markers:
- `| COLLAB:<date>-<slug>` → task has external review pending
- `| PR #<n>` → PR open, awaiting merge

## Step 4 — Aggregate by status

Group rows into these buckets, in this order:

1. **IN_PROGRESS** (in flight — most important)
2. **WAITING_APPROVAL** (HIGH-risk Approval Gate)
3. **PENDING — Parallelizable Now** (Depends On = none OR all upstream DONE)
4. **PENDING — Blocked** (upstream not yet DONE — show the blocker slug)
5. **DONE recently** (within recency window)
6. **FAILED** (within recency window)

Within each bucket, sort by Risk (HIGH → MEDIUM → LOW → RES), then alphabetic by slug.

## Step 5 — Compute Next Action

Priority chain (first match wins):

1. Any **WAITING_APPROVAL** row → `Run /h-resume to load <first WAITING_APPROVAL slug> — review Human Section and approve/reject`
2. Any **IN_PROGRESS** row → `Run /h-resume to continue <first IN_PROGRESS slug>` (if multiple IN_PROGRESS, mention count + recommend reducing to ≤ 3 concurrent)
3. Any **IN_PROGRESS** row with `COLLAB:` marker → `Run /h-collab-update <slug> to log external feedback or sign off`
4. Any **IN_PROGRESS** row with `PR #` marker → `PR awaiting merge. After merge, run /h-archive <slug> to close out.`
5. **PENDING — Parallelizable Now** exists → `Flip <first parallelizable slug>'s status to IN_PROGRESS, then run /h-resume`
6. **Only PENDING — Blocked** → `All pending work is blocked. Unblock by completing: <list upstream slugs>`
7. **Only DONE/FAILED** → `Queue clean. Ready for new work via /h-brief, /h-from-ticket, /h-decompose, or /h-research. If preparing release, run /h-release.`

## Step 6 — Report

Output exactly this block:

```
[Queue Status]
[Source]: <latest launch_spec path> (or "merged from N launch_specs" if --all)
[Filter]: slug_prefix=<value or "none">, age_cutoff=<DONE/FAILED window in days>
[Totals]: in_progress=<N>, waiting_approval=<N>, pending_now=<N>, pending_blocked=<N>, done_recent=<N>, failed_recent=<N>

[IN_PROGRESS] (<count>)
  - <slug> | <risk> | <phase> | <markers if any> | <artifact>

[WAITING_APPROVAL] (<count>)
  - ...

[PENDING — Parallelizable Now] (<count>)
  - <slug> | <risk> | <phase> | (no blockers)

[PENDING — Blocked] (<count>)
  - <slug> ← blocked by: <upstream slug(s)>

[DONE recently] (<count>)
  - <slug> | <risk> | finished within cutoff

[FAILED] (<count>)
  - <slug> | <risk> | <reason from row note or "see brief">

[Next Action]: <from Step 5 priority chain>
```

If any bucket has > 50 rows, truncate with `(<N more hidden — re-run with --slug filter)`.

## Hard constraints

- **Read-only.** No edits to launch_spec, briefs, or any other file. Pure probe.
- **No sub-agent dispatch.** Synchronous parsing only.
- **Do NOT auto-flip status.** Even when a row's upstream is DONE, this command surfaces the parallelizable opportunity — flipping `PENDING → IN_PROGRESS` is the user's call (or `/h-resume`'s).
- Anti-loop: not applicable — this is a single-pass report. If the launch_spec table is malformed, surface the parse error verbatim and STOP.
