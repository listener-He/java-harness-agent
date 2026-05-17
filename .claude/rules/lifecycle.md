# Lifecycle — Phases, Profiles, and State Machine

One-way state machine with hard gates and rollback rules.

---

## Agent Obligations (MUST)

- Determine the current phase from context; execute the correct next action.
- Apply hook constraints from [hooks.md](hooks.md) before moving to the next phase.
- Maintain `launch_spec_{timestamp}.md` (`Status / Phase / Depends On / Artifact / Failed_Reason`) for resumability and dependency tracking. **When task_brief.md is created, immediately write its full path to the `Artifact` column.** Only two state files exist: `launch_spec_*.md` and `task_brief.md`.
- **PDD**: Declare task dependencies and parallelism constraints in launch_spec. A task whose `Depends On` are not all `DONE` MUST NOT enter Implement. Respect the max parallel tasks soft limit.
- Never break the one-way flow, hard gates, or anti-runaway rules.

---

## Execution Profiles

| Profile | Flow | Approval Gate | Artifact |
|---|---|---|---|
| LEARN | Read-only; no lifecycle, no write-back | No | None |
| PATCH (TRIVIAL) | `Implement(Grep Check) → QA → Archive` | No | None |
| PATCH (LOW) | `Explorer(inline) → Implement → QA → Archive` | No | 1-line drift note |
| STANDARD (MEDIUM) | `Explorer(inline) → Propose(task_brief) → Review → Implement → QA → Archive` | No | `task_brief.md` |
| STANDARD (HIGH) | `Explorer(inline+) → Propose(task_brief) → Review(adversarial) → [GATE] → Implement → QA → Archive` | Yes | `task_brief.md` |
| MAINTENANCE | Role-specific (see Maintenance Phases below). No code phases. Write-back required. | No | WAL fragments, merged indexes, scan reports |

---

## Phases

### Phase 1: Explorer

**Mounted Roles:** `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard`
**Skills:** `requirement-intake` (pre-phase), `product-manager-expert`, `task-decomposition-guide`, `adversarial-review` (Category A — HIGH only)

**Core reasoning steps (MUST — internalized, not bureaucratized):**

1. Run `pre_hook`. Read `../wiki/wiki/preferences/index.md`.
2. **Specification Inference:** What does the codebase currently *guarantee* in the affected area?
   State: `Current: [X]. Required: [Y]. Delta: [Z].` — the gap IS the true scope.
3. **Contradiction Detection (ongoing):** Does each new fact contradict a prior fact? Resolution rule: code > wiki; explicit > implicit. Flag immediately, never overwrite silently.
4. **BDD — AC-as-Tests Translation (MUST):** Convert every requirement unit to:
   `Given [precondition], when [action], then [observable, measurable result].`
   Vague language ("handle correctly", "work properly") is BLOCKED.
   This is **Behavior-Driven Development (BDD)** : executable specifications in shared language, written BEFORE any code exists.
5. **AC-Driven Impact Check:** Run `code_index.py --impact-of <target_file>` using the files identified by AC translation. Record hidden scope in `Hidden Scope` section.
6. **Adversarial Check (HIGH risk only, one round):** Run `adversarial-review` Category A. CRITICAL → revise before proceeding. MINOR → annotate AC.

**Output — tiered by risk:**

| Risk | Output |
|---|---|
| TRIVIAL / LOW | No file. Steps 2–4 executed inline as reasoning. |
| MEDIUM | Inline `[Explore]` block in response: Spec Gap + AC list + Hidden Scope. Feeds directly into task_brief Machine Section. |
| HIGH | Same inline block + Adversarial findings. All content feeds into task_brief. No separate explore_report file. |

**On-demand only:** Human explicitly asks "show me your analysis" → show inline analysis in response. Never write a standalone explore_report.md file.

---

### Phase 2: Propose

**Mounted Roles:** `@System Architect`
**Skills:** `brainstorming`, `java-architecture-standards`, `task-decomposition-guide`

**Actions:**
1. **PDD — Plan as First-Class Artifact**: Declare task dependencies and parallelism constraints BEFORE writing the spec. Each task MUST list its upstream dependencies. When ≥3 tasks exist in a launch_spec, draw a dependency graph (DAG). Tasks without mutual dependencies MAY run in parallel (soft limit: 3).
2. **SDD/SPEC — Contract-First Design**: Select design approach. Emit a **Constraint List** (decisions that bind all downstream work). The `task_brief.md` IS the specification — no code is written until the spec is complete.
3. Populate Allowed Scope (file list that constrains implementation).
4. Write `task_brief.md` — the single artifact readable by both AI and human. This is Specification-Driven Development (SDD): the spec is the contract that governs all subsequent phases.

