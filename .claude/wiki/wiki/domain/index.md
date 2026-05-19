# Domain Index (Vocabulary & State)

Business vocabulary, state machines, and invariants. Drilled into during Explorer/Propose to avoid term drift.

## Core Concepts & State Machines

| Concept | Definition | Related Concepts | Details |
|---|---|---|---|
| (Example) Opportunity | A sales opportunity representing a potential deal | Lead, Account, Deal | `[opportunity_states.md]` |

> Append rule: WAL fragment → `wal/YYYYMMDD_<slug>_domain.md`. Format enforced by `wal_template_gate.py`. Split into per-line dictionaries when > 30 concepts.

## WAL Fragments
