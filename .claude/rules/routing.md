# Intent Routing — Profiles & Risk Classification

Lifecycle phases: [lifecycle.md](lifecycle.md)

---

## Profiles

| Profile | When | Artifacts | Approval Gate |
|---|---|---|---|
| **LEARN** | Read/explain/understand code | None | No |
| **PATCH** | TRIVIAL or LOW risk change | None (TRIVIAL) / Slim Spec (LOW) | No |
| **STANDARD** | MEDIUM or HIGH risk change | task_brief.md + launch_spec | MEDIUM: FYI only; HIGH: required |
| **MAINTENANCE** | Wiki/WAL operations, no code changes | WAL fragments | No |

---

## Risk Classification

| Risk | Criteria | Profile |
|---|---|---|
| **TRIVIAL** | ≤1 file, no API/DB/schema changes, purely defensive (null checks, validation, error codes, logs, comments, formatting, typos) | PATCH |
| **LOW** | Small bugfix, clear blast radius, logic tweak within single domain | PATCH |
| **MEDIUM** | New/changed external API, core business path change without DB/auth foundation changes | STANDARD |
| **HIGH** | DB schema/index changes, auth/permission strategy, error code system changes, cross-domain changes, shared utilities, unclear blast radius | STANDARD |

**TRIVIAL flow:** `Implement → QA → Archive` (no task_brief, no WAL write-back)
**LOW flow:** `Explorer(inline) → Implement → QA → Archive`
**STANDARD flow:** `Explorer → Propose → Review → [Approval Gate if HIGH] → Implement → QA → Archive`

---

## Special Scenarios

These override the default risk classification.

### Scenario DEBUG — Deep Troubleshooting
**Trigger:** Bug/error with unknown root cause.
**Routing:** Profile PATCH. ALLOWED to run terminal commands (≤5 retries). FORBIDDEN from modifying code. Once root cause found → yield to user or transition to Change intent.

### Scenario EPIC — Massive Refactoring / Cross-Domain Feature
**Trigger:** Feature spanning ≥3 domains, framework migration, or massive refactoring.
**Routing:** Profile STANDARD, risk HIGH (forced). MUST slice work into micro-tasks. MUST delegate to sub-agents via contract schema. MUST NOT write code directly — act as Foreman + QA.

### Scenario A — Emergency Hotfix
**Trigger:** Production incident, critical bug, ship immediately.
**Routing:** Profile PATCH. No Propose/Review. Requires `## Emergency Justification` + `secrets_linter.py` before Archive.

### Scenario B — Database Migration
**Trigger:** DDL changes (CREATE TABLE, ALTER TABLE, ADD INDEX, DROP COLUMN, etc.).
**Routing:** Profile STANDARD, risk HIGH (forced). Approval Gate required. Gate: `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>`. Data WAL write-back MANDATORY.

### Scenario C — Breaking API Change
**Trigger:** Removing/renaming public endpoint, backward-incompatible schema change, auth/permission strategy change.
**Routing:** Profile STANDARD, risk HIGH (forced). Gate: `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>`. Must document migration guide in task_brief.

### Scenario D — Performance Tuning
**Trigger:** Performance-focused request (slow query, high latency, memory/CPU).
**Routing:** LEARN first (gather baseline evidence: bottleneck + metric + proposed fix). Then re-route as Change.

### Scenario E — Dependency Upgrade
**Trigger:** Changes to `pom.xml` dependencies.
**Routing:** PATCH for patch-version bumps; STANDARD for major/minor version or new dependency. Gate: `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>`.

---

## Maintenance Operations

| Trigger | Role | Flow |
|---|---|---|
| "整理/合并 wiki", `@gc` | Librarian | Aggregate → Merge → Clean → Lint |
| "提取/沉淀知识", `@wiki-update` | Knowledge Extractor | Diff → Extract → WAL fragments → Lint |
| "拆分文档", index > 500 lines | Knowledge Architect | Check → Deduplicate → Split → Rewrite index |
| "扫描项目", "审计代码库" | Explorer (inline) | Scan → Index → Report |

---

## Shortcuts (Explicit Overrides)

| Shortcut | Profile |
|---|---|
| `@read` / `@learn` | LEARN |
| `@patch` / `@quickfix` | PATCH |
| `@standard` | STANDARD |
| `@gc` / `@librarian` | MAINTENANCE (Librarian) |
| `@wiki-update` / `@milestone` | MAINTENANCE (Knowledge Extractor) |

Flags: `--risk low|medium|high`, `--launch`, `--no-launch`, `--test "<cmd>"`, `--yes` (auto-confirm).
`@learn` MUST NOT combine with `--launch` or `--writeback`.
