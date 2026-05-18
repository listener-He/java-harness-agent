# CLAUDE.md — Project Entry Point

Single entry point for all AI coding assistants. Read this file first on every session start.

@.claude/rules/safety-constraints.md

---

## Methodological Anchor (PDD → BDD → SDD/SPEC → TDD → BDD)

This framework composes four methodologies into one lifecycle. Understand them before executing any phase:

| Methodology | Role in Lifecycle | Where |
|---|---|---|
| **PDD** (Plan-Driven Development) | Plan first, then execute. The plan is a first-class artifact: task dependencies, parallelism constraints, and success metrics are explicitly declared before any code exists. SDD/SPEC is PDD's contract-encoding mechanism. | Phase 2 (plan design), Phase 3 (plan review), Phase 6 (plan deviation reflection) |
| **BDD** (Behavior-Driven Development) | Define expected behavior as executable specs in `Given/When/Then` format before any code exists | Phase 1 (write specs), Phase 5 (verify behaviors) |
| **SDD / SPEC** (Specification-Driven Development) | A contract-first approach — `task_brief.md` is the universal spec that governs all downstream work. No code until spec is complete. | Phase 2 (write spec), Phase 3 (review spec), Phase 4 (implement from spec) |
| **TDD** (Test-Driven Development) | Write failing test from ACs first (RED), implement minimum code to pass (GREEN), refactor (REFACTOR). Tests are derived from BDD specs, not invented by implementer. | Phase 4 (RED → GREEN → REFACTOR) |

**Composition**: PDD establishes *what* to plan and *how* dependencies interlock → SDD/SPEC encodes the plan into a *contract* → BDD defines *what* behavior the contract must satisfy → TDD enforces *how* implementation satisfies the contract → BDD at QA *proves* the contract was fulfilled. See [purpose.md](.claude/wiki/purpose.md) for full explanation.

### Maintenance Intent (Non-Code Operations)

When the user input contains maintenance verbs (整理, 合并, 提取, 清理, 拆分, 扫描, 刷新, 沉淀, GC, compact, extract, scan, etc.) combined with knowledge artifacts (wiki, WAL, 文档, 索引, etc.), classify as `Maintenance` intent and route to one of four maintenance flows (see lifecycle.md Maintenance Phases):

| Trigger | Role | Flow |
|---|---|---|
| "整理/合并 wiki", "GC", `@gc`, `@librarian` | `@Librarian` | Aggregate → Merge → Clean → Lint |
| "提取/沉淀知识", "刷新 wiki", `@wiki-update` | `@Knowledge Extractor` | Diff → Extract → WAL fragments → Lint |
| "拆分文档", "index 超过 500 行" | `@Knowledge Architect` | Check size → Deduplicate → Split → Rewrite index |
| "扫描项目", "审计代码库" | Explorer (inline) | Scan → Index → Report |

Maintenance tasks do NOT go through code phases (Propose/Implement/QA). No task_brief needed. No compile checks.

---

## Sub-Agent Dispatch Strategy

This framework treats all AI assistants as sub-agents dispatched via a shared contract. The human decides which sub-agent to assign for each work type — the framework defines the dispatch protocol.

### Work Layers (each dispatchable as a sub-agent task)

| Layer | Work Type | Dispatch Format |
|---|---|---|
| **1. Design & Contract** | Architecture design, API contracts, task breakdown | `task_brief.md` (Machine Section) as output |
| **2. Implementation** | Code generation from detailed spec | `task_brief.md` (Machine Section) as input |
| **3. Search & Explore** | Codebase scanning, call chain tracing | Read-only, return findings |
| **4. Verification** | Gate script execution, test runs | Gate report |
| **5. Knowledge Extraction** | WAL write-back, wiki update | WAL fragments |

Each layer is a self-contained work unit that can be dispatched to any sub-agent via the [sub-agent contract schema](.claude/wiki/schema/subagent_contract_schema.md).

### Agent Invocation — Two-Tier Architecture

