# Hooks — Guards, Rollbacks, and Loop

Defines when and how to enforce constraints throughout the lifecycle.

---

## Session Resume Anchors (MUST, in order)

1. Read `router/runs/launch_spec_*.md` — find the row where `Status = IN_PROGRESS` or `WAITING_APPROVAL`.
2. Read the `Artifact` column of that row — this is the full path to the active `task_brief.md`.
3. Load that specific `task_brief.md` — read `## Allowed Scope`, `## Acceptance Criteria`, `## Hard Constraints`.

**If Artifact column is empty but Status = IN_PROGRESS:** task_brief was not yet created (interrupted during Explorer). Resume from Explorer step 2 — do not guess scope.

**If no IN_PROGRESS row exists:** all tasks are PENDING or DONE. Ask human which task to start next.

### Resume Fidelity Check (MUST, after step 3)

```
[Resume Fidelity Check]
launch_spec loaded: YES/NO — IN_PROGRESS row found: YES/NO
task_brief path from Artifact column: {path or EMPTY}
task_brief loaded: YES/NO
  → Allowed Scope: [N files]
  → Acceptance Criteria: [N ACs]
  → Status header in task_brief: IN_PROGRESS / DONE (DONE = stale, do not use)
Phase to resume: [Phase N — from launch_spec Phase column]
```

Mismatch or missing → STOP. Report `[Resume Blocked] <reason>`. Ask human to confirm correct task. Do NOT reconstruct from memory.

---

## Hook Definitions

### 1. `pre_hook` — Pre-Phase Gate

**Trigger:** Before entering any new phase.

**Bound skills:** `java-architecture-standards`

**Purpose:** Load the relevant rule sets before the phase begins. Example: before `Implement`, load defensive programming standards and project preferences.

**Required output (MUST):** Be aware of budget guides (see `../router/CONTEXT_FUNNEL.md` Rule 0.1). This is internal — no visible output needed unless asked.

**Local Intelligence Actions (run before reading any files):**

| When | Command | Purpose |
|---|---|---|
| Explorer phase, scope unknown | `wiki_search.py --query "<intent>"` | Get top-3 wiki docs to read instead of blind drill-down |
| Explorer phase, Change intent | `failure_memory.py query --intent Change --phase Explorer` | Warn about recurring failure patterns |
| Before writing Focus Card | `code_index.py --impact-of <target_file>` | Enumerate callers/importers for accurate Allowed Scope |
| Before writing Focus Card | `code_index.py --what-touches-table <table>` | Find all mappers using a table (Scenario B) |

These commands are zero-cost (read local index files, no token budget consumed).

---

### 2. `guard_hook` — Execution Guard

**Trigger:** While performing core actions (generating code, writing SQL).

**Bound skills:** `java-coding-style`

**Purpose:**
- **Architectural Defense (MUST):** Ensure operations spanning multiple DB tables/domains are pushed down to a `@Transactional` Service or Facade layer. Controllers must remain thin.
- **Standards guard:** Enforce style, custom project exceptions (e.g., `CustomerException`), and required patterns (e.g., `jakarta.validation` vs `javax`).
- **Domain boundary guard:** Do NOT modify cross-domain files unless explicitly listed in `## Allowed Scope` of the current `task_brief.md`.
- **Anti-runaway guard (MUST):** Enforce budgeted navigation + stop rules + escalation protocol (see `../router/CONTEXT_FUNNEL.md`).
- **Anti-drift guard (MUST):** Maintain a `Focus Card` and enforce scope via `scope_guard.py` (see `../workflow/ROLE_MATRIX.md`).
- **Fast-Path Impact Guard:** For `TRIVIAL` tasks bypassing `Explorer`, the Agent MUST execute a global `Grep` or `SearchCodebase` to ensure the variable/method being renamed or modified has no hidden or hardcoded dependencies (e.g., XML mappings, reflection).
- **Secrets Scan (MUST):** 每次代码变更后执行 `python3 .agents/scripts/gates/secrets_linter.py --paths "<changed_files>"`。FAIL 时阻断流程（已从 `@Security Sentinel` 角色降级为 hook 步骤）。

---

### 2.5 `shift_left_hook` — Active Verification (MUST)

**Trigger:** Immediately after writing/modifying code, BEFORE telling the user "I am done".

**Purpose:**
Prevent delivery of uncompilable code, broken dependencies, or unverified "fast-path" logic.

**Actions:**
- The Agent MUST autonomously run `RunCommand` to execute `javac`, `mvn clean compile`, or `gradle build`.
- Do NOT run a heavy test suite unless the workflow is in Phase 5 (QA Test) or the human explicitly approves.
- If compilation fails, the Agent MUST fix the error and re-verify. **MAX 2 RETRIES**. If it still fails after 2 attempts, STOP and ask the human for help. Do not enter an infinite loop.
- **Fast-Path QA Guard (Soft Interrupt):** For `TRIVIAL` and `LOW` risk tasks in the `PATCH` profile, if the modified method/class lacks unit test coverage, the Agent MUST trigger a "Soft Interrupt". The Agent must present the `git diff` to the user and wait 5 seconds (or ask for a quick confirmation) before proceeding to Archive. Do not blindly assume QA is complete without tests.

---

### 3. `post_hook` — Post-Phase Audit

