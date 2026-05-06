# API Index (Contracts)

This index is the routing table for all externally exposed APIs.

## Hard Rules (MUST)
- During `Archive`, the Agent MUST extract API signatures from `<YYYY-MM-DD>_<slug>_openspec.md` and append them into the table(s) below.
- Do not guess API contracts by scanning the whole codebase. Use the wiki as the source of truth, then validate against code when needed.

## Core Domain APIs

| API (Method + Path) | Summary | Auth & Identity | Version | Doc Link | Write-back Date |
|---|---|---|---|---|---|
| (Example) POST /api/v1/user/login | User login and token issuance | None / Guest | v1 | `[user_api.md]` | 2026-04-14 |

---

## Archive Extraction SOP
During `Archive`, append a new row using the template below.

### Append Template
```markdown
| {Method} {Path} | {one-line summary} | {Auth Type} / {Identity Type} | {Version} | `[{spec_doc_name}]` | {YYYY-MM-DD} |
```

Anti-bloat rule: if this table exceeds 50 rows, you MUST split it into per-module sub-indexes (example: `user/`, `trade/`) and keep this file as a high-level router only.


---

## WAL Compaction - api - 2026-05-06 15:26:56


### 20260506_trae_skills_import_api_append.md

# API WAL Append - 2026-05-06 - trae_skills_import

Source spec:
- `.agents/workflow/runs/2026-05-06_trae_skills_import_openspec.md`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| N/A | No API contract changes (skills import only). | `[2026-05-06_trae_skills_import_openspec.md]` | 2026-05-06 |


---

## WAL Compaction - api - 2026-05-06 15:52:44


### 20260506_skills_align_api_append.md

# API WAL Append - 2026-05-06 - skills_align

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_align_openspec.md`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| N/A | No API contract changes (skills alignment only). | `[2026-05-06_skills_align_openspec.md]` | 2026-05-06 |


---

## WAL Compaction - api - 2026-05-06 16:09:12


### 20260506_skills_consolidate_api_append.md

# API WAL Append - 2026-05-06 - skills_consolidate

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate_openspec.md`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| N/A | No API contract changes (skills consolidate only). | `[2026-05-06_skills_consolidate_openspec.md]` | 2026-05-06 |


---

## WAL Compaction - api - 2026-05-06 16:26:06


### 20260506_skills_consolidate2_api_append.md

# API WAL Append - 2026-05-06 - skills_consolidate2

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate2_openspec.md`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| N/A | No API contract changes (skills consolidate2 only). | `[2026-05-06_skills_consolidate2_openspec.md]` | 2026-05-06 |


---

## WAL Compaction - api - 2026-05-06 16:36:38


### 20260506_skills_enable_set_api_append.md

# API WAL Append - 2026-05-06 - skills_enable_set

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_enable_set_openspec.md`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| N/A | No API contract changes (skills enable set/index only). | `[2026-05-06_skills_enable_set_openspec.md]` | 2026-05-06 |
