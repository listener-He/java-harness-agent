# AGENTS.md — Multi-Assistant Entry Point

Single entry point for all AI coding assistants. Read this file first on every session start. All links use paths relative to the repo root.

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

Each layer is a self-contained work unit that can be dispatched to any sub-agent via the [sub-agent contract schema](.agents/llm_wiki/schema/subagent_contract_schema.md).

### Dispatch Protocol

When dispatching work to a sub-agent:
1. Format the prompt using the contract schema — include allowed scope, constraints, and expected output format
2. Sub-agents do NOT inherit the main agent's context, roles, or wiki — the contract is their sole source of truth
3. If the sub-agent has native agent tooling, prefer that over manual contract formatting

### Handoff Between Sub-Agents

When one sub-agent finishes and another takes over:
1. Incoming sub-agent reads `.agents/router/runs/launch_spec_*.md` → finds the IN_PROGRESS row
2. Reads the `task_brief.md` from the Artifact column
3. Resumes from the Phase in the launch spec

The `task_brief.md` Machine Section (Allowed Scope + ACs + Hard Constraints) is the universal contract — any sub-agent can read it and know exactly what to do.

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Context Bloat Prevention** | When dispatching tasks to sub-agents, format prompts using the contract in [.agents/llm_wiki/schema/subagent_contract_schema.md](.agents/llm_wiki/schema/subagent_contract_schema.md). If the sub-agent has native agent tooling, use that instead. |
| **Budget exhausted** | STOP and ask human. Do not guess paths or continue reading. Soft budgets: Wiki ≤ 5, Code ≤ 12, Web ≤ 4. |
| **Approval Gate** | For HIGH risk changes only: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval. MEDIUM: show spec summary as FYI, proceed without waiting. |
| **Anti-loop** | Max 3 retries for scripts/linters. Max 2 retries for compilation fixes. On exceed: STOP and ask human. |
| **Scope Guard** | Do not modify files outside `## Allowed Scope` of `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md` without explicit human permission. If no task_brief exists (PATCH/TRIVIAL), scope = the single file being changed. |
| **Artifact Paths** | Runtime artifacts live under `.agents/workflow/runs/`. Never generate artifacts in the repo root. TRIVIAL/LOW: no task_brief file needed. Archive phase moves task_brief to `llm_wiki/archive/`. |
| **State Files** | Only two state files: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract). No other runtime state files (no brake_snapshot, no engine_state.json). |

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
- This single line replaces the old `[Intent Check]` + `<Cognitive_Brake>` + `[Lifecycle]` + `[Mounted Role]` ceremony.

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
│   └─ Read AGENTS.md. Lazy-load other docs only when needed.
├─ Rule -1: Input Normalization
│   └─ No @shortcut AND input > one-liner? → Apply requirement-intake skill.
│   └─ @shortcut or simple one-liner? → Skip intake, proceed directly.
├─ Rule 1: User provided explicit file path / class / snippet?
│   └─ YES → Read it directly. Skip wiki funnel.
├─ Rule 2: Resuming an interrupted session?
│   └─ YES → Read router/runs/launch_spec_*.md. Restore from Phase.
└─ Rule 3: Exploring without explicit scope?
    └─ YES → Start at KNOWLEDGE_GRAPH.md and drill down.
```

---

## Single Sources of Truth (SSOT)

| Topic | File |
|---|---|
| Intent routing, profiles, shortcut DSL | [.agents/router/ROUTER.md](.agents/router/ROUTER.md) |
| Context navigation + write-back | [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md) |
| Lifecycle phases + phase gates | [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md) |
| Hook definitions | [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md) |
| Role definitions + sub-agent dispatch | [.agents/workflow/ROLE_MATRIX.md](.agents/workflow/ROLE_MATRIX.md) |

---

## Essential Navigation Pointers

| Resource | Path |
|---|---|
| Wiki root index | [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md) |
| Skill index | [.agents/skills/skill-index/SKILL.md](.agents/skills/skill-index/SKILL.md) |
| Project constraints & anti-patterns | [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md) |
| Task brief schema | [.agents/llm_wiki/schema/task_brief_schema.md](.agents/llm_wiki/schema/task_brief_schema.md) |

---

## Commit Policy

**Never commit runtime state or caches:**

- `.agents/router/runs/`
- `.agents/workflow/runs/` (includes active `task_brief.md` and `launch_spec_*.md`)
- `.agents/events/drift_queue/`
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, archived task briefs (`.agents/llm_wiki/archive/*_task_brief.md`), and `.agents/**/wal/` fragments.

---

## Standard Workflow Reference

For a multi-turn example of a STANDARD task, see [.agents/workflow/EXAMPLES.md](.agents/workflow/EXAMPLES.md).
