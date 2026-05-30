---
description: TRIGGER after compile+tests pass and QA needs context to design test cases OR user says 'QA 接手' / 'test handoff'. NOT FOR: PR description (use /h-pr — for reviewers, not QA); QA execution itself. Returns: structured handoff doc (reproduce / impact / test scope / rollback / open questions).
argument-hint: [slug] [--bug-fix] [--commits <range>] [--branch <name>] [--ticket <ref>]
---

Produce a structured handoff document for the QA / test team based on a code change or bug fix that is **already complete** (compile + tests pass on the developer side). The document gives QA enough context to design test cases without re-reading the diff line-by-line.

**Distinction:**
- `/h-pr` produces a PR description for code reviewers (focus: what + why).
- `/h-test-handoff` produces a QA briefing (focus: how to verify + what to test + what to skip).

Both can be run on the same change; they answer different questions.

## Step 1 — Parse `$ARGUMENTS`

- `[slug]` (optional): the task slug. If omitted, derive from the active `task_brief.md` in `.claude/runs/task-briefs/` or from the current git branch name.
- `--bug-fix` (optional): forces the bug-fix template (different sections — see Step 5b). If omitted, auto-detect: presence of an incident file at `.claude/wiki/incidents/*<slug>*.md` OR a launch_spec row prefixed `fix-` → bug-fix mode; otherwise feature-change mode.
- `--commits <range>` (optional): explicit git commit range (e.g. `main..HEAD` or `abc123..def456`). Default: `$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)..HEAD`.
- `--branch <name>` (optional): override branch name in the report. Default: `$(git branch --show-current)`.
- `--ticket <ref>` (optional): ticket reference (GitHub issue #, Jira key, Linear ID) to link from the handoff. If a task_brief frontmatter already has `ticket_ref` / `ticket_url`, prefer those.

## Step 2 — Locate the source artifacts (manual workflows are first-class)

The user **may have worked manually** (edited code directly, no `/h-fix-bug` / `/h-brief` run). Do NOT assume a task_brief or incident file exists. The command must work whether the change came from our pipeline OR from raw manual editing.

Probe in this order, **collect every hit** (do not stop early — multiple sources combine):

1. Active `task_brief.md`: `ls .claude/runs/task-briefs/*<slug>*_task_brief.md` (1 match expected). Read Machine Section if present.
2. Archived `task_brief.md`: `ls .claude/wiki/archive/*<slug>*_task_brief.md`. Read.
3. Incident file (bug-fix mode): `ls .claude/wiki/incidents/*<slug>*.md`. Read.
4. PR description: `gh pr view --json title,body 2>/dev/null` (if `gh` available and PR exists).
5. **Commit messages** (always — even when 1-4 hit): `git log --pretty=format:"%h%n%an %ad%n%s%n%b%n---" <commits>` — full subject + body. Commit body often contains rationale that no other artifact captured.
6. **Uncommitted working tree** (always — for in-progress local edits): `git status --porcelain` + `git diff HEAD` + `git diff --cached`. If non-empty, the change set extends BEYOND `--commits <range>` — treat working-tree edits as part of the change for this handoff.

If steps 1-4 all miss AND only steps 5-6 yield signal → mark mode as `manual-workflow` in the report. This is a normal scenario, not an error.

**Source-of-truth ordering when sources conflict:**
1. Uncommitted working tree (most recent intent)
2. Local commits in `<range>`
3. task_brief / incident / PR descriptions
4. User answers from Step 2.5 below

A later layer overrides earlier — i.e. if working-tree changes contradict the task_brief, trust the working tree and flag the divergence in `[Sections with author-confirmed gaps]` of the final report.

## Step 2.5 — Clarification loop (BEFORE drafting)

**When content or boundary is unclear, ask the user — do NOT guess, do NOT pre-fill placeholders.**

After gathering all sources from Step 2, run a mental checklist of the QA-doc sections (see Step 5). For any section where the gathered signal is thin (no clear answer derivable from sources), **ask the human via `AskUserQuestion` and wait**. Repeat until either:

- Every required section has answerable signal, OR
- The user explicitly waives a section ("skip §6 What NOT to Test" → write `_Not applicable — confirmed by author._`), OR
- 5 question-rounds elapsed (anti-loop cap — STOP and emit `[Status]: ESCALATE` with the remaining gaps)

Typical clarifications to ask (only the ones actually unclear — don't ask everything):

| Section | When unclear | Question to ask |
|---|---|---|
| §1 Change Summary | Commit messages cryptic, no task_brief | "Describe in one paragraph what changed for the end user — business outcome, not code." |
| §2 Affected Surfaces — HTTP/DB | Diff touches a class but the public surface is ambiguous | "Does this change alter any HTTP endpoint response shape, status code, or DB table/column? Name them if yes." |
| §3 How to Verify | No ACs in any source | "Give me 1-3 concrete scenarios I can convert to test cases — Given/When/Then format if possible." |
| §3 (bug-fix) Reproduce ORIGINAL bug | No incident file, no repro in commit body | "What were the exact steps to reproduce the bug before this fix? Environment, inputs, expected vs actual." |
| §4 Edge Cases | Happy path clear, edges absent | "Any edge cases or negative inputs the fix should handle? (invalid input / empty / max / concurrent)" |
| §6 What NOT to Test | Scope boundary unclear | "What parts of the system are explicitly NOT affected by this change? QA should skip those." |
| §7 Environment | Config / migration touched but no setup instructions | "What does QA need in their env? (apply migration X, set feature flag Y, seed data Z)" |
| §8 Rollback | HIGH risk or DB migration without rollback notes | "How do we roll back if this regresses? (revert commit / flag flip / rollback script)" |

After every answer batch, re-evaluate the section list. Continue until covered.

**Hard rule:** writing `_None observed_` for a section is only allowed AFTER asking the user about it and the user explicitly waived. Otherwise, ASK.

## Step 3 — Collect the diff facts

```bash
# Committed range
git diff --stat <commits>          # files + line count
git diff --name-only <commits>     # raw file list for categorization
git log --pretty=format:"%h %s%n%n%b%n---" <commits>  # subjects + bodies

# Working tree (uncommitted edits — manual workflow case)
git status --porcelain             # staged + untracked summary
git diff HEAD --stat               # uncommitted diff against HEAD
git diff --cached --stat           # staged but not committed
```

**Combine the committed and uncommitted file lists** into a single "change set" for the rest of the analysis. Annotate each file in the final report's reference section with its state:
- `[committed]` — in `<commits>` range
- `[staged]` — `git diff --cached` shows it
- `[unstaged]` — `git diff HEAD` shows it, NOT staged
- `[untracked]` — `git status --porcelain` reports `??` prefix

QA will need the unstaged/untracked annotations to know what they're testing is NOT in git yet — important for environment reproducibility.

Categorize changed files:
- **Production code** (`src/main/**`): the actual behavior change
- **Test code** (`src/test/**`): asserts the change
- **SQL / DDL** (`*.sql`, `**/db/migration/**`): schema change → high QA priority
- **Config / properties** (`*.properties`, `*.yml`, `*.yaml`): environment dependency → flag for QA env
- **Docs only** (`*.md`, `README*`): low QA priority
- **Build / pom** (`pom.xml`, `build.gradle`): dependency change → regression risk

If `src/main/**` changes touch `**/controller/**` or `**/Mapper.xml` → mark as **public-surface change** (API contract or DB query observably differs).

## Step 4 — Derive impact scope

For each modified production class, identify callers:

```bash
# Example: for ChangedClass.java, find what calls it
grep -rln "ChangedClass" src/main/ src/test/ --include="*.java" | grep -v "ChangedClass.java"
```

Aggregate into:
- **Direct impact** (files in the diff)
- **Indirect impact** (files that import / call changed classes, within the same module)
- **External surface** (HTTP endpoints / public service methods / DB tables touched — name them explicitly)

If the change touches a `@Mapper` XML / `*Mapper.java` / migration `*.sql` → also list affected tables and columns.

## Step 5 — Pick the template

### 5a. Feature-change template (default)

```markdown
# QA Handoff — <Feature Title>

> Generated by /h-test-handoff on <YYYY-MM-DD>. Source: <task_brief path | manual>.

## 1. Change Summary
**What changed:** <one paragraph — business outcome, not implementation detail>
**Why:** <link to ticket / PRD / requirement>
**Risk tier:** <LOW | MEDIUM | HIGH> (from task_brief frontmatter, or inferred)

## 2. Affected Surfaces
- **HTTP endpoints:** <METHOD path → behavior change; or "none">
- **Service methods (public):** <Class.method → behavior change; or "none">
- **Database schema:** <tables / columns added or altered; or "none">
- **Config keys:** <new or changed properties; or "none">
- **External integrations:** <upstream / downstream systems; or "none">

## 3. How to Verify (positive cases)
For each AC in the task_brief, restate as a QA-runnable scenario:
- **AC-1 ↔ Test scenario:** Given <precondition in QA env>, When <action>, Then <observable result>
- ...

## 4. Edge / Negative Cases to Cover
- Invalid input: <list>
- Boundary conditions: <list — empty, max, concurrent>
- Permission / tenant boundary: <if applicable>
- Idempotency: <if API mutates state>

## 5. Regression Risk Areas
**Files that share calls with the diff:**
- `<file>` — touched indirectly via `<ChangedClass>`. Smoke-test <feature> still works.

## 6. What NOT to Test (out of scope)
- <Unaffected feature 1>
- <Unrelated module>

## 7. Test Environment / Preconditions
- DB migration: <yes (apply script X) | no>
- Feature flag: <flag name = value | none>
- Required test data: <fixtures / seed scripts>
- Authentication: <tenant / user role required>

## 8. Rollback Plan
<one paragraph — what reverts the change if regressed (revert commit, feature flag flip, schema rollback script)>

## 9. Open Questions for QA
<list any ambiguity the test team needs to resolve with the dev>

## 10. Reference
- Branch: `<branch>`
- Commit range: `<range>`
- task_brief: `<path or "none">`
- PR: `<url or "not yet opened">`
- Ticket: `<ref or "none">`
```

### 5b. Bug-fix template (--bug-fix or auto-detected)

Same skeleton with these section replacements:

```markdown
## 1. Bug Summary
**Original bug:** <symptom — what the user saw>
**Root cause:** <verbatim from incident file's `## 根本原因` or task_brief; one line>
**Severity (original):** <p1 | p2 | p3>
**Fix shape:** <one sentence — what the fix actually does>

## 2. Affected Surfaces
<same as feature template>

## 3. How to Reproduce the ORIGINAL Bug (before fix)
Step-by-step reproduction the dev confirmed. **QA should reproduce this on the previous commit** (`<commit-before-fix>`) to validate the symptom, then re-test on the fix commit to confirm absence:
1. <precondition>
2. <action>
3. <observed wrong result>

## 4. How to Verify the FIX (after fix applied)
1. <same precondition>
2. <same action>
3. <expected correct result>

## 5. Regression Risk Areas
<callers of the changed code — most important for bug fixes since the surface is narrow>

## 6. Edge Cases (often re-introduce the same bug)
- <variant of the original repro path>
- <similar input space>
- <concurrent / race scenarios if applicable>

## 7. Test Environment / Preconditions
<same as feature template>

## 8. Rollback Plan
<same as feature template>

## 9. Linked Records
- Incident file: `.claude/wiki/incidents/<...>.md`
- failure_memory pattern: `<pattern recorded>`

## 10. Open Questions for QA
<same as feature template>
```

## Step 6 — Draft the document

Pick the template from Step 5. Fill each section from (in source-of-truth order from Step 2):
1. **Working tree edits** (uncommitted, most recent intent)
2. **Local commits** in `<range>` — subjects AND bodies from Step 3 `git log` output
3. **task_brief.md Machine Section** — Allowed Scope (drives §2 Affected Surfaces), ACs (drives §3 How to Verify), §6 NFR (drives §7 Test Environment), §10 QA Evidence if archived
4. **incident file** (bug-fix mode) — `## 根本原因` / `## 提醒未来 LLM` / reproduction steps
5. **PR description** (if any)
6. **User answers from Step 2.5 clarification loop**
7. **Impact analysis** from Step 4 — §5 Regression Risk Areas

Hard rules during drafting:
- **Every named identifier (class, method, endpoint, table) MUST appear in the actual diff (committed OR uncommitted) or be explicitly supplied by the user in Step 2.5** — do not infer or invent.
- **Do NOT pre-fill `_None observed_` without asking.** If a section's signal is thin, return to Step 2.5 and ask. Only write `_Not applicable — confirmed by author._` after the user explicitly waives that section.
- **Keep §1 readable by a non-developer** — translate code-change into business outcome.
- **§3/§4 must be runnable as test cases** — not "verify the feature works" but "Given X, When Y, Then Z observable".
- **§6 What NOT to Test must be non-empty** for non-trivial changes — explicit out-of-scope prevents QA from running a full regression suite. If the diff is genuinely localized and the boundary is obvious from the diff, say so; otherwise ASK in Step 2.5.
- **Working-tree edits MUST be flagged** in §10 Reference — QA needs to know if part of what they're testing isn't in git yet.

## Step 7 — Save and report

Save to: `.claude/runs/qa-handoffs/<YYYYMMDD>_<slug>_qa_handoff.md`

(Create the directory if it does not exist: `mkdir -p .claude/runs/qa-handoffs/`. This directory is under `.claude/runs/` which is `.gitignore`d — the handoff is a local artifact the dev shares with QA out-of-band.)

After saving, report:

```
[Test-Handoff Status]: WRITTEN | SKIPPED | ESCALATE
[Slug]: <slug>
[Mode]: feature-change | bug-fix
[Workflow Origin]: pipeline (task_brief / incident exists) | manual-workflow (no upstream artifact) | hybrid
[Output Path]: .claude/runs/qa-handoffs/<YYYYMMDD>_<slug>_qa_handoff.md
[Source task_brief]: <path or "none — manual workflow">
[Source incident]: <path or "n/a">
[Files in diff]: <N production, M test, K SQL, J config>
[Commit range]: <range or "uncommitted-only">
[Uncommitted edits]: <N staged, M unstaged, K untracked — or "none">
[Clarification rounds]: <N — how many times Step 2.5 asked the user>
[Author-confirmed gaps]: <list sections the user explicitly waived as "not applicable" — empty if every section has substantive content>
[Next Step]: <e.g. "Open the handoff, share with QA" | "Author still needs to commit the unstaged files before QA pulls the branch">
```

## Hard constraints

- **Read the actual diff (committed + uncommitted) before drafting** — every identifier in the document must trace back to a changed file or an explicit user answer in Step 2.5. No hallucination of class names, endpoints, or tables.
- **Manual workflows are first-class** — the user is NOT required to have run `/h-fix-bug`, `/h-brief`, or any other command first. They may have edited code directly with their hands. Step 2 gathers from git + working tree regardless; Step 2.5 fills the rest by asking.
- **When unclear → ASK, do not guess** — the human must clarify content or boundary ambiguity before a section is written. `_None observed_` is forbidden as a default; only `_Not applicable — confirmed by author._` (after explicit waiver) is allowed.
- **Bug-fix mode requires an incident file OR an explicit root cause from the user** — if neither exists, ask in Step 2.5 for the root cause statement before generating §1 Bug Summary. Do NOT proceed without it.
- **Read-only on `src/**`** — this command does not modify source code. It only writes to `.claude/runs/qa-handoffs/` and reads git/working tree.
- **Allowed read sources** — `git log` (commit history, including bodies), `git diff` (committed range AND uncommitted working tree AND staged), `git status`, `git show <commit>`, raw files under any path. These are fact-based inspections of what the human did.
- **Do not auto-share** — the command produces the file; sharing with QA (Slack / email / ticket comment) is the user's call.
- **Anti-loop A — impact analysis**: if Step 4 exceeds 30s OR returns > 100 indirect files → cap §5 at top-10-by-call-frequency and note the truncation in `[Author-confirmed gaps]`.
- **Anti-loop B — clarification**: max 5 question-rounds in Step 2.5; if signal still thin, emit `[Status]: ESCALATE` with the remaining gaps listed — do NOT silently fall back to `_None observed_` placeholders.

## When NOT to use

- Pure documentation change (`*.md` only) — no QA testing needed; skip the command.
- Refactor with zero behavior change (verified by green tests + reviewer confirmation) — skip; tell QA "no behavior change, run smoke only".
- Pre-merge speculative drafts — wait until the change is finalized; QA documents drift if the diff keeps changing.
