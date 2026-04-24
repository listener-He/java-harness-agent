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
| PATCH | `Explorer → Implement → QA → Archive` | No | Slim Spec (Change Log + QA evidence) |
| STANDARD | `Explorer → Propose → Review → [GATE] → Implement → QA → Archive` | Yes (MEDIUM/HIGH) | Full `openspec.md` |

---

## Phases

### Phase 1: Explorer

**Mounted Roles:** `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard`
**Skills:** `product-manager-expert`, `devops-requirements-analysis`, `prd-task-splitter`

**Actions:**
1. Run `pre_hook`.
2. Read `../llm_wiki/wiki/preferences/index.md`.
3. Clarify requirements and scope.

**Output:** `explore_report.md` — MUST include a `## Core Context Anchors` section (key wiki links, business vocabulary, engineering red lines).

---

### Phase 2: Propose

**Mounted Roles:** `@System Architect`
**Skills:** `devops-system-design`, `devops-task-planning`

**Actions:** Follow the contract template in `../llm_wiki/schema/openspec_schema.md`.

**Output:** `.agents/workflow/runs/openspec.md` and `.agents/workflow/runs/focus_card.md`.
- LOW risk: MAY use Slim Spec.
- MEDIUM / HIGH risk: MUST use full schema.

---

### Phase 3: Review

**Mounted Roles:** `@System Architect`
**Skills:** `devops-review-and-refactor`, `global-backend-standards`

**Review matrix:**
- Engineering: `java-engineering-standards`, `java-backend-guidelines`
- API & DB: `java-backend-api-standard`, `mybatis-sql-standard`
- Security & permissions: `error-code-standard`

**Failure rule:** If review fails → trigger `fail_hook` → roll back to Phase 2.

---

### Approval Gate (Human-in-the-Loop)

**Purpose:** Stop the engine before code is written against a wrong contract.

**Actions:**
1. Present an `.agents/workflow/runs/openspec.md` summary to the human.
2. Ask for explicit approval to enter implementation.

**Persistence:** Set the intent row in `launch_spec.md` to `WAITING_APPROVAL`. Include a link to `.agents/workflow/runs/openspec.md`.

**Risk classification:**

| Level | Examples |
|---|---|
| HIGH | DB schema/index changes; auth/permission strategy; error code system changes; cross-domain changes; shared utilities; unclear or large blast radius |
| MEDIUM | New or changed external APIs; core business path changes without DB/auth foundation changes |
| LOW | Docs only; pure renames/formatting; small bugfixes with clear blast radius |

**Rules:**
- MEDIUM/HIGH: MUST stop at `WAITING_APPROVAL`.
- LOW: MAY skip approval, but MUST state the justification in the delivery note.

---

### Phase 4: Implement

**Mounted Roles:** `@Lead Engineer`, `@Focus Guard`, `@Security Sentinel`
**Skills:** `devops-feature-implementation`, `devops-bug-fix`, `utils-usage-standard`, `aliyun-oss`

**Actions:**
1. Execute the `<Cognitive_Brake>` template to establish boundaries (transactional layers, existing exceptions/validations) BEFORE coding.
2. Implement strictly according to the approved contract. Follow Checkstyle and defensive programming. No uncontrolled improvisation.
3. Create new tables/schemas only in the WAL data domain (`wiki/data/wal/`), not as root `.sql` scripts.
4. **STOP (Yield):** Once code is written, you MUST STOP and ask the human for permission to proceed to Phase 5 (QA Test). Do not auto-continue into heavy compilation.

---

### Phase 5: QA Test

**Mounted Roles:** `@Code Reviewer`, `@Documentation Curator`
**Skills:** `devops-testing-standard`, `code-review-checklist`

**Actions:**
1. Trigger `shift_left_hook`: Autonomously execute `javac` or Maven/Gradle build commands. Fix all compilation errors (`javax` vs `jakarta`, missing imports).
2. Run tests and produce objective evidence (logs, test output, screenshots).

**Failure rule:** If QA fails → roll back to Phase 4. **STRICT MAX RETRIES: 2.** If tests or compilation fail more than 2 times, STOP immediately and ask the human for help. Do not enter an infinite fixing loop.

---

### Phase 6: Archive

**Mounted Roles:** `@Knowledge Extractor`, `@Documentation Curator`, `@Skill Graph Curator`
**Purpose:** Close the loop and prevent knowledge bloat. Execute seamlessly in the **same session**. Rely on targeted `git diff <files>` or `.agents/workflow/runs/openspec.md` to summarize changes, strictly avoiding re-reading heavy coding history. Follow `ARCHIVE_WAL.md` to move the spec to `.agents/llm_wiki/archive/YYYYMMDD_<feature>_openspec.md`.

**Steps (in order):**
1. Sync docs via `api-documentation-rules` and `database-documentation-sync` skills.
2. Extract stable knowledge into wiki indexes via the reverse funnel in `../router/CONTEXT_FUNNEL.md`.
3. Move the original spec into `../llm_wiki/archive/`.
4. Trigger WAL Compaction: `python3 .agents/scripts/wiki/compactor.py`
   - If target `index.md` < 400 lines: append/merge WAL fragments.
   - If target `index.md` ≥ 400 lines: compactor sets `NEEDS_REFACTOR`. Mount the `Knowledge Architect` role to split the bloated index, update routing links, and pass `wiki_linter.py` before continuing.
5. Process Drift Events: read `.agents/events/drift_queue/` (if events exist), validate discrepancies, generate WAL fragments to heal the wiki.
6. Ask the human for a 1–10 rating. Extract preferences (rating ≥ 8) or anti-patterns (rating ≤ 5) into `../llm_wiki/wiki/preferences/index.md`.
7. Re-read the launch spec and dispatch the next `PENDING` / `IN_PROGRESS` intent (loop until queue is empty).
