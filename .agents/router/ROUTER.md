# Intent Gateway Router

Routing contract: selects an execution profile, then optionally launches a lifecycle queue.

Lifecycle rules: [LIFECYCLE.md](../workflow/LIFECYCLE.md)

---

## Guiding Principle

Keep a small set of top-level intents. Use profiles and parameters to express execution differences — do not create more intent codes for every micro-scenario.

---

## 0. Shortcuts (Explicit Routing — Highest Priority)

If the user supplies an explicit shortcut, it MUST override automatic routing.

| Shortcut | Forced Profile |
|---|---|
| `@read` / `@learn` | LEARN (read-only) |
| `@patch` / `@quickfix` | PATCH (small change / bugfix) |
| `@standard` | STANDARD (full lifecycle) |
| `@gc` / `@librarian` | STANDARD (Forced role: `@Librarian`, triggers WAL Compaction) |
| `@wiki-update` / `@milestone` | STANDARD (Forced role: `@Knowledge Extractor`, triggers full wiki refresh from recent specs) |

### Shortcut DSL (Composable)

```
@<profile> <flags...> -- <natural language request>
```

**Flags (order-independent)**

*Scope / read:*
- `--scope <path|glob|symbol>` — explicit read scope
- `--direct` — skip Knowledge Graph; read files directly
- `--funnel` — force funnel even if scope is explicit
- `--depth shallow|normal|deep` — explanation depth (LEARN only)

*Risk / artifacts:*
- `--risk low|medium|high` — explicit risk override
- `--slim` — Slim Spec (PATCH only, or STANDARD with `--risk low`)
- `--changelog` — Change Log only (PATCH only)
- `--evidence required|optional|none` — default: PATCH=required

*Launch / write-back:*
- `--launch` — force lifecycle launch (STANDARD only)
- `--no-launch` — suppress launch
- `--writeback` — allow wiki/WAL write-back
- `--no-writeback` — forbid write-back (LEARN only; PATCH/STANDARD require it)

*Verification:*
- `--test "<cmd>"` — required verification command + evidence
- `--no-test` — skip tests (LEARN only; PATCH requires explicit justification)

*DocQA actionize:*
- `--actionize` — convert DocQA into an executable STANDARD queue (requires confirmation)
- `--yes` — auto-confirm `--actionize` / `--launch` (use with caution)

*Maintenance:*
- `@gc` / `@librarian` — shortcut to mount `@Librarian` role and perform WAL compaction.

**Conflict rules (MUST enforce)**

- `@learn` MUST NOT combine with `--launch` or `--writeback`.
- `--launch` MUST be used with `@standard` only.
- `--slim` requires `--risk low` (or implied low risk in PATCH).
- `--actionize` MUST prompt for confirmation unless `--yes` is present.

**Examples**
```
@learn --scope src/foo/bar.ts --direct --depth deep -- explain this file
@patch --risk low --slim --test "mvn test -Dtest=OrderServiceTest" -- fix NPE in createOrder
@standard --risk high --launch -- implement tenant permission checks for order list API
@learn --funnel -- what is the API design standard? --actionize
```

---

## 1. Profiles (Execution Modes)

| Profile | When to use | Launch spec | Write-back | Approval Gate |
|---|---|---|---|---|
| **LEARN** | Understand / explain code | No | No | No |
| **PATCH** | Small change, LOW risk bugfix | No | No (spec archive only) | No |
| **STANDARD** | MEDIUM/HIGH risk or wide blast radius | Yes | Required (WAL) | Yes (MEDIUM/HIGH) |

### LEARN
- No launch spec. No wiki write-back. No lifecycle phases.
- Direct file read is preferred when scope is explicit.

