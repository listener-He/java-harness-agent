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
| **Scope Guard** | Do not modify files outside the agreed `focus_card.md` scope without explicit human permission. |
| **Exit Gate (Archive)** | Before yielding the final response to the human, you MUST output an `[Lifecycle: Archive]` block and write WAL fragments for any new API, Domain, or Logic changed. NEVER say you are done without writing the WAL. |
| **Task Checklist** | Before entering `Execute` phase, you MUST create `.agents/workflow/runs/current_task.md` with `[ ] Write-back to wiki (WAL)` as the last item to track progress. |

---

## Mandatory First Outputs

Before any action (reading files, searching, writing code), the Agent MUST output the following headers AND a structured thinking block:

```xml
[Intent Check] intent=<Learn|Change|DocQA|Audit> | profile=@<learn|patch|standard> | risk=<LOW|MEDIUM|HIGH> | scenario=<none|DEBUG|EPIC|A|B|C|D|E> | emergency=<true|false>
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
- `.agents/workflow/runs/`
- `.agents/events/drift_queue/`
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, `openspec.md`, delivery capsules, and `wal/` fragments.

---

## Standard Workflow Saga (Few-Shot Paradigm for STANDARD Profile)

To build muscle memory and respect the Human-in-the-Loop constraints, follow this multi-turn rhythm for any `STANDARD` task:

**User:** "Add a new asset type to the tenant and invalidate the old one."

**Turn 1: Explorer & Propose (Phase 1 & Phase 2)**
1. **Output headers:** `[Lifecycle: Propose] | [Mounted Role: @System Architect + @Requirement Engineer + @Ambiguity Gatekeeper]`
2. **Cognitive Brake:**
```xml
<Cognitive_Brake>
- Role & Scope: As @Ambiguity Gatekeeper, current boundary is None. Must output focus_card.md to lock scope. As @System Architect, must output openspec.md mapping AC.
- Budget & Context: Wiki: 1/3, Code: 2/8. Must grep `CustomerException` standards.
- Architectural Defense: Cross-table operation (Tenant/Asset). Requires `@Transactional` Facade. Currently in Propose phase -> reaching Approval Gate. MUST STOP. No coding allowed.
- Next State: Output explore_report.md, focus_card.md, and openspec.md. Yield for human approval.
</Cognitive_Brake>
```
3. **Action:** Agent reads context, creates the spec detailing a `@Transactional` Facade layer, and defines the exact files to touch in `focus_card.md`.
4. **Approval Gate (STOP):** Agent stops and asks the User: *"The spec is ready. Please review `openspec.md`. Do you approve moving to implementation?"* (Agent MUST NOT write code yet).

**Turn 2: Implement (Phase 4) — *After Human Approves***
1. **Output headers:** `[Lifecycle: Implement] | [Mounted Role: @Lead Engineer + @Focus Guard + @Security Sentinel]`
2. **Cognitive Brake:**
```xml
<Cognitive_Brake>
- Role & Scope: As @Focus Guard, strict boundary is Controller/Service per focus_card.md. Zero drift. As @Lead Engineer, writing code.
- Budget & Context: Wiki: 0/3, Code: 0/8 (reset for new turn). Verified `jakarta.validation` requirement.
- Architectural Defense: Write operation requires `@Transactional` in Manage layer per openspec.md. After writing code, MUST STOP at Validation Gate before compilation.
- Next State: Execute SearchReplace. STOP and prompt: "Code generated. Requesting permission to run mvn compile."
</Cognitive_Brake>
```
3. **Action:** Agent writes code using `SearchReplace`.
4. **Validation Gate (STOP):** Agent stops and asks the User for permission to run heavy compilations or tests.

**Turn 3: Shift-Left Validation (Phase 5) — *After Human Approves***
1. **Output headers:** `[Lifecycle: Validate] | [Mounted Role: @Code Reviewer + @Documentation Curator]`
2. **Cognitive Brake:**
```xml
<Cognitive_Brake>
- Role & Scope: As @Code Reviewer, scope is test/compile and static analysis only. No feature drift.
- Budget & Context: Wiki: 0/3, Code: 0/8.
- Architectural Defense: STRICT MAX RETRIES is 2. If `mvn compile` fails twice, MUST stop and escalate to human. No infinite loops.
- Next State: Execute `mvn clean compile` via RunCommand.
</Cognitive_Brake>
```
3. **Action:** Agent uses `RunCommand` (`mvn clean compile`). Fixes a `javax` import error (Retry 1/2) and recompiles successfully.
4. **Yield:** Agent reports: *"Compilation passed! Transitioning automatically to Archive phase to extract knowledge."*

**Turn 4: Archive (Phase 6) — *Seamless Write-back***
1. **Output headers:** `[Lifecycle: Archive] | [Mounted Role: @Knowledge Extractor + @Documentation Curator + @Skill Graph Curator]`
2. **Cognitive Brake:**
```xml
<Cognitive_Brake>
- Role & Scope: As @Knowledge Extractor, extraction only. No code mutation.
- Budget & Context: Wiki: 0/3, Code: 0/8.
- Architectural Defense: Execute Archive seamlessly in the same session. Rely on targeted `git diff <files>` or `openspec.md` to summarize changes, strictly avoiding re-reading heavy coding history.
- Next State: Write unified knowledge fragment to `data/wal/YYYYMMDD_asset_type.md`.
</Cognitive_Brake>
```
3. **Action:** Agent writes the database schema changes into `data/wal/YYYYMMDD_asset_type.md`.
4. **Yield:** Agent reports full completion to the User.
