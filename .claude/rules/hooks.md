# Hooks & Gates Reference

Real Claude Code hooks are configured in `.claude/settings.json`. This file documents what each lifecycle phase needs in terms of validation and gates — the agent executes these at the appropriate moments.

---

## Automated Hooks (settings.json)

| Hook | Trigger | Action |
|---|---|---|
| PostToolUse | After every Edit/Write | `secrets_linter.py` on changed file |
| UserPromptSubmit | Before every user prompt | `failure_memory.py query` (if cache exists) |

These run automatically. The agent does not need to invoke them manually.

---

## Phase Gates (Agent-Executed)

### Explorer → Propose

- Run `python3 .claude/scripts/local_intel/failure_memory.py query --intent Change --phase Explorer` to surface past failures
- Run `python3 .claude/scripts/local_intel/code_index.py --impact-of <target>` to enumerate callers before writing Allowed Scope
- MEDIUM/HIGH: Convert requirements to Given/When/Then ACs — vague language blocked

### Propose → Implement

- Run `python3 .claude/scripts/gates/task_brief_gate.py --require <path>` (task_brief structural validation)
- HIGH risk: Approval Gate — present Human Section, wait for explicit approval

### Implement → QA

- `shift_left`: Run `mvn compile -q` after each code change. MAX 2 retries.
- Run `python3 .claude/scripts/gates/scope_guard.py --task-brief <path> --files "<list>"` after each change
- TRIVIAL/LOW: if no unit tests cover the change, present `git diff` to user before proceeding
- Do NOT run full test suite here (that's QA)

### QA

- Run tests. Produce objective evidence (test output).
- ACs ≥ 4 or risk = HIGH: map each Given/When/Then AC → test method → expected → actual → status

### QA → Archive

- Run `python3 .claude/scripts/gates/secrets_linter.py --paths "<changed files>"`

---

## Scenario-Specific Gates

| Scenario | Gate |
|---|---|
| B (DB Migration) | `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` |
| C (Breaking API) | `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>` |
| E (Dependency) | `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>` |

---

## Failure Protocol

On any gate failure:
1. Record: `python3 .claude/scripts/local_intel/failure_memory.py record --intent <intent> --profile <profile> --phase <phase> --gate <script> --pattern "<reason>" --task-id <id>`
2. Fix and re-run. MAX 2 retries per phase.
3. Same phase fails 3 times: STOP and ask human.

## Compound Failure Decision Matrix

| Scenario | Action |
|---|---|
| QA → back to Implement, scope unchanged | Normal rollback within existing Allowed Scope |
| QA → back to Implement, scope needs expansion | STOP. Output `[Boundary Exception Request]`. Wait for approval. |
| Same phase fails twice, same root cause | STOP. Escalate with evidence. |
| Same phase fails twice, different root causes | STOP. Roll back to Propose for contract amendment. |
| Implement → compile failure (shift_left) | Fix, max 2 retries. Both fail → downgrade to Propose. |