| Tier | Agents | Context | How to Invoke |
|---|---|---|---|
| **Mounted Roles** | system-architect, lead-engineer | Full CLAUDE.md + rules + lifecycle + skill-index | Main agent reads the `.md` and adopts the role inline |
| **Isolated Sub-Agents** | All others (code-reviewer, requirement-engineer, documentation-curator, knowledge-extractor, knowledge-architect, librarian, ambiguity-gatekeeper, focus-guard, security-sentinel, skill-graph-curator) | Only their own `.md` file | Spawned via `Agent` tool in isolated context |

**Mounted Roles** share the main agent's full context — they inherit CLAUDE.md, lifecycle.md, safety-constraints, and skill-index. Reserved for roles that require deep codebase understanding and continuous access to project standards (architecture design, code implementation).

**Isolated Sub-Agents** are self-contained. Their `.md` file must embed all required context. Each isolated agent's `## Context` section declares which skills and constraints it depends on. Dispatch them for well-scoped, predictable tasks with clear inputs and outputs.

### Dispatch Protocol

**For Mounted Roles:** Main agent reads the role's `.md` file and adopts the persona inline. No separate dispatch needed — the role acts within the current conversation context.

**For Isolated Sub-Agents:** Spawn via `Agent` tool. The dispatch prompt must include:
1. The `task_brief.md` Machine Section (Allowed Scope + ACs + Hard Constraints) — the universal contract
2. Any task-specific inputs (file paths, commit ranges, etc.)
3. Expected output format

The sub-agent reads its own `.md` for skill references and workflow — the dispatch prompt only carries task-specific information.

### Handoff Between Agents

When one agent finishes and another takes over:
1. Incoming agent reads `.claude/runs/launch-specs/launch_spec_*.md` → finds the IN_PROGRESS row
2. Reads the `task_brief.md` from the Artifact column
3. Resumes from the Phase in the launch spec

The `task_brief.md` Machine Section (Allowed Scope + ACs + Hard Constraints) is the universal contract — any agent can read it and know exactly what to do.

---

## Session Start

- Read CLAUDE.md. Lazy-load rule/wiki files only when needed.
- If resuming an interrupted session: read `.claude/runs/launch-specs/launch_spec_*.md` and restore from Phase.
- If the user provides explicit file paths or code snippets: read them directly. No ceremony.
- If the intent is ambiguous: ask one clarifying question, then proceed.

### When to classify explicitly

Only emit a classification line when the task is **MEDIUM or HIGH risk** and needs a task_brief:

```
[Risk: HIGH | Scenario: B] → task_brief required
```

Routine interactions (reading files, explaining code, simple edits, PATCH-level fixes) — act directly. No classification line.

---

## Single Sources of Truth (SSOT)

| Topic | File |
|---|---|
| Intent routing, profiles, shortcut DSL, context navigation | [.claude/rules/routing.md](.claude/rules/routing.md) |
| Lifecycle phases + phase gates | [.claude/rules/lifecycle.md](.claude/rules/lifecycle.md) |
| Hook definitions | [.claude/rules/hooks.md](.claude/rules/hooks.md) |
| Role definitions + sub-agent dispatch | [.claude/agents/](.claude/agents/) |
| Safety constraints + commit policy | [.claude/rules/safety-constraints.md](.claude/rules/safety-constraints.md) |
| WAL write-back + anti-bloat rules | [.claude/rules/writeback-policy.md](.claude/rules/writeback-policy.md) |

---

## Essential Navigation Pointers

| Resource | Path |
|---|---|
| Wiki root index | [.claude/wiki/KNOWLEDGE_GRAPH.md](.claude/wiki/KNOWLEDGE_GRAPH.md) |
| Skill index | [.claude/skills/skill-index/SKILL.md](.claude/skills/skill-index/SKILL.md) |
| Project constraints & anti-patterns | [.claude/wiki/wiki/preferences/index.md](.claude/wiki/wiki/preferences/index.md) |
| Task brief schema | [.claude/wiki/schema/task_brief_schema.md](.claude/wiki/schema/task_brief_schema.md) |
| Sub-agent contract schema | [.claude/wiki/schema/subagent_contract_schema.md](.claude/wiki/schema/subagent_contract_schema.md) |
