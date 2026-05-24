# Routing, Lifecycle & Hooks

Single source of truth for: how a request gets classified, what phases follow, which hooks fire when, and what to do on failure. Merged from former `routing.md` + `lifecycle.md` + `hooks.md`.

---

# Part 1 — Routing: Profiles & Risk Classification

## Profiles

| Profile | When | Artifacts | Approval Gate |
|---|---|---|---|
| **LEARN** | Read/explain/understand code (conversation only) | None | No |
| **RESEARCH** | Analysis / feasibility / baseline — produces a report, NOT code | research_report.md + launch_spec | No |
| **PATCH** | TRIVIAL or LOW risk change | None (TRIVIAL) / Slim Spec (LOW) | No |
| **STANDARD** | MEDIUM or HIGH risk change | task_brief.md + launch_spec | MEDIUM: FYI only; HIGH: required |
| **MAINTENANCE** | Wiki/WAL operations, no code changes | WAL fragments | No |

LEARN vs RESEARCH discriminator:
- LEARN → conversation only, no artifact
- RESEARCH → committed file at `.claude/wiki/archive/reports/`

## Step 0 — Triage Probe (auto-injected via UserPromptSubmit hook)

Before applying shortcuts or the Risk table, check the `[triage]` block injected by `.claude/scripts/local_intel/triage_probe.py` (runs in the UserPromptSubmit hook, after `[failure-memory]` and `[ambiguity]`).

The probe synthesizes four signals into a `suggested_profile`:
- **blast_radius** — `code_index.py --impact-of` for any file/class names in the prompt
- **failure_history** — `failure_memory.py summary --days 30 --min-count 2`
- **ambiguity** — `ambiguity_gate.py` (OK / WARN / FAIL)
- **danger_keywords** — HIGH tier (auth, schema, migration, error code, secret, framework routing files) / MEDIUM tier (public api, hook, gate)

