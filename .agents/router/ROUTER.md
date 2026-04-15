# Intent Gateway (Router)

This document defines how to route natural-language requests into a structured intent queue, then (optionally) launch the queue into the lifecycle engine.

## Scope
- This is the routing contract. It defines intent codes, when to use them, and what artifacts they produce.
- It does not implement the lifecycle. For lifecycle rules, see [LIFECYCLE.md](../workflow/LIFECYCLE.md).

## Rule 1: Start with the Context Funnel (MUST)
DO NOT start with full-text search.

When any request arrives, the Agent MUST:
1. Read the root: [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)
2. Drill down via: [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)
3. If you cannot pick a specialist skill, consult: [trae-skill-index](../skills/trae-skill-index/SKILL.md)

## Rule 2: Map to intent codes
After enough context is collected, map the request into a queue of standard intents.

Example: “Add an API and tests” -> `Propose.API -> Implement.Code -> QA.Test`

| Intent Code | Trigger | Lifecycle Phase | Core Skills | Concurrency |
|---|---|---|---|---|
| `Explore.Req` | Requirement clarification and task breakdown | Explorer | `[product-manager-expert](../skills/product-manager-expert/SKILL.md)`, `[prd-task-splitter](../skills/prd-task-splitter/SKILL.md)` | Serial |
| `Audit.Codebase` | Codebase assessment / architecture review / risk scan (read-only) | Gateway (Read-only) | `[intent-gateway](../skills/intent-gateway/SKILL.md)`, `[devops-review-and-refactor](../skills/devops-review-and-refactor/SKILL.md)` | Serial |
| `QA.Doc` | Answer questions from wiki/spec docs (read-only) | Gateway (Doc QA) | `[intent-gateway](../skills/intent-gateway/SKILL.md)` | Serial |
| `QA.Doc.Actionize` | Convert doc QA conclusion into an executable intent queue (requires confirmation) | Gateway -> Lifecycle (HITL) | `[intent-gateway](../skills/intent-gateway/SKILL.md)`, `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)` | Serial |
| `Propose.API` | Create/update API contract and design | Propose -> Review | `[devops-system-design](../skills/devops-system-design/SKILL.md)` | Order-independent (can run with Data) |
| `Propose.Data`| Create/update database tables or indexes | Propose -> Review | `[devops-system-design](../skills/devops-system-design/SKILL.md)` | Order-independent (can run with API) |
| `Implement.Code` | Implement business logic / fix bugs | Implement -> QA | `[devops-feature-implementation](../skills/devops-feature-implementation/SKILL.md)`, `[devops-bug-fix](../skills/devops-bug-fix/SKILL.md)` | Wait for Propose |
| `QA.Test` | Tests + review checklist | QA | `[devops-testing-standard](../skills/devops-testing-standard/SKILL.md)` | Wait for Implement |

## Flow A: Read-only codebase audit (`Audit.Codebase`)
- Goal: assess the current codebase and output a structured report with evidence links
- Hard constraint: DO NOT modify code, DO NOT write to the wiki, DO NOT generate a launch spec, DO NOT enter the lifecycle
- Allowed actions: read-only search and file reads; running build/tests is allowed, but you MUST NOT modify tracked files
- Output requirements: each finding MUST include evidence (file path + line range), impact, and a fix suggestion (suggest only; do not apply)

## Flow B: Doc QA with optional actionize (`QA.Doc` / `QA.Doc.Actionize`)
- `QA.Doc`: answer questions by drilling down the wiki; include citations to wiki sections (and code citations only if needed)
- `QA.Doc.Actionize`: convert the answer into an executable intent queue; you MUST ask once before launching
- Gate: before any write-back or launch, you MUST pass the Doc Consistency Gate in [HOOKS.md](../workflow/HOOKS.md)

## Rule 3: Launch Spec (optional)
When you decide to launch an intent queue into the lifecycle engine:
1. Persist the queue to `router/runs/launch_spec_{timestamp}.md`
2. Drive state transitions by updating only `Status/Phase/Failed_Reason`
3. Optional helper: `python ../scripts/harness/engine.py init "..."` can create and maintain the file

After each `Archive` phase, the Agent MUST re-read the launch spec to decide whether to continue with the next intent.

### Launch Spec Template (machine-friendly)
Status enum: `PENDING`, `IN_PROGRESS`, `DONE`, `WAITING_APPROVAL`, `FAILED`

```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## State Machine
| Intent | Status | Phase | Artifact/Log | Failed_Reason |
|---|---|---|---|---|
| Explore.Req | IN_PROGRESS | 1_Explorer | `explore_report.md` | - |
| Propose.API | PENDING | - | - | - |
| Implement.Code | PENDING | - | - | - |

## Resume
- If the session is interrupted, the first action is to read this file and restore from `Status/Phase`.
- If any row is `WAITING_APPROVAL`, stop and wait for human approval; then switch back to `IN_PROGRESS` and continue.
- If any row is `FAILED`, stop and report `Failed_Reason`.
```
