---
name: "wal-documentation-rules"
description: "MANDATORY documentation capture during the Archive phase. Defines how to extract stable API and Database facts into Write-Ahead Log (WAL) fragments to keep the LLM Wiki synced without merge conflicts."
---

# Write-Ahead Log (WAL) Documentation Capture

> **Trigger:** Invoke this skill during the **Archive Phase** (Lifecycle Phase 6) whenever there are changes to external API contracts or the Database schema.

## 0) Single Source of Truth (SSOT)
- Routing / profiles / shortcuts / write-back switches: `.agents/router/ROUTER.md`
- Navigation + write-back methodology: `.agents/router/CONTEXT_FUNNEL.md`
- WAL + compaction policy: `.agents/workflow/ARCHIVE_WAL.md`

## 1) Universal Write-back Rules (MUST)
- **NO DIRECT EDITS:** NEVER edit `api/index.md` or `data/index.md` directly. You MUST write WAL fragments into the respective `wal/` directories.
- **TRACEABILITY:** Every WAL entry MUST cite the source specification (`<YYYY-MM-DD>_<slug>_openspec.md` or the corresponding delivery capsule).
- **STABLE FACTS ONLY:** Do not copy-paste the entire spec. Extract only the key, stable facts (e.g., table names, API paths, summaries).
- **FILENAME CONVENTION:** `YYYYMMDD_<feature_or_change>_<type>_append.md`

---

## 📝 Scenario A: API Contract Changes

**When to capture:**
- New/changed external endpoint (method/path)
- Request/response schema changes
- Auth/Permission changes on endpoints

**Output Location:**
`.agents/llm_wiki/wiki/api/wal/`

**WAL Template (API Append Block):**
```markdown
# API WAL Append - {YYYY-MM-DD} - {feature_or_change}

Source spec:
- `{relative_path_to_<YYYY-MM-DD>_<slug>_openspec.md}`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| {METHOD} {PATH} | {one-line summary} | `[{spec_doc_name}]` | {YYYY-MM-DD} |
```
*(Note: `Doc Link` is the source of truth. Do not generate a separate per-endpoint detail page here.)*

---

## 🗄️ Scenario B: Database Model Changes

**When to capture:**
- Create/drop a table
- Column changes (add/remove/type/semantics)
- Index or Relationship changes (FK semantics)

**Output Location:**
`.agents/llm_wiki/wiki/data/wal/`

**WAL Template (Data Append Block):**
```markdown
# Data WAL Append - {YYYY-MM-DD} - {feature_or_change}

Source spec:
- `{relative_path_to_<YYYY-MM-DD>_<slug>_openspec.md}`

Append rows for data/index.md:
| Table Name | Purpose | Key Fields / Index Notes | Source Spec |
|---|---|---|---|
| {table_name} | {one-line purpose} | `{key fields + index notes}` | `[{spec_doc_name}]` |

Optional relationship note (text ER):
{table_a} (N) -> {table_b} (1)
```
*(Note: Relationship notes should describe ONLY the changed key relationships. Avoid generating massive global ER diagrams.)*

---

## 3) Merge Policy (Out of Scope for this Skill)
This skill does not auto-merge the WAL fragments to the main index to avoid Git conflicts in team collaboration. The merging is handled by the `.agents/workflow/ARCHIVE_WAL.md` compaction policy (usually triggered by `@Librarian`).
