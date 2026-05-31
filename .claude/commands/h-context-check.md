---
description: Pull-model context probe — recent events + recurring failures + active task + dirty diff + sensitive-surface scan. Replaces P2-removed [triage-evidence] / [failure-memory] auto-injection. TRIGGER: phase start / 不确定状态 / 进入未知领域. NOT FOR: every prompt (this is on-demand, not push).
argument-hint: [--prompt "<text>"] [--brief-only] [--no-events]
---

Run when you (the main agent) need a quick situational read **before** deciding profile / scope / next action. Hooks no longer push context blocks since P2; this command is the canonical pull entry.

## What it does

Aggregates 5 cheap data sources, formats a single readable block:

| Source | What it tells you |
|---|---|
| `events_query.py --kind edit_post --since 1h` | Files edited in the last hour (scope of in-flight work) |
| `failure_memory.py summary --days 30 --min-count 2` | Recurring gate failures (likely-to-repeat patterns) |
| `find_active_task_brief.py` + `launch_spec_*.md` | Current task identity / phase / status |
| `git diff --name-only` | Uncommitted change set |
| `triage_probe.py --json` (only if `--prompt` provided) | Per-prompt evidence: keywords / blast / ambiguity / intent class |

All inputs are reads. The command writes nothing.

## Step 1 — Parse args

| Arg | Effect |
|---|---|
| `--prompt "<text>"` | Also run triage_probe on this prompt for keyword + intent evidence |
| `--brief-only` | Skip events + failures + git; only show active brief + phase. Fastest, smallest output. |
| `--no-events` | Skip events_query (use when events.jsonl unavailable or very large) |

Defaults: all sources, no triage_probe.

## Step 2 — Run the queries in parallel

Use Bash where possible to overlap subprocess startup. Each step is read-only and silent on individual failure.

```bash
# Active brief (always)
python3 .claude/scripts/harness/find_active_task_brief.py

# Recent events (unless --no-events)
python3 .claude/scripts/local_intel/events_query.py --kind edit_post --since 1h --last 10

# Recurring failures (unless --brief-only)
python3 .claude/scripts/local_intel/failure_memory.py summary --days 30 --min-count 2 --top 5

# Git diff scope (unless --brief-only)
git diff --name-only | head -20

# Per-prompt evidence (if --prompt)
echo "$PROMPT_TEXT" | python3 .claude/scripts/local_intel/triage_probe.py --json
```

## Step 3 — Format the output block

Render exactly this structure (omit sections with no data):

```
[context-check] @ <ISO timestamp>

== Active Task ==
brief: <path or "none">
phase: <Explore | Propose | Implement | QA | Archive | n/a>
status: <PENDING | IN_PROGRESS | WAITING_APPROVAL | DONE | FAILED | n/a>

== Recent Edits (last 1h, ≤10) ==
- <file_path> (<count> times)
- ...
(or "none")

== Recurring Failures (last 30d, ≥2 hits) ==
- ×<n> <phase>/<gate>: <pattern> (last <date>)
- ...
(or "none")

== Dirty Diff ==
<N files uncommitted>; sample: <file1>, <file2>, ...
(or "clean")

== Prompt Evidence == (if --prompt)
intent_class: <CHANGE | RESEARCH | OTHER>
profile_hint: <advisory>
keywords_observed: <comma-list or "none">
ambiguity: <OK | WARN | FAIL>

== Suggested Next Action ==
<one line — what you'd most logically do given the above>
```

## Step 4 — Read the block AND act

`[context-check]` is for the main agent. Do not blindly forward it to the user. Use it to:
- pick a profile (read prompt + this context → decide Vibe/Patch/Standard/Research)
- detect "you're about to repeat a known failure" (recurring + your planned action overlap)
- spot dirty diff that shouldn't ship (uncommitted ≥5 files + new task starting)
- confirm there's no active task brief blocking your scope

## When to call this command

| Situation | Call? |
|---|---|
| New prompt arrived, you're about to pick a profile | YES if any HIGH-sensitivity keyword in prompt, OR you don't recall recent failures |
| Continuing work on a task you set up this session | NO (you already have context in conversation) |
| /h-resume invoked | NO (h-resume does its own state read) |
| Before /h-pr or /h-archive | YES (last-chance review) |
| User asks "what's the state" | YES (then report a synthesized summary, not the raw block) |

## Hard constraints

- **Read-only command** — never edit files. All queries are reads.
- **Each query has its own timeout** — if any single query hangs > 5s, skip it and note in output. Don't block the whole context-check on one slow source.
- **No subagent dispatch** — this is a synchronous data-gather, not a reasoning task.
- **Output once, do not loop** — single block per invocation. If you want updated context, call again.
