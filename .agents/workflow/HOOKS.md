# Hooks — Guards, Rollbacks, and Loop

Defines when and how to enforce constraints throughout the lifecycle.

---

## Session Resume Anchors (MUST, in order)

1. Read `router/runs/launch_spec_*.md` — restore from `Status / Phase`.
2. If `<YYYY-MM-DD>_<slug>_explore_report.md` exists — read its `## Core Context Anchors` section before any heavy navigation.

---

## Hook Definitions

### 1. `pre_hook` — Pre-Phase Gate

**Trigger:** Before entering any new phase.

**Bound skills:** `java-architecture-standards`

**Purpose:** Load the relevant rule sets before the phase begins. Example: before `Implement`, load defensive programming standards and project preferences.

**Required output (MUST):** Decision-First Preflight + budget declaration (see Rule 0.1 and Rules 4/5 in `../router/CONTEXT_FUNNEL.md`). This may be internal unless the user explicitly asks to see it; the mandatory `[Intent Check]` and `<Cognitive_Brake>` are always visible.

---

### 2. `guard_hook` — Execution Guard

**Trigger:** While performing core actions (generating code, writing SQL).

**Bound skills:** `java-coding-style`

**Purpose:**
- **Architectural Defense (MUST):** Ensure operations spanning multiple DB tables/domains are pushed down to a `@Transactional` Service or Facade layer. Controllers must remain thin.
- **Standards guard:** Enforce style, custom project exceptions (e.g., `CustomerException`), and required patterns (e.g., `jakarta.validation` vs `javax`).
- **Domain boundary guard:** Do NOT modify cross-domain files unless explicitly authorized in `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md`.
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

Read-only checks (do NOT modify files):

| Gate | Command | When required |
|---|---|---|
| OpenSpec schema | `python3 .agents/scripts/wiki/schema_checker.py <path_to_.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md>` | Every STANDARD task |
| Wiki graph lint | `python3 .agents/scripts/wiki/wiki_linter.py` | Every task with write-back |
| Ambiguity check | `python3 .agents/scripts/gates/ambiguity_gate.py --intent "<intent>" [--anchors-file <file>]` | Every task start |
| Write-back check | `python3 .agents/scripts/gates/writeback_gate.py --topic "<topic>" --date YYYYMMDD [--require-data]` | PATCH + STANDARD Archive |
| Delivery capsule | `python3 .agents/scripts/gates/delivery_capsule_gate.py --file <delivery_capsule.md>` | STANDARD Archive |
| Secrets scan | `python3 .agents/scripts/gates/secrets_linter.py --paths "<glob...>"` | Every code change |
| Java comment lint | `python3 .agents/scripts/gates/comment_linter_java.py --path <dir> [--fail-on-missing]` | Java code changes |
| **WAL compliance** | `python3 .agents/scripts/gates/wal_template_gate.py --wal-dir <dir>` | Every Archive with WAL output |
| **DB migration** | `python3 .agents/scripts/gates/migration_gate.py --sql-dir <path>` | Scenario B (DDL changes) |
| **Breaking API** | `python3 .agents/scripts/gates/api_breaking_gate.py --openspec .agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md` | Scenario C (API schema changes) |
| **Dependency** | `python3 .agents/scripts/gates/dependency_gate.py --pom <pom.xml>` | Scenario E (pom.xml changes) |
| Unified runner | `python3 .agents/scripts/gates/run.py --intent <...> --profile <...> --phase <...> --topic <...> --date <YYYYMMDD> [--verify-level quick\|standard\|strict] [--artifact-tags ...]` | Any phase (convenience wrapper) |

**Severity and bypass:**
- Follow `linter-severity-standard` skill.
- The Agent is ENCOURAGED to use `quality-checklist` from `.agents/skills/spec-quality-checklist/SKILL.md` to self-correct documents BEFORE running strict python gates.
- If a gate returns FAIL due to a rule violation (e.g., missing Javadoc on a trivial private method, or a legacy pattern): the Agent MAY generate a `bypass_justification.md` explaining why the rule should be waived in this specific context.
- When `bypass_justification.md` is present for a specific gate failure: the runner downgrades FAIL to WARN, allowing the workflow to proceed.
- Python gates should be treated as guidelines rather than absolute blockers if logic dictates otherwise. Use `WARN` instead of `FAIL` for stylistic mismatches.

**Bypass Lifecycle (MUST):**
- Every `bypass_justification.md` is valid ONLY for the current task (the task whose `focus_card.md` it references).
- When the task's Archive phase completes, all bypass files for that task are stale and MUST NOT be reused for subsequent tasks.
- A bypass file MUST include the header `task_id: <intent>:<profile>:<topic>:<date>` on its first line.
- A bypass file MUST include the header `expires_after: Archive` on its second line.
- If a gate detects a bypass file without these headers: downgrade FAIL to WARN as usual, but output a `STALE_BYPASS` warning in the gate report.
- Stale bypass files (from completed tasks) remaining in `.agents/workflow/runs/` will be flagged by `bypass_audit_gate.py` during Archive.

**Write-back policy (MUST):**
- For **STANDARD**: full write-back is REQUIRED.
  - Domain WAL + API WAL + Rules WAL: always mandatory.
  - Data WAL: mandatory when schema/DDL changes.
- For **PATCH**: WAL write-back is NOT required.
  - Move openspec to `../llm_wiki/archive/`.
  - Write 1-line changelog to `.agents/events/drift_queue/`.
  - Wiki refresh is deferred to milestone boundaries or explicit `@wiki-update` command.
- The Agent MUST NOT mark a STANDARD change as "done" if write-back gates fail.

**Optional audit report:**
```
python .agents/scripts/wiki/zero_residue_audit.py
```
Default output: `.agents/workflow/runs/`

#### Archive Cleanup (Conservative Mode)

After Phase 6 (Archive) has extracted WAL and moved the spec into cold storage, archive the session runtime artifacts and leave pointer files:

```bash
python3 .agents/scripts/tools/archive_session_artifacts.py --slug <feature_slug>
```

#### Explorer Post-Hook: Core Context Anchors (MUST)

The `<YYYY-MM-DD>_<slug>_explore_report.md` produced by the Explorer `post_hook` MUST include a section named `## Core Context Anchors` containing:

- Key links collected via drill-down (domain / api / data / architecture / preferences / security_rules, etc.)
- Business vocabulary and invariants (terms, enums, state notes)
- Explicit engineering red lines (forbidden patterns, permission strategy, idempotency strategy, rollback placeholder)

Usage: In Propose / Implement phases, if context is unstable or time has passed, read this anchor section before any heavy navigation.

---

### 4. `fail_hook` — Failure Rollback

**Trigger:** Any test, review, or compile failure.

**Bound skills:** `code-review-checklist`

**Actions:**
- **State downgrade:** Move back to the previous phase. Append the failure reason to `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md` (or the relevant task artifact). Fix all failed checklist items.
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
4. If the root cause is missing context or ambiguous scope: use the Escalation Card format in `../router/CONTEXT_FUNNEL.md` and set the `launch_spec` row to `WAITING_APPROVAL`.
