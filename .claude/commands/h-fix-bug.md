---
description: Drive Scenario DEBUG — collect bug info, query failure_memory, root-cause analysis, create fix task, optionally record production incident
argument-hint: [ticket-ref] [--source github|jira|linear|manual] [--production] [--severity p1|p2|p3]
---

Full debug-to-fix pipeline per `.claude/rules/lifecycle.md` Scenario DEBUG. Covers both test-environment bugs and production incidents. Root cause MUST be confirmed before any fix is proposed — this is a hard constraint of Scenario DEBUG.

## Step 1 — Parse `$ARGUMENTS`

- `[ticket-ref]` (optional): GitHub issue number, Jira ID, or any reference string. If omitted, bug is described via conversation.
- `--source github|jira|linear|manual` (optional, default `manual`): ticket source. Only matters when `ticket-ref` is provided.
- `--production` (optional): marks this as a live production bug. Triggers incident recording in Step 6. If P1/P2 severity is set, `--production` is implied.
- `--severity p1|p2|p3` (optional, default `p3`):
  - `p1`: service down or data loss — emergency
  - `p2`: degraded functionality, significant user impact
  - `p3`: test/QA environment bug, low user impact

If `--severity p1` or `--severity p2` AND `--production` is not explicitly set → treat as `--production` implied.

## Step 2 — Collect bug details

**If `ticket-ref` + `--source github` provided:**
```bash
gh issue view <ticket-ref> --json title,body,labels,comments \
  [--repo <owner/repo>]
```
Extract: title, description, steps to reproduce, expected vs actual behavior, error messages, stack traces. If `gh issue view` fails → fall back to manual input.

**Otherwise:** Ask via `AskUserQuestion`:
- "Describe the bug — include: what you expected, what actually happened, steps to reproduce, any error messages or stack traces."

Write collected content to `.claude/runs/decompositions/<YYYYMMDD>_<slug>_bug_raw.md`.

Derive slug: kebab-case from ticket title or first 5 words of description (e.g. `user-login-500-error`).

## Step 3 — Query failure_memory for similar past bugs

```bash
python3 .claude/scripts/local_intel/failure_memory.py query \
  --intent Change \
  --phase Explorer
```

Scan the output for patterns that overlap with the current bug's component or error message. If matches found, surface them inline:

```
[Past Incidents Matching This Area]
- <pattern>: <N occurrences>, last seen <date>
```

This context feeds the root-cause analysis in Step 4. Do not skip even if no matches — the empty result is itself signal.

## Step 4 — Root-cause analysis (Scenario DEBUG Phase 1)

Invoke `root-cause-debug` skill. This skill MUST complete Phase 1 (root cause confirmed) before any fix is proposed. Hard constraint — do not shortcut.

Run the skill with the collected bug details + failure_memory context as input. The skill drives:
- Hypothesis formation
- Evidence gathering (read relevant source files, logs, tests)
- Systematic elimination
- Root cause statement

**Output expected from skill:**
```
[Root Cause]: <one-line invariant violated or condition causing the bug>
[Evidence]: <file:line or log excerpt confirming the cause>
[Blast Radius]: <what else could be affected>
[Fix Shape]: <high-level approach — NOT code yet>
```

If root cause is NOT found after the skill runs → record in failure_memory and STOP:
```bash
python3 .claude/scripts/local_intel/failure_memory.py record \
  --intent Debug \
  --profile PATCH \
  --phase Explorer \
  --gate root-cause-debug \
  --pattern "root cause unresolved: <bug slug>" \
  --task-id <slug>
```
Report `[Status]: ESCALATE` — root cause unknown, cannot proceed to fix. Ask user for additional evidence (logs, reproduction steps, environment info).

## Step 5 — Create fix task in launch_spec

Once root cause is confirmed, create a tracked task.

**Risk inference:**
- p3 (test bug) → LOW
- p2 (production degraded) → MEDIUM
- p1 (production down) → HIGH (forced)

**Scenario:**
- p3 → Scenario DEBUG → normal Implement flow (PATCH profile)
- p1/p2 → Scenario A (Emergency Hotfix) — note in row

