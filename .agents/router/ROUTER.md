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
| **PATCH** | Small change, LOW risk bugfix | No | Required (WAL) | No |
| **STANDARD** | MEDIUM/HIGH risk or wide blast radius | Yes | Required (WAL) | Yes (MEDIUM/HIGH) |

### LEARN
- No launch spec. No wiki write-back. No lifecycle phases.
- Direct file read is preferred when scope is explicit.

### PATCH
- Minimal artifacts: Slim Spec or Change Log + objective verification evidence.
- No `Propose → Review → Approval` chain.
- Hooks still apply.
- Archive write-back is REQUIRED: Domain WAL + API WAL + Rules WAL at minimum.
- Abbreviated flow: `1_Explorer → 4_Implement → 5_QA → 6_Archive`

### STANDARD
- Full lifecycle: Explorer → Propose → Review → Approval Gate → Implement → QA → Archive.
- Requires `openspec.md` (full schema for MEDIUM/HIGH, Slim Spec for LOW).

---

## 2. Top-level Intents

| Intent | When | Default Profile | Launch spec | Write-back |
|---|---|---|---|---|
| `Learn` | "Explain / read / understand" with explicit scope | LEARN | No | No |
| `Change` | "Modify code" (feature, refactor, bugfix) | PATCH or STANDARD | Yes (STANDARD only) | Required (WAL) |
| `DocQA` | "What is the rule / process / template?" | LEARN | No | No (unless actionized) |
| `Audit` | "Assess the codebase" (read-only review / risk scan) | LEARN | No | No |

### Intent Signal Matrix

The Agent MUST classify every incoming request against this matrix before taking any action, then output an `[Intent Check]` line (see [AGENTS.md](../../AGENTS.md)).

**Design principle:** Only abstract *development process* signals are defined here. Business domain objects (table names, API paths, service names, feature names, etc.) are intentionally absent — the LLM reads the workspace to identify them independently.

| Signal type | Purpose | Examples (English) | Examples (Chinese) |
|---|---|---|---|
| **Action** | What the developer wants to do — purely process-level verbs | implement, add, create, fix, refactor, optimize, design, migrate, update, remove, delete, integrate, deploy, test, review, build, generate, write, change, modify | 设计, 实现, 修复, 新增, 改造, 优化, 落地, 上线, 测试 |
| **Process artifact** | Abstract workflow artifacts managed by this harness | hook, gate, lifecycle, router, workflow, wiki, wal, openspec, launch_spec, focus_card, skill, agent, role_matrix, explore_report | 流程, 门控, 生命周期 |
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
3. If no specialist skill can be identified: consult [trae-skill-index](../skills/trae-skill-index/SKILL.md)

### Rule 3: Change intent → profile by risk
- LOW → Profile `PATCH` (Slim Spec allowed)
- MEDIUM/HIGH → Profile `STANDARD` (full schema + Approval Gate)

### Rule 3.1: Budgeted Navigation (MUST)
For `Change` and `Audit` intents, uncontrolled exploration is forbidden.

- Wiki budget: 3 documents
- Code budget: 8 files
- Same-file pagination reads do NOT count.
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
2. Drive transitions by updating only `Status / Phase / Failed_Reason`
3. Optional: `python3 ../scripts/harness/engine.py init "..."` to create and maintain the file

After QA is done, transition automatically to the Archive phase in the **same session**. Use lightweight targeted commands (like `git diff <specific_files>` based on `focus_card.md`) or review `openspec.md` to summarize changes for WAL write-back, avoiding heavy context rereads.

**Status values:** `PENDING` | `IN_PROGRESS` | `DONE` | `WAITING_APPROVAL` | `FAILED`

**Template:**
```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## State Machine
| Intent | Status | Phase | Artifact/Log | Failed_Reason |
|---|---|---|---|---|
| Explore.Req | IN_PROGRESS | 1_Explorer | explore_report.md | - |
| Propose.API | PENDING | - | - | - |
| Implement.Code | PENDING | - | - | - |

## Resume Protocol
- On session interrupt: read this file first and restore from Status/Phase.
- If any row is WAITING_APPROVAL: stop and wait for human approval, then set back to IN_PROGRESS.
- If any row is FAILED: stop and report Failed_Reason.
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
- The Agent MUST first write a highly detailed `openspec.md` (defining API contracts, schemas, etc.).
- **Micro-tasking:** The Agent MUST NOT dispatch massive goals to sub-agents (e.g., "Refactor this module"). It MUST slice the work into `tasks.md`.
- The Agent delegates work to Sub-agents using high-frequency, short-lifecycle prompts (e.g., *"Read openspec.md section 2, ONLY generate UserEntity.java"*).
- **Verification Gate:** The Agent MUST verify the sub-agent's return output against the spec before dispatching the next micro-task. Sub-agents are treated as "typewriters", not architects.
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
python3 .agents/scripts/gates/api_breaking_gate.py --openspec <openspec.md>
```
FAIL → block Implement phase. The Agent MUST document the migration guide in `openspec.md` before proceeding.

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
