# AGENTS.md — Entry Point & Hard Constraints

Single entry point. Read this file first on every session start. All links here use paths relative to the repo root.

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Context Bloat Prevention** | Prefer native Search Sub-Agents (e.g., Trae, Qoder, Claude Code, Gemini CLI, Codex) for codebase scanning. When dispatching tasks to Sub-Agents, you MUST format your prompt using [.agents/llm_wiki/schema/subagent_contract_schema.md](.agents/llm_wiki/schema/subagent_contract_schema.md). If unavailable, STRICTLY enforce Budget Limits (Wiki ≤ 3, Code ≤ 8, Web Search ≤ 2) as the "Poor Man's Sub-Agent". Pagination doesn't count. |
| **Reward Mechanism** | Two-tier budget extension (see [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)): **Tier 1 — Auto-Extension (silent):** Budgets auto-extend when measurable progress triggers fire — no formal block required. Triggers include Progress Signal, Saturation Near-Miss, Wiki-Rot Bypass, and External Dependency. Grants +1~3 wiki / +2~3 code / +1~2 web search per trigger. **Tier 2 — Confidence_Assessment (explicit):** When auto-extensions are exhausted, output a `<Confidence_Assessment>` block explaining the missing concept to earn +2 wiki / +3 code / +2 web search. **Hard Ceilings:** Wiki ≤ 8, Code ≤ 20, Web Search ≤ 6 total. Hit any ceiling → escalate. |
| **Budget exhausted** | STOP. File an Escalation Card (format in [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). Do not guess paths or continue reading. Applies to all three budgets: Wiki, Code, and Web Search. |
| **Approval Gate** | For HIGH risk changes only: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval before writing any code. MEDIUM: show spec summary as FYI, proceed without waiting. |
| **Anti-loop** | Max 3 retries for scripts/linters. STRICT MAX 2 retries for compilation/RunCommand fixes. On exceed: STOP and ask human. Never infinite loop. |
| **Scope Guard** | Do not modify files outside the `## Allowed Scope` section of `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md` without explicit human permission. If no task_brief exists (PATCH/TRIVIAL), scope = the single file being changed. |
| **Artifact Paths** | The only runtime artifact is `<YYYY-MM-DD>_<slug>_task_brief.md` under `.agents/workflow/runs/`. TRIVIAL/LOW: no file. Never generate artifacts in the repo root. Archive phase moves task_brief to `llm_wiki/archive/`. |
| **Exit Gate (Archive)** | STANDARD tasks: output `[Lifecycle: Archive]` block, move `task_brief.md` to `.agents/llm_wiki/archive/`, write WAL fragments for any new API/Domain/Rules changed. PATCH: write 1-line drift note only. LEARN/Audit: `[Lifecycle: Archive]` with “no write-back”. |

---

## Mandatory First Outputs

Before any action (reading files, searching, writing code), the Agent MUST output the following headers AND a structured thinking block:

```xml
[Intent Check] intent=<Learn|Change|DocQA|Audit> | profile=@<learn|patch|standard> | risk=<TRIVIAL|LOW|MEDIUM|HIGH> | scenario=<none|DEBUG|EPIC|A|B|C|D|E> | emergency=<true|false>
        [Lifecycle: <Plan|Execute|Validate|Archive>] | [Mounted Role: @<Role>]   ← omit Mounted Role for TRIVIAL

<Cognitive_Brake>
- Role & Scope: As [@RoleX], my Allowed Scope is [## Allowed Scope in task_brief.md / None]. Am I crossing it?
- Budget & Context: Wiki: [X]/3, Code: [Y]/8, Web: [Z]/2. Do I need to Grep specific project standards/exceptions first?
- Architectural Defense: Is this a cross-domain/transactional change? Am I at a STOP gate like Approval or Validation?
- Next State: What exact artifact, WAL, or validation command will I output/run right now?
- Confidence: <HIGH | MEDIUM — assumption: [X] | LOW — blocking question: [Y]>
</Cognitive_Brake>
```

**Cognitive Brake — tiered by risk:**
- **HIGH risk (STANDARD):** Full 5-point `<Cognitive_Brake>` is MANDATORY.
- **MEDIUM risk (STANDARD):** Micro-Brake: `<Brake>Scope: [boundary]. Action: [next step]. Confidence: [HIGH|MEDIUM|LOW]</Brake>`
- **LOW / TRIVIAL (PATCH):** No brake block. Reasoning is inline. Do not output a brake template.

**Confidence Gradient — Binding Behavioral Rules:**
| Level | Condition | Required Action |
|---|---|---|
| `HIGH` | All key facts confirmed from code/wiki, no open assumptions | Proceed. |
| `MEDIUM` | Proceeding on an unverified assumption | State the assumption explicitly in the task_brief Hard Constraints section. Double-check the single most critical constraint before writing code. |
| `LOW` | A blocking unknown that changes the Profile or Scenario if wrong | **STOP.** Ask exactly ONE targeted question. Do not proceed until answered. |

**Rules:**
- **CoT Requirement**: The `<Cognitive_Brake>` block is MANDATORY. It forces you to adopt the assigned Role Personas (e.g., as `@Security Sentinel` or `@Focus Guard`) before acting like a Coder.
- **Language Matching**: The internal reasoning text inside the `<Cognitive_Brake>` MUST be written in the same natural language as the user's most recent prompt (e.g., 简体中文, にほんご, Español,  English) to maximize human readability. The XML tags and protocol headers (e.g., `[Intent Check]`) MUST remain in English for script parsing.
- **Audience-Aware Documentation**: `task_brief.md` has two sections — Machine Section (English: file paths, class names, AC assertions, constraints) and Human Section (Chinese by default: 做什么/为什么/怎么做). WAL fragments: English for technical facts, Chinese allowed for business rationale. Never mix audiences within a section.
- If the intent is ambiguous (missing action or object signal): output `[Intent Check] AMBIGUOUS — <reason>` and ask one clarifying question before proceeding.
- If a special scenario (DEBUG, EPIC, A–E) is matched: include `scenario=<name>` and apply Scenario routing overrides (see [ROUTER.md](.agents/router/ROUTER.md#6-special-scenarios)).
- You MUST explicitly declare any Phase transition using the `[Lifecycle: ...]` header.
- The `[Mounted Role: ...]` MUST be derived from `.agents/workflow/ROLE_MATRIX.md` based on the current Phase.
- These lines are the only required headers. Do not add verbose preamble before them.

**Brake Snapshot (HIGH risk STANDARD only):**
At phase transitions, persist the `<Cognitive_Brake>` block into `<YYYY-MM-DD>_<slug>_brake_snapshot.md`. MEDIUM and below: no snapshot file required.

---

## Initial Action Decision Tree

```
Session start
├─ Rule 0.0: Workflow Initialization (SSOT Lazy Loading)
│   └─ Read ONLY `AGENTS.md` on startup. Lazy-load `LIFECYCLE.md`, `ROLE_MATRIX.md`, or specific `SKILL.md` ONLY when transitioning phases or executing specific tasks.
├─ Rule -1: Input Normalization (MUST, before Intent Signal Matrix)
│   └─ No @shortcut AND input is longer than a one-liner (PRD, bug report, vague idea, security finding, etc.)?
│       └─ YES → Apply `requirement-intake` skill. Emit [Intake] block. Use its Intent/Profile as routing seed.
│       └─ NO (explicit @shortcut or simple one-liner) → Skip intake, proceed directly.
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
| Skill index | [.agents/skills/skill-index/SKILL.md](.agents/skills/skill-index/SKILL.md) |
| Project constraints & anti-patterns | [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md) |
| Spec / proposal template | [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md) |

---

## Commit Policy

**Never commit runtime state or caches.** The directories below are runtime-only:

- `.agents/router/runs/`
- `.agents/workflow/runs/` (This includes active `<YYYY-MM-DD>_<slug>_task_brief.md`)
- `.agents/events/drift_queue/`
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, archived task briefs (`.agents/llm_wiki/archive/*_task_brief.md`), delivery capsules, and `.agents/**/wal/` fragments.

---

## Standard Workflow Saga

To build muscle memory and respect the Human-in-the-Loop constraints, refer to [.agents/workflow/EXAMPLES.md](.agents/workflow/EXAMPLES.md) for a multi-turn rhythm example of any `STANDARD` task.