Locate or create the latest `.claude/runs/launch-specs/launch_spec_*.md`. Append row:
```
| fix-<slug> | <LOW|MEDIUM|HIGH> | Implement | PENDING | none | (no brief — PATCH inline fix) |
```

For HIGH risk (p1): status starts as `PENDING`, phase `Implement`, and add note: `Scenario A — Emergency Hotfix. No Propose/Review. Requires secrets_linter before Archive.`

For MEDIUM (p2): brief is recommended. Add note: `Slim Spec required before Implement.`

## Step 6 — Production incident recording (if --production or p1/p2)

Run the `/h-incident` command flow inline with:
- `source`: `manual` (or `github` if ticket-ref was provided)
- `slug`: `<slug>`
- raw file: `.claude/runs/decompositions/<YYYYMMDD>_<slug>_bug_raw.md`

This records the bug as a structured incident at `.claude/wiki/incidents/<YYYYMMDD>_<slug>.md`, ensuring future `[failure-memory]` blocks surface it. The `## 提醒未来 LLM` field is derived from the root cause statement in Step 4.

For p3 (test-only bugs): skip this step entirely — do not create an incident file for non-production bugs.

## Step 7 — Fix scope proposal

Present the fix plan for user confirmation via `AskUserQuestion`:

```
Root Cause: <from Step 4>
Fix Shape: <from Step 4>
Estimated Risk: <LOW|MEDIUM|HIGH>
Files likely in scope: <from blast radius analysis>

How do you want to proceed?
```
Options:
- "Fix it now (inline PATCH)" — proceed directly to Implement; no task_brief required for LOW
- "Write a Slim Spec first (MEDIUM)" — invoke `/h-brief <slug> --risk medium --slim` before Implement
- "Full STANDARD task_brief (HIGH)" — invoke `/h-brief <slug> --risk high` before Implement
- "Stop here — I'll fix it manually" — STOP, report findings only

**FORBIDDEN before user confirms:** do NOT write any fix code. Scenario DEBUG: root cause phase must complete and user must approve before any code is written.

## Step 8 — Transition to fix

Based on user choice from Step 7:

**"Fix it now":**
- Update launch_spec row: status `IN_PROGRESS`
- Begin Implement phase inline (PATCH profile, no sub-agent dispatch)
- Apply TDD: write failing test reproducing the root cause first, then fix

**"Slim Spec" or "Full STANDARD":**
- Invoke the appropriate `/h-brief` flow inline
- Leave launch_spec row as `PENDING` until brief is validated
- Report: brief created, ready for Review → Implement

**"Stop here":**
- Leave launch_spec row as `PENDING`
- Do not write code

## Step 9 — Report

Output exactly this block:

```
[Fix-Bug Status]: IN_PROGRESS | SPEC_PENDING | STOPPED | ESCALATE
[Slug]: fix-<slug>
[Severity]: p1 | p2 | p3
[Production]: yes | no
[Root Cause]: <one-line — verbatim from Step 4>
[Blast Radius]: <from Step 4>
[failure_memory]: recorded | skipped (p3, non-production)
[Incident File]: <path or "n/a (p3)">
[Launch Spec Row]: fix-<slug> (<status>)
[Fix Approach]: inline-PATCH | slim-spec-pending | standard-brief-pending | stopped
[Next Action]: <one specific sentence>
```

## Hard constraints

- **Root cause MUST precede any fix code** — this is Scenario DEBUG's core rule. No exceptions.
- **p3 bugs do NOT create incident files** — incident records are for production impact only.
- **p1 bugs are always HIGH risk** — do not downgrade, even if the fix looks simple.
- **`--production` + p3 is a contradiction** — if user sets both, ask for clarification before proceeding.
- **No source-code edits in Steps 1–7** — Scenario DEBUG profile: FORBIDDEN from modifying code until root cause is confirmed and user approves fix scope.
- Anti-loop: if root-cause-debug skill fails to find root cause twice → STOP, record in failure_memory, ask user for more evidence. Do not guess.
