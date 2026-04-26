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
