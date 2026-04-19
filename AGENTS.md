# AGENTS.md — Entry Point & Hard Constraints

Single entry point. Read this file first on every session start. All links here use paths relative to the repo root.

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Budget** | Intelligently calculate initial budget based on task complexity. Default: wiki 3, code 8. Pagination of the same file does NOT count. |
| **Reward Mechanism** | (Elastic extension) Output a `<Confidence_Assessment>` block explaining the specific missing concept/symbol to earn a budget reward (+2 wiki / +3 code) before hitting the hard stop (see [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). |
| **Budget exhausted** | STOP. File an Escalation Card (format in [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). Do not guess paths or continue reading. |
| **Approval Gate** | For MEDIUM/HIGH risk changes: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval before writing any code. |
| **Anti-loop** | Max 3 retries for any failing script, test, or linter per task. On exceed: STOP and ask human. Use `bypass_justification.md` only to downgrade trivial failures to WARN. |
| **Scope Guard** | Do not modify files outside the agreed `focus_card.md` scope without explicit human permission. |
| **Exit Gate (Archive)** | Before yielding the final response to the human, you MUST output an `[Lifecycle: Archive]` block and write WAL fragments for any new API, Domain, or Logic changed. NEVER say you are done without writing the WAL. |
| **Task Checklist** | Before entering `Execute` phase, you MUST create `.agents/workflow/runs/current_task.md` with `[ ] Write-back to wiki (WAL)` as the last item to track progress. |

---

## Mandatory First Outputs

Before any action (reading files, searching, writing code), the Agent MUST output the following headers AND a structured thinking block:

```xml
[Intent Check] intent=<Learn|Change|DocQA|Audit> | profile=@<learn|patch|standard> | risk=<LOW|MEDIUM|HIGH> | scenario=<none|A|B|C|D|E> | emergency=<true|false>
[Lifecycle: <Plan|Execute|Validate|Archive>] | [Mounted Role: @<Role>]

<Cognitive_Brake>
- Role Assumption: What are my currently mounted roles (e.g., @Focus Guard + @Security Sentinel) and what specific artifacts/guards must I deliver in this phase per `ROLE_MATRIX.md`?
- Context Sniffing: What existing project conventions, custom exceptions, or validation rules do I need to Grep/Search before assuming standard Java behavior?
- Architectural Defense: Does this operation span multiple tables/domains? If so, what is the transaction boundary and rollback strategy (e.g., Facade layer)?
- Shift-Left Validation: How will I verify this change (e.g., `javac`, Maven, tests) before telling the user I am done?
- State Mutation: What WAL fragments or documentation will need updating in the Archive phase?
</Cognitive_Brake>
```

**Rules:**
- **CoT Requirement**: The `<Cognitive_Brake>` block is MANDATORY. It forces you to adopt the assigned Role Personas (e.g., as `@Security Sentinel` or `@Focus Guard`) before acting like a Coder.
- If the intent is ambiguous (missing action or object signal): output `[Intent Check] AMBIGUOUS — <reason>` and ask one clarifying question before proceeding.
- If a special scenario (A–E) is matched: include `scenario=<letter>` and apply Scenario routing overrides (see [ROUTER.md](.agents/router/ROUTER.md#6-special-scenarios)).
- You MUST explicitly declare any Phase transition using the `[Lifecycle: ...]` header.
- The `[Mounted Role: ...]` MUST be derived from `.agents/workflow/ROLE_MATRIX.md` based on the current Phase.
- These lines are the only required headers. Do not add verbose preamble before them.

---

## Initial Action Decision Tree

```
Session start
├─ Rule 0.0: Workflow Initialization (MANDATORY)
│   └─ Even if explicit paths are provided (Rule 0), you MUST read LIFECYCLE.md and ROLE_MATRIX.md before taking any action.
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

## Standard Agent Turn (Few-Shot Paradigm)

To build muscle memory and avoid impulsive "Coder" behavior, follow this exact rhythm for code modification turns:

**User:** "Add a new asset type to the tenant and invalidate the old one."

**Agent Internal Loop (Perfect Execution):**
1. **Output headers & CoT (Mandatory):**
```xml
[Intent Check] intent=Change | profile=@standard | risk=MEDIUM | scenario=none | emergency=false
[Lifecycle: Execute] | [Mounted Role: @Focus Guard + @Security Sentinel]

<Cognitive_Brake>
- Role Assumption: As @Focus Guard, I must strictly only edit the Controller and Service classes authorized in the `focus_card.md`. As @Security Sentinel, I must ensure no raw passwords or PII are exposed in the new exception messages.
- Context Sniffing: I need to Grep for `CustomerException` or `BaseResponse` instead of throwing raw `RuntimeException`. I must check for existing validation annotations (e.g., `jakarta` vs `javax`).
- Architectural Defense: Adding an asset and invalidating an old one touches multiple tables. This MUST be wrapped in a `@Transactional` Facade/Manage layer, NOT crammed into the Controller.
- Shift-Left Validation: After generating code, I will use `RunCommand` to run `mvn compile` or `javac` to catch import errors before responding to the user.
- State Mutation: I will write a WAL fragment into `.agents/llm_wiki/wiki/data/wal/YYYYMMDD_asset_type.md` for the new enum/DB change.
</Cognitive_Brake>
```
2. **Action 1 (Sniffing):** Agent uses `Grep` or `SearchCodebase` to find custom exceptions and validation imports.
3. **Action 2 (Coding):** Agent uses `SearchReplace` / `Write` to create the Facade layer and update the Controller, ensuring high cohesion.
4. **Action 3 (Shift-Left Validation):** Agent uses `RunCommand` (`mvn clean compile`). It catches a `javax` import error, fixes it, and recompiles successfully.
5. **Action 4 (Archive):** Agent transitions to `[Lifecycle: Archive]`, writes the database schema/enum change as a Markdown fragment into `data/wal/`, and ONLY THEN yields the final response to the user.
