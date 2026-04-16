# Lifecycle (Phases + Hooks)

This document defines the execution lifecycle as a one-way state machine with hard gates and rollback rules.

## Agent as the Engine (MUST)
- The Agent MUST determine the current phase from context and execute the correct next action.
- Before moving to the next phase, the Agent MUST apply the constraints in [HOOKS.md](HOOKS.md).
- The Agent MUST maintain `launch_spec_{timestamp}.md` (`Status/Phase/Failed_Reason`) for resumability. Optional helper: `python ../scripts/harness/engine.py`.
- Non-negotiable: one-way flow, hard gates, and anti-runaway rules MUST NOT be broken.

## Phases (6) + Approval Gate
This lifecycle is orchestrated by `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)`.

Approval is a human gate. It is NOT counted as a phase.

## Profiles (Execution Modes)
Not every request needs the full lifecycle.

- Profile `LEARN`: read-only explanation (no launch spec, no lifecycle, no write-back).
- Profile `PATCH`: small change / bugfix (minimal artifacts; hooks still apply; archive is optional).
- Profile `STANDARD`: full lifecycle (this document).

### Phase 1: Explorer
- Skills: `[product-manager-expert](../skills/product-manager-expert/SKILL.md)`, `[devops-requirements-analysis](../skills/devops-requirements-analysis/SKILL.md)`, `[prd-task-splitter](../skills/prd-task-splitter/SKILL.md)`
- Actions:
  - Run `pre_hook`.
  - Read `../llm_wiki/wiki/preferences/index.md`.
  - Clarify requirements and scope.
- Output: `explore_report.md` including a `## Core Context Anchors` section.

### Phase 2: Propose
- Skills: `[devops-system-design](../skills/devops-system-design/SKILL.md)`, `[devops-task-planning](../skills/devops-task-planning/SKILL.md)`
- Actions: follow the contract template `../llm_wiki/schema/openspec_schema.md`.
- Output: `openspec.md` under `../llm_wiki/wiki/specs/`.
  - LOW risk MAY use Slim Spec (see the schema).
  - MEDIUM/HIGH risk MUST use the full schema.

### Phase 3: Review
- Skills: `[devops-review-and-refactor](../skills/devops-review-and-refactor/SKILL.md)`, `[global-backend-standards](../skills/global-backend-standards/SKILL.md)`
- Review matrix:
  - Engineering: `[java-engineering-standards](../skills/java-engineering-standards/SKILL.md)`, `[java-backend-guidelines](../skills/java-backend-guidelines/SKILL.md)`
  - API & DB: `[java-backend-api-standard](../skills/java-backend-api-standard/SKILL.md)`, `[mybatis-sql-standard](../skills/mybatis-sql-standard/SKILL.md)`
  - Security & permissions: `[error-code-standard](../skills/error-code-standard/SKILL.md)`, `[java-data-permissions](../skills/java-data-permissions/SKILL.md)`
- If review fails, the workflow MUST trigger `fail_hook` and roll back to Phase 2.

### Approval Gate (HITL)
- Purpose: stop the engine before code is written under a wrong contract.
- Actions:
  - Present an `openspec.md` summary to the human.
  - Ask for explicit approval to enter implementation.
- Persistence: update the intent row in `launch_spec.md` to `WAITING_APPROVAL` and include the `openspec.md` link.
- Risk levels:
  - HIGH: DB schema/index changes, auth/permission strategy changes, error code system changes, cross-domain changes, shared foundations/utilities, unclear or large blast radius.
  - MEDIUM: new/changed external APIs, core business path changes without DB/auth foundation changes.
  - LOW: docs, pure renames/formatting, small bug fixes with clear blast radius.
- Rule:
  - MEDIUM/HIGH MUST stop at `WAITING_APPROVAL`.
  - LOW MAY skip approval, but the Agent MUST state why in the delivery note.

### Phase 4: Implement
- Skills: `[devops-feature-implementation](../skills/devops-feature-implementation/SKILL.md)`, `[devops-bug-fix](../skills/devops-bug-fix/SKILL.md)`, `[utils-usage-standard](../skills/utils-usage-standard/SKILL.md)`, `[aliyun-oss](../skills/aliyun-oss/SKILL.md)`
- Actions: implement strictly according to the approved contract.
- Constraint: no uncontrolled improvisation; follow Checkstyle and defensive programming.

### Phase 5: QA Test
- Skills: `[devops-testing-standard](../skills/devops-testing-standard/SKILL.md)`, `[code-review-checklist](../skills/code-review-checklist/SKILL.md)`
- Actions: run tests and produce objective evidence.
- If QA fails, the workflow MUST roll back to Phase 4.

### Phase 6: Archive
This phase closes the loop and prevents bloat.
1. Sync docs via `[api-documentation-rules](../skills/api-documentation-rules/SKILL.md)` and `[database-documentation-sync](../skills/database-documentation-sync/SKILL.md)`.
2. Extract stable knowledge into wiki indexes via the reverse funnel in `../router/CONTEXT_FUNNEL.md`.
3. Move the original spec into `../llm_wiki/archive/`.
4. Ask the human for a 1–10 rating and extract preferences/anti-patterns into `../llm_wiki/wiki/preferences/index.md`.
5. Trigger loop: re-read the launch spec and continue until the queue is empty.
