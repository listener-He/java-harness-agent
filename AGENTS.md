# AGENTS.md — Entry Point & Hard Constraints

Single entry point. Read this file first on every session start. All links here use paths relative to the repo root.

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Context Bloat Prevention** | Prefer native Search Sub-Agents (e.g., Trae, Qoder, Claude Code, Gemini CLI, Codex) for codebase scanning. When dispatching tasks to Sub-Agents, you MUST format your prompt using [.agents/llm_wiki/schema/subagent_contract_schema.md](.agents/llm_wiki/schema/subagent_contract_schema.md). If unavailable, STRICTLY enforce Budget Limits (Wiki ≤ 3, Code ≤ 8) as the "Poor Man's Sub-Agent". Pagination doesn't count. |
| **Reward Mechanism** | (Elastic extension) Output a `<Confidence_Assessment>` block explaining the specific missing concept/symbol to earn a budget reward (+2 wiki / +3 code) before hitting the hard stop (see [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). |
| **Budget exhausted** | STOP. File an Escalation Card (format in [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). Do not guess paths or continue reading. |
| **Approval Gate** | For MEDIUM/HIGH risk changes: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval before writing any code. |
| **Anti-loop** | Max 3 retries for scripts/linters. STRICT MAX 2 retries for compilation/RunCommand fixes. On exceed: STOP and ask human. Never infinite loop. |
| **Scope Guard** | Do not modify files outside the agreed `.agents/workflow/runs/focus_card.md` scope without explicit human permission. |
| **Artifact Paths** | ALL runtime artifacts (`openspec.md`, `focus_card.md`) MUST be generated in `.agents/workflow/runs/`. Never generate them in the root directory. Follow `ARCHIVE_WAL.md` during Archive phase to move them. |
| **Exit Gate (Archive)** | Before yielding the final response to the human, you MUST output an `[Lifecycle: Archive]` block, move `openspec.md` to `.agents/llm_wiki/archive/YYYYMMDD_<feature>_openspec.md`, and write WAL fragments for any new API, Domain, or Logic changed. NEVER say you are done without writing the WAL. |
| **Task Checklist** | Before entering `Execute` phase, you MUST create `.agents/workflow/runs/current_task.md` with `[ ] Write-back to wiki (WAL)` as the last item to track progress. |

---

## Mandatory First Outputs

Before any action (reading files, searching, writing code), the Agent MUST output the following headers AND a structured thinking block:

```xml
[Intent Check] intent=<Learn|Change|DocQA|Audit> | profile=@<learn|patch|standard> | risk=<TRIVIAL|LOW|MEDIUM|HIGH> | scenario=<none|DEBUG|EPIC|A|B|C|D|E> | emergency=<true|false>
        [Lifecycle: <Plan|Execute|Validate|Archive>] | [Mounted Role: @<Role>]

<Cognitive_Brake>
- Role & Scope: As [@RoleX], my authorized file boundary is [focus_card.md / None]. Am I crossing it?
- Budget & Context: Wiki reads: [X]/3, Code reads: [Y]/8. Do I need to Grep specific project standards/exceptions first?
- Architectural Defense: Is this a cross-domain/transactional change? Am I at a STOP gate like Approval or Validation?
- Next State: What exact artifact, WAL, or validation command will I output/run right now?
</Cognitive_Brake>
```

**Dynamic Cognitive Brake (Token Optimization):**
- For `@standard` profile or high-risk tasks: The FULL 4-point `<Cognitive_Brake>` is MANDATORY.
- For `@patch` profile or minor continuous steps: You may use a Micro-Brake to save tokens: `<Brake>Scope: [safe/boundaries]. Action: [next step]</Brake>`.

**Rules:**
- **CoT Requirement**: The `<Cognitive_Brake>` block is MANDATORY. It forces you to adopt the assigned Role Personas (e.g., as `@Security Sentinel` or `@Focus Guard`) before acting like a Coder.
- **Language Matching**: The internal reasoning text inside the `<Cognitive_Brake>` MUST be written in the same natural language as the user's most recent prompt (e.g., 简体中文, にほんご, Español,  English) to maximize human readability. The XML tags and protocol headers (e.g., `[Intent Check]`) MUST remain in English for script parsing.
- **Audience-Aware Documentation**: When generating artifacts (e.g., `openspec.md`, `WAL fragments`, or `explore_report.md`), the Agent MUST distinguish the audience. Machine-facing content (code, schema, paths) MUST be in **English**. Human-facing content (rationale, business logic, summaries) MUST default to the user's natural language (e.g., **Chinese** has priority over English if the user speaks Chinese).
- If the intent is ambiguous (missing action or object signal): output `[Intent Check] AMBIGUOUS — <reason>` and ask one clarifying question before proceeding.
- If a special scenario (DEBUG, EPIC, A–E) is matched: include `scenario=<name>` and apply Scenario routing overrides (see [ROUTER.md](.agents/router/ROUTER.md#6-special-scenarios)).
- You MUST explicitly declare any Phase transition using the `[Lifecycle: ...]` header.
- The `[Mounted Role: ...]` MUST be derived from `.agents/workflow/ROLE_MATRIX.md` based on the current Phase.
- These lines are the only required headers. Do not add verbose preamble before them.

---

## Initial Action Decision Tree

```
Session start
├─ Rule 0.0: Workflow Initialization (SSOT Lazy Loading)
│   └─ Read ONLY `AGENTS.md` on startup. Lazy-load `LIFECYCLE.md`, `ROLE_MATRIX.md`, or specific `SKILL.md` ONLY when transitioning phases or executing specific tasks.
├─ Rule 0: User provided explicit file path / class / snippet?
│   └─ YES → Read it directly. Skip wiki funnel.
├─ Resuming an interrupted session?
│   └─ YES → Read router/runs/launch_spec_*.md first. Restore from Status/Phase.
└─ Exploring a domain without explicit scope?
    └─ YES → Start at KNOWLEDGE_GRAPH.md and drill down.
```

---

## Single Sources of Truth (SSOT)

| Topic | File |
|---|---|
| Intent routing, profiles, shortcut DSL | [.agents/router/ROUTER.md](.agents/router/ROUTER.md) |
| Context navigation + write-back | [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md) |
| Lifecycle phases + phase gates | [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md) |
| Hook definitions (pre/guard/post/fail/loop) | [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md) |
| Role mounting by (intent, profile, phase) | [.agents/workflow/ROLE_MATRIX.md](.agents/workflow/ROLE_MATRIX.md) |

---

## Essential Navigation Pointers

| Resource | Path |
|---|---|
| Wiki root index | [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md) |
| Skill index | [.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md) |
| Project constraints & anti-patterns | [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md) |
| Spec / proposal template | [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md) |

---

## Commit Policy

**Never commit runtime state or caches.** The directories below are runtime-only:

- `.agents/router/runs/`
- `.agents/workflow/runs/` (This includes active `openspec.md` and `focus_card.md`)
- `.agents/events/drift_queue/`
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, archived specs (`.agents/llm_wiki/archive/*_openspec.md`), delivery capsules, and `.agents/**/wal/` fragments.

---

## Standard Workflow Saga

To build muscle memory and respect the Human-in-the-Loop constraints, refer to [.agents/workflow/EXAMPLES.md](.agents/workflow/EXAMPLES.md) for a multi-turn rhythm example of any `STANDARD` task.
