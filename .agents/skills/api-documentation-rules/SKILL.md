---
name: "api-documentation-rules"
description: "API documentation capture: treat LLM Wiki as the source of truth, write via WAL fragments (do not edit index directly), and use openspec.md as the detailed source."
---

# API Documentation Capture (LLM Wiki + WAL)

Use this skill when an externally exposed API changes. Capture stable API contract facts into the LLM Wiki so future agents can drill down to the source.

## 0) Single Source of Truth (SSOT)

- Routing / profiles / shortcuts / write-back switches: `.agents/router/ROUTER.md`
- Navigation + write-back methodology (reverse funnel + WAL): `.agents/router/CONTEXT_FUNNEL.md`
- WAL + compaction policy: `.agents/workflow/ARCHIVE_WAL.md`
- API index entry: `.agents/llm_wiki/wiki/api/index.md`

This skill defines how to write back API knowledge when write-back is enabled. Defaults and conflict rules are defined by the Router.

## 1) When to capture (Triggers)

Capture is required when any of the following changes:
- New/changed external endpoint (method/path)
- Request/response schema changes (fields, types, required flags, error structure)
- Auth changes (permissions, data scope, tenant isolation)

If it is an internal refactor with no contract change, you may skip capture (subject to Router write-back switches).

## 2) Write-back rules (MUST)

- Do not edit `api/index.md` directly: write WAL fragments and merge later in a low-conflict window.
- Use `openspec.md` as the detailed source: every index entry must cite the source spec.
- Every entry must be traceable: at minimum method + path + one-line summary + spec reference.
- Anti-bloat: when indexes grow large, split by ARCHIVE_WAL rules.

## 3) Output location and naming

WAL output directory:
```
.agents/llm_wiki/wiki/api/wal/
```

Filename:
```
YYYYMMDD_<feature_or_change>_api_append.md
```

## 4) WAL template (Append Block)

Append (or create) a WAL fragment file using this template:

```markdown
# API WAL Append - {YYYY-MM-DD} - {feature_or_change}

Source spec:
- `{relative_path_to_openspec.md}`

Append rows for api/index.md:
| API (Method + Path) | Summary | Doc Link | Write-back Date |
|---|---|---|---|
| {METHOD} {PATH} | {one-line summary} | `[{spec_doc_name}]` | {YYYY-MM-DD} |
```

Notes:
- `{spec_doc_name}` should be the file name under the specs directory (or the consistent spec reference in your workflow).
- `Doc Link` is the source of truth. Do not generate a separate per-endpoint detail page here.

## 5) Merge policy (Out of scope)

Rules and timing for merging WAL -> index:
- `.agents/workflow/ARCHIVE_WAL.md`

This skill does not auto-merge to avoid index conflicts in team collaboration.