**Trigger:** After a phase completes, before transitioning to the next.

**Bound skills:** `wal-documentation-rules`

**Purpose:** Ensure API/DB documentation stays in sync with code changes. Optionally append logs to `workflow/runs/`.

#### Doc Consistency Gate

Read-only checks (do NOT modify files). Only run when relevant — not all gates apply to all tasks.

| Gate | Command | When |
|---|---|---|
| Task brief schema | `python3 .agents/scripts/wiki/schema_checker.py <path_to_task_brief>` | Every STANDARD task |
| Wiki graph lint | `python3 .agents/scripts/wiki/wiki_linter.py` | When wiki files changed |
| Secrets scan | `python3 .agents/scripts/gates/secrets_linter.py --paths "<glob>"` | Every code change |
| DB migration | `python3 .agents/scripts/gates/migration_gate.py --sql-dir <path>` | Scenario B (DDL changes) |
| Breaking API | `python3 .agents/scripts/gates/api_breaking_gate.py --task-brief <path>` | Scenario C (API schema changes) |
| Dependency | `python3 .agents/scripts/gates/dependency_gate.py --pom <pom.xml>` | Scenario E (pom.xml changes) |

**Severity and bypass:**
- Follow `linter-severity-standard` skill.
- The Agent is ENCOURAGED to use `quality-checklist` from `.agents/skills/spec-quality-checklist/SKILL.md` to self-correct documents BEFORE running strict python gates.
- Python gates are guidelines, not absolute blockers. Use `WARN` instead of `FAIL` for stylistic mismatches. If a gate fails on a non-critical issue, note it and move on — no bypass file ceremony required.

**Write-back policy (MUST):**
- **STANDARD**: Write WAL fragments (Domain + API + Rules; Data if schema change). Move task_brief to archive.
- **PATCH**: Write 1-line changelog to `.agents/events/drift_queue/`. No WAL required. Wiki refresh deferred to milestone.
- The Agent MUST NOT mark a STANDARD change as "done" if WAL fragments are missing.

**Explorer Post-Hook: Core Context Anchors (MUST)**

After Explorer, key context anchors feed into `task_brief.md ## Hard Constraints`:
- Business vocabulary and invariants (terms, enums, state notes)
- Engineering red lines (forbidden patterns, permission strategy, idempotency strategy)

In Propose / Implement phases: read `task_brief.md` Machine Section to restore context. No separate explore_report needed.

---

### 4. `fail_hook` — Failure Rollback

**Trigger:** Any test, review, or compile failure.

**Bound skills:** `code-review-checklist`

**Actions:**
- **Record to failure memory (MUST):** Before rolling back, persist the failure pattern so future sessions can learn from it:
  ```bash
  python3 .agents/scripts/local_intel/failure_memory.py record \
    --intent <intent> --profile <profile> --phase <phase> \
    --gate <gate_script> --pattern "<one-line failure reason>" \
    --task-id <task_id>
  ```
- **State downgrade:** Move back to the previous phase. Append the failure reason to `task_brief.md` (or state inline if no file exists). Fix all failed checklist items.
- **Max retries (3):** If the same phase fails 3 times: STOP and ask for human intervention.
- **Script retries cap (3):** Per task, each gate script can fail at most 3 times. On exceed: STOP and request human intervention.
- **Retry state reset:** Auto-cleared when task ends (Archive) or process receives an interruption signal. Explicit reset: `run.py --end-task`.
- **Persistence:** Update the `launch_spec.md` row to `FAILED` and write `Failed_Reason`.

**Compound Failure Decision Matrix (MUST):**

| Scenario | Action |
|---|---|
| QA → back to Implement, scope unchanged | Normal rollback. Re-execute Implement within existing Focus Card. |
| QA → back to Implement, scope needs expansion | STOP. Output `[Boundary Exception Request]`. Do NOT re-enter Implement until human approves expanded scope. |
| Same phase fails twice with same root cause | STOP. Escalate with root cause evidence. Do NOT attempt a 3rd fix without human input. |
| Same phase fails twice with different root causes | STOP. The contract may be flawed. Roll back to Propose phase for contract amendment. |
| Implement → compile failure (shift_left) | Fix and re-compile. MAX 2 RETRIES. If both fail → downgrade to Propose, re-evaluate API/Data contract feasibility. |

---

### 5. `loop_hook` — Queue Loop and Concurrency Guard

**Trigger:** After Phase 6 (Archive) completes, or immediately after launching a queue.

**Purpose:**
- **Queue consumption:** Read `launch_spec_{timestamp}.md` and resume the next `PENDING` / `IN_PROGRESS` intent.
- **Concurrency:** Identify what can run in parallel (example: `Propose.API` with `Propose.Data`).
- **Loop restart:** Dispatch the next intent into the correct lifecycle phase until the queue is empty.

---

## Non-Convergence Fallback (MUST)

If the workflow gets stuck repeating the same action without converging (e.g., a doc rewrite or linter failure loop):

1. STOP repeating the same change.
2. Run deterministic verification. Identify the exact failing evidence (file path + minimal excerpt).
3. Report the mismatch and request human intervention.
4. If the root cause is missing context or ambiguous scope: state what you know, what's missing, and ask the human. Set the `launch_spec` row to `WAITING_APPROVAL`.