**Output — tiered by risk:**

| Risk | Alternatives Required | Artifact |
|---|---|---|
| LOW | None | No file. State approach inline. |
| MEDIUM | 1 option + explicit rationale | `<YYYY-MM-DD>_<slug>_task_brief.md` |
| HIGH | ≥2 ADR alternatives with Pros / Cons / Failure Condition | `<YYYY-MM-DD>_<slug>_task_brief.md` (fuller Human Section) |

**`task_brief.md` format (header + two sections):**

```markdown
# {Task Name} — Task Brief
Status: IN_PROGRESS | {YYYY-MM-DD} | Risk: {MEDIUM/HIGH}
launch_spec: .claude/runs/launch-specs/launch_spec_{timestamp}.md

<!-- MACHINE SECTION — AI reads to constrain implementation -->
## Allowed Scope
- {file path 1}
- {file path 2}

## Acceptance Criteria
- AC-001: Given [precondition], when [action], then [measurable result]
- AC-002: ...

## Task Dependencies
- Depends on: {task description} — Status: {DONE / IN_PROGRESS / PENDING}
- Blocks: {task description} (optional)

## Hard Constraints
- {constraint 1 — e.g., "All DB writes must go through @Transactional Service layer"}
- {constraint 2}

<!-- HUMAN SECTION — 中文，业务语言 -->
## 做什么 / 为什么
**现状：** {用业务语言描述当前代码保证了什么}
**需要：** {需要的行为}
**范围：** {一句话说明范围}

## 怎么做
{选定的设计方案 + 理由。HIGH 风险：包含方案对比摘要和淘汰原因。}

## 需要你确认的  ← 仅 HIGH 风险出现；MEDIUM 省略
- [ ] {需要人类决策的问题}
```

**Bidirectional binding rules (MUST sync when writing files):**
1. When creating `task_brief.md` → immediately write its path into the `Artifact` column of the corresponding row in `launch_spec.md`
2. When a task reaches Archive → change the task_brief header `Status` to `DONE`, then archive
3. If the two are not synced → cross-session resume is unreliable

