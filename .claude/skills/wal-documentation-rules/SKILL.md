---
name: "wal-documentation-rules"
description: "MANDATORY documentation capture during the Archive phase. Defines how to extract stable knowledge into Write-Ahead Log (WAL) fragments (domain, api, rules + optional data) to keep the LLM Wiki synced without merge conflicts."
---

# Write-Ahead Log (WAL) Documentation Capture

> **Trigger:** Invoke during the **Archive Phase** (STANDARD tasks only). NOT invoked for PATCH tasks (hotfix-only changes with no new domain knowledge).

## When to Write WAL

| Task Type | WAL Required? |
|---|---|
| STANDARD Archive (new feature, refactor, design) | YES — mandatory |
| PATCH Archive (hotfix, typo, config tweak) | NO — skip WAL entirely |

If unsure, check the task's `_task_brief.md`: if `task_type: PATCH`, skip this skill.

---

## 0. Single Source of Truth

- WAL + compaction policy: `.claude/workflow/ARCHIVE_WAL.md`
- Write-back verification tool: `.claude/scripts/tools/writeback_gate.py`
- Routing and navigation: `.claude/rules/routing.md`

---

## 1. Universal Write-back Rules (MUST)

- **NO DIRECT INDEX EDITS:** NEVER edit any `index.md` files directly during automated runs. Write only WAL fragment files.
- **TRACEABILITY:** Every WAL fragment MUST cite its source spec: `<YYYY-MM-DD>_<slug>_task_brief.md`.
- **STABLE FACTS ONLY:** Extract minimal stable facts. Do not copy-paste entire spec sections.
- **FACT PROVENANCE:** Every fact row in a WAL fragment MUST include a `[Confidence]` and `[Evidence]` annotation:
  - `[Confidence: HIGH]` — verified by tests or explicit specification
  - `[Confidence: MEDIUM]` — inferred from code reading or implicit behavior; assumption stated
  - `[Confidence: LOW]` — based on single observation or undocumented behavior; mark as `⚠ Verify`
  - `[Evidence: file:line]` — the source location that supports this fact
  - Example row: `| OrderStatus | NEW, PROCESSING, DONE, CANCELLED | OrderService.java:87 [Confidence: HIGH] [Evidence: OrderServiceTest.java:42] |`
- **FILENAME CONVENTION:** `.claude/wiki/wiki/{domain}/wal/YYYYMMDD_{topic}_{type}_append.md`
  - `{domain}`: `domain`, `api`, `rules`, or `data`
  - `{type}`: matches domain name — e.g., `domain_append`, `api_append`, `rules_append`, `data_append`
  - Example: `20240315_user_auth_domain_append.md`

---

## 2. Three Mandatory WAL Types (STANDARD Archive)

### WAL Type 1 — Domain (`domain_append`)

**When to write:** New terms, enums, roles, bounded-context concepts appear in the spec.

**Output location:** `.claude/wiki/wiki/domain/wal/`

**Template:**
```markdown
# Domain WAL Append - {YYYY-MM-DD} - {topic}

Source spec: `{relative_path_to_task_brief.md}`

## New / Updated Terms

| Term | Definition | Context / Usage | Confidence | Evidence |
|---|---|---|---|---|
| {term} | {one-line definition} | {which module or flow uses it} | HIGH/MEDIUM/LOW | file:line |

## New / Updated Enums

| Enum | Values | Notes | Confidence | Evidence |
|---|---|---|---|---|
| {EnumName} | `VALUE_A`, `VALUE_B` | {when each applies} | HIGH/MEDIUM/LOW | file:line |
```

---

### WAL Type 2 — API (`api_append`)

**When to write:** New or changed external endpoints (method/path), request/response schema changes, auth/permission changes on endpoints.

**Output location:** `.claude/wiki/wiki/api/wal/`

**Template:**
```markdown
# API WAL Append - {YYYY-MM-DD} - {topic}

Source spec: `{relative_path_to_task_brief.md}`

## New / Changed Endpoints

| API (Method + Path) | Summary | Auth Required | Write-back Date |
|---|---|---|---|
| {METHOD} {/path/action} | {one-line summary} | {role or token type} | {YYYY-MM-DD} |

## Request / Response Notes (if schema changed)

- {endpoint}: request adds `{fieldName}: {type}` — {reason}
- {endpoint}: response removes `{fieldName}` — {reason}
```

---

### WAL Type 3 — Rules (`rules_append`)

**When to write:** New business rules, constraints, invariants, or validation logic are codified that did not exist before.

**Output location:** `.claude/wiki/wiki/rules/wal/`

**Template:**
```markdown
# Rules WAL Append - {YYYY-MM-DD} - {topic}

Source spec: `{relative_path_to_task_brief.md}`

## New / Updated Rules

| Rule ID | Description | Enforcement Point | Violation Behavior | Confidence | Evidence |
|---|---|---|---|---|---|
| RULE-{NNN} | {what must/must not happen} | {controller / service / DB} | {DomainException code or DB constraint} | HIGH/MEDIUM/LOW | file:line |
```

---

### WAL Type 4 — Data (`data_append`) — OPTIONAL

**When to write:** Only when the database schema changes (create/drop table, add/remove/change columns, index changes). Skip if no schema change.

**Output location:** `.claude/wiki/wiki/data/wal/`

**Template:**
```markdown
# Data WAL Append - {YYYY-MM-DD} - {topic}

Source spec: `{relative_path_to_task_brief.md}`

## Table Changes

| Table Name | Change Type | Key Fields / Index Notes | Notes |
|---|---|---|---|
| {table_name} | CREATE / ALTER / DROP | {key fields, indexes} | {purpose or migration note} |

## Relationship Notes (text ER, changed only)

{table_a} (N) -> {table_b} (1) via {foreign_key_column}
```

---

## 3. Verification Step (MUST before closing Archive)

After writing all WAL fragments, run the gate check:

```bash
python3 .claude/scripts/tools/writeback_gate.py --slug <feature_slug>
```

Expected output: all required WAL types listed as `PRESENT`. If any mandatory type is `MISSING`, write the missing fragment before proceeding.

Do NOT close the Archive phase until the gate passes.

---

## 4. Anti-Patterns (NEVER do these)

| Anti-Pattern | Why It Fails |
|---|---|
| Writing raw `.sql` migration files to the project root | Bypasses WAL traceability; causes merge conflicts in team repos |
| Editing `index.md` directly during automated runs | Creates Git conflicts and breaks compaction integrity |
| Writing WAL for PATCH tasks | Pollutes the wiki with trivial entries; PATCH = no WAL |
| Copy-pasting entire spec sections into WAL | WAL must be distilled facts, not raw spec content |
| Skipping `writeback_gate.py` verification | Silent missing WAL; downstream consumers get stale data |
| Using freeform filenames (no convention) | Makes compaction impossible; files cannot be auto-discovered |

---

## 5. Merge Policy (Out of Scope for this Skill)

This skill writes only fragment files. It does NOT merge WAL into stable `index.md` files. Merging is handled by the compaction policy in `.claude/workflow/ARCHIVE_WAL.md`, triggered separately (usually by `@Librarian` or `compactor.py`).
