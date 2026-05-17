# Write-back Policy — WAL & Anti-Bloat

## Language Rule

- **Machine-facing** (code snippets, schemas, paths, script names): **English**
- **Human-facing** (explanations, rationale, context, summaries): **User's primary language** (Chinese for this project)

## WAL Fragment Naming

```
.claude/wiki/wiki/<domain>/wal/YYYYMMDD_<slug>_<category>.md
```

Domains: `domain/`, `api/`, `data/`, `preferences/`, `architecture/`, `testing/`, `reviews/`

## Archive Location

Completed task_briefs move to: `.claude/wiki/archive/<YYYY-MM-DD>_<slug>_task_brief.md`

After extraction, replace the active `task_brief.md` in `runs/task-briefs/` with a pointer file:
```bash
python3 .claude/scripts/tools/archive_session_artifacts.py --slug <feature_slug>
```

## Anti-Bloat: 500-line Hard Limit

When any wiki index file exceeds 500 lines:
1. Split content into focused sub-documents per topic
2. Rewrite original `index.md` as a lean routing graph (links + 1-2 line summaries)
3. If top-level structure changes, update `KNOWLEDGE_GRAPH.md`

Gate: `python3 .claude/scripts/wiki/wiki_linter.py` — FAIL if dead links or any file > 500 lines.

## Extraction Rules

- Do NOT directly edit shared `index.md` files during automated runs. Write to `wal/` fragments.
- WAL fragments are merged later by the Librarian (via `@gc`).
- STANDARD tasks: WAL write-back is MANDATORY (Domain + API + Rules; Data if schema change).
- PATCH tasks: no WAL required. Wiki refresh deferred to `@wiki-update`.
- New tables/schemas go into WAL data domain (`wiki/data/wal/`) as Markdown with DDL code blocks — NOT as root `.sql` files.
