## Profiles

| Profile | When | Artifact | Approval |
|---|---|---|---|
| **LEARN** | Read/explain code; conversation only | none | no |
| **RESEARCH** | Analysis / feasibility / baseline → report | `research_report.md` + launch_spec | no |
| **PATCH** | TRIVIAL or LOW risk change | none (TRIVIAL) / Slim Spec (LOW) | no |
| **STANDARD** | MEDIUM or HIGH risk change | `task_brief.md` + launch_spec | HIGH: required |
| **MAINTENANCE** | Wiki / WAL operations | WAL fragments | no |

## Step 0 — Evidence on Demand (no auto-injection)

As of P2 (Sensor/Policy/Enforce refactor) + P7 (Insight Layer), the architecture is:

```
Sensor (hook → events.jsonl + failure_memory.json + usage_tracker)
   ↓
Insight Layer (insight_detector → insights.jsonl; pattern recognition)
   ↓
Policy (agent + /h-context-check + /h-evolve; decisions, on-demand)
   ↓
Enforce (PreToolUse secrets pre-check + /h-gates --phase ...; the only blocking layer)
```

Hooks emit events; insight_detector finds patterns; agent **pulls** context via `/h-context-check` and turns insights into rule changes via `/h-evolve` (always human-approved). No more `[triage-evidence]` / `[failure-memory]` / `[ambiguity]` blocks pushed on every prompt.

How to gather evidence:

| Need | Tool |
|---|---|
| "what's been edited recently / scope of changes" | `python3 .claude/scripts/local_intel/events_query.py --kind edit_post --since 1h` |
| "any recurring failures in this area" | `python3 .claude/scripts/local_intel/failure_memory.py summary --days 30 --min-count 2` |
| "past incident touched this file" | `python3 .claude/scripts/local_intel/incident_hint.py <path>` |
| "blast radius of touching <symbol>" | `python3 .claude/scripts/local_intel/code_index.py --impact-of <symbol>` |
| "is this prompt structurally ambiguous" | `python3 .claude/scripts/gates/ambiguity_gate.py --intent "<text>"` |
| "any new insights since last check" | `python3 .claude/scripts/local_intel/insight_detector.py --write && python3 .claude/scripts/local_intel/insight_writer.py query` |
| **all of the above bundled (incl. insights)** | `/h-context-check` (preferred entry, runs the relevant subset based on session state) |
| "act on a specific insight (turn it into a rule change)" | `/h-evolve --insight-id <id>` (proposal only); `--apply` to commit after human OK |
| "I genuinely can't disambiguate intent semantically" | dispatch `triage-reviewer` Haiku sub-agent explicitly |

