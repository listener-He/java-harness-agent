# Lifecycle — Phases & State Machine

This file documents the **phases** in detail. The mapping from profile/risk to per-profile flow lives in [routing.md](routing.md). Gate checklists per phase live in [hooks.md](hooks.md).

---

## Canonical Phase Flow

```
Explorer → Propose → Review → [Approval Gate if HIGH] → Implement → QA → Archive
```

PATCH profiles skip Explorer/Propose/Review entirely. MAINTENANCE has its own role-specific flow. See routing.md → "Risk Classification" for the per-profile flow tables.

---

## PDD: Task Dependencies & Parallelism

- Declare dependencies BEFORE writing code. Each task lists its upstream dependencies.
- ≥3 tasks: draw a dependency graph (DAG). Tasks without mutual dependencies MAY run in parallel (soft limit: 3).
- A task whose `Depends On` are not all `DONE` MUST remain PENDING.

## BDD: AC Format

Every requirement MUST be: `Given [precondition], when [action], then [observable, measurable result].`
Vague language ("handle correctly", "work properly") is BLOCKED.

## SDD/SPEC: Contract-First

`task_brief.md` is the universal contract. No code until spec is complete. Two sections:
- **Machine Section** (English): Allowed Scope, ACs, Hard Constraints — AI consumption
- **Human Section** (Chinese): business rationale, design trade-offs, decision questions

## TDD: Red → Green → Refactor

Tests are derived from BDD ACs, not invented by implementer.
1. RED — write failing test from AC
2. GREEN — minimum code to pass
3. REFACTOR — clean up within passing tests

---

## Phase Details

### Phase 1: Explorer
1. Infer specification gap: `Current: [X]. Required: [Y]. Delta: [Z].`
2. Convert requirements to Given/When/Then ACs
3. Run `code_index.py --impact-of <target>` to discover hidden scope
4. HIGH risk: run adversarial review Category A. CRITICAL → revise. MINOR → annotate AC.

**Output:** MEDIUM/HIGH → inline `[Explore]` block (Spec Gap + ACs + Hidden Scope). TRIVIAL/LOW → reasoning inline only. Never write a standalone explore_report.md.

### Phase 2: Propose
1. Design solution (MEDIUM: 1 option + rationale; HIGH: ≥2 ADR with Pros/Cons/Failure Conditions)
2. Define Allowed Scope (exhaustive file list) and Hard Constraints
3. Write `task_brief.md` with bidirectional binding: immediately write its path into launch_spec Artifact column

### Phase 3: Review
- MEDIUM: `code-review-checklist` + `java-architecture-standards`
- HIGH: above + `adversarial-review` Category B (one round)
- Plan Review Checklist (≥3 tasks): completeness, consistency, feasibility, risk coverage, dependency soundness
- Review fails → roll back to Propose. Adversarial CRITICAL → roll back to Propose.

### Approval Gate (HIGH only)
Present Human Section to user. Approval responses:
- Full → enter Implement
- Partial → record approved sections, roll back rejected only
- Full rejection → roll back to Propose

### Phase 4: Implement
1. Read task_brief Machine Section before any code
2. TDD: RED (failing test from AC) → GREEN (minimum code) → REFACTOR (clean up)
3. Stay within Allowed Scope. Violations → `[Boundary Exception Request]`, wait for approval.
4. Run `mvn compile -q` after each change. MAX 2 retries.
5. After compile passes: yield to human for QA permission.

**[Plan Invalidation]:** If a core assumption in task_brief proves wrong (structural, not a missing dependency):
```
[Plan Invalidation]
Discovery: [file:line or test output]
Invalidated Assumption: [specific constraint contradicted]
Impact: [which ACs are unreliable]
Proposed Action: ROLLBACK_TO_PROPOSE | ROLLBACK_TO_EXPLORER
```
Do NOT fix by expanding scope. Wait for human decision.

### Phase 5: QA
1. Run compile if not run since last change
2. Run tests. ACs ≥ 4 or HIGH risk: map each Given/When/Then → test method → expected → actual → status
3. QA fails → roll back to Implement. MAX 2 retries. Third failure: STOP, ask human.

### Phase 6: Archive
1. Write WAL fragments (Domain + API + Rules; Data if schema change)
2. Plan Deviation Reflection: scope drift? dependency accuracy? plan invalidations? deferred ACs?
3. Move task_brief to `.claude/wiki/archive/`

---

## State Files

Only two: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract).

**Launch spec statuses:** PENDING | IN_PROGRESS | WAITING_APPROVAL | DONE | FAILED

**Resume protocol:** Find IN_PROGRESS row → read Artifact → load task_brief Machine Section.

---

## Maintenance Flows

Maintenance tasks have no code phases (no Explorer/Propose/Implement/QA). The trigger→role→flow table lives in [routing.md → Maintenance Operations](routing.md#maintenance-operations). Detailed checklists for each role are in `.claude/agents/`.
