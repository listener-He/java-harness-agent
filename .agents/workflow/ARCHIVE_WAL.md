# Knowledge Extraction & Anti-Bloat Rules (WAL + Compaction)

Focus: define how the Agent extracts stable knowledge from a single `openspec.md` during `Archive`, writes WAL fragments safely, and prevents index bloat over time.

---

## 1. Core Objectives
- De-duplication: consolidate repeated knowledge into a single stable place.
- Slimming: split documents when they exceed hard limits.
- Cold/Hot separation: after extraction, move specs to cold storage.
- **Language Preference (Audience separation):**
  - **Machine-facing content** (e.g., Code snippets, schemas, YAML, directory structures, script names) MUST be kept in **English**.
  - **Human-facing content** (e.g., explanations, context, rationale, mitigation strategies, and summaries) MUST be written in the **User's primary language** (e.g., if Chinese, use Chinese; English is the fallback).

---

## 2. Extraction Protocol (MUST in `Archive`)
During `Archive` `post_hook`, the Agent MUST extract from the current `openspec.md`:

### 2.1 Domain Extraction
- Scan: the "Context" / domain sections.
- Action (WAL write-back): if new terms/enums/roles appear, write a short definition into `.agents/llm_wiki/wiki/domain/wal/` as a fragment file (example: `YYYYMMDD_feature_x_domain_append.md`).
- Hard rule: DO NOT directly edit shared `index.md` files during automated runs.

### 2.2 Data Extraction
- Scan: the "Data Model" section.
- Action (WAL write-back): write table summaries (table name, key fields, index strategy) into `.agents/llm_wiki/wiki/data/wal/` as a fragment file (example: `YYYYMMDD_feature_x_data_append.md`).

### 2.3 API Extraction
- Scan: the "API Contract" section.
- Action (WAL write-back): write new/changed API signatures (Method + Path + short request/response note) into `.agents/llm_wiki/wiki/api/wal/` as a fragment file (example: `YYYYMMDD_feature_x_api_append.md`).

---

## 3. Archiving & Cleanup (MUST)
### 3.1 Move spec to cold storage
- Move the spec: after extraction, move the session `openspec.md` to:
  - `.agents/llm_wiki/archive/`
- Rename it with a date prefix to avoid collisions:
  - `YYYYMMDD_<feature>_openspec.md`

### 3.2 Clean the active index
 - update `.agents/llm_wiki/wiki/specs/index.md` by removing the entry from the active list (or moving it into "Recently Archived").

### 3.3 Keep pointer files in `runs/` (Conservative Mode)

To prevent the next task from accidentally reusing the previous session’s spec/scope, replace:
- `.agents/workflow/runs/openspec.md`
- `.agents/workflow/runs/focus_card.md`

with read-only pointer files that only contain the archive location.

Use the provided tool:

```bash
python3 .agents/scripts/tools/archive_session_artifacts.py --slug <feature_slug>
```
### 3.5 Merge (Low-conflict Window)
- Goal: merge WAL fragments into stable `index.md` files and reorganize them if needed.
- Approach:
  - Human merges periodically; or
  - Use an optional merge script (example: `.agents/scripts/wiki/compactor.py`) only when explicitly triggered.

---

## 4. Anti-Bloat Hard Limits

### 500-line Split Rule (MUST)
When merging knowledge, if any target file exceeds 500 lines, you MUST split it:
1. Create subdirectories per business module and new `index.md` files.
2. Move content into the sub-indexes.
3. Keep the original file as a router with links only.
4. If top-level structure changes, update `.agents/llm_wiki/KNOWLEDGE_GRAPH.md`.