`@vibe`/`@patch`/`@quickfix` on a prompt containing HIGH-sensitivity keywords (auth/mutating DDL/migration/secret/lifecycle/policy/routing files) → emit `[Probe Override]` audit block per [policy.md](policy.md#probe-override) before acting.

## Risk Classification (agent self-assessed from semantic read + on-demand evidence)

| Risk | When | Profile |
|---|---|---|
| **TRIVIAL** | Read-only / explanation / cosmetic ≤3-line edit / no sensitive surface | PATCH (inline) |
| **LOW** | Small bounded change (≤6 files), no irreversible decision, recoverable mid-flight | PATCH (Slim Spec) |
| **MEDIUM** | Cross-cutting refactor (blast ≥7) OR repeated-failure area (≥3 recurring in 30d) OR multi-domain touch without irreversible call | STANDARD |
| **HIGH** | Auth strategy / mutating DDL / migration / error code semantics / lifecycle-policy-routing files / secret-token-credential handling. Additive `CREATE TABLE` = B1, NOT HIGH | STANDARD + ADR per actual irreversible decision + Approval Gate |

Never escalate on "important"/"production" alone. Mid-implementation public-API/DB/auth discovery → `[Plan Invalidation]`.

## Special Scenarios

`Read:` rows mean: that file MUST be read at the indicated phase.

| Scenario | Trigger | Profile | Key extras |
|---|---|---|---|
| **DEBUG** | bug, unknown root cause | PATCH | terminal ≤5 retries; code edit FORBIDDEN until root cause |
| **EPIC** | feature ≥3 domains / framework migration / massive refactor | STANDARD-HIGH (forced) | Foreman; slice to micro-tasks; TaskList one per sub-task. Read: `skills-archive/blueprint`, `dispatching-parallel-agents` |
| **A** Emergency Hotfix | production incident, ship now | PATCH | `## Emergency Justification` + `secrets_linter.py` before Archive. Read: `skills-archive/incident-response` |
| **B1** Additive DDL | only `CREATE TABLE` / `CREATE INDEX` on new tables | PATCH (LOW) | `migration_gate.py`; Data WAL strongly recommended (carve-out) |
| **B2** Mutating DDL / Migration | `ALTER`/`DROP`/`MODIFY`/`RENAME` on existing OR A→B migration | STANDARD-HIGH (forced) | Approval Gate; `migration_gate.py`; `h-archive` pre-checks Data WAL. Read: `skills-archive/migration-planner` |
| **C** Breaking API | remove/rename endpoint, BC-incompatible, auth strategy change | STANDARD-HIGH (forced) | `api_breaking_gate.py`; migration guide in task_brief |
| **D** Performance | slow query / high latency / memory / CPU | RESEARCH → STANDARD | baseline → §5 Recommendations → user picks Option → STANDARD with §5.chosen as Context |
| **RESEARCH** | analyze/research/evaluate/feasibility verb in prompt; or `@research` shortcut | RESEARCH | report at `.claude/runs/reports/<...>_research.md`; `research_report_gate.py` at Archive. Forbidden edits: `src/`, `pom.xml`, `*.sql`, migrations, any `task_brief.md` |
| **E** Dependency Upgrade | `pom.xml` change | PATCH (patch ver) / STANDARD (minor+) | `dependency_gate.py` |
| **GREENFIELD** | no `src/` OR "from scratch" | STANDARD-HIGH | Read: `skills-archive/greenfield-scaffold` (optionally `deepinit`) |
| **RELEASE** | release / version tag / deploy | MAINTENANCE | Read: `skills-archive/release` |
| **PIPELINE** | "from idea to delivery" | STANDARD multi-phase | Read: `skills-archive/ai-pipeline`, `self-improve`, `eval-harness` |

## Maintenance Operations

| Trigger | Agent | Flow |
|---|---|---|
| Wiki consolidation / WAL merge | `librarian` | Aggregate → Merge → Clean → Lint |
| Knowledge extraction / milestone WAL flush | `knowledge-extractor` | Diff → Extract → WAL fragments → Lint |
| Stale-knowledge distillation / wiki cleanup | `librarian` | Scan → Plan → Human-approve → Execute → Lint |
| Wiki index > 3000 lines | `knowledge-architect` | Check → Deduplicate → Split → Rewrite |
| Project scan / codebase audit | Explorer (inline) | Scan → Index → Report |

## Shortcuts

| Shortcut | Profile | Effect |
|---|---|---|
| `@read` / `@learn` | LEARN | Read-only |
| `@research` / `@analyze` / `@feasibility` | RESEARCH | Report, NOT code |
| `@vibe` / `@patch` / `@quickfix` | PATCH | Act directly |
| `@standard` | STANDARD | Force task_brief |

Flags: `--risk`, `--launch`/`--no-launch`, `--test "<cmd>"`, `--yes`; RESEARCH uses `--scope quick|deep`. `@learn`/`@research` MUST NOT combine with `--writeback`; `@learn` MUST NOT combine with `--launch`.


**Flow:** `Explorer → Propose → Review → [Approval if HIGH] → Implement → QA → Archive` (PATCH skips Explorer/Propose/Review; MAINTENANCE owns its flow). **Discipline:** PDD (deps before code; ≥3 tasks need DAG; soft parallel 3) · BDD (every AC = `Given X, when Y, then Z`; vague BLOCKED) · SDD (`task_brief.md` Machine English + Human Chinese) · TDD (RED→GREEN→REFACTOR; tests derived from ACs).

## Phase 1: Explorer

> Sub-agents have no `AskUserQuestion`. Interactive actions stay on main agent; dispatch heavy reasoning.

**Dispatch decision:** `@vibe`/`@patch` OR single-domain & < 200 chars → main agent inline. Otherwise → `input-classifier` (inline), then dispatch by Input-Type:

| Input-Type | Dispatch |
|---|---|
| PRD | `product-manager-expert` Mode A → `task-decomposition-guide` |
| Idea / Feedback / Compliance | `ambiguity-gatekeeper` → PASS: `requirement-engineer`; FAIL: relay `[Must-Ask]`, re-enter |
| Security | as above + `security-review-checklist` |
| Bug / Signal | Scenario DEBUG → `root-cause-debug` (skip Phase 1) |
| Performance | LEARN baseline first; re-classify after data |

**Additional layers** (compose): Risk=HIGH → `adversarial-review` Cat A; EPIC / ≥3 domains → `system-architect` (Foreman); multi-stakeholder conflict → `stakeholder-conflict-resolver`.

Every dispatch MUST include `## Memory Snapshot` per [dispatch-template.md](dispatch-template.md) — sub-agents inherit nothing else. Return contracts in `.claude/agents/<name>.md`; main agent MUST raise every `Must-Ask` via `AskUserQuestion` before Phase 2.

**Order:** dispatch → spec gap (`Current/Required/Delta`) → collect ACs → ask Must-Ask → `code_index.py --impact-of <target>` → HIGH: `adversarial-review` Cat A → echo confirmation ("I understand X; AC is Y; we are NOT doing Z. Correct?").

**Output:** MEDIUM/HIGH → inline `[Explore]` block; TRIVIAL/LOW → reasoning inline. Never write a standalone `explore_report.md`.

## Phase 2: Propose

1. **MEDIUM:** 1 option + rationale. **HIGH:** one ADR per *actual* irreversible decision (transport, persistence, sync/async, framework, API shape) with 2–3 alternatives + Pros/Cons/Failure + chosen rationale. Mechanical CRUD → `> Mechanical implementation — no irreversible architectural decision; no ADR required.`
2. Define Allowed Scope (exhaustive) + Hard Constraints
3. Write `task_brief.md`; write path into launch_spec Artifact column (bidirectional binding)

## Phase 3: Review

- MEDIUM: `code-review-checklist` + `java-architecture-standards`
- HIGH: + `adversarial-review` Category B (one round)
- Plan Review (≥3 tasks): completeness / consistency / feasibility / risk coverage / dependency soundness
- Review FAIL or adversarial CRITICAL → roll back to Propose

## Approval Gate (HIGH only)

Present Human Section. Full → Implement. Partial → record approved, roll back rejected. Full reject → Propose. TaskList: open `WAITING_APPROVAL: <task slug>` until resolved (see [tasklist-policy.md §1](tasklist-policy.md)).

## Phase 4: Implement

1. Read task_brief Machine Section first
2. TDD: RED → GREEN → REFACTOR. AC ≥ 4 → TaskList one per AC
3. Stay within Allowed Scope. Violation → `[Boundary Exception Request]`, wait
4. After each change: `mvn -pl <modules> compile -q`. MAX 2 retries for **in-scope** errors (on failure dispatch `java-build-resolver` for diagnosis, max 2 dispatches per `[Root Cause]`); out-of-scope = pre-existing upstream → `[Issues Found]`, don't count or fix
5. Compile passes → yield for QA permission

**`[Plan Invalidation]`**: emit when a core task_brief assumption proves structurally wrong. Fields: `Discovery` (file:line or test output), `Invalidated Assumption`, `Impact` (which ACs), `Proposed Action` (`ROLLBACK_TO_PROPOSE` | `ROLLBACK_TO_EXPLORER`). Do NOT expand scope to absorb.

## Phase 5: QA

1. Compile if not run since last change
2. AC ≥ 4 or HIGH: dispatch `test-runner` (returns `AC-id → test method → PASS|FAIL|SKIP`); else main agent runs tests inline. If changed files include `src/main/resources/mapper/**/*.xml`, `**/*Mapper.java`, or migration `*.sql` → also dispatch `database-reviewer` (HIGH/MEDIUM findings block Archive)
3. Test failures by scope (same contract as Phase 4 compile rule): in-scope → roll back to Implement, MAX 2 retries, 3rd → STOP. Out-of-scope + pre-existing → `[Issues Found]`; do NOT fix or count.

## Phase 6: Archive

1. WAL write-back is user-elected via `h-archive` (scans diff → multi-select). **None** is valid (stub file; HIGH + None needs justification line)
2. Plan Deviation Reflection: scope drift, dependency accuracy, plan invalidations, deferred ACs
3. Move `task_brief.md` to `.claude/wiki/archive/`

<a id="research-phase-flow"></a>## RESEARCH Phase Flow

`Investigate → Synthesize → Archive`. No Propose/Review/Approval/ADR. WAL default Skip.

- **R1 Investigate:** refine §1 Question via single `AskUserQuestion` if ambiguous; append findings to §3 inline (≥1 evidence pointer per bullet); edits limited to `.claude/runs/reports/<this-report>.md`; §2 step count > 12 with §3 not converging → emit `[Investigation Runaway]`
- **R2 Synthesize:** §4 cites §3 bullets by number; mark uncertainty `[high confidence]`/`[inferred]`/`[speculative]`; §5 Recommendations 0–4 Options each with explicit next-step; §7 Evidence Index backfilled; §6 Open Questions per template
- **R3 Archive:** `research_report_gate.py --require <path>` blocking (FAIL → R2, max 2 retries); WAL single AskUserQuestion default Skip, ≤2 dimensions; `mv .claude/runs/reports/<file>` → `.claude/wiki/archive/reports/<file>`; launch_spec → DONE. §5 Options surface as next-step prompts; MUST NOT auto-trigger

**Failure recording:** R1 runaway → `--intent Research --phase Investigate --pattern "runaway"`. R2 findings-without-synthesis (§3 ≥5 but §4 < 100 chars) → `--intent Research --phase Synthesize --pattern "findings-without-synthesis"`. Gate FAIL on first archive → standard `failure_memory` flow.

## State Files

`launch_spec_*.md` queue + per-task `task_brief.md` (STANDARD/PATCH) OR `research_report.md` (RESEARCH). **Resume:** find IN_PROGRESS row → read Artifact → dispatch by path pattern; honor COLLAB suffix.

| Column | Values |
|---|---|
| Status | PENDING / IN_PROGRESS / WAITING_APPROVAL / DONE / FAILED |
| Risk | LOW / MEDIUM / HIGH; RES (RESEARCH, risk-orthogonal) |
| Phase (RESEARCH) | single `Research` covering R1/R2/R3 |
| Artifact | `.claude/runs/task-briefs/<...>.md` OR `.claude/runs/reports/<...>_research.md`; collab pending → `\| COLLAB:<slug>` → `.claude/runs/collabs/<date>_<slug>_collab.md` |


## Automated Hooks (settings.json)

All hooks (except PreToolUse secrets-pre-check) are **pure sensors** as of P2/P3: they append events to `.claude/runs/local_intel/events.jsonl` and never inject inline context. Use `events_query.py` to pull when needed.

| Hook | Trigger | Action |
|---|---|---|
| PreToolUse | every Edit/Write | `pre_tool_use_hook.py`: ONLY `secrets_linter --content-stdin` — FAIL exit 2 blocks. PASS/WARN → emit `edit_pre` event + return 0. Scope_guard moved to `/h-gates`. |
| PostToolUse (Edit\|Write) | every Edit/Write | `post_tool_use_hook.py`: emit `edit_post` event + bump session_stats edit counter. No subprocess, no inline output. |
| PostToolUse (Read) | every Read | `post_read_hook.py`: usage_tracker bump (wiki/skill only) + emit `read` event. |
| UserPromptSubmit | every prompt | `user_prompt_submit_hook.py`: emit `prompt` event with text (truncated 2000) + session_id. No inline blocks. |
| SubagentStop | every sub-agent return | `subagent_stop_hook.py`: extract last assistant text (3-shape aware) + emit `subagent_return` event. Gate validation moved to `/h-gates`. |
| Stop | every main agent turn end | `stop_hook.py`: emit `turn_end` event with branch/head/dirty_files. Health checks moved to `/h-context-check`. |
| Notification | UI notification event | `notification_hook.py`: append `notifications.jsonl` + opt-in macOS bell via `CLAUDE_NOTIFY_SOUND=1`. |
| PreCompact | before context compression | `pre_compact_hook.py`: snapshot active task_brief / launch_spec rows / HEAD / recent commits to `last_compact_snapshot.json` + inject one-line recovery hint. |

Per-script semantics in script docstrings. Env vars: `CLAUDE_SCOPE_GUARD_BYPASS=1` (legacy, skips PreToolUse entirely), `CLAUDE_SECRETS_BYPASS=1` (skips secrets pre-check only), `CLAUDE_NOTIFY_SOUND=1` (macOS bell on notification), `CLAUDE_SUBAGENT_RETURN_QUIET=1` (skip subagent_stop event).

## Phase Gates (Agent-Executed)

| Boundary | Command(s) |
|---|---|
| Explorer → Propose | `failure_memory.py query --intent Change --phase Explorer`; `code_index.py --impact-of <target>`; MEDIUM/HIGH: convert reqs to Given/When/Then ACs |
| Propose → Implement | `task_brief_gate.py --require <path>`; HIGH: Approval Gate |
| Implement → QA | `mvn -pl <modules> compile -q` (max 2 in-scope retries). PreToolUse hook handles scope automatically; full diff audit: `scope_guard.py --task-brief <path>` |
| QA | Run tests + produce objective evidence. AC ≥ 4 or HIGH: map `AC-id → test method → expected → actual → status` |
| QA → Archive | `secrets_linter.py --paths "<changed files>"` |
| RESEARCH → Archive (R3) | `research_report_gate.py --require <report path>` (blocking) |

## Scenario-Specific Gates

| Scenario | Gate |
|---|---|
| B1 / B2 (DDL) | `migration_gate.py --sql-dir <path>` |
| C (Breaking API) | `api_breaking_gate.py --task-brief <path>` |
| E (Dependency) | `dependency_gate.py --pom <pom.xml>` |

## Failure Protocol

On gate failure: (1) `failure_memory.py record --intent <i> --profile <p> --phase <ph> --gate <s> --pattern "<r>" --task-id <id>`; (2) fix + re-run (MAX 2 retries); (3) 3rd → STOP, ask human.

## Compound Failure Decision Matrix

| Scenario | Action |
|---|---|
| Rollback needs scope expansion | STOP. `[Boundary Exception Request]`. Wait |
| Same phase fails twice, same root cause | STOP. Escalate with evidence |
| Same phase fails twice, different root causes | STOP. Roll back to Propose |
| In-scope compile/test failure | Fix, max 2 retries; 3rd → STOP / downgrade |
| Out-of-scope compile/test failure | `[Issues Found]`; do NOT fix or count |