How to use the suggestion:
- No `[triage]` block printed → input was heuristic-skipped (too short, pure question, `@learn`/`@read` shortcut). Proceed by normal shortcut rules.
- `[triage]` present → **adopt the suggested profile or higher**. The probe never downgrades; you may only escalate further.
- `suggested: RESEARCH` — risk-orthogonal. MUST NOT escalate RESEARCH to PATCH/STANDARD on danger keywords; treat `signals_yellow` as evidence-rigor amplifier within RESEARCH. RESEARCH → PATCH/STANDARD transition is user-driven only (explicit "now do it" after reviewing §5 Recommendations).
- User used `@vibe`/`@patch` AND probe shows red signals → emit a `[Probe Override]` block at turn start enumerating ignored signals, then proceed in the requested mode. See [policy.md](policy.md#probe-override).

## Risk Classification

Pick the tier whose Probe Signals row best matches your `[triage]` output. When in doubt, escalate one tier — the probe is conservative; tipping points around the boundaries should round up.

| Risk | Probe Signals (all must hold) | Profile |
|---|---|---|
| **TRIVIAL** | suggested=VIBE AND signals_red=[] AND no danger_keywords | PATCH (act inline, no spec) |
| **LOW** | suggested=PATCH (any single soft signal: blast 3–6 files, OR ambiguity FAIL, OR 2 recurring failures, OR MEDIUM keyword) | PATCH (Slim Spec, no task_brief) |
| **MEDIUM** | suggested=STANDARD-MEDIUM (blast ≥7, OR ≥3 recurring failures, OR two PATCH-tier signals compounding) | STANDARD (task_brief required) |
| **HIGH** | suggested=STANDARD-HIGH (any HIGH-tier danger keyword: auth, mutating DDL `ALTER/DROP/MODIFY/RENAME`, migration, error code, lifecycle/policy/routing files, secret/token/credential). Note: pure `CREATE TABLE` additive DDL is **not** HIGH — see Scenario B1. | STANDARD (task_brief + ADR per actual irreversible decision + Approval Gate). See [Phase 2](#phase-2-propose) for ADR criteria. |

**Per-profile flows:**
- **TRIVIAL:** `Implement → QA → Archive` — no task_brief, no inline Explorer, no WAL.
- **LOW:** `Implement → QA → Archive` — no task_brief, no WAL; Slim Spec = one paragraph stating scope + AC before code.
- **MEDIUM:** `Explorer → Propose(task_brief) → Review → Implement → QA → Archive`
- **HIGH:** `Explorer → Propose(task_brief, ADR per actual decision) → Review(adversarial) → Approval Gate → Implement → QA → Archive`
- **RESEARCH:** `Investigate → Synthesize → Archive` — no Propose/Review/Approval/ADR. Produces `research_report.md`. Trigger: `@research` shortcut OR `[Suggested Profile]: RESEARCH`. Risk-orthogonal: danger keywords → `signals_yellow` (rigor amplifier), NOT escalation. Detail: [RESEARCH Phase Flow](#research-phase-flow).

### Boundary rules

- **Never** force STANDARD on a TRIVIAL/LOW change just because the user mentioned "important" or "production". Use the Probe Signals row, not vibes.
- **Always** escalate if, mid-implementation, you discover the change actually touches public API/DB/auth — stop, emit `[Plan Invalidation]`, ask whether to switch to STANDARD.
- **Vibe override:** if the user invokes `@vibe`, `@patch`, or starts the request with a clear directive ("just add", "quick fix", "tweak"), Probe signals are still computed but the user's declared intent takes precedence. Emit `[Probe Override]` if any signals were red.

## Special Scenarios

These override the default risk classification. When a scenario specifies a **Read:** line, that exact archive file must be read at the indicated phase — the path is the instruction.

### Scenario DEBUG — Deep Troubleshooting
**Trigger:** Bug/error with unknown root cause.
**Routing:** Profile PATCH. ALLOWED to run terminal commands (≤5 retries). FORBIDDEN from modifying code. Once root cause found → yield to user or transition to Change intent.

### Scenario EPIC — Massive Refactoring / Cross-Domain Feature
**Trigger:** Feature spanning ≥3 domains, framework migration, or massive refactoring.
**Routing:** Profile STANDARD, risk HIGH (forced). MUST slice work into micro-tasks. MUST delegate to sub-agents via contract schema. MUST NOT write code directly — act as Foreman + QA.
**Read:** `.claude/skills-archive/blueprint/SKILL.md` (system-architect, Propose phase) + `.claude/skills-archive/dispatching-parallel-agents/SKILL.md` (when ≥2 independent workstreams).
**TaskList:** open one item per INVEST sub-task — the only mechanism that visualizes the sub-task DAG (`launch_spec` is a flat list). See [tasklist-policy.md §1](tasklist-policy.md).

### Scenario A — Emergency Hotfix
**Trigger:** Production incident, critical bug, ship immediately.
**Routing:** Profile PATCH. No Propose/Review. Requires `## Emergency Justification` + `secrets_linter.py` before Archive.
**Read:** `.claude/skills-archive/incident-response/SKILL.md` (main agent, FIRST action — triage → mitigation → post-mortem).
**TaskList:** open 1-2 audit items (`Emergency Justification written`, `secrets_linter clean`) so post-incident review can trace required artifacts in the transcript. See [tasklist-policy.md §1](tasklist-policy.md).

### Scenario B1 — Additive DDL (new tables / new indexes on new tables)
**Trigger:** Only adds new schema objects — `CREATE TABLE` for a brand-new table, `CREATE INDEX` on a new table. All `.sql` / mapper changes are new files; nothing touches existing schema.
**Detection:** `git status` shows only added files under the migration dir; `grep -E '\b(ALTER|DROP|MODIFY|RENAME)\b' <sql-dir>` returns nothing.
**Routing:** Profile **PATCH (LOW)**. Slim Spec (scope + AC) required, no task_brief. Gate: `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` still runs. Data WAL write-back strongly recommended (DDL is high-value knowledge; PATCH normally skips WAL but B1 carries it as a per-scenario carve-out — write a Data WAL fragment manually using the template in `.claude/skills/wal-documentation-rules/SKILL.md`).
**Skip:** adversarial review, ADR ceremony, Approval Gate, system-architect dispatch — additive new schema has no live rows and is mechanically reversible (`DROP TABLE`).

### Scenario B2 — Mutating DDL or System Migration
**Trigger:** Modifies existing schema (`ALTER TABLE`, `DROP COLUMN`, `DROP TABLE`, `MODIFY COLUMN`, `RENAME`, adding `NOT NULL` / `UNIQUE` / `FK` to an existing table) OR any A→B system migration.
**Routing:** Profile STANDARD, risk HIGH (forced). Approval Gate required. Gate: `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>`. WAL write-back follows the user-elected scheme; the diff scan in `h-archive` Step 3a pre-checks **Data** for any B2 task. Deselecting Data is allowed but discouraged — if user picks None, the justification line should explain why a live-schema mutation needs no Data WAL.
**Read:** `.claude/skills-archive/migration-planner/SKILL.md` (system-architect, Propose phase — equivalence-test-first protocol).

### Scenario C — Breaking API Change
**Trigger:** Removing/renaming public endpoint, backward-incompatible schema change, auth/permission strategy change.
**Routing:** Profile STANDARD, risk HIGH (forced). Gate: `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>`. Must document migration guide in task_brief.

### Scenario D — Performance Tuning
**Trigger:** Performance-focused request (slow query, high latency, memory/CPU).
**Routing:** RESEARCH first (baseline evidence → §5 Recommendations). User picks an Option → STANDARD task with §5.chosen as Context input.
**Read (optional):** `.claude/skills-archive/external-research/SKILL.md` if baseline reveals an unknown systemic pattern.

### Scenario RESEARCH — Analysis / Feasibility / Baseline
**Trigger (any):** `@research` shortcut; OR research-class verb (analyze/research/evaluate/assess/feasibility/调研/分析/评估/可行性) with no Change verb co-occurring; OR `[Suggested Profile]: RESEARCH` from gatekeeper.
**Routing:** Profile RESEARCH. Flow: Investigate → Synthesize → Archive. Skip Propose/Review/Approval/ADR. WAL default Skip.
**Allowed edits:** ONLY `.claude/runs/reports/<...>_research.md` + active `launch_spec_*.md` row.
**Forbidden edits:** `src/`, `pom.xml`, `*.sql`, migration files, any `task_brief.md`.
**Artifact:** `.claude/runs/reports/<YYYY-MM-DD>_<slug>_research.md` per `wiki/schema/research_report_schema.md`. Archive moves to `wiki/archive/reports/<...>_research.md` (committed).
**Gate (Archive only):** `python3 .claude/scripts/gates/research_report_gate.py --require <path>`
**Read (optional):** `.claude/skills-archive/external-research/SKILL.md`.

### Scenario E — Dependency Upgrade
**Trigger:** Changes to `pom.xml` dependencies.
**Routing:** PATCH for patch-version bumps; STANDARD for major/minor version or new dependency. Gate: `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>`.

### Scenario GREENFIELD — Starting from scratch
**Trigger:** No `src/` directory OR user explicitly says "from scratch / new project".
**Routing:** Profile STANDARD, risk HIGH (because everything is being decided for the first time).
**Read:** `.claude/skills-archive/greenfield-scaffold/SKILL.md` (requirement-engineer + system-architect, replaces "infer from existing code" Explorer logic). Optionally `.claude/skills-archive/deepinit/SKILL.md` for hierarchical CLAUDE.md generation.

### Scenario RELEASE — Release / Deployment
**Trigger:** User requests a release, version tag, deploy.
**Routing:** Profile MAINTENANCE (no code change typically).
**Read:** `.claude/skills-archive/release/SKILL.md` (main agent — validates pre-release gates).

### Scenario PIPELINE — Full Idea→Delivery Loop
**Trigger:** User invokes `@ai-pipeline` or "run the full pipeline" or "from idea to delivery".
**Routing:** Profile STANDARD, multi-phase orchestration.
**Read:** `.claude/skills-archive/ai-pipeline/SKILL.md` (main agent — orchestrates blueprint → decisions → eval → improve → cleanup). Also read `.claude/skills-archive/self-improve/SKILL.md` and `.claude/skills-archive/eval-harness/SKILL.md` when their phases fire.

## Maintenance Operations

| Trigger | Role | Flow |
|---|---|---|
| "整理/合并 wiki", `@gc` | Librarian | Aggregate → Merge → Clean → Lint |
| "提取/沉淀知识", `@wiki-update` | Knowledge Extractor | Diff → Extract → WAL fragments → Lint |
| "萃取 wiki / 清理过期", `@distill` | Librarian | Scan → Plan → Human-approve → Execute → Lint |
| "看能力 / 我有哪些 agent", `@capabilities` / `@cap` | Documentation Curator | Regenerate `.claude/CAPABILITIES.md` |
| "拆分文档", index > 3000 lines | Knowledge Architect | Check → Deduplicate → Split → Rewrite index |
| "扫描项目", "审计代码库" | Explorer (inline) | Scan → Index → Report |

Maintenance tasks have no code phases (no Explorer/Propose/Implement/QA). Detailed checklists for each role are in `.claude/agents/`.

## Shortcuts (Explicit Overrides)

| Shortcut | Profile | Effect |
|---|---|---|
| `@read` / `@learn` | LEARN | Read-only; never write code, never run gates |
| `@research` / `@analyze` / `@feasibility` | RESEARCH | Produce report artifact, NOT code; skip Approval/ADR; default no WAL |
| `@vibe` / `@patch` / `@quickfix` | PATCH | Act directly; skip Explorer/Propose/WAL even if heuristics suggest LOW |
| `@standard` | STANDARD | Force task_brief + lifecycle, even if heuristics suggest PATCH |
| `@gc` / `@librarian` | MAINTENANCE | Librarian compact flow |
| `@distill` | MAINTENANCE | Librarian distill flow (scan → human approval → execute) |
| `@capabilities` / `@cap` | MAINTENANCE | Documentation Curator regenerates `.claude/CAPABILITIES.md` |
| `@wiki-update` / `@milestone` | MAINTENANCE | Knowledge Extractor flow |

Flags: `--risk low|medium|high`, `--launch`, `--no-launch`, `--test "<cmd>"`, `--yes` (auto-confirm). RESEARCH uses `--scope quick|deep` (risk-orthogonal).
`@learn` MUST NOT combine with `--launch` or `--writeback`.
`@research` MUST NOT combine with `--writeback` — WAL opt-in is a single archive-time AskUserQuestion, default Skip.

When no shortcut is given, classify by the Risk Classification table; default to the lower tier when ambiguous.

---

# Part 2 — Lifecycle: Phases & State Machine

## Canonical Phase Flow

```
Explorer → Propose → Review → [Approval Gate if HIGH] → Implement → QA → Archive
```

PATCH profiles skip Explorer/Propose/Review entirely. MAINTENANCE has its own role-specific flow (see Maintenance Operations above).

## Discipline Pillars

### PDD: Task Dependencies & Parallelism
- Declare dependencies BEFORE writing code. Each task lists its upstream dependencies.
- ≥3 tasks: draw a dependency graph (DAG). Tasks without mutual dependencies MAY run in parallel (soft limit: 3).
- A task whose `Depends On` are not all `DONE` MUST remain PENDING.

### BDD: AC Format
Every requirement MUST be: `Given [precondition], when [action], then [observable, measurable result].`
Vague language ("handle correctly", "work properly") is BLOCKED.

### SDD/SPEC: Contract-First
`task_brief.md` is the universal contract. No code until spec is complete. Two sections:
- **Machine Section** (English): Allowed Scope, ACs, Hard Constraints — AI consumption
- **Human Section** (Chinese): business rationale, design trade-offs, decision questions

### TDD: Red → Green → Refactor
Tests are derived from BDD ACs, not invented by implementer.
1. RED — write failing test from AC
2. GREEN — minimum code to pass
3. REFACTOR — clean up within passing tests

## Phase Details

### Phase 1: Explorer

> **Asymmetric division of labor.** Heavy reasoning (parsing long input, AC transcription, adversarial review) is dispatched to sub-agents to keep the main agent's context clean. Interactive actions (`AskUserQuestion`, echo confirmation) stay on the main agent — sub-agents do NOT have access to `AskUserQuestion`, that is the hard boundary.

#### 1.0 Dispatch decision (three-step triage)

**Step A — Triage**

| Raw-input condition | Next |
|---|---|
| `@vibe` / `@patch` / single-domain & < 200 chars | Main agent inline. Skip Steps B & C. |
| ≥ 200 chars OR contains a PRD/spec block OR `@standard` is set | Step B (classifier first) |
| Spans ≥ 3 domains OR EPIC scope | Step B (classifier first) |

**Step B — Classify, then dispatch by input type**

Run `input-classifier` skill INLINE on the main agent (this skill never dispatches — it is the front-door classifier). It emits an `[Intake]` block with `Input-Type` and `Route`. Then dispatch by Input-Type:

| `[Intake] Input-Type` | Dispatch |
|---|---|
| PRD | Run `product-manager-expert` Mode A (Ingestion) → `task-decomposition-guide` |
| Idea / Feedback / Compliance | Dispatch **`ambiguity-gatekeeper`** → PASS: dispatch `requirement-engineer`; FAIL: relay `[Must-Ask Questions]` via `AskUserQuestion`, wait for answers, re-enter Step B with enriched input |
| Security | Dispatch **`ambiguity-gatekeeper`** → PASS: dispatch `requirement-engineer` + apply `security-review-checklist`; FAIL: relay questions, wait, re-enter |
| Bug / Signal | Switch to Scenario DEBUG → `root-cause-debug` (skip Phase 1) |
| Performance | LEARN baseline first; re-classify as Change after data is collected |

Why this split: `input-classifier` is a thin classifier (Inline). `ambiguity-gatekeeper` is a semantic gate — reads project context and detects undefined scope, untestable goals, and unbounded blast radius before AC transcription begins; the `[triage]` hook only catches surface-level vagueness. `product-manager-expert` is heavy PRD work (PRD only). `requirement-engineer` is the AC transcription engine for non-PRD inputs. Four names, four contracts, no overlap.

**Step C — Additional layered dispatches (compose on top of Step B)**

| Condition | Additional dispatch |
|---|---|
| Risk = HIGH | `adversarial-review` Category A |
| EPIC / spans ≥ 3 domains | `system-architect` (Foreman) for slicing |
| Multi-stakeholder conflict signaled by intake | `stakeholder-conflict-resolver` |

Sub-agents do NOT inherit `CLAUDE.md` / rules / memory. Every dispatch MUST include the `## Memory Snapshot` section from [dispatch-template.md](dispatch-template.md), copying any `type=user` and `type=feedback` entries relevant to the task.

#### 1.1 Sub-agent return handling (ambiguity-gatekeeper)

`ambiguity-gatekeeper` returns a `[Status]: PASS | FAIL` structured block — full contract in [ambiguity-gatekeeper.md](../agents/ambiguity-gatekeeper.md). Main agent behavior:
- **PASS** → proceed to `requirement-engineer` dispatch (adding `security-review-checklist` for Security type).
- **FAIL** → relay every `[Must-Ask Questions]` item via `AskUserQuestion`. After receiving user answers, re-enter Step B with the enriched input. Do NOT proceed to `requirement-engineer` until `ambiguity-gatekeeper` returns PASS.

The `[triage]` hook (`ambiguity_gate.py`) is a surface-level keyword filter and does NOT substitute for this dispatch — `ambiguity-gatekeeper` reasons over actual project context with `Read / Bash / Grep / Glob` tools.

#### 1.2 Sub-agent return handling (requirement-engineer)

`requirement-engineer` returns a structured block with `[Intent Summary]`, `[ACs]`, `[Must-Ask Questions]`, `[Source Documents]`, `[Source Documents Read]`, etc. — full contract in [requirement-engineer.md](../agents/requirement-engineer.md) Output Format section. The `[Source Documents]` anti-summarization rules are documented there and in [dispatch-template.md](dispatch-template.md).

The main agent MUST raise every `Must-Ask` question through `AskUserQuestion` before entering Phase 2. Skipping is not allowed.

#### 1.3 Phase 1 steps

1. **Dispatch decision** (per 1.0): inline or sub-agent.
2. **Specification gap**: `Current: [X]. Required: [Y]. Delta: [Z].`
3. **Collect ACs**: from sub-agent return OR derive inline.
4. **Ask Must-Ask questions** via `AskUserQuestion` (main agent only).
5. **`code_index.py --impact-of <target>`**: discover hidden scope.
6. **HIGH risk**: dispatch `adversarial-review` Category A. CRITICAL → revise AC. MINOR → annotate AC.
7. **Echo confirmation** (main agent only): use `AskUserQuestion` to confirm: "I understand you want **X**; AC is **Y**; we are NOT doing **Z**. Correct?" Receive explicit "yes" before Phase 2.

**Output:** MEDIUM/HIGH → inline `[Explore]` block (Spec Gap + ACs + Hidden Scope + Echo-Confirmed=Yes). TRIVIAL/LOW → reasoning inline only, no echo required. Never write a standalone explore_report.md.

### Phase 2: Propose
1. Design solution. **MEDIUM:** 1 option + rationale. **HIGH:** one ADR per *actual* irreversible architectural decision (transport choice, persistence model, sync vs async, framework selection, API contract shape) — each ADR carries 2–3 alternatives with Pros/Cons/Failure Conditions and the chosen option's rationale. If the design genuinely has no irreversible decision (mechanical CRUD with no choice between alternatives), state this explicitly in §8: `> Mechanical implementation — no irreversible architectural decision; no ADR required.` Adversarial-review Category B (Phase 3) is the safety net either way.
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

**TaskList:** open one "WAITING_APPROVAL: <task slug>" item until resolved — UI persistence prevents the user missing the approval request. Mark `completed` on Full/Partial; cancel on Full rejection. See [tasklist-policy.md §1](tasklist-policy.md).

### Phase 4: Implement
1. Read task_brief Machine Section before any code
2. TDD: RED (failing test from AC) → GREEN (minimum code) → REFACTOR (clean up). **AC count ≥ 4:** open TaskList with one item per AC — see [tasklist-policy.md §1](tasklist-policy.md).
3. Stay within Allowed Scope. Violations → `[Boundary Exception Request]`, wait for approval.
4. Run `mvn -pl <modules> compile -q` (scoped to modules containing Allowed Scope files) after each change. MAX 2 retries for **in-scope** compile errors. Out-of-scope errors are pre-existing upstream breakage — report via `[Issues Found]`, do not count toward the budget, do not try to fix.
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
3. Test failures classify by file scope (same contract as the compile rule in Phase 4):
   - Failing test file is **inside Allowed Scope** OR is a newly added test for in-scope code → it's your bug. Roll back to Implement. MAX 2 retries; third failure → STOP, ask human.
   - Failing test file is **outside Allowed Scope** AND `git log` shows it was already broken before this task started → pre-existing flake/breakage. Report via `[Issues Found]: pre-existing test failure in <test file>`, do NOT count toward the budget, do NOT silently fix the test. Continue to Archive only if every in-scope AC has objective PASS evidence.

### Phase 6: Archive
1. WAL write-back is **user-elected**: `h-archive` scans the diff, suggests dimensions, asks the user via multi-select. Only chosen dimensions are written. **None** is a valid choice — writes a single stub file (HIGH risk + None requires a one-line justification; MEDIUM does not).
2. Plan Deviation Reflection: scope drift? dependency accuracy? plan invalidations? deferred ACs?
3. Move task_brief to `.claude/wiki/archive/`

<a id="research-phase-flow"></a>
## RESEARCH Phase Flow

```
Investigate → Synthesize → Archive
```

### Phase R1: Investigate
- MUST refine §1 Question via single `AskUserQuestion` if input ambiguous; no iteration loop
- MUST append findings to §3 inline as collected; each bullet carries ≥ 1 evidence pointer per schema
- MUST NOT `Edit`/`Write` outside `.claude/runs/reports/<this-report>.md`
- Bounded exploration: § 2 step count > 12 with §3 not converging → emit `[Investigation Runaway]`, ask user to scope down

### Phase R2: Synthesize
- §4 Analysis MUST cite §3 bullets by number
- §4 MUST mark uncertainty with `[high confidence]` / `[inferred]` / `[speculative]`
- §5 Recommendations: 0–4 Option blocks per schema; each ends with explicit next-step
- §7 Evidence Index MUST be backfilled (dedup §3 pointers)
- §6 Open Questions per schema template

### Phase R3: Archive
- Gate (blocking): `python3 .claude/scripts/gates/research_report_gate.py --require <path>` — FAIL → roll back to R2 (max 2 retries)
- WAL: single AskUserQuestion, default Skip; Extract limited to ≤ 2 dimensions
- `mv .claude/runs/reports/<file>` → `.claude/wiki/archive/reports/<file>`
- launch_spec row → `Status=DONE, Phase=Archive`
- §5 Recommendations options surfaced as candidate next-step prompts; MUST NOT auto-trigger

### Failure recording (failure_memory)

| Pattern | Record key |
|---|---|
| R1 runaway (no §3 progress in 12 steps) | `--intent Research --phase Investigate --pattern "runaway"` |
| R2 findings-without-synthesis (§3 ≥ 5 but §4 < 100 chars) | `--intent Research --phase Synthesize --pattern "findings-without-synthesis"` |
| Gate FAIL on first archive | standard failure_memory flow |

## State Files

Only two: `launch_spec_*.md` (task queue) and a per-task contract — either `task_brief.md` (STANDARD/PATCH) or `research_report.md` (RESEARCH).

**Launch spec statuses:** PENDING | IN_PROGRESS | WAITING_APPROVAL | DONE | FAILED

**Risk column:** `LOW` | `MEDIUM` | `HIGH` (STANDARD/PATCH); `RES` (RESEARCH, risk-orthogonal).

**Phase column for RESEARCH:** single value `Research` covering R1/R2/R3 internally — launch_spec does NOT churn on sub-phase transitions.

**Artifact column path patterns:**

| Pattern | Profile | Resume context |
|---|---|---|
| `.claude/runs/task-briefs/<...>_task_brief.md` | STANDARD / PATCH | load Machine Section |
| `.claude/runs/reports/<...>_research.md` | RESEARCH | load §1 Question + §3 progress |

**Collab in-progress marker:** Awaiting external review → status stays `IN_PROGRESS`, Artifact column appends `| COLLAB:<slug>` → `.claude/runs/collabs/<date>_<slug>_collab.md`. Resume script reads the marker to surface pending review.

**Resume protocol:** Find IN_PROGRESS row → read Artifact → dispatch by path pattern (table above). Honor COLLAB suffix if present.

---

# Part 3 — Hooks & Gates Reference

Real Claude Code hooks are configured in `.claude/settings.json`. This part documents what each lifecycle phase needs in terms of validation and gates — the agent executes these at the appropriate moments.

## Automated Hooks (settings.json)

| Hook | Trigger | Action |
|---|---|---|
| PreToolUse | Before every Edit/Write | `pre_tool_use_hook.py` → `scope_guard.py` (blocks out-of-scope edits when an active task_brief exists; silent skip otherwise) |
| PostToolUse | After every Edit/Write | `post_tool_use_hook.py` → `secrets_linter.py` on changed file |
| UserPromptSubmit | Before every user prompt | `user_prompt_submit_hook.py` → emits up to four compact context blocks: `[failure-memory]`, distill nudge, `[ambiguity]`, `[triage]`. Each is silent when there is nothing to surface. |

These run automatically. The agent does not need to invoke them manually.

**triage_probe UserPromptSubmit semantics (Step 0 routing input — see Part 1):**
- Skips silently when prompt < 15 chars, contains `@learn`/`@read`/`@cap`/maintenance shortcuts, or is a question without an action verb
- Synthesizes five signals (blast_radius, failure_history, ambiguity, danger_keywords, intent_class) → `suggested_profile` ∈ {VIBE, RESEARCH, PATCH, STANDARD-MEDIUM, STANDARD-HIGH}
- `intent_class=RESEARCH` (computed by `ambiguity_gate.classify_intent`) short-circuits Change-side escalation: danger keywords → `signals_yellow`, not `signals_red`
- Prints `[triage]` block when profile > VIBE OR any red/yellow signal; silent on ALL-GREEN VIBE
- Each upstream subprocess capped at 3s; total budget typically < 600ms
- Quiet env: `CLAUDE_TRIAGE_QUIET=1`

**failure_memory UserPromptSubmit semantics:**
- Reads `.claude/runs/local_intel/failure_memory.json` (gitignored via `.claude/runs/`, populated by gate-failure `record` calls)
- Aggregates failures from the last 30 days, groups by `(phase, gate, pattern)`, keeps only patterns that recurred ≥ 2 times
- Top 5 are emitted to stdout as a `[failure-memory]` context block prepended to the user prompt
- Silent (no injection) when: no memory file, no recurring patterns, or `CLAUDE_FAILURE_MEMORY_QUIET=1`
- Token budget: typically < 200 tokens; well under the 5-minute prompt-cache window

**scope_guard PreToolUse semantics:**
- Looks up active task_brief via `find_active_task_brief.py` (latest `launch_spec_*.md` → IN_PROGRESS row → Artifact path)
- If no launch_spec exists or no IN_PROGRESS row: silent skip (PATCH/Vibe/maintenance work is not restricted)
- If file is in Allowed Scope: silent pass
- If file is out of scope: exit 2 with stderr message — Claude Code blocks the Edit and surfaces the reason to the agent
- Emergency bypass: `CLAUDE_SCOPE_GUARD_BYPASS=1` env var skips the check (one-shot, for stuck cases)

## Phase Gates (Agent-Executed)

### Explorer → Propose
- Run `python3 .claude/scripts/local_intel/failure_memory.py query --intent Change --phase Explorer` to surface past failures
- Run `python3 .claude/scripts/local_intel/code_index.py --impact-of <target>` to enumerate callers before writing Allowed Scope
- MEDIUM/HIGH: Convert requirements to Given/When/Then ACs — vague language blocked

### Propose → Implement
- Run `python3 .claude/scripts/gates/task_brief_gate.py --require <path>` (task_brief structural validation)
- HIGH risk: Approval Gate — present Human Section, wait for explicit approval

### Implement → QA
- `shift_left`: Run `mvn -pl <modules> compile -q` (scoped to Allowed Scope modules) after each code change. MAX 2 retries for **in-scope** errors only — pre-existing upstream compile breakage must be reported via `[Issues Found]`, not fixed, and does not count toward the budget.
- Scope enforcement is automatic via the PreToolUse hook (see above) — no manual scope_guard.py call needed when a launch_spec is active. To audit the full change set in one shot (e.g., before commit), run `python3 .claude/scripts/gates/scope_guard.py --task-brief <path>` (omit `--files` to default to git diff).
- TRIVIAL/LOW: if no unit tests cover the change, present `git diff` to user before proceeding
- Do NOT run full test suite here (that's QA)

### QA
- Run tests. Produce objective evidence (test output).
- ACs ≥ 4 or risk = HIGH: map each Given/When/Then AC → test method → expected → actual → status

### QA → Archive
- Run `python3 .claude/scripts/gates/secrets_linter.py --paths "<changed files>"`

### RESEARCH → Archive (R3)
- `python3 .claude/scripts/gates/research_report_gate.py --require <report path>` (blocking)
- FAIL → R2 (max 2 retries). PASS → WAL AskUserQuestion (default Skip) → `mv` into `wiki/archive/reports/`.

## Scenario-Specific Gates

| Scenario | Gate |
|---|---|
| B1 (Additive DDL — PATCH) | `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` |
| B2 (Mutating DDL / Migration — HIGH) | `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` |
| C (Breaking API) | `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>` |
| E (Dependency) | `python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>` |

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
| Implement → in-scope compile failure (shift_left) | Fix, max 2 retries. Both fail → downgrade to Propose. |
| Implement → out-of-scope compile failure | Report via `[Issues Found]`, do NOT fix, do NOT count toward retries. Continue with own work. |
| QA → in-scope test failure | Roll back to Implement. Max 2 retries. Third fails → STOP, ask human. |
| QA → out-of-scope test failure (pre-existing breakage / flake) | Report via `[Issues Found]: pre-existing test failure in <file>`. Do NOT fix the test to make it green. Do NOT count toward retries. |
