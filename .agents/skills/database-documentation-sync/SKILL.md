---
name: "database-documentation-sync"
description: "Database documentation capture: treat LLM Wiki as the source of truth, write via WAL fragments (do not edit index directly), and use openspec.md as the detailed source."
---

# Database Documentation Capture (LLM Wiki + WAL)

Use this skill when the data model changes. Capture stable table/index/relationship facts into the LLM Wiki so future agents can drill down to the source.

## 0) Single Source of Truth (SSOT)

- Routing / profiles / shortcuts / write-back switches: `.agents/router/ROUTER.md`
- Navigation + write-back methodology (reverse funnel + WAL): `.agents/router/CONTEXT_FUNNEL.md`
- WAL + compaction policy: `.agents/workflow/ARCHIVE_WAL.md`
- Data index entry: `.agents/llm_wiki/wiki/data/index.md`

This skill defines how to write back data-model knowledge when write-back is enabled. Defaults and conflict rules are defined by the Router.

## 1) When to capture (Triggers)

Capture is required when any of the following changes:
- Create/drop a table
- Column changes (add/remove/type/required/default/semantics)
- Index changes (add/remove/column order/uniqueness)
- Relationship changes (FK semantics, direction, cardinality)

If it is a code-only refactor and the data model is unchanged, you may skip capture (subject to Router write-back switches).

## 2) Write-back rules (MUST)

- Do not edit `data/index.md` directly: write WAL fragments and merge later in a low-conflict window.
- Use `openspec.md` as the detailed source: every index entry must cite the source spec.
- Capture only stable facts: table name, purpose, key field/index notes, relationship summary (do not generate full SQL docs here).
- Anti-bloat: when indexes grow large, split by ARCHIVE_WAL rules.

## 3) Output location and naming

WAL output directory:
```
.agents/llm_wiki/wiki/data/wal/
```

Filename:
```
YYYYMMDD_<feature_or_change>_data_append.md
```

## 4) WAL template (Append Block)

Append (or create) a WAL fragment file using this template:

```markdown
# Data WAL Append - {YYYY-MM-DD} - {feature_or_change}

Source spec:
- `{relative_path_to_openspec.md}`

Append rows for data/index.md:
| Table Name | Purpose | Key Fields / Index Notes | Source Spec |
|---|---|---|---|
| {table_name} | {one-line purpose} | `{key fields + index notes}` | `[{spec_doc_name}]` |

Optional relationship note (text ER):
{table_a} (N) -> {table_b} (1)
```

Notes:
- `Source Spec` MUST be traceable to a spec document.
- Relationship notes should describe only the changed key relationships. Avoid large global ER diagrams.

## 5) Merge policy (Out of scope)

Rules and timing for merging WAL -> index:
- `.agents/workflow/ARCHIVE_WAL.md`

This skill does not auto-merge to avoid index conflicts in team collaboration.
