# API Index (Contracts)

Routing table for externally exposed API endpoints.

| API (Method + Path) | Summary | Auth & Identity | Version | Doc Link | Write-back Date |
|---|---|---|---|---|---|
| (Example) POST /api/v1/user/login | User login and token issuance | None / Guest | v1 | `[user_api.md]` | 2026-04-14 |

> Append rule: WAL fragment → `wal/YYYYMMDD_<slug>_api.md`. Format enforced by `wal_template_gate.py`. Split per-module (e.g. `user/`, `trade/`) when > 50 rows.

## WAL Fragments
