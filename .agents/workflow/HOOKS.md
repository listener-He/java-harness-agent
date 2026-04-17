# Hooks (Guards, Rollbacks, Loop)

This document defines when and how to enforce constraints throughout the lifecycle.

## Resume & Memory Anchors
- First action on resume (MUST): read `router/runs/launch_spec_*.md` and restore from `Status/Phase`.
- Second action (SHOULD): if `explore_report.md` exists, read its "core context anchors" section before doing any heavy navigation again.

### 1. `pre_hook` (Pre-Phase Gate)
- Trigger: before entering a new phase.
- Bound skills:
  - `[global-backend-standards](../skills/global-backend-standards/SKILL.md)`
  - `[java-backend-guidelines](../skills/java-backend-guidelines/SKILL.md)`
- Purpose: load the relevant rule sets. Example: before `Implement`, load defensive programming standards and project preferences.
- Required output (MUST): Decision-First Preflight + budgets (see `Rule 0.1` and `Rule 4/5` in `../router/CONTEXT_FUNNEL.md`).

### 2. `guard_hook` (Execution Guard)
- Trigger: while performing core actions (generating code, writing SQL).
- Bound skills:
  - `[checkstyle](../skills/checkstyle/SKILL.md)`
  - `[java-javadoc-standard](../skills/java-javadoc-standard/SKILL.md)`
  - `[java-data-permissions](../skills/java-data-permissions/SKILL.md)`
- Purpose:
  - Standards guard: enforce style and required patterns.
  - Domain boundary guard: DO NOT modify cross-domain files unless explicitly authorized in `openspec.md`.
- Anti-runaway guard (MUST): enforce budgeted navigation + stop rules + escalation protocol (see `../router/CONTEXT_FUNNEL.md`).
- Anti-drift guard (MUST): maintain a `Focus Card` and enforce scope via `scope_guard.py` (see `../workflow/ROLE_MATRIX.md`).

### 3. `post_hook` (Post-Phase Audit)
- Trigger: after completing a phase, before transitioning.
- Bound skills:
  - `[api-documentation-rules](../skills/api-documentation-rules/SKILL.md)`
  - `[database-documentation-sync](../skills/database-documentation-sync/SKILL.md)`
- Purpose: ensure API/DB documentation stays in sync with code changes. Optionally append logs into `workflow/runs/`.

#### Doc Consistency Gate
Goal: reduce wiki drift and contract corruption risk with deterministic checks.

Read-only checks (DO NOT modify files):
- OpenSpec checker: `python3 .agents/scripts/wiki/schema_checker.py <path_to_openspec.md>`
- Wiki graph linter: `python3 .agents/scripts/wiki/wiki_linter.py`
- Ambiguity gate: `python3 .agents/scripts/gates/ambiguity_gate.py --intent "<intent>" [--anchors-file <file>]`
- Write-back gate: `python3 .agents/scripts/gates/writeback_gate.py --topic "<topic>" --date YYYYMMDD [--require-data]`
- Delivery capsule gate: `python3 .agents/scripts/gates/delivery_capsule_gate.py --file <delivery_capsule.md>`
- Secrets gate: `python3 .agents/scripts/gates/secrets_linter.py --paths "<glob...>"`
- Java comment gate: `python3 .agents/scripts/gates/comment_linter_java.py --path <dir> [--fail-on-missing]`
- Unified runner (recommended): `python3 .agents/scripts/gates/run.py --intent <...> --profile <...> --phase <...> --topic <...> --date <YYYYMMDD> [--verify-level quick|standard|strict] [--artifact-tags ...]`

Severity & Justification Bypass (Flexible Constraints):
- Follow `[linter-severity-standard](../skills/linter-severity-standard/SKILL.md)`.
- **Justification Bypass**: If a gate script returns a FAIL (non-zero) due to a rule violation (e.g., missing Javadoc on a trivial private method, or a legacy code pattern), the Agent is NOT forced into an infinite loop. The Agent MAY generate a `bypass_justification.md` explaining why the rule should be waived in this specific context.
- When a `bypass_justification.md` is present for a specific gate failure, the runner WILL downgrade the FAIL to a WARN, allowing the workflow to proceed.
- WARN is allowed to proceed, but the Agent MUST explain and state a follow-up action. This justification will be presented to the human during the `Approval Gate`.

Write-back policy (MUST):
- For Profile `PATCH` and `STANDARD`, write-back is REQUIRED:
  - Domain WAL + API WAL + Rules WAL are mandatory.
  - Data WAL is mandatory when schema/DDL changes.
- The Agent MUST NOT end a change as “done” if write-back gates fail.

Optional evidence (writes a report file):
- `python .agents/scripts/wiki/zero_residue_audit.py` (default output: `.agents/workflow/runs/`)

#### Explorer Patch: Core Context Anchors in `explore_report.md`

Hard rule:
- The Explorer `post_hook` output `explore_report.md` MUST include a section named `## Core Context Anchors`.

Required contents:
- Key links collected via drill-down (domain/api/data/architecture/preferences/security_rules, etc.).
- Business vocabulary and invariants (terms, enums, state notes).
- Explicit engineering red lines (forbidden patterns, permission strategy, idempotency strategy, rollback placeholder).

Usage:
- In Propose/Implement, if context is unstable or time has passed, read this anchor section first before doing heavy navigation again.

### 4. `fail_hook` (Failure Rollback)
- Trigger: any test, review, or compile failure.
- Bound skills:
  - `[code-review-checklist](../skills/code-review-checklist/SKILL.md)`
- Purpose:
  - State downgrade: move back to the previous phase, and append the failure reason to `openspec.md` (or the relevant task artifact). Fix all failed checklist items.
  - Max retries (3): if the same phase fails 3 times, the Agent MUST stop and ask for human intervention.
  - Script retries cap (3): in one task, each gate script can fail at most 3 times; when failures exceed 3, the Agent MUST stop and request human intervention.
  - Task-state reset: retry state is auto-cleared when task ends (`Archive`) or process receives interruption signals; optional explicit reset via `run.py --end-task`.
  - Persistence: update `launch_spec.md` row to `FAILED` and write `Failed_Reason`.

### 5. `loop_hook` (Queue Loop + Concurrency Guard)
- Trigger: after Phase 6 (`Archive`) completes, or right after launching a queue.
- Purpose:
  - Queue consumption: read `launch_spec_{timestamp}.md` and resume the next `PENDING` / `IN_PROGRESS` intent.
  - Concurrency: decide what can run in parallel (example: `Propose.API` with `Propose.Data`).
  - Loop restart: dispatch the next intent into the correct lifecycle phase until the queue is empty.

## Non-Convergence Fallback (MUST)
If the workflow gets stuck repeating the same action without converging (for example: a doc rewrite or a linter failure loop), the Agent MUST:
1. Stop repeating the same change.
2. Run deterministic verification and identify the exact failing evidence (file path + minimal excerpt).
3. Report the mismatch and request human intervention.
4. If the root cause is missing context or ambiguous scope, use the Escalation Card format in `../router/CONTEXT_FUNNEL.md` and set `launch_spec` row to `WAITING_APPROVAL`.
