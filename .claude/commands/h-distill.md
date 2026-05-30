---
description: TRIGGER when '[wiki-distill] threshold hit' appears OR user says '整理 wiki' / '清理过期'. NOT FOR doc cleanup (use documentation-curator) or index split (use knowledge-architect). Returns cleanup execution report.
argument-hint: (none)
---

Wiki cleanup pipeline. Triggered when `distill_threshold.py` flags growth, or on user request ("清理过期 wiki" / "整理 wiki"). Sequential; any sub-agent FAIL/ESCALATE STOPS the flow.

## Step 1 — Dispatch librarian Distill scan (read-only)

Build the dispatch prompt strictly from `.claude/rules/dispatch-template.md`. Required content:

- `## Inputs`: no task_brief (this is a MAINTENANCE-only dispatch); `[Mode]: Distill-Scan`
- `## Source Documents`: pointer to `.claude/wiki/KNOWLEDGE_GRAPH.md` and the librarian agent's scan-mode contract at `.claude/agents/librarian.md#L86-L107`
- `## Memory Snapshot`: copy any `type=feedback` entries about wiki maintenance (likely "none")
- `## Expected Output`: per librarian.md template — return MUST include `[Mode]: Distill-Scan` and `[Plan Path]: <path>`

After return:
```
python3 .claude/scripts/gates/subagent_return_gate.py --return-stdin --task-kind audit
```
- exit 0 → continue
- exit 1 (WARN) → surface inline, continue
- exit 2 (FAIL) → re-dispatch ONCE; second FAIL → STOP

Capture `<plan-path>` from `[Plan Path]:` for Step 2.

## Step 2 — Human approval via AskUserQuestion

Read `<plan-path>`. The plan is grouped by domain with two kinds of rows:

```
- [ ] `DELETE` <file>   — <reason>
- [ ] `MERGE`  <file> → <target>  — <reason>
```

For each non-empty domain section, ask the user to multi-select which rows to approve. Group by domain to avoid one massive question:

```
Q: <domain> — approve which cleanup operations?
- [ ] DELETE <file1> — <reason>
- [ ] DELETE <file2> — <reason>
- [ ] MERGE  <file3> → <target> — <reason>
- [ ] Skip this domain
```

If a domain has ≥ 5 candidates, split the question across two prompts to stay within `AskUserQuestion` UX bounds.

After collecting answers across all domains, use `Edit` to flip approved rows from `[ ]` to `[x]` in `<plan-path>` — leave rejected rows untouched (they stay `[ ]` and `distill.py execute` skips them by design).

If the user approved **zero** rows across all domains:
```
[Distill Status]: NO-OP
[Plan Path]: <plan-path>
[Next]: Plan saved for later review. Re-run /h-distill to start fresh.
```
STOP here (no Step 3).

## Step 3 — Dispatch librarian Distill execute (destructive)

Build dispatch per `.claude/rules/dispatch-template.md`. Required content:

- `## Inputs`: `[Mode]: Distill-Execute` and `[Plan Path]: <plan-path>`
- `## Source Documents`: pointer to `<plan-path>` (the librarian validates `[x]` row count ≥ 1) and `.claude/agents/librarian.md#L108-L126` (execute contract)
- `## Hard Limits`: standard template
- `## Expected Output`: per librarian.md template

After return:
```
python3 .claude/scripts/gates/subagent_return_gate.py --return-stdin --task-kind audit
```

Then verify wiki integrity:
```
python3 .claude/scripts/wiki/wiki_linter.py
```
- OK → continue
- WARN → surface inline
- FAIL → STOP, report linter output (no rollback — `git rm` history is preserved; user can `git restore` if needed)

## Step 4 — Final report

Output exactly this block, nothing else:

```
[Distill Status]: COMPLETE | PARTIAL | NO-OP | FAILED
[Plan Path]: <plan-path>
[Approved Ops]: <N delete + M merge>
[Executed Ops]: <N delete + M merge, or 0 if NO-OP>
[wiki_linter]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Next]: Run /h-status to see queue. Wiki growth was the trigger — re-check thresholds with: python3 .claude/scripts/wiki/distill_threshold.py
```

## Hard constraints

| Rule | Value |
|---|---|
| Allowed edit set | the resolved `<plan-path>` only (Edit `[ ]` → `[x]`); librarian sub-agent owns wiki edits |
| Source-code edits | FORBIDDEN |
| Anti-loop | max 2 retries per sub-agent dispatch; second FAIL → STOP |
| Step ordering | fixed; Step 2 MUST collect approval before Step 3 dispatches execute |
| Zero-approval shortcut | Step 2 NO-OP path skips Step 3 entirely — never dispatch execute on a plan with no `[x]` rows |
