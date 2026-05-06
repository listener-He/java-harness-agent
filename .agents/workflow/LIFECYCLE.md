# Lifecycle — Phases, Profiles, and State Machine

One-way state machine with hard gates and rollback rules.

---

## Agent Obligations (MUST)

- Determine the current phase from context; execute the correct next action.
- Apply hook constraints from [HOOKS.md](HOOKS.md) before moving to the next phase.
- Maintain `launch_spec_{timestamp}.md` (`Status / Phase / Failed_Reason`) for resumability.
- Never break the one-way flow, hard gates, or anti-runaway rules.

---

## Execution Profiles

| Profile | Flow | Approval Gate | Spec Required |
|---|---|---|---|
| LEARN | Read-only; no launch spec, no lifecycle, no write-back | No | No |
| PATCH | `(TRIVIAL)` `Implement(Grep Check) → QA(Soft Interrupt?) → Archive(Drift)`<br>`(LOW)` `Implement → QA(Soft Interrupt?) → Archive` | No | TRIVIAL: None<br>LOW: Slim Spec |
| STANDARD | `Explorer → Propose → Review → [GATE] → Implement → QA → Archive` | Yes (MEDIUM/HIGH) | Full `<YYYY-MM-DD>_<slug>_openspec.md` |

---

## Phases

### Phase 1: Explorer

**Mounted Roles:** `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard`
**Skills:** `product-manager-expert`, `task-decomposition-guide`

**Actions:**
1. Run `pre_hook`.
2. Read `../llm_wiki/wiki/preferences/index.md`.
3. Clarify requirements and scope.

**Output:** `<YYYY-MM-DD>_<slug>_explore_report.md` — MUST include a `## Core Context Anchors` section (key wiki links, business vocabulary, engineering red lines).

---

### Phase 2: Propose

**Mounted Roles:** `@System Architect`
**Skills:** `java-architecture-standards`, `task-decomposition-guide`

**Actions:** Follow the contract template in `../llm_wiki/schema/openspec_schema.md`.

**Output:** `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md` and `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_focus_card.md`.
- LOW risk: MAY use Slim Spec.
- MEDIUM / HIGH risk: MUST use full schema.

---

### Phase 3: Review

**Mounted Roles:** `@System Architect`
**Skills:** `code-review-checklist`, `java-architecture-standards`

**Review matrix:**
- Engineering & API: `java-architecture-standards`
- DB & SQL: `mybatis-sql-standard`
- Style & Util: `java-coding-style`

**Failure rule:** If review fails → trigger `fail_hook` → roll back to Phase 2.

---

### Approval Gate (Human-in-the-Loop)

**Purpose:** Stop the engine before code is written against a wrong contract.

**Actions:**
1. Present an `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md` summary to the human.
2. Ask for explicit approval to enter implementation.

**Persistence:** Set the intent row in `launch_spec.md` to `WAITING_APPROVAL`. Include a link to `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md`.

**Risk classification:**

| Level | Examples | Rules |
|---|---|---|
| HIGH | DB schema/index changes; auth/permission strategy; error code system changes; cross-domain changes; shared utilities; unclear or large blast radius | MUST use `STANDARD` profile. MUST stop at `WAITING_APPROVAL`. Triggers strict Python gates (e.g., `migration_gate.py`). |
| MEDIUM | New or changed external APIs; core business path changes without DB/auth foundation changes | MUST use `STANDARD` profile. MUST stop at `WAITING_APPROVAL`. |
| LOW | Small bugfixes with clear blast radius; logic tweaks within a single domain | Uses `PATCH` profile. Requires Slim Spec. **QA Guard:** If no unit tests cover the change, MUST trigger a Soft Interrupt (display Diff to human). |
| TRIVIAL | Docs only; pure renames/formatting; adding comments; fixing typos; 纯防御性/纠正性代码（null check、参数校验、错误码修正、日志补充）且 ≤1 文件、无 API/DB 变更 | Uses `PATCH` profile. No Spec required. **Impact Guard:** MUST perform a global `Grep` before renaming/changing to ensure no hidden dependencies. **Archive Guard:** MUST write a 1-line summary to `drift_queue` before exit. |

---

### Phase 4: Implement

**Mounted Roles:** `@Lead Engineer`, `@Focus Guard`
**Skills:** `java-architecture-standards`, `java-coding-style`

**Actions:**
1. Execute the `<Cognitive_Brake>` template to establish boundaries (transactional layers, existing exceptions/validations) BEFORE coding.
2. Implement strictly according to the approved contract. Follow Checkstyle and defensive programming. No uncontrolled improvisation.
3. Create new tables/schemas only in the WAL data domain (`wiki/data/wal/`), not as root `.sql` scripts.
4. Trigger `shift_left_hook` to ensure basic build/compile sanity (no heavy test suite here).
5. **STOP (Yield):** After shift-left compile passes, ask the human for permission to proceed to Phase 5 (QA Test).

---

### Phase 5: QA Test

**Mounted Roles:** `@Code Reviewer`
**Skills:** `java-testing-standards`, `code-review-checklist`

**Actions:**
1. If shift-left compile was not executed in Phase 4 (or code changed since), trigger `shift_left_hook` to ensure compile sanity before running tests.
2. Run tests and produce objective evidence (logs, test output, screenshots).

**Failure rule:** If QA fails → roll back to Phase 4. **STRICT MAX RETRIES: 2.** If tests or compilation fail more than 2 times, STOP immediately and ask the human for help. Do not enter an infinite fixing loop.

---

### Phase 6: Archive

**Profile-differentiated behavior:**

| Profile | Mounted Roles | Actions |
|---|---|---|
| **PATCH** | (no mounted roles) | 1. Move `<YYYY-MM-DD>_<slug>_openspec.md` to `../llm_wiki/archive/`. 2. Write 1-line changelog to `.agents/events/drift_queue/`. 3. Ask human for 1–10 rating; extract preferences. |
| **STANDARD** | `@Knowledge Extractor`, `@Documentation Curator` | Full WAL write-back (Domain + API + Rules; Data if schema change). Follow steps 1–7 below. |

**On-demand roles:** `@Skill Graph Curator` (仅本次涉及 skill 创建/修改时挂载), `@Librarian` (仅显式 `@gc` / `@librarian` 触发)

**STANDARD Steps (in order):**
1. Sync docs via `wal-documentation-rules` skill.
2. Extract stable knowledge into wiki indexes via the reverse funnel in `../router/CONTEXT_FUNNEL.md`.
3. Move the original spec into `../llm_wiki/archive/`.
4. Optional (explicit only): Trigger WAL Compaction (e.g., `@gc` / `@librarian`) via `python3 .agents/scripts/wiki/compactor.py`.
   - Default behavior is WAL-first: write fragments and let a human or explicit librarian run merge them in a low-conflict window.
5. Process Drift Events: read `.agents/events/drift_queue/` (if events exist), validate discrepancies, generate WAL fragments to heal the wiki.
6. Ask the human for a 1–10 rating. Extract preferences (rating ≥ 8) or anti-patterns (rating ≤ 5) into `../llm_wiki/wiki/preferences/index.md`.
7. Re-read the launch spec and dispatch the next `PENDING` / `IN_PROGRESS` intent (loop until queue is empty).
