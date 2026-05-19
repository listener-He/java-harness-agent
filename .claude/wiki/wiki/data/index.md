# Data Index (Models)

Routing table for database tables, ER notes, and index strategy.

| Table Name | Store Type | Purpose | Key Fields / Index Notes | Retention Policy | Source Spec |
|---|---|---|---|---|---|
| (Example) sys_user | MySQL | Stores core user info and credentials | `id, username, tenant_id (indexed)` | Soft delete (is_deleted) | `[user_table.md]` |

> Append rule: WAL fragment → `wal/YYYYMMDD_<slug>_data.md`. Format enforced by `wal_template_gate.py`. Split per-module (e.g. `auth_tables.md`, `trade_tables.md`) when > 50 tables.

## WAL Fragments