### PATCH
- Minimal artifacts: Slim Spec or Change Log + objective verification evidence.
- No `Propose → Review → Approval` chain.
- Hooks still apply.
- Archive: write 1-line changelog to `drift_queue`. No Domain/API/Rules WAL required (wiki refresh deferred to milestone or `@wiki-update`).
- Abbreviated flow (LOW): `4_Implement → 5_QA → 6_Archive` (requirement clarification deferred into Implement phase's Cognitive Brake)
- Abbreviated flow (TRIVIAL): `4_Implement → 5_QA → 6_Archive`

### STANDARD
- Full lifecycle: Explorer → Propose → Review → Approval Gate → Implement → QA → Archive.
- Requires `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md` (MEDIUM: task_brief with single option; HIGH: task_brief with ≥2 ADR alternatives).

---

## 2. Top-level Intents

| Intent | When | Default Profile | Launch spec | Write-back |
|---|---|---|---|---|
| `Learn` | "Explain / read / understand" with explicit scope | LEARN | No | No |
| `Change` | "Modify code" (feature, refactor, bugfix) | PATCH or STANDARD | Yes (STANDARD only) | Required (WAL) |
| `DocQA` | "What is the rule / process / template?" | LEARN | No | No (unless actionized) |
| `Audit` | "Assess the codebase" (read-only review / risk scan) | LEARN | No | No |

### Intent Signal Matrix

**Pre-condition:** If a `[Intake]` block was emitted by `requirement-intake`, use its `Intent` and `Profile` as the starting seed for classification. The matrix below may confirm or upgrade (never downgrade) the intake result.

The Agent MUST classify every incoming request against this matrix before taking any action, then output an `[Intent Check]` line (see [AGENTS.md](../../AGENTS.md)).

**Design principle:** Only abstract *development process* signals are defined here. Business domain objects (table names, API paths, service names, feature names, etc.) are intentionally absent — the LLM reads the workspace to identify them independently.

| Signal type | Purpose | Examples (English) | Examples (Chinese) |
|---|---|---|---|
| **Action** | What the developer wants to do — purely process-level verbs | implement, add, create, fix, refactor, optimize, design, migrate, update, remove, delete, integrate, deploy, test, review, build, generate, write, change, modify | 设计, 实现, 修复, 新增, 改造, 优化, 落地, 上线, 测试 |
| **Process artifact** | Abstract workflow artifacts managed by this harness | hook, gate, lifecycle, router, workflow, wiki, wal, task_brief, launch_spec, skill, agent, role_matrix | 流程, 门控, 生命周期 |
| **Domain object** | Any noun/target from the actual workspace — NOT hardcoded | *(LLM reads code to identify)* | *(LLM reads code to identify)* |
| **Success/Evidence** | How the developer knows the task is done | pass, deliver, working, verified, evidence, test case, doc, documented, returns | 验收, 通过, 可用, 跑通, 门禁, 测试用例, 文档 |

**Classification rules:**
- Action + (Process artifact OR any domain noun) + Evidence → `Change` intent, PASS ambiguity gate.
- Action + object (no evidence) → `Change` intent, WARN — ask for acceptance criteria.
- No action signal → ambiguity gate FAIL — request clarification before proceeding.
- No action / learning goal → `Learn` or `DocQA` intent.

---

## 3. Automatic Routing Rules

### Rule 1: Explicit scope + learning goal → Direct Read (MUST)
If the user provides an explicit scope (file path, directory, class/method, or pasted snippet) and the goal is learning:
- Select `Learn` + Profile `LEARN`.
- Do NOT start with Knowledge Graph drill-down.
- Use the funnel only if background context is needed after the first read.

### Rule 2: No explicit scope → Context Funnel (MUST)
Do NOT start with full-text search.

Required sequence:
1. Read root: [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)
2. Drill down via: [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)
3. If no specialist skill can be identified: consult [skill-index](../skills/skill-index/SKILL.md)

### Rule 3: Change intent → profile by risk
- TRIVIAL → Profile `PATCH` (No Spec, No Approval Gate, No Brake Snapshot, No rating, No WAL). Direct fast-path: `Implement → QA → Archive(drift_queue only)`. (Meets ALL of: ≤ 1 file; no API signature changes; no DB schema changes; no new dependencies; purely defensive/corrective code such as null checks, parameter validation, error code fixes, log additions, comments, formatting, typo fixes)
  - MUST still: output `[Intent Check]` line + Micro-Brake, run Grep/SearchCodebase for hidden deps, run `shift_left_hook` (compile), run `secrets_linter.py`.
  - MUST NOT: create task_brief, write Brake Snapshot, request 1-10 rating.
- LOW → Profile `PATCH` (Slim Spec allowed, NO Approval Gate needed). Direct fast-path: `Explorer -> Implement -> QA -> Archive`.
- MEDIUM → Profile `STANDARD` (task_brief, no Approval Gate — FYI only)
- HIGH → Profile `STANDARD` (task_brief + Approval Gate + Adversarial Review + Strict Security/Migration Gates)

### Rule 3.1: Budgeted Navigation (MUST)
For `Change` and `Audit` intents, uncontrolled exploration is forbidden.

- Wiki budget: 3 documents
- Code budget: 8 files
- Web Search budget: 2 searches
- Same-file pagination reads do NOT count.
- Budgets auto-extend via the two-tier reward mechanism (see [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)). Hard ceilings: Wiki ≤ 8, Code ≤ 20, Web ≤ 6.
- On budget exhaustion without meeting success criteria: file an Escalation Card (see [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)) and STOP.

### Rule 4: DocQA actionize is explicit opt-in (MUST)
DocQA is read-only by default. MUST NOT launch a lifecycle queue unless:
- The user explicitly requests actionize (via `--actionize` or equivalent natural language), AND
- The user confirms (or uses `--yes`).

---

## 4. Lifecycle Queue Codes (STANDARD only)

| Code | Phase | Notes |
|---|---|---|
| `Explore.Req` | Explorer | Clarify requirements + scope anchors |
| `Propose.API` | Propose → Review | API contract and design |
| `Propose.Data` | Propose → Review | Database schema changes |
| `Implement.Code` | Implement → QA | Code changes |
| `QA.Test` | QA | Tests + evidence |

---

## 5. Launch Spec (STANDARD only)

When launching a lifecycle queue:
1. Persist to `router/runs/launch_spec_{timestamp}.md`
2. Drive transitions by updating `Status / Phase / Artifact / Failed_Reason`
3. Optional: `python3 ../scripts/harness/engine.py init "..."` to create and maintain the file

**Status values:** `PENDING` | `IN_PROGRESS` | `WAITING_APPROVAL` | `DONE` | `FAILED`

**Artifact binding rule:** When a task moves to `IN_PROGRESS` and a `task_brief.md` is created, write its full path into the `Artifact` column immediately. This is the only mechanism a new session uses to find the active task context — it MUST be set before leaving Explorer/Propose phase.

**Template:**
```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## Task Queue
| Task | Status | Phase | Artifact | Failed_Reason |
|---|---|---|---|---|
| {task description — business language} | IN_PROGRESS | Implement | .agents/workflow/runs/2026-05-17_order-cancel_task_brief.md | — |
| {task description 2} | PENDING | — | — | — |
| {task description 3} | DONE | Archive | — | — |

## Resume Protocol
When starting a new session (MUST, in order):
1. Read this file → find the row where Status = IN_PROGRESS or WAITING_APPROVAL
2. Read the Artifact column of that row → get the full path to task_brief.md
3. Load the task_brief Machine Section (Allowed Scope + AC + Hard Constraints)
4. Run the Resume Fidelity Check (see HOOKS.md)

Rules:
- WAITING_APPROVAL: Wait for human approval before changing back to IN_PROGRESS; do not auto-continue
- FAILED: Report Failed_Reason, wait for human decision; do not auto-retry
- Artifact column is empty but Status = IN_PROGRESS: session was interrupted during Explorer phase, no task_brief to load; restart from Explorer step 2
```

---

## 6. Special Scenarios

These scenarios override the default routing rules. Match the user's request against the scenario list BEFORE applying standard routing.

### Scenario DEBUG — Deep Troubleshooting

**Trigger:** The user reports a bug, error, or exception but the root cause is unknown, requiring investigation before fixing.

**Routing:** Profile `PATCH`, Intent `Audit` (downgraded from `Change`). 

**Engine Behavior:** 
- The Agent is ALLOWED to execute terminal commands (e.g., tests, log reading) with a higher Retry limit (up to 5 times) to gather evidence.
- The Agent is FORBIDDEN from modifying business code (`SearchReplace`) during the DEBUG scenario.
- The `<Cognitive_Brake>` MUST include `[Hypothesis]` and `[Verification]` steps.
- Once the root cause is found, the Agent MUST yield to the user or transition to a standard `Change` intent to apply the fix.

---

### Scenario EPIC — Massive Refactoring or Cross-Domain Feature

**Trigger:** The user requests a massive feature, a framework migration, or a task spanning more than 2 distinct domains.

**Routing:** Profile `STANDARD`, Intent `Change`, Risk `HIGH`.

**Engine Behavior:**
- **Contract-driven Delegation:** The Agent MUST NOT write code directly. It assumes the role of "Foreman + QA".
- The Agent MUST first write `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md` (HIGH risk: defining API contracts, schemas, ≥2 ADR alternatives in Human Section).
- **Micro-tasking:** The Agent MUST NOT dispatch massive goals to sub-agents (e.g., "Refactor this module"). It MUST slice the work into `<YYYY-MM-DD>_<slug>_tasks.md`.
- **Parallel Dispatch:** The Orchestrator Agent MUST dispatch tasks to sub-agents, acting as the scheduler.
- The Agent delegates work to Sub-agents using high-frequency, short-lifecycle prompts. When dispatching, the Agent MUST use the contract schema defined in [subagent_contract_schema.md](../llm_wiki/schema/subagent_contract_schema.md) to format the prompt.
- **Delegation Logging (MUST):** Persist each dispatched sub-agent contract prompt into `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_delegation_<id>.md` so deterministic gates can validate contract compliance.
- **Verification Gate:** The Agent MUST verify the sub-agent's return output against the contract schema before dispatching the next micro-task. Sub-agents are treated as "typewriters", not architects.
- The `<Cognitive_Brake>` MUST include an evaluation of the "Blast Radius" and "Dependencies".

---

### Scenario A — Emergency Hotfix (`@patch --emergency`)

**Trigger:** Production incident, critical bug, must ship immediately.

**Routing:** Force Profile `PATCH`. No Proposal/Review phases.

**Required output:**
1. `[Intent Check]` line with `emergency=true`.
2. Slim Spec with `## Emergency Justification` section.
3. Objective QA evidence before Archive.

**Extra gate:** After QA, run `secrets_linter.py` on changed files. FAIL blocks Archive.

---

### Scenario B — Database Migration

**Trigger:** Request involves DDL changes (CREATE TABLE, ALTER TABLE, ADD INDEX, DROP COLUMN, etc.).

**Routing:** Profile `STANDARD`, risk `HIGH` (forced). Approval Gate MUST NOT be skipped.

**Required gates (post-hook):**
```
python3 .agents/scripts/gates/migration_gate.py --sql-dir <path>
```
FAIL → block Archive. Bypass requires `bypass_justification.md` with DBA sign-off note.

**Extra constraint:** Data WAL write-back is MANDATORY in Archive (even if schema diff is small).

---

### Scenario C — Breaking API Change

**Trigger:** Removing or renaming a public endpoint, changing request/response schema in a backward-incompatible way, or modifying auth/permission strategy on an existing endpoint.

**Routing:** Profile `STANDARD`, risk `HIGH` (forced).

**Required gates (post-hook):**
```
python3 .agents/scripts/gates/api_breaking_gate.py --task-brief .agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md
```
FAIL → block Implement phase. The Agent MUST document the migration guide in `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_task_brief.md` before proceeding.

---

### Scenario D — Performance Tuning

**Trigger:** Request is performance-focused (slow query, high latency, memory/CPU optimization).

**Routing:** Start with `@read --audit performance` (LEARN, read-only) to gather baseline evidence. Do NOT jump to implementation before the audit is complete.

**Required output from audit:**
- Identified bottleneck (file + line or SQL).
- Baseline metric (time, count, size).
- Proposed fix with expected improvement.

Then re-route as `Change` intent with the audit as anchor context.

---

### Scenario E — Dependency Upgrade

**Trigger:** Changes to `pom.xml` dependencies (version bump, add/remove artifact).

**Routing:** Profile `PATCH` for patch-version bumps; `STANDARD` for major/minor version or new dependency.

**Required gates (post-hook):**
```
python3 .agents/scripts/gates/dependency_gate.py --pom <pom.xml>
```
FAIL → block Archive. Bypass requires `bypass_justification.md` with compatibility evidence (test output or changelog excerpt).
