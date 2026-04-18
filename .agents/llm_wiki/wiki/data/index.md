# Data Index (Models)

This index is the routing table for database tables, ER notes, and index strategy.

## Hard Rules (MUST)
- You MUST NOT guess schemas by scanning the entire codebase.
- During `Archive`, the Agent MUST extract table changes from `openspec.md` and append them to the table below.

## Core Tables

| Table Name | Store Type | Purpose | Key Fields / Index Notes | Retention Policy | Source Spec |
|---|---|---|---|---|---|
| (Example) sys_user | MySQL | Stores core user info and credentials | `id, username, tenant_id (indexed)` | Soft delete (is_deleted) | `[user_table.md]` |

---

## Archive Extraction SOP
Append a new row during `Archive` using the template below.

### Append Template
```markdown
| {Table Name} | {Store Type} | {one-line purpose} | `{key fields and index notes}` | {Retention Policy} | `[{spec_doc_name}]` |
```

Anti-bloat rule: if this index grows beyond 50 tables, you MUST split by module (example: `auth_tables.md`, `trade_tables.md`) and keep only top-level links here.