**Language rule:** Machine Section uses English (file paths, class names, constraints). Human Section uses Chinese (or the user's language). Do not mix languages within the same section.

---

### Phase 3: Review

**Mounted Roles:** `@System Architect`
**Skills:** `code-review-checklist`, `java-architecture-standards`, `adversarial-review` (HIGH only)

**Review matrix:**

| Risk | Review scope |
|---|---|
| MEDIUM | `code-review-checklist` + `java-architecture-standards` |
| HIGH | Above + `adversarial-review` Category B (ONE round, scenario-specific frame) |

**Plan Review Checklist (PDD — MUST pass before exiting Review for ≥3 tasks in launch_spec):**

| Check | Question | Fail → |
|---|---|---|
| **Completeness** | Are all ACs covered by at least one task? Are all files declared in Allowed Scope? | Add missing coverage |
| **Consistency** | Do task dependencies form a DAG (no cycles)? Do constraints conflict across tasks? | Resolve conflicts |
| **Feasibility** | Can each task be completed within its constraints? Is scope realistic? | Adjust scope or split tasks |
| **Risk Coverage** | Are all risks identified in Explorer addressed? Is the rollback path clear? | Add risk mitigations |
| **Dependency Soundness** | Are all upstream dependencies resolvable? Can tasks proceed without deadlock? | Fix dependency graph |

**Failure rule:** If review fails → trigger `fail_hook` → roll back to Phase 2.
**Adversarial CRITICAL finding** → roll back to Phase 2. Do NOT re-run adversarial on the revised proposal.

---

### Approval Gate — HIGH Risk Only

**Actions:**
1. Present the `task_brief.md` **Human Section** to the human (Chinese, business language).
2. Ask for explicit approval to enter implementation.

**Approval responses:**

| Response | Action |
|---|---|
| Full approval ("LGTM", "proceed", "approved") | Enter Phase 4 immediately |
| Partial approval ("API-OK, DB needs revision") | Record approved sections in `launch_spec.md` under `Approved-Sections`. Roll back ONLY the rejected sections to Phase 2. Proceed to implement approved sections only. |
| Full rejection ("rework this") | Roll back to Phase 2 (Propose). State which assumption changed. Do NOT re-run adversarial review on the revised proposal. |
| No response / timeout | Do NOT proceed. Remain at `WAITING_APPROVAL`. |

**For partial approval:** annotate each task_brief section with `[APPROVED]` or `[PENDING-REVISION: <reason>]` before entering Phase 4. Phase 4 MUST implement only `[APPROVED]` sections and explicitly skip `[PENDING-REVISION]` ones.

**Persistence:** Set the intent row in `launch_spec.md` to `WAITING_APPROVAL`. Include a link to `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md`.

**Risk classification:**

| Level | Examples | Rules |
|---|---|---|
| HIGH | DB schema/index changes; auth/permission strategy; error code system changes; cross-domain changes; shared utilities; unclear or large blast radius | STANDARD profile. MUST stop at `WAITING_APPROVAL`. Adversarial Review required. Strict Python gates. |
| MEDIUM | New or changed external APIs; core business path changes without DB/auth foundation changes | STANDARD profile. No Approval Gate — proceed after Review. Show summary to human as FYI, not a gate. |
| LOW | Small bugfixes with clear blast radius; logic tweaks within a single domain | Uses `PATCH` profile. Requires Slim Spec. **QA Guard:** If no unit tests cover the change, MUST trigger a Soft Interrupt (display Diff to human). |
| TRIVIAL | Docs only; pure renames/formatting; adding comments; fixing typos; purely defensive/corrective code (null checks, parameter validation, error code fixes, log additions) with ≤ 1 file and no API/DB changes | Uses `PATCH` profile. No Spec required. **Impact Guard:** MUST perform a global `Grep` before renaming/changing to ensure no hidden dependencies. |

---

### Phase 4: Implement

**Mounted Roles:** `@Lead Engineer`, `@Focus Guard`
**Skills:** `java-architecture-standards`, `java-coding-style`

**Actions:**
1. Read `task_brief.md` **Machine Section** (Allowed Scope + AC + Hard Constraints) before touching any file.
2. **TDD — Test-Driven Development**: Write failing tests derived from the ACs first (RED), then implement the minimum code to pass (GREEN), then refactor (REFACTOR). The ACs come from Phase 1 BDD — TDD is the implementation arm of the spec.
3. Implement strictly within Allowed Scope. No file outside it without explicit human permission.
4. Create new tables/schemas only in the WAL data domain (`wiki/data/wal/`), not as root `.sql` scripts.
5. Trigger `shift_left_hook` (compile sanity). No heavy test suite here.
6. **STOP (Yield):** After compile passes, ask human for permission to proceed to QA.

**Plan Invalidation Protocol (MUST — if discovery contradicts task_brief):**

If a core assumption in task_brief Machine Section proves wrong (not a missing dependency, a structural flaw):

```
[Plan Invalidation]
Discovery: [what was found — file:line or test output]
Invalidated Assumption: [the specific constraint in task_brief that this contradicts]
Impact: [which ACs are now unreliable]
Proposed Action: ROLLBACK_TO_PROPOSE | ROLLBACK_TO_EXPLORER
```

Normal dependency insertion (table X needed before service Y) → insert task, continue. Plan Invalidation is for structural contradictions only.

Do NOT attempt to fix a plan-invalidating discovery by expanding scope. File the `[Plan Invalidation]` block and wait for human decision.

---

### Phase 5: QA Test

**Mounted Roles:** `@Code Reviewer`
**Skills:** `java-testing-standards`, `code-review-checklist`

**Actions:**
1. Trigger `shift_left_hook` if compile has not run since last code change.
2. Run tests. Produce objective evidence (test output, logs).

**BDD — Evidence Mapping Table (ultraqa):** Required when ACs ≥ 4 OR risk = HIGH. Each Given/When/Then AC from Phase 1 is mapped to a test method → expected → actual → status. This closes the BDD loop: every behavior declared in Explorer is verified in QA. For simpler cases (≤ 3 ACs, MEDIUM/LOW): run tests and report pass/fail inline — no table required.

**Failure rule:** QA fails → roll back to Phase 4. **MAX RETRIES: 2.** On third failure: STOP, ask human. No infinite loop.

---

### Phase 6: Archive

**Profile-differentiated behavior:**

| Profile | Steps |
|---|---|
| **STANDARD** | 1. Write WAL fragments (Domain + API + Rules; Data if schema change). 2. Plan Deviation Reflection (see below). 3. Move `task_brief.md` to `.claude/wiki/archive/`. Done. |

No delivery capsule, no writeback_gate, no rating — unless the task explicitly involves those. Dispatch next PENDING intent from launch_spec if queue has more items.

**Plan Deviation Reflection (PDD — STANDARD only, after WAL write-back):**

Before archiving, compare the plan vs. actual execution:

| Metric | Check |
|---|---|
| **Scope Drift** | Were any files modified outside Allowed Scope? (If yes: document why in WAL `[Rules]` fragment) |
| **Dependency Accuracy** | Did any task execute out of declared dependency order? (If yes: record in failure_memory) |
| **Plan Invalidations** | Were any `[Plan Invalidation]` blocks raised during Implement? (If yes: annotate task_brief with resolution before archiving) |
| **AC Coverage** | Did all ACs pass, or were any deferred? Record deferred ACs. |

Output a 1-line `[Plan Deviation]` summary in the Archive response. If deviation is significant (≥2 extra files, ≥1 cycle break, ≥1 deferred AC), write a brief `plan_deviation.md` fragment into `.claude/wiki/wiki/process/wal/`.

---

## Maintenance Phases (MAINTENANCE Profile)

Maintenance tasks do NOT go through the standard 6-phase code lifecycle. They use role-specific flows:

### M1: WAL Compaction (GC) — triggered by `@gc` / `@librarian` or "整理/合并 wiki"

**Mounted Role:** `@Librarian`
**Skills:** `wal-documentation-rules`

| Step | Action |
|---|---|
| 1 | Run `python3 .claude/scripts/tools/librarian_gc.py --aggregate` to collect unmerged WAL fragments |
| 2 | Merge aggregated knowledge into the correct domain index files |
| 3 | Run `python3 .claude/scripts/tools/librarian_gc.py --clean` to remove merged fragments |
| 4 | If any merged file exceeds 500 lines → invoke `@Knowledge Architect` for document split |
| **Gate** | `python3 .claude/scripts/wiki/wiki_linter.py` — FAIL if dead links exist |

### M2: Wiki Refresh (Milestone) — triggered by `@wiki-update` / `@milestone` or "提取/沉淀/刷新 wiki"

**Mounted Role:** `@Knowledge Extractor`
**Skills:** `wal-documentation-rules`

| Step | Action |
|---|---|
| 1 | Run `git diff` to identify recent changes since last wiki update |
| 2 | Extract knowledge into structured WAL fragments: `[Domain]`, `[API]`, `[Rules]` (and `[Data]` if schema changed) |
| 3 | Write fragments into `wiki/domain/wal/`, `wiki/api/wal/`, etc. |
| **Gate** | `python3 .claude/scripts/gates/writeback_gate.py` (validates 3 required sections) + `wiki_linter.py` |

### M3: Document Split (Anti-Bloat) — triggered by 500-line limit or "拆分/重组文档"

**Mounted Role:** `@Knowledge Architect`
**Skills:** `wal-documentation-rules`

| Step | Action |
|---|---|
| 1 | Check if target wiki index file exceeds 500 lines; if not, abort |
| 2 | Deduplicate repeated entries |
| 3 | Split bloated `index.md` into focused sub-documents |
| 4 | Rewrite original `index.md` as a lean routing graph with links |
| **Gate** | `python3 .claude/scripts/wiki/wiki_linter.py` — FAIL if dead links or any file still exceeds 500 lines |

### M4: Project Scan — triggered by "扫描项目/审计代码库"

**Mounted Role:** Explorer (inline)
**Skills:** `local-code-intelligence`, `deepinit`

| Step | Action |
|---|---|
| 1 | Run `python3 .claude/scripts/local_intel/code_index.py --build` to rebuild symbol index |
| 2 | Run `python3 .claude/scripts/local_intel/wiki_search.py` to surface relevant wiki docs |
| 3 | Run `python3 .claude/scripts/local_intel/failure_memory.py query` to surface past failures |
| 4 | Produce a structured scan report (directories, modules, key symbols, risks) |
| **Output** | Scan report (no file written unless human requests it) |
