---
description: Archive current STANDARD task — WAL fragments → move task_brief → wiki lint → mark DONE
argument-hint: [slug]
---

Execute Phase 6 (Archive) per `.claude/rules/lifecycle.md` and Zone D of `.claude/rules/skill-precedence.md`. Steps are sequential; a failure in any step STOPS the flow and reports — do not skip ahead.

## Step 1 — Resolve target task_brief

- If `$ARGUMENTS` is non-empty: treat it as the slug, resolve to the latest matching `.claude/runs/task-briefs/*_<slug>_task_brief.md`.
- Else: run `python3 .claude/scripts/harness/find_active_task_brief.py` — stdout is the IN_PROGRESS row's task_brief path (empty if none).
- If neither yields a valid path → STOP and report: `No active task_brief — pass slug as argument or ensure launch_spec has an IN_PROGRESS row`.

Read the resolved task_brief's Machine Section before continuing. Capture: AC list, Allowed Scope, declared dependencies.

## Step 2 — Plan Deviation Reflection (mandatory, feeds extraction)

Append a `## Plan Deviation Reflection` section to the task_brief covering each bullet (write "none" if not applicable, do NOT silently omit):

- **Scope drift**: files edited outside Allowed Scope (path + reason) or "none"
- **Plan invalidations**: any `[Plan Invalidation]` raised mid-Implement and how resolved
- **Dependency accuracy**: declared upstream deps that did/did not actually block
- **Deferred ACs**: AC-id + PARTIAL/SKIP + reason
- **QA evidence pointer**: commit SHA or test output path

This section is the input contract for Step 3 — do not skip.

## Step 3 — User-elected WAL fragments

