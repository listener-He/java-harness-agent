---
description: Capture production incident → wiki/incidents/<date>_<slug>.md with future-LLM reminder line. TRIGGER: Sentry alert / '记录事故'. NOT FOR: bug pipeline (use /h-fix-bug).
argument-hint: <source> <slug> [--from-file <path>]
---

Capture a production incident (Sentry alert / Jira ticket / oncall log / post-mortem) into the project's incident memory. The script saves the raw fact and emits a structured prompt; **you write the `.md`**. The single most load-bearing field is `## 提醒未来 LLM` — every future session reads it via the `[failure-memory]` hook block. Optimize for that line.

## Step 1 — Parse `$ARGUMENTS`

- `<source>` (required): one of `sentry | jira | log | manual`. Reject any other value.
- `<slug>` (required): kebab-case identifier, e.g. `user-login-500-spike`. Reject if it contains uppercase or underscores.
- `--from-file <path>` (optional): path to an existing raw fact file.

If `<source>` or `<slug>` missing/invalid → STOP and ask user to re-invoke with corrected args.

## Step 2 — Obtain the raw fact

- If `--from-file <path>` provided → use that path. Confirm the file exists; if not, STOP.
- Else → invoke `AskUserQuestion` asking the user how to provide the raw fact, with two options:
  - "Paste it in the next message — I'll write it to a temp file and continue"
  - "I'll give you a file path"
  
Once raw fact is on disk at a known path, continue. Do NOT proceed without a concrete file path — `ingest_incident.py` requires one or stdin.

## Step 3 — Path collision check

Compute target: `.claude/wiki/incidents/<YYYY-MM-DD>_<slug>.md` using today's date.

If the file already exists → STOP and report. Ask user whether to pick a different slug or explicitly delete the existing file. Never silently overwrite — historical incidents are immutable evidence.

## Step 4 — Run the ingestion script

```
python3 .claude/scripts/local_intel/ingest_incident.py --source <source> --slug <slug> --from-file <raw-path>
```

Read the structured prompt the script emits on stdout. That prompt contains hints for filling the template. The script also saves the raw fact under its own managed location — do not move or alter it.

If the script exits non-zero → report stderr verbatim, STOP.

## Step 5 — Write the incident `.md`

Render `.claude/wiki/incidents/<YYYY-MM-DD>_<slug>.md` strictly following `.claude/wiki/incidents/TEMPLATE.md`. Required structure:

```markdown
---
date: <YYYY-MM-DD>
slug: <kebab-case-slug>
severity: P1 | P2 | P3
source: <sentry|jira|log|manual>
status: resolved | ongoing | watch
---

## 现象
<one line, measurable: numbers + duration + scope>

## 根因
<one line, the WHY — invariant violated, NOT the stack trace>

## 受影响代码栈
- `<file path>#<method-or-line>`
- `<mapper XML id>`
- table `<table_name>`

## 修复
<one line: PR # / commit SHA / config change / rollback>

## 提醒未来 LLM
**下次改这片代码时考虑：** <1-2 actionable sentences with a concrete code reference. Will be injected into [failure-memory].>
```

**Do NOT include** the "Anti-pattern reference" section from TEMPLATE.md — that block is for the template only and must be deleted from the copy.

Populate every section. Use the raw fact + the script's structured prompt + conversation context as input. Do not leave a section as `TBD`, `N/A`, or whitespace — if information is genuinely missing, STOP and ask user before writing the file.

## Step 6 — Quality check before saving (mandatory)

Self-review against the TEMPLATE.md anti-pattern table BEFORE writing the file. Reject and revise if any of these apply:

| Section | Reject if it reads like |
|---|---|
| 现象 | "服务挂了" / "用户报错" / vague verb without numbers |
| 根因 | a pasted stack trace, or any text > 1 line |
| 受影响代码栈 | module names only ("user 模块") — must be `file:line` or `class.method` or `mapper#id` or `table t_xxx` |
| 修复 | "已修复" / "fixed" — must name a PR / commit / config |
| **提醒未来 LLM** | "注意 X" / "小心 Y" / "performance matters" — must be specific enough for grep |

The `## 提醒未来 LLM` line is the highest-leverage field. Apply a stronger smell test:

- Does it name a specific anti-pattern? (e.g., `LOWER(email)` 索引失效)
- Does it give the fix shape, not just the warning? (e.g., "用应用层 normalize", not just "注意 email")
- Is it grep-actionable — could a future LLM `grep "LOWER"` and find this incident?

If any field fails the smell test, revise before writing.

## Step 7 — Wiki lint (non-blocking)

Run `python3 .claude/scripts/wiki/wiki_linter.py`. Surface output but do not block — a new incident may legitimately be an "island" (not yet linked from any index); that's a `librarian` consolidation job, not yours.

## Step 8 — Report

Output exactly this block:

```
[Incident Status]: RECORDED | FAILED
[Source]: <sentry|jira|log|manual>
[Slug]: <slug>
[Path]: .claude/wiki/incidents/<YYYY-MM-DD>_<slug>.md
[Severity]: P1 | P2 | P3
[Status]: resolved | ongoing | watch
[提醒未来 LLM (verbatim)]: <copy the exact one-line warning so user can sanity-check it>
[受影响代码栈 count]: <N — confirms PostToolUse [incident-hint] hook can grep N references>
[wiki_linter]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Next Action]: <one sentence — usually "Done. PostToolUse hook will surface this when listed files are edited.">
```

## Hard constraints

- **Allowed edits**: only the new incident `.md` and whatever `ingest_incident.py` itself writes. NO edits to wiki indexes, NO edits to source code, NO edits to other incident files.
- **Never overwrite** an existing incident at the computed path.
- **`## 提醒未来 LLM` is non-negotiable** — must be substantive and grep-actionable. Vague text fails Step 6.
- **`status: watch`** is legitimate when the root cause is hypothesized but not fully confirmed — use it deliberately, not as a fallback for laziness.
- Anti-loop: max 2 revisions on Step 6 quality check, then STOP and ask user to provide better raw input.
