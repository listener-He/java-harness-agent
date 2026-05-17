# Hooks — Guards, Rollbacks, and Loop

---

## Hook Definitions

### 1. `pre_hook` — Pre-Phase Gate

**Trigger:** Before entering any new phase.

Load `java-architecture-standards` skill. Check budget guides (see `routing.md` Rule 0.1).

**Local Intelligence Actions (run before reading any files):**

| When | Command |
|---|---|
| Explorer phase, scope unknown | `python3 .claude/scripts/local_intel/wiki_search.py --query "<intent>"` |
| Explorer phase, Change intent | `python3 .claude/scripts/local_intel/failure_memory.py query --intent Change --phase Explorer` |
| Before writing Allowed Scope | `python3 .claude/scripts/local_intel/code_index.py --impact-of <target_file>` |
| Before writing Allowed Scope (DB scenario) | `python3 .claude/scripts/local_intel/code_index.py --what-touches-table <table>` |

---

### 2. `guard_hook` — Execution Guard

**Trigger:** While generating code or writing SQL.

Load `java-coding-style` skill. Enforce all of the following:

- Push operations spanning multiple DB tables/domains to a `@Transactional` Service or Facade layer. Controllers MUST remain thin.
- Enforce style, custom project exceptions (e.g., `CustomerException`), and required patterns (e.g., `jakarta.validation` vs `javax`).
- Do NOT modify cross-domain files unless explicitly listed in `## Allowed Scope` of the current `task_brief.md`.
- Enforce budgeted navigation + stop rules + escalation protocol (see `routing.md`).
- Enforce scope via `scope_guard.py`. Do not drift outside the declared Allowed Scope.
- For `TRIVIAL` tasks: execute a global `Grep` or `SearchCodebase` before renaming or modifying anything — confirm no hidden dependencies (XML mappings, reflection).
- After every code change: run `python3 .claude/scripts/gates/secrets_linter.py --paths "<changed_files>"`. FAIL blocks the flow.

---

### 2.5 `shift_left_hook` — Active Verification (MUST)

**Trigger:** Immediately after writing/modifying code, BEFORE reporting completion to the user.

**Actions:**
- Run `javac`, `mvn clean compile`, or `gradle build`. Fix compile errors and re-verify. MAX 2 RETRIES — on third failure, STOP and ask the human.
- Do NOT run the full test suite unless in Phase 5 (QA) or the human explicitly approves.
- For `TRIVIAL` / `LOW` / `PATCH` tasks: if the modified method/class has no unit test coverage, trigger a Soft Interrupt — present `git diff` to the user and wait for confirmation before proceeding to Archive.

---

### 3. `post_hook` — Post-Phase Audit

**Trigger:** After a phase completes, before transitioning to the next.

Load `wal-documentation-rules` skill.

**Doc Consistency Gate** (read-only — do NOT modify files; run only when relevant):

| Gate | Command | When |
|---|---|---|
| Task brief schema | `python3 .claude/scripts/wiki/schema_checker.py <path_to_task_brief>` | Every STANDARD task |
| Wiki graph lint | `python3 .claude/scripts/wiki/wiki_linter.py` | When wiki files changed |
| Secrets scan | `python3 .claude/scripts/gates/secrets_linter.py --paths "<glob>"` | Every code change |
| DB migration | `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` | Scenario B (DDL changes) |
| Breaking API | `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>` | Scenario C (API schema changes) |
| Dependency | `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>` | Scenario E (pom.xml changes) |
| Plan review (PDD) | Checklist — see lifecycle.md Phase 3 Plan Review Checklist | Every STANDARD task with ≥3 tasks in launch_spec |

- Follow `linter-severity-standard` skill for severity handling.
- Run `.claude/skills/spec-quality-checklist/SKILL.md` to self-correct documents BEFORE running Python gates.
- Python gates are not absolute blockers: use `WARN` for stylistic mismatches; move on if the issue is non-critical.

**Write-back (MUST):**
- STANDARD: Write WAL fragments (Domain + API + Rules; Data if schema change). Move task_brief to archive. MUST NOT mark done if WAL fragments are missing.
- PATCH: No WAL required.

**After Explorer phase — populate `task_brief.md ## Hard Constraints` with:**
- Business vocabulary and invariants (terms, enums, state transitions)
- Engineering red lines (forbidden patterns, permission strategy, idempotency strategy)

In Propose / Implement phases: restore context from `task_brief.md` Machine Section only.

---

### 4. `fail_hook` — Failure Rollback

**Trigger:** Any test, review, or compile failure.

Load `code-review-checklist` skill.

**Actions:**
- Record failure pattern before rolling back:
  ```bash
  python3 .claude/scripts/local_intel/failure_memory.py record \
    --intent <intent> --profile <profile> --phase <phase> \
    --gate <gate_script> --pattern "<one-line failure reason>" \
    --task-id <task_id>
  ```
- Move back to the previous phase. Append the failure reason to `task_brief.md`. Fix all failed checklist items.
- Same phase fails 3 times: STOP and ask for human intervention.
- Same gate script fails 3 times per task: STOP and request human intervention.
- Retry state resets automatically at Archive. Explicit reset: `python3 .claude/scripts/run.py --end-task`.
- Update the `launch_spec.md` row to `FAILED` and write `Failed_Reason`.

**Compound Failure Decision Matrix (MUST):**

| Scenario | Action |
|---|---|
| QA → back to Implement, scope unchanged | Normal rollback. Re-execute Implement within existing Allowed Scope. |
| QA → back to Implement, scope needs expansion | STOP. Output `[Boundary Exception Request]`. Do NOT re-enter Implement until human approves expanded scope. |
| Same phase fails twice with same root cause | STOP. Escalate with root cause evidence. Do NOT attempt a 3rd fix without human input. |
| Same phase fails twice with different root causes | STOP. Roll back to Propose phase for contract amendment. |
| Implement → compile failure (shift_left) | Fix and re-compile. MAX 2 RETRIES. Both fail → downgrade to Propose, re-evaluate API/Data contract feasibility. |

---

### 5. `loop_hook` — Queue Loop

**Trigger:** After Archive completes, or immediately after launching a queue.

**Actions:**
- Read `launch_spec_{timestamp}.md` and resume the next `PENDING` / `IN_PROGRESS` intent.
- Identify tasks that can run in parallel using the `## Parallelism` section and dependency graph. Tasks whose `Depends On` are all `DONE` are eligible for dispatch.
- Respect the max parallel tasks soft limit. Do not dispatch more than the limit concurrently.
- Dispatch the next intent into the correct lifecycle phase. Repeat until the queue is empty.

---

## Non-Convergence Fallback (MUST)

If the workflow repeats the same action without converging:

1. STOP repeating the same change.
2. Identify the exact failing evidence (file path + minimal excerpt).
3. Report the mismatch and request human intervention.
4. If root cause is missing context or ambiguous scope: state what you know, what's missing, and ask one direct question. Set the `launch_spec` row to `WAITING_APPROVAL`.
