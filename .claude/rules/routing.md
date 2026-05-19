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

Pick the lowest tier whose criteria fully cover the request. Default to lower tier when ambiguous — escalation is cheap, downgrade is wasted ceremony.

| Risk | Criteria | Profile |
|---|---|---|
| **TRIVIAL** | ≤3 files. No public API, DB schema, auth, or error-code system change. Includes: bugfixes within a single domain, defensive checks, validation, logs, comments, formatting, typos, internal refactors. | PATCH |
| **LOW** | 4–6 files OR small bugfix spanning two related domains. Still no public API/DB/auth/error-code change. | PATCH |
| **MEDIUM** | New/changed external API, public method signature change, or core business path change. No DB/auth foundation change. | STANDARD |
| **HIGH** | DB schema/index changes, auth/permission strategy, error code system changes, ≥3 domains, shared utilities, unclear blast radius. | STANDARD |

**TRIVIAL flow:** `Implement → QA → Archive` — no task_brief, no inline Explorer, no WAL.
**LOW flow:** `Implement → QA → Archive` — no task_brief, no WAL; if scope is unclear at start, do a quick mental Explorer (no document).
**STANDARD (MEDIUM) flow:** `Explorer → Propose(task_brief) → Review → Implement → QA → Archive`
**STANDARD (HIGH) flow:** `Explorer → Propose(task_brief, ≥2 ADR) → Review(adversarial) → Approval Gate → Implement → QA → Archive`

### Boundary rules

- **Never** force STANDARD on a TRIVIAL/LOW change just because the user mentioned "important" or "production". Use the table criteria, not vibes.
- **Always** escalate if, mid-implementation, you discover the change actually touches public API/DB/auth — stop, emit `[Plan Invalidation]`, ask whether to switch to STANDARD.
- **Vibe override:** if the user invokes `@vibe`, `@patch`, or starts the request with a clear directive ("just add", "quick fix", "tweak"), bias one tier down.

---

## Special Scenarios

These override the default risk classification. When a scenario below specifies a **Read:** line, that exact archive file must be read at the indicated phase — the path is the instruction, no decision needed.

### Scenario DEBUG — Deep Troubleshooting
**Trigger:** Bug/error with unknown root cause.
**Routing:** Profile PATCH. ALLOWED to run terminal commands (≤5 retries). FORBIDDEN from modifying code. Once root cause found → yield to user or transition to Change intent.

### Scenario EPIC — Massive Refactoring / Cross-Domain Feature
**Trigger:** Feature spanning ≥3 domains, framework migration, or massive refactoring.
**Routing:** Profile STANDARD, risk HIGH (forced). MUST slice work into micro-tasks. MUST delegate to sub-agents via contract schema. MUST NOT write code directly — act as Foreman + QA.
**Read:** `.claude/skills-archive/blueprint/SKILL.md` (system-architect, Propose phase) + `.claude/skills-archive/dispatching-parallel-agents/SKILL.md` (when ≥2 independent workstreams).

### Scenario A — Emergency Hotfix
**Trigger:** Production incident, critical bug, ship immediately.
**Routing:** Profile PATCH. No Propose/Review. Requires `## Emergency Justification` + `secrets_linter.py` before Archive.
**Read:** `.claude/skills-archive/incident-response/SKILL.md` (main agent, FIRST action — triage → mitigation → post-mortem).

### Scenario B — Database / System Migration
**Trigger:** DDL changes (CREATE TABLE, ALTER TABLE, ADD INDEX, DROP COLUMN, etc.) OR A→B system migration.
**Routing:** Profile STANDARD, risk HIGH (forced). Approval Gate required. Gate: `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>`. Data WAL write-back MANDATORY.
**Read:** `.claude/skills-archive/migration-planner/SKILL.md` (system-architect, Propose phase — equivalence-test-first protocol).

### Scenario C — Breaking API Change
**Trigger:** Removing/renaming public endpoint, backward-incompatible schema change, auth/permission strategy change.
**Routing:** Profile STANDARD, risk HIGH (forced). Gate: `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>`. Must document migration guide in task_brief.

### Scenario D — Performance Tuning
**Trigger:** Performance-focused request (slow query, high latency, memory/CPU).
**Routing:** LEARN first (gather baseline evidence: bottleneck + metric + proposed fix). Then re-route as Change.
**Read (optional):** `.claude/skills-archive/external-research/SKILL.md` if baseline reveals an unknown systemic pattern.

### Scenario E — Dependency Upgrade
**Trigger:** Changes to `pom.xml` dependencies.
**Routing:** PATCH for patch-version bumps; STANDARD for major/minor version or new dependency. Gate: `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>`.

### Scenario GREENFIELD — Starting from scratch
**Trigger:** No `src/` directory OR user explicitly says "from scratch / new project".
**Routing:** Profile STANDARD, risk HIGH (because everything is being decided for the first time).
**Read:** `.claude/skills-archive/greenfield-scaffold/SKILL.md` (requirement-engineer + system-architect, replaces "infer from existing code" Explorer logic). Optionally `.claude/skills-archive/deepinit/SKILL.md` for hierarchical CLAUDE.md generation.

### Scenario RELEASE — Release / Deployment
**Trigger:** User requests a release, version tag, deploy.
**Routing:** Profile MAINTENANCE (no code change typically).
**Read:** `.claude/skills-archive/release/SKILL.md` (main agent — validates pre-release gates).

### Scenario PIPELINE — Full Idea→Delivery Loop
**Trigger:** User invokes `@ai-pipeline` or "run the full pipeline" or "from idea to delivery".
**Routing:** Profile STANDARD, multi-phase orchestration.
**Read:** `.claude/skills-archive/ai-pipeline/SKILL.md` (main agent — orchestrates blueprint → decisions → eval → improve → cleanup). Also read `.claude/skills-archive/self-improve/SKILL.md` and `.claude/skills-archive/eval-harness/SKILL.md` when their phases fire.

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

| Shortcut | Profile | Effect |
|---|---|---|
| `@read` / `@learn` | LEARN | Read-only; never write code, never run gates |
| `@vibe` / `@patch` / `@quickfix` | PATCH | Act directly; skip Explorer/Propose/WAL even if heuristics suggest LOW |
| `@standard` | STANDARD | Force task_brief + lifecycle, even if heuristics suggest PATCH |
| `@gc` / `@librarian` | MAINTENANCE | Librarian flow |
| `@wiki-update` / `@milestone` | MAINTENANCE | Knowledge Extractor flow |

Flags: `--risk low|medium|high`, `--launch`, `--no-launch`, `--test "<cmd>"`, `--yes` (auto-confirm).
`@learn` MUST NOT combine with `--launch` or `--writeback`.

When no shortcut is given, classify by the Risk Classification table; default to the lower tier when ambiguous.
