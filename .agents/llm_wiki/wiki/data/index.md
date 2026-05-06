# Data Index (Models)

This index is the routing table for database tables, ER notes, and index strategy.

## Hard Rules (MUST)
- You MUST NOT guess schemas by scanning the entire codebase.
- During `Archive`, the Agent MUST extract table changes from `<YYYY-MM-DD>_<slug>_openspec.md` and append them to the table below.

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


---

## WAL Compaction - data - 2026-05-06 15:26:56


### 20260424_mingsi_skills_analysis.md

# Mingsi-skills Analysis WAL

- **Date**: 2026-04-24
- **Domain**: External AI Agent Skills / Prompt Engineering
- **Concept**: Analyzed `https://github.com/qingjian0/mingsi-skills`
- **Key Findings**: Mingsi is a structured thinking framework for AI. It uses Complexity Scaling (L1-L3), Critical Thinking (Cognitive Bias Checks), Pragmatism (Assess before thinking), and Closed-loop validation (Quality Gates).
