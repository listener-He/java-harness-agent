---
description: Archive current STANDARD/RESEARCH task — gate → move artifact → wiki lint → mark DONE
argument-hint: [slug]
---

Phase 6 / Phase R3 Archive. Sequential steps; any failure STOPS the flow.

## Step 0 — Resolve target + dispatch by mode

Resolve target artifact path:
- `$ARGUMENTS` non-empty → treat as slug → latest `.claude/runs/task-briefs/*_<slug>_task_brief.md` OR `.claude/runs/reports/*_<slug>_research.md`
- Else → `python3 .claude/scripts/harness/find_active_task_brief.py` (resolves IN_PROGRESS row's Artifact path)

Dispatch by path pattern (first match wins):

| Artifact path pattern | Mode | Branch |
|---|---|---|
| `.claude/runs/task-briefs/*_task_brief.md` | STANDARD | Step 1 → Step 8 (below) |
| `.claude/runs/reports/*_research.md` | RESEARCH | Step 1R → Step 4R (further below) |
| (no match) | — | invoke `AskUserQuestion` per block below |

When no pattern matches but `find_active_task_brief.py` returned non-empty (path exists but unrecognized), or `$ARGUMENTS` slug resolved to ambiguous candidates, invoke `AskUserQuestion`:

```
Q: Artifact path "<resolved>" does not match a known archive mode. How to proceed?
- Treat as STANDARD — point me at the task_brief path
- Treat as RESEARCH — point me at the report path
- Abort — I'll diagnose the launch_spec manually
```

If user picks STANDARD or RESEARCH, follow up with a single text input asking for the actual file path (use `AskUserQuestion` with one option labeled "(paste path)" so `Other` auto-captures the response). Then re-enter the dispatch table with the corrected path. Abort → STOP with no state change.

## Step 1 — Resolve target task_brief (STANDARD branch)

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
  - **Why `domain/wal/` regardless of the task's actual dimension**: a "None" decision is meta-knowledge ("we deliberately chose not to capture WAL"), not domain/api/data content. By convention all None stubs land in one location so a downstream scan can find them with a single `find <path> -name "*_stub.md"`. Tooling MUST filter `_stub.md` out when aggregating real domain knowledge — the `_stub.md` suffix is the signal.
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

## RESEARCH branch (Phase R3 Archive)

Invoked when Step 0 dispatch resolved the artifact to `.claude/runs/reports/*_research.md`. Do NOT execute STANDARD Steps 1–8 in this branch.

### Step 1R — Validate report (blocking)

```bash
python3 .claude/scripts/gates/research_report_gate.py --require <report path>
```

| Exit | Action |
|---|---|
| 0 (PASS) | Continue Step 2R |
| 1 (WARN) | Surface inline, ask user continue/revise |
| 2 (FAIL) | STOP. Roll back to Phase R2 Synthesize. Max 2 retries per anti-loop. Third FAIL → ask user. Record via `failure_memory.py record --intent Research --phase Synthesize --gate research_report_gate.py --pattern <gate-message>` |

### Step 2R — Optional WAL (single AskUserQuestion, default Skip)

Per `policy.md` RESEARCH Profile Write-back:

```
Q: Extract reusable knowledge to WAL? (Report itself is the primary knowledge artifact.)
- [✓] Skip (recommended) — no WAL written; report archive is the citable record
- [ ] Extract — research surfaced stable reusable facts independent of §5 Recommendations
```

- **Skip** → no WAL written; no stub file (RESEARCH default; no justification required).
- **Extract** → follow-up multi-select limited to ≤ 2 dimensions from {Domain, API, Data, Architecture}. Then dispatch `knowledge-extractor` per `.claude/rules/dispatch-template.md` with `[Chosen Dimensions]: <list>`. Source Documents: the report file with `#L<a>-L<b>` pointers to §3 Findings + §7 Evidence Index.

### Step 3R — Move report + mark DONE

```bash
mkdir -p .claude/wiki/archive/reports
mv .claude/runs/reports/<file> .claude/wiki/archive/reports/<file>
```

- Edit latest `.claude/runs/launch-specs/launch_spec_*.md`: row `Status: IN_PROGRESS` → `DONE`. MUST NOT touch other rows.

### Step 4R — Wiki lint + final report

```bash
python3 .claude/scripts/wiki/wiki_linter.py
```

- OK / WARN → proceed (cap on `archive/reports/` is 3000 lines per policy override)
- FAIL → STOP, do NOT mark DONE; report the linter output

Final block:

```
[Archive Status]: COMPLETE | FAILED
[Mode]: RESEARCH
[Slug]: <slug>
[Archived Report]: .claude/wiki/archive/reports/<file>
[Gate]: PASS | WARN(<one-line>)
[WAL]: Skip | <dimensions>
[wiki_linter]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Recommendations]: <count> Option blocks in §5 — list each "If chosen, run: ..." line verbatim for user as next-step candidates
```

§5 next-step candidates MUST be surfaced verbatim; MUST NOT auto-trigger.

## Hard constraints (apply to BOTH branches)

| Rule | Value |
|---|---|
| Allowed edit set (STANDARD) | `.claude/wiki/**/wal/`, the resolved task_brief, target `launch_spec_*.md`, ADR/memory files from Step 4 |
| Allowed edit set (RESEARCH) | the resolved report, target `launch_spec_*.md`, optional WAL via sub-agent |
| Source-code edits | FORBIDDEN in both branches |
| Anti-loop | max 2 retries per step; second same-step failure → STOP, ask user |
| Step ordering | fixed; STANDARD Step 2 MUST precede Step 3 (extractor depends on reflection); RESEARCH Steps 1R-4R MUST execute in order |
| PATCH profile | STOP if `$ARGUMENTS` resolves to PATCH task_brief (Archive WAL is STANDARD-only per policy) |
