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

### Agent Invocation Modes

Agents in `.claude/agents/` operate in two distinct modes:

| Mode | How | Context available | When to use |
|---|---|---|---|
| **Mounted Role** | Main agent reads the `.md` file and adopts the role inline | Full CLAUDE.md + rules context | Lifecycle phases (Explorer, Implement, QA) — agent = persona overlay |
| **True Sub-Agent** | Spawned via `Agent` tool in an isolated context | Only the agent file itself | Parallel EPIC tasks, isolated heavy operations |

**Critical:** True sub-agents do NOT see CLAUDE.md, lifecycle.md, or rules. Their `.md` file must be self-contained. Current agents in this project are designed as **Mounted Roles** — they assume lifecycle context is present. Do not dispatch them as true isolated sub-agents without first embedding the required context.

### Dispatch Protocol

When dispatching work to a sub-agent:
1. Format the prompt using the contract schema — include allowed scope, constraints, and expected output format
2. Sub-agents do NOT inherit the main agent's context, roles, or wiki — the contract is their sole source of truth
3. If the sub-agent has native agent tooling, prefer that over manual contract formatting

### Handoff Between Sub-Agents

When one sub-agent finishes and another takes over:
1. Incoming sub-agent reads `.claude/runs/launch-specs/launch_spec_*.md` → finds the IN_PROGRESS row
2. Reads the `task_brief.md` from the Artifact column
3. Resumes from the Phase in the launch spec

The `task_brief.md` Machine Section (Allowed Scope + ACs + Hard Constraints) is the universal contract — any sub-agent can read it and know exactly what to do.

---

## Mandatory First Output

Before any action, output a single classification line. No XML blocks.

```
[Intent: Change | Profile: STANDARD | Risk: MEDIUM]
```

**Rules:**
- **STANDARD only** — PATCH and LEARN skip this line entirely. Act directly.
- If the intent is ambiguous: ask one clarifying question before proceeding.
- If a special scenario is matched (DEBUG, EPIC, A–E): append `| Scenario: <name>`.
- Phase transitions use `→ Phase: Implement` inline (no separate `[Lifecycle]` header).

**Scope & confidence check (STANDARD only, inline, no block):**
```
→ Scope: OrderController, OrderService. Confidence: HIGH | MEDIUM — assumption: [X] | LOW — blocking: [Y]
```

For LOW confidence: STOP and ask. For MEDIUM: state the assumption, proceed. For HIGH: proceed directly.

PATCH/TRIVIAL: no scope check line needed. Reasoning is inline with the action.

---

## Initial Action Decision Tree

```
Session start
├─ Rule 0: Workflow Initialization
│   └─ Read CLAUDE.md. Lazy-load other docs only when needed.
├─ Rule -1: Input Normalization
│   └─ No @shortcut AND input > one-liner? → Apply requirement-intake skill.
│   └─ @shortcut or simple one-liner? → Skip intake, proceed directly.
├─ Rule 1: User provided explicit file path / class / snippet?
│   └─ YES → Read it directly. Skip wiki funnel.
├─ Rule 2: Resuming an interrupted session?
│   └─ YES → Read .claude/runs/launch-specs/launch_spec_*.md. Restore from Phase.
└─ Rule 3: Exploring without explicit scope?
    └─ YES → Start at KNOWLEDGE_GRAPH.md and drill down.
```

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
