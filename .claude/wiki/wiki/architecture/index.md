# Architecture Index (Baselines & ADRs)

Architecture baselines and ADRs (Architecture Decision Records). Consulted for cross-cutting technical choices (module boundaries, middleware, global patterns).

## Baselines & Guards
- Security baseline: [../preferences/security_rules.md](../preferences/security_rules.md)

## ADR List

| ADR # | Title | Status | Decision Summary | Date | Doc Link |
|---|---|---|---|---|---|
| (Example) ADR-001 | Use JWT for stateless auth | Accepted | Reduce Redis dependency; validate at the gateway | 2026-04-14 | `[adr_001_jwt.md]` |

> Append rule: WAL fragment → `wal/YYYYMMDD_<slug>_architecture.md`. Format enforced by `wal_template_gate.py`.

## WAL Fragments
