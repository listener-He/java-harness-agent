# Lifecycle — Phases, Profiles, and State Machine

One-way state machine with hard gates and rollback rules.

---

## Agent Obligations (MUST)

- Determine the current phase from context; execute the correct next action.
- Apply hook constraints from [HOOKS.md](HOOKS.md) before moving to the next phase.
- Maintain `launch_spec_{timestamp}.md` (`Status / Phase / Artifact / Failed_Reason`) for resumability. **When task_brief.md is created, immediately write its full path to the `Artifact` column** — this + task_brief.md are the only two state files. No brake_snapshot, no engine_state.json.
- Never break the one-way flow, hard gates, or anti-runaway rules.

---

## Execution Profiles

| Profile | Flow | Approval Gate | Artifact |
|---|---|---|---|
| LEARN | Read-only; no lifecycle, no write-back | No | None |
| PATCH (TRIVIAL) | `Implement(Grep Check) → QA → Archive(Drift)` | No | None |
| PATCH (LOW) | `Explorer(inline) → Implement → QA → Archive` | No | 1-line drift note |
| STANDARD (MEDIUM) | `Explorer(inline) → Propose(task_brief) → Review → Implement → QA → Archive` | No | `task_brief.md` |
| STANDARD (HIGH) | `Explorer(inline+) → Propose(task_brief) → Review(adversarial) → [GATE] → Implement → QA → Archive` | Yes | `task_brief.md` |

**Friction principle:** generate artifacts only when their cross-session value exceeds the cost of writing them. A single-session MEDIUM task with 3 ACs does not need 8 files.

---

## Phases

### Phase 1: Explorer

**Mounted Roles:** `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard`
**Skills:** `requirement-intake` (pre-phase), `product-manager-expert`, `task-decomposition-guide`, `adversarial-review` (Category A — HIGH only)

**Core reasoning steps (MUST — internalized, not bureaucratized):**

1. Run `pre_hook`. Read `../llm_wiki/wiki/preferences/index.md`.
2. **Specification Inference:** What does the codebase currently *guarantee* in the affected area?
   State: `Current: [X]. Required: [Y]. Delta: [Z].` — the gap IS the true scope.
3. **Contradiction Detection (ongoing):** Does each new fact contradict a prior fact? Resolution rule: code > wiki; explicit > implicit. Flag immediately, never overwrite silently.
4. **AC-as-Tests Translation (MUST):** Convert every requirement unit to:
   `Given [precondition], when [action], then [observable, measurable result].`
   Vague language ("handle correctly", "work properly") is BLOCKED.
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
1. Select design approach. Emit a **Constraint List** (decisions that bind all downstream work).
2. Populate Allowed Scope (file list that constrains implementation).
3. Write `task_brief.md` — the single artifact readable by both AI and human.

**Output — tiered by risk:**

| Risk | Alternatives Required | Artifact |
|---|---|---|
| LOW | None | No file. State approach inline. |
| MEDIUM | 1 option + explicit rationale | `<YYYY-MM-DD>_<slug>_task_brief.md` |
| HIGH | ≥2 ADR alternatives with Pros / Cons / Failure Condition | `<YYYY-MM-DD>_<slug>_task_brief.md` (fuller Human Section) |

**`task_brief.md` format (header + two sections):**

```markdown
# {任务名} — Task Brief
状态：IN_PROGRESS | {YYYY-MM-DD} | 风险：{MEDIUM/HIGH}
launch_spec：.agents/workflow/runs/launch_spec_{timestamp}.md

<!-- MACHINE SECTION — AI reads to constrain implementation -->
## Allowed Scope
- {file path 1}
- {file path 2}

## Acceptance Criteria
- AC-001: Given [precondition], when [action], then [measurable result]
- AC-002: ...

## Hard Constraints
- {constraint 1 — e.g., "所有DB写入必须经过@Transactional Service层"}
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

**Failure rule:** If review fails → trigger `fail_hook` → roll back to Phase 2.
**Adversarial CRITICAL finding** → roll back to Phase 2. Do NOT re-run adversarial on the revised proposal.

---

### Approval Gate (Human-in-the-Loop)

**Purpose:** Stop the engine before code is written against a wrong contract. **HIGH risk only.**

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

**Persistence:** Set the intent row in `launch_spec.md` to `WAITING_APPROVAL`. Include a link to `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md`.

**Risk classification:**

| Level | Examples | Rules |
|---|---|---|
| HIGH | DB schema/index changes; auth/permission strategy; error code system changes; cross-domain changes; shared utilities; unclear or large blast radius | STANDARD profile. MUST stop at `WAITING_APPROVAL`. Adversarial Review required. Strict Python gates. |
| MEDIUM | New or changed external APIs; core business path changes without DB/auth foundation changes | STANDARD profile. No Approval Gate — proceed after Review. Show summary to human as FYI, not a gate. |
| LOW | Small bugfixes with clear blast radius; logic tweaks within a single domain | Uses `PATCH` profile. Requires Slim Spec. **QA Guard:** If no unit tests cover the change, MUST trigger a Soft Interrupt (display Diff to human). |
| TRIVIAL | Docs only; pure renames/formatting; adding comments; fixing typos; purely defensive/corrective code (null checks, parameter validation, error code fixes, log additions) with ≤ 1 file and no API/DB changes | Uses `PATCH` profile. No Spec required. **Impact Guard:** MUST perform a global `Grep` before renaming/changing to ensure no hidden dependencies. **Archive Guard:** MUST write a 1-line summary to `drift_queue` before exit. |

---

### Phase 4: Implement

**Mounted Roles:** `@Lead Engineer`, `@Focus Guard`
**Skills:** `java-architecture-standards`, `java-coding-style`

**Actions:**
1. Read `task_brief.md` **Machine Section** (Allowed Scope + AC + Hard Constraints) before touching any file.
2. Implement strictly within Allowed Scope. No file outside it without explicit human permission.
3. Create new tables/schemas only in the WAL data domain (`wiki/data/wal/`), not as root `.sql` scripts.
4. Trigger `shift_left_hook` (compile sanity). No heavy test suite here.
5. **STOP (Yield):** After compile passes, ask human for permission to proceed to QA.

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

**Evidence Mapping Table (ultraqa):** Required when ACs ≥ 4 OR risk = HIGH. For simpler cases (≤ 3 ACs, MEDIUM/LOW): run tests and report pass/fail inline — no table required.

**Failure rule:** QA fails → roll back to Phase 4. **MAX RETRIES: 2.** On third failure: STOP, ask human. No infinite loop.

---

### Phase 6: Archive

**Profile-differentiated behavior:**

| Profile | Steps |
|---|---|
| **PATCH (TRIVIAL/LOW)** | Write 1-line changelog to `.agents/events/drift_queue/`. Done. |
| **STANDARD** | 1. Write WAL fragments (Domain + API + Rules; Data if schema change). 2. Move `task_brief.md` to `.agents/llm_wiki/archive/`. Done. |

No delivery capsule, no writeback_gate, no drift_queue processing, no rating — unless the task explicitly involves those. Dispatch next PENDING intent from launch_spec if queue has more items.
