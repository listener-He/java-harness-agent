# Incidents — Real Production Facts for LLM Code Reviewers

This directory stores **distilled records of real production incidents** in a format the LLM workflow can ingest. The goal: when the LLM is about to modify code that was the scene of a past incident, it should be reminded — not because we logged it, but because the failure-memory hook will surface it.

## What lives here

- `<YYYY-MM-DD>_<slug>.md` — structured incident record (committed)
- `<YYYY-MM-DD>_<slug>.raw.txt` — original fact source (committed; useful when re-reading later)

That's all. No JSON index, no DB — readers parse `*.md` directly.

## How an incident gets here

```
事故事实源 (Sentry / Jira / log / 工程师口述)
        │
        ▼
python3 .claude/scripts/local_intel/ingest_incident.py \
    --source sentry|jira|log|manual \
    --slug user-login-500-spike \
    [--from-file path | < stdin]
        │
        ▼ saves raw + emits a structured prompt
        │
LLM 读 raw → 按 TEMPLATE.md 萃取 → 写入 .md
```

The Python script does almost nothing — it's a thin envelope. The LLM does the actual extraction so that schema drift in upstream sources (Sentry/Jira API changes, free-form log formats) doesn't break the pipeline.

## How it influences future code

Two injection points:

1. **UserPromptSubmit hook** — at the start of every user turn, `failure_memory.py summary` reads incidents from the last 30 days and appends an `incidents:` section to the `[failure-memory]` block. The LLM sees a one-line lesson per incident.
2. **PostToolUse hook** — when the LLM edits a file, `incident_hint.py` scans recent incidents for mentions of that file path or class name. On hit, it injects `[incident-hint]` pointing at the relevant `.md`.

Both are **non-blocking signals**, never gates. The LLM keeps the right to ignore them; the system just makes ignoring visible.

## Filename convention

- Date: `YYYY-MM-DD` of the incident (not the day you wrote the record)
- Slug: `kebab-case`, short, action-oriented (`user-login-500-spike`, `order-cancel-race`)
- Always pair: `<date>_<slug>.md` + `<date>_<slug>.raw.txt`

## Pruning

- Default 30-day window for hook injection — older incidents stay in the directory but stop being noisy.
- An incident with `status: watch` in frontmatter is **never pruned** — used for permanent reminders ("this category of bug burned us multiple times").