### 3a. Suggest dimensions from diff
Run `git diff HEAD~1 HEAD --name-only --diff-filter=AM` (or against the task's base commit if known) plus a content scan. Pre-check the dimensions whose patterns match:

- `*.sql` / `*Migration*` / DDL keywords (CREATE/ALTER/DROP) in diff → **Data**
- New `*Controller.java` / new `@RestController` / `@*Mapping` / new public DTO → **API**
- New `enum {` block / new state-machine class / new value object → **Domain**
- New `@Valid` / `@PreAuthorize` / new `DomainException` subclass / new business invariant in service code → **Rules**
- An ADR file was written under `.claude/wiki/wiki/architecture/adr/ADR-*.md` for this task → **Architecture**

If a dimension's signal is absent, leave it un-checked. The user can still toggle it on.

### 3b. Ask the user (mandatory question — silent zero-WAL is not allowed)
Use `AskUserQuestion` with a multi-select listing all five dimensions plus **None**. Each option must surface its pre-check state and the WHY (one line). Wording template:

```
Q: Which WAL fragments should we write for this task? (Suggested based on diff; adjust freely.)
- [✓] Domain — <reason: e.g. "new OrderStatus enum"> or "no signal in diff"
- [✓] API — <reason or "no signal in diff">
- [ ] Rules — <reason or "no signal in diff">
- [ ] Data — <reason or "no signal in diff">
- [ ] Architecture — <reason or "no ADR written for this task">
- [ ] None — record explicit decision to skip
```

If user picks **None** AND `risk: HIGH` in the task_brief, follow up with a single-question prompt for a one-line justification (the answer goes verbatim into the stub). MEDIUM tasks skip the follow-up.

### 3c. Write the selected fragments

**Path A — user chose ≥1 dimension:** Dispatch `knowledge-extractor` per skill-precedence Zone D, strictly from `.claude/rules/dispatch-template.md`:

- **Inputs**: include the line `[Chosen Dimensions]: <comma-separated list, e.g. "domain,api">` so the extractor writes only those — no other dimensions, no padding.
- **Source Documents**: the resolved task_brief with `#L<a>-L<b>` covering Machine Section + Plan Deviation Reflection (pointers, no summaries — see dispatch-template anti-summarization contract). For each chosen dimension, also add pointers to the diff files most relevant to it.
- **Acceptance Criteria**: one AC per chosen dimension, e.g. `AC-1: Domain WAL fragment written at expected path`. Do NOT include ACs for dimensions the user did not select.
- **Memory Snapshot**: copy any `type=user` / `type=feedback` entries relevant to WAL writing.

After the sub-agent returns:
```
python3 .claude/scripts/gates/subagent_return_gate.py --return-file <tmp> --task-kind extract
```
- exit 0 → continue
- exit 1 (WARN) → surface warning to user inline, continue
- exit 2 (FAIL) → re-dispatch ONCE with the template; second FAIL → STOP and ask user

Then verify the chosen dimensions were actually written:
```
python3 .claude/scripts/gates/writeback_gate.py --topic <slug> --date <YYYYMMDD> --require "<chosen-list>"
```

**Path B — user chose None:** Skip the sub-agent dispatch. Write a single stub file directly (you, the main agent, write it — no sub-agent needed for one file):

- Path: `.claude/wiki/wiki/domain/wal/<YYYYMMDD>_<slug>_stub.md`
- Content:
  ```markdown
  # WAL Stub - <YYYY-MM-DD> - <slug>

  Source spec: `<relative_path_to_task_brief.md>`

  ## WAL Election
  User elected: **None** — no WAL fragments written for this task.

  ## Justification
  <verbatim justification from user, or "n/a (MEDIUM task)">
  ```

Then verify:
```
python3 .claude/scripts/gates/writeback_gate.py --topic <slug> --date <YYYYMMDD> --accept-stub
```

## Step 4 — Conditional add-ons (skip with one-line reason if not applicable)

- An architectural decision was made during this task → invoke skill `architecture-decision-records` to write the ADR file under `.claude/wiki/architecture/wal/`.
- A non-obvious constraint, invariant, or cross-session fact surfaced → invoke skill `remember` to classify (project memory / notepad / durable doc).

Each add-on either runs OR gets a one-line skip reason in the final report.

## Step 5 — Move task_brief to archive

Derive `<slug>` from the resolved task_brief filename — the segment between `<YYYY-MM-DD>_` and `_task_brief.md`. Then run:

```
python3 .claude/scripts/tools/archive_session_artifacts.py --slug <slug>
```

Confirm afterwards that `.claude/wiki/archive/<date>_<slug>_task_brief.md` exists and `.claude/runs/task-briefs/<original>` is now a pointer file.

If a collab file exists for this task (`find .claude/runs/collabs/*_<slug>_collab.md`):
- Status `SIGNED_OFF` → move to `.claude/wiki/archive/collabs/<date>_<slug>_collab.md`
- Status not `SIGNED_OFF` → warn: `Collab for <slug> is not yet signed off. Archive anyway? (deliverable will be moved but marked UNRESOLVED)`. If user confirms, move with `status: UNRESOLVED` appended.

## Step 6 — Wiki lint

Run `python3 .claude/scripts/wiki/wiki_linter.py`.

- OK / WARN → proceed (surface WARN details inline so user can decide whether to fix later)
- FAIL → STOP, do NOT proceed to Step 7, report the failure with the script's exact output

## Step 7 — Mark launch_spec row DONE

Edit the latest `.claude/runs/launch-specs/launch_spec_*.md` — change this task's row status from `IN_PROGRESS` to `DONE`. Do not touch other rows.

## Step 8 — Final report

Output exactly this block, nothing else:

```
[Archive Status]: COMPLETE | PARTIAL | FAILED
[Task]: <slug>
[Archived task_brief]: <new wiki/archive/ path>
[WAL fragments]: <comma-separated paths, or "none">
[ADR]: <path or "n/a — no architectural decision">
[remember entries]: <list or "n/a — no cross-session knowledge">
[wiki_linter]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Plan Deviations]: <one-sentence summary>
[Next]: <one sentence — usually "ready for next task" or a deferred-AC follow-up>
```

## Hard constraints (apply to YOU executing this command)

- **Allowed edit set**: `.claude/wiki/**/wal/`, the resolved task_brief, the target `launch_spec_*.md`, and any ADR/memory files written in Step 4. NO source-code edits.
- **Anti-loop**: max 2 retries per step. Second failure of the same step → STOP and ask user.
- **Step ordering is fixed**: do not pre-emptively reorder or merge steps. Step 2 must precede Step 3 (extractor depends on the reflection section).
- **PATCH profile tasks must not invoke this command** — Archive WAL is only for STANDARD profile (per `.claude/rules/policy.md` Part 2). If `$ARGUMENTS` resolves to a PATCH task_brief, STOP and report.
