# Data Index (Models)

This index is the routing table for database tables, ER notes, and index strategy.

## Hard Rules (MUST)
- You MUST NOT guess schemas by scanning the entire codebase.
- During `Archive`, the Agent MUST extract table changes from `openspec.md` and append them to the table below.

## Core Tables

| Table Name | Purpose | Key Fields / Index Notes | Source Spec |
|---|---|---|---|
| (Example) sys_user | Stores core user info and credentials | `id, username, tenant_id (indexed)` | `[user_table.md]` |

---

## Archive Extraction SOP
Append a new row during `Archive` using the template below.

### Append Template
```markdown
| {Table Name} | {one-line purpose} | `{key fields and index notes}` | `[{spec_doc_name}]` |
```

Anti-bloat rule: if this index grows beyond 50 tables, you MUST split by module (example: `auth_tables.md`, `trade_tables.md`) and keep only top-level links here.
