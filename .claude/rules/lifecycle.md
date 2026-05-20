# Routing, Lifecycle & Hooks

Single source of truth for: how a request gets classified, what phases follow, which hooks fire when, and what to do on failure. Merged from former `routing.md` + `lifecycle.md` + `hooks.md`.

---

# Part 1 — Routing: Profiles & Risk Classification

## Profiles

| Profile | When | Artifacts | Approval Gate |
|---|---|---|---|
| **LEARN** | Read/explain/understand code | None | No |
| **PATCH** | TRIVIAL or LOW risk change | None (TRIVIAL) / Slim Spec (LOW) | No |
| **STANDARD** | MEDIUM or HIGH risk change | task_brief.md + launch_spec | MEDIUM: FYI only; HIGH: required |
| **MAINTENANCE** | Wiki/WAL operations, no code changes | WAL fragments | No |

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
- User used `@vibe`/`@patch` AND probe shows red signals → emit a `[Probe Override]` block at turn start enumerating ignored signals, then proceed in the requested mode. See [policy.md](policy.md#probe-override).

## Risk Classification

Pick the tier whose Probe Signals row best matches your `[triage]` output. When in doubt, escalate one tier — the probe is conservative; tipping points around the boundaries should round up.

| Risk | Probe Signals (all must hold) | Profile |
|---|---|---|
| **TRIVIAL** | suggested=VIBE AND signals_red=[] AND no danger_keywords | PATCH (act inline, no spec) |
| **LOW** | suggested=PATCH (any single soft signal: blast 3–6 files, OR ambiguity FAIL, OR 2 recurring failures, OR MEDIUM keyword) | PATCH (Slim Spec, no task_brief) |
| **MEDIUM** | suggested=STANDARD-MEDIUM (blast ≥7, OR ≥3 recurring failures, OR two PATCH-tier signals compounding) | STANDARD (task_brief required) |
| **HIGH** | suggested=STANDARD-HIGH (any HIGH-tier danger keyword: auth, schema, migration, error code, lifecycle/policy/routing files, secret/token/credential) | STANDARD (task_brief + ≥2 ADR + Approval Gate) |

**Per-profile flows:**
- **TRIVIAL:** `Implement → QA → Archive` — no task_brief, no inline Explorer, no WAL.
- **LOW:** `Implement → QA → Archive` — no task_brief, no WAL; Slim Spec = one paragraph stating scope + AC before code.
- **MEDIUM:** `Explorer → Propose(task_brief) → Review → Implement → QA → Archive`
- **HIGH:** `Explorer → Propose(task_brief, ≥2 ADR) → Review(adversarial) → Approval Gate → Implement → QA → Archive`

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

### Scenario A — Emergency Hotfix
**Trigger:** Production incident, critical bug, ship immediately.
**Routing:** Profile PATCH. No Propose/Review. Requires `## Emergency Justification` + `secrets_linter.py` before Archive.
**Read:** `.claude/skills-archive/incident-response/SKILL.md` (main agent, FIRST action — triage → mitigation → post-mortem).

### Scenario B — Database / System Migration
**Trigger:** DDL changes (CREATE TABLE, ALTER TABLE, ADD INDEX, DROP COLUMN, etc.) OR A→B system migration.
**Routing:** Profile STANDARD, risk HIGH (forced). Approval Gate required. Gate: `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>`. Data WAL write-back MANDATORY.
**Read:** `.claude/skills-archive/migration-planner/SKILL.md` (system-architect, Propose phase — equivalence-test-first protocol).

### Scenario C — Breaking API Change
**Trigger:** Removing/renaming public endpoint, backward-incompatible schema change, auth/permission strategy change.
**Routing:** Profile STANDARD, risk HIGH (forced). Gate: `python3 .claude/scripts/gates/api_breaking_gate.py --task-brief <path>`. Must document migration guide in task_brief.

### Scenario D — Performance Tuning
**Trigger:** Performance-focused request (slow query, high latency, memory/CPU).
**Routing:** LEARN first (gather baseline evidence: bottleneck + metric + proposed fix). Then re-route as Change.
**Read (optional):** `.claude/skills-archive/external-research/SKILL.md` if baseline reveals an unknown systemic pattern.

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
| "拆分文档", index > 500 lines | Knowledge Architect | Check → Deduplicate → Split → Rewrite index |
| "扫描项目", "审计代码库" | Explorer (inline) | Scan → Index → Report |

Maintenance tasks have no code phases (no Explorer/Propose/Implement/QA). Detailed checklists for each role are in `.claude/agents/`.

## Shortcuts (Explicit Overrides)

| Shortcut | Profile | Effect |
|---|---|---|
| `@read` / `@learn` | LEARN | Read-only; never write code, never run gates |
| `@vibe` / `@patch` / `@quickfix` | PATCH | Act directly; skip Explorer/Propose/WAL even if heuristics suggest LOW |
| `@standard` | STANDARD | Force task_brief + lifecycle, even if heuristics suggest PATCH |
| `@gc` / `@librarian` | MAINTENANCE | Librarian compact flow |
| `@distill` | MAINTENANCE | Librarian distill flow (scan → human approval → execute) |
| `@capabilities` / `@cap` | MAINTENANCE | Documentation Curator regenerates `.claude/CAPABILITIES.md` |
| `@wiki-update` / `@milestone` | MAINTENANCE | Knowledge Extractor flow |

Flags: `--risk low|medium|high`, `--launch`, `--no-launch`, `--test "<cmd>"`, `--yes` (auto-confirm).
`@learn` MUST NOT combine with `--launch` or `--writeback`.

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

Run `requirement-intake` skill INLINE on the main agent (this skill never dispatches — it is the front-door classifier). It emits an `[Intake]` block with `Input-Type` and `Route`. Then dispatch by Input-Type:

| `[Intake] Input-Type` | Dispatch |
|---|---|
| PRD | Run `product-manager-expert` Mode A (Ingestion) → `task-decomposition-guide` |
| Idea / Feedback / Compliance | Dispatch **`requirement-engineer`** sub-agent |
| Security | Dispatch **`requirement-engineer`** + apply `security-review-checklist` |
| Bug / Signal | Switch to Scenario DEBUG → `systematic-debugging` (skip Phase 1) |
| Performance | LEARN baseline first; re-classify as Change after data is collected |

Why this split: `requirement-intake` is a thin classifier (Inline). `product-manager-expert` is heavy PRD work (PRD only). `requirement-engineer` is the AC transcription engine for non-PRD inputs. Three names, three contracts, no overlap.

**Step C — Additional layered dispatches (compose on top of Step B)**

| Condition | Additional dispatch |
|---|---|
| Risk = HIGH | `adversarial-review` Category A |
| EPIC / spans ≥ 3 domains | `system-architect` (Foreman) for slicing |
| Multi-stakeholder conflict signaled by intake | `stakeholder-conflict-resolver` |

Sub-agents do NOT inherit `CLAUDE.md` / rules / memory. Every dispatch MUST include the `## Memory Snapshot` section from [dispatch-template.md](dispatch-template.md), copying any `type=user` and `type=feedback` entries relevant to the task.

#### 1.1 Sub-agent return contract (requirement-engineer)

When dispatched, `requirement-engineer` MUST return this exact structured block. The main agent parses it before proceeding.

```
[Intent Summary]: <one-line restatement of what the user wants>
[ACs]: <numbered Given/When/Then list>
[Ambiguities]: <vague terms, missing info, unbounded scope; or "none">
[Must-Ask Questions]: <questions the main agent MUST raise via AskUserQuestion; or "none">
[Optional Questions]: <worth asking but not blocking; or "none">
[Scope Hint]: <files / modules likely in Allowed Scope, comma-separated; or "unknown">
[Source Documents]:
  - <path>[#L<a>-L<b>] — <one-line WHY>
  - VERBATIM: """<逐字 quote — use ONLY when no source file exists>"""
```

Rules for `[Source Documents]` (anti-summarization contract — see also `.claude/rules/dispatch-template.md`):
- Each line MUST be either a path pointer (with optional `#L<a>-L<b>` range) OR a `VERBATIM:"""..."""` block. Never paraphrase.
- This field flows verbatim into the next sub-agent's `## Source Documents (MUST READ before producing output)` dispatch section.
- Empty value = `unknown` only when the user input is < 1 sentence and there is literally no file to point at. In that case the field MUST be `VERBATIM:"""<the user's exact prompt>"""`.

The main agent MUST raise every `Must-Ask` question through `AskUserQuestion` before entering Phase 2. Skipping is not allowed.

#### 1.2 Phase 1 steps

1. **Dispatch decision** (per 1.0): inline or sub-agent.
2. **Specification gap**: `Current: [X]. Required: [Y]. Delta: [Z].`
3. **Collect ACs**: from sub-agent return OR derive inline.
4. **Ask Must-Ask questions** via `AskUserQuestion` (main agent only).
5. **`code_index.py --impact-of <target>`**: discover hidden scope.
6. **HIGH risk**: dispatch `adversarial-review` Category A. CRITICAL → revise AC. MINOR → annotate AC.
7. **Echo confirmation** (main agent only): use `AskUserQuestion` to confirm: "I understand you want **X**; AC is **Y**; we are NOT doing **Z**. Correct?" Receive explicit "yes" before Phase 2.

**Output:** MEDIUM/HIGH → inline `[Explore]` block (Spec Gap + ACs + Hidden Scope + Echo-Confirmed=Yes). TRIVIAL/LOW → reasoning inline only, no echo required. Never write a standalone explore_report.md.

### Phase 2: Propose
1. Design solution (MEDIUM: 1 option + rationale; HIGH: ≥2 ADR with Pros/Cons/Failure Conditions)
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

### Phase 4: Implement
1. Read task_brief Machine Section before any code
2. TDD: RED (failing test from AC) → GREEN (minimum code) → REFACTOR (clean up)
3. Stay within Allowed Scope. Violations → `[Boundary Exception Request]`, wait for approval.
4. Run `mvn compile -q` after each change. MAX 2 retries.
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
3. QA fails → roll back to Implement. MAX 2 retries. Third failure: STOP, ask human.

### Phase 6: Archive
1. Write WAL fragments (Domain + API + Rules; Data if schema change)
2. Plan Deviation Reflection: scope drift? dependency accuracy? plan invalidations? deferred ACs?
3. Move task_brief to `.claude/wiki/archive/`

## State Files

Only two: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract).

**Launch spec statuses:** PENDING | IN_PROGRESS | WAITING_APPROVAL | DONE | FAILED

**Resume protocol:** Find IN_PROGRESS row → read Artifact → load task_brief Machine Section.

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
- Synthesizes four signals (blast_radius, failure_history, ambiguity, danger_keywords) into `suggested_profile` ∈ {VIBE, PATCH, STANDARD-MEDIUM, STANDARD-HIGH}
- Prints `[triage]` block only when profile > VIBE or there are red signals; silent on ALL-GREEN VIBE
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
- `shift_left`: Run `mvn compile -q` after each code change. MAX 2 retries.
- Scope enforcement is automatic via the PreToolUse hook (see above) — no manual scope_guard.py call needed when a launch_spec is active. To audit the full change set in one shot (e.g., before commit), run `python3 .claude/scripts/gates/scope_guard.py --task-brief <path>` (omit `--files` to default to git diff).
- TRIVIAL/LOW: if no unit tests cover the change, present `git diff` to user before proceeding
- Do NOT run full test suite here (that's QA)

### QA
- Run tests. Produce objective evidence (test output).
- ACs ≥ 4 or risk = HIGH: map each Given/When/Then AC → test method → expected → actual → status

### QA → Archive
- Run `python3 .claude/scripts/gates/secrets_linter.py --paths "<changed files>"`

## Scenario-Specific Gates

| Scenario | Gate |
|---|---|
| B (DB Migration) | `python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>` |
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
| Implement → compile failure (shift_left) | Fix, max 2 retries. Both fail → downgrade to Propose. |
