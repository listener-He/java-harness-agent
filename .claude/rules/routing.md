# Intent Gateway Router

Routing contract: selects an execution profile, then optionally launches a lifecycle queue.

Lifecycle rules: [lifecycle.md](lifecycle.md)

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
| **MAINTENANCE** | Wiki/WAL compaction, knowledge extraction, project scan, document split — no code changes | No | Yes (WAL fragments, merged indexes) | No |

### LEARN
- No launch spec. No wiki write-back. No lifecycle phases.
- Direct file read is preferred when scope is explicit.

### PATCH
- Minimal artifacts: Slim Spec or Change Log + objective verification evidence.
- No `Propose → Review → Approval` chain.
- Hooks still apply.
- Abbreviated flow (LOW): `Explorer(inline) → Implement → QA → Archive`
- Abbreviated flow (TRIVIAL): `4_Implement → 5_QA → 6_Archive`

### MAINTENANCE
- For knowledge/wiki maintenance operations. No code changes involved.
- No Explorer / Propose / Review / Implement / QA phases — these are not code tasks.
- Flow is role-specific based on the maintenance subtype (see lifecycle.md MAINTENANCE profile):
  - WAL Compaction (`@Librarian`): Aggregate → Merge → Clean → Lint
  - Wiki Refresh (`@Knowledge Extractor`): Diff → Extract → WAL fragments → Lint
  - Document Split (`@Knowledge Architect`): Check size → Deduplicate → Split → Rewrite index → Lint
  - Project Scan (mounted Explorer): Scan → Index → Report
- Hooks: pre_hook + post_hook apply. shift_left_hook (compile) does NOT apply.

### STANDARD
- Full lifecycle: Explorer → Propose → Review → Approval Gate → Implement → QA → Archive.
- Requires `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` (MEDIUM: task_brief with single option; HIGH: task_brief with ≥2 ADR alternatives).

---

## 2. Top-level Intents

| Intent | When | Default Profile | Launch spec | Write-back |
|---|---|---|---|---|
| `Learn` | "Explain / read / understand" with explicit scope | LEARN | No | No |
| `Change` | "Modify code" (feature, refactor, bugfix) | PATCH or STANDARD | Yes (STANDARD only) | Required (WAL) |
| `DocQA` | "What is the rule / process / template?" | LEARN | No | No (unless actionized) |
| `Audit` | "Assess the codebase" (read-only review / risk scan) | LEARN | No | No |
| `Maintenance` | "Clean / organize / extract / compact wiki or knowledge" — WAL compaction, wiki refresh, knowledge extraction, project scanning, document split | MAINTENANCE (see lifecycle.md) | No | Yes (WAL fragments, merged indexes) |

### Intent Signal Matrix

If a `[Intake]` block was emitted by `requirement-intake`, use its `Intent` and `Profile` as the starting seed. The matrix below may confirm or upgrade (never downgrade) the intake result.

Classify every incoming request against this matrix before taking any action, then output an `[Intent Check]` line (see [CLAUDE.md](../../CLAUDE.md)).

Domain objects (table names, API paths, service names, feature names) are not predefined — identify them by reading the workspace.

| Signal type | Purpose | Examples (English) | Examples (Chinese) |
|---|---|---|---|
| **Action** | What the developer wants to do — purely process-level verbs | implement, add, create, fix, refactor, optimize, design, migrate, update, remove, delete, integrate, deploy, test, review, build, generate, write, change, modify | 设计, 实现, 修复, 新增, 改造, 优化, 落地, 上线, 测试 |
| **Maintenance Action** | Knowledge/Wiki maintenance verbs — no code changes | compact, merge, extract, clean, organize, split, scan, refresh, consolidate, gc, collect, archive, index, rebuild | 整理, 合并, 提取, 清理, 拆分, 扫描, 刷新, 沉淀, 重构, 归档, 收集, 压缩, GC, 重组 |
| **Process artifact** | Abstract workflow artifacts managed by this harness | hook, gate, lifecycle, router, workflow, wiki, wal, task_brief, launch_spec, skill, agent, role_matrix | 流程, 门控, 生命周期 |
| **Knowledge artifact** | Wiki/WAL/Knowledge domain objects | wiki, wal, knowledge graph, fragment, index, document, archive, spec, domain, api doc, data doc | 知识图谱, 文档, 索引, 碎片, 归档, 知识库, 知识, wiki |
| **Domain object** | Any noun/target from the actual workspace — NOT hardcoded | *(LLM reads code to identify)* | *(LLM reads code to identify)* |
| **Success/Evidence** | How the developer knows the task is done | pass, deliver, working, verified, evidence, test case, doc, documented, returns | 验收, 通过, 可用, 跑通, 门禁, 测试用例, 文档 |

**Classification rules:**
- **Maintenance Action** + (Knowledge artifact OR Process artifact) → `Maintenance` intent. Route to MAINTENANCE profile (see lifecycle.md). No spec, no approval gate — Librarian / Knowledge Extractor / Knowledge Architect roles handle these directly.
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
1. Read root: [KNOWLEDGE_GRAPH.md](../wiki/KNOWLEDGE_GRAPH.md)
2. Drill down via: Context Funnel (see section below)
3. If no specialist skill can be identified: consult [skill-index](../skills/skill-index/SKILL.md)

### Rule 3: Change intent → profile by risk
- TRIVIAL → Profile `PATCH` (No Spec, No Approval Gate, No Brake Snapshot, No rating, No WAL). Direct fast-path: `Implement → QA → Archive`. (Meets ALL of: ≤ 1 file; no API signature changes; no DB schema changes; no new dependencies; purely defensive/corrective code such as null checks, parameter validation, error code fixes, log additions, comments, formatting, typo fixes)
  - MUST still: output `[Intent Check]` line + Micro-Brake, run Grep/SearchCodebase for hidden deps, run `shift_left_hook` (compile), run `secrets_linter.py`.
  - MUST NOT: create task_brief, write Brake Snapshot, request 1-10 rating.
- LOW → Profile `PATCH` (Slim Spec allowed, NO Approval Gate needed). Direct fast-path: `Explorer -> Implement -> QA -> Archive`.
- MEDIUM → Profile `STANDARD` (task_brief, no Approval Gate — FYI only)
- HIGH → Profile `STANDARD` (task_brief + Approval Gate + Adversarial Review + Strict Security/Migration Gates)

### Rule 3.1: Budgeted Navigation (MUST)
For `Change` and `Audit` intents, uncontrolled exploration is forbidden.

- Wiki budget: 5 documents (soft guide, not a hard ceiling)
- Code budget: 12 files (soft guide)
- Web Search budget: 4 searches (soft guide)
- Same-file pagination reads do NOT count.
- On budget exhaustion: STOP and ask human directly.

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
1. Persist to `runs/launch-specs/launch_spec_{timestamp}.md`
2. Drive transitions by updating `Status / Phase / Artifact / Failed_Reason`

**Status values:** `PENDING` | `IN_PROGRESS` | `WAITING_APPROVAL` | `DONE` | `FAILED`

**Artifact binding rule:** When a task moves to `IN_PROGRESS` and a `task_brief.md` is created, write its full path into the `Artifact` column immediately. MUST be set before leaving Explorer/Propose phase.

**Template:**
```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## Task Queue
| Task | Status | Phase | Artifact | Failed_Reason |
|---|---|---|---|---|
| {task description — business language} | IN_PROGRESS | {phase} | {full path to task_brief.md, or — if not yet created} | — |
| {task description 2} | PENDING | — | — | — |

## Resume Protocol
When starting a new session (MUST, in order):
1. Read this file → find the row where Status = IN_PROGRESS or WAITING_APPROVAL
2. Read the Artifact column of that row → get the full path to task_brief.md
3. Load the task_brief Machine Section (Allowed Scope + AC + Hard Constraints)
4. Run the Resume Fidelity Check (see ../rules/hooks.md)

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
- State hypothesis and verification steps inline in the scope check.
- Once the root cause is found, the Agent MUST yield to the user or transition to a standard `Change` intent to apply the fix.

---

### Scenario EPIC — Massive Refactoring or Cross-Domain Feature

**Trigger:** The user requests a massive feature, a framework migration, or a task spanning more than 2 distinct domains.

**Routing:** Profile `STANDARD`, Intent `Change`, Risk `HIGH`.

**Engine Behavior:**
- **Contract-driven Delegation:** The Agent MUST NOT write code directly. It assumes the role of "Foreman + QA".
- The Agent MUST first write `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` (HIGH risk: defining API contracts, schemas, ≥2 ADR alternatives in Human Section).
- **Micro-tasking:** The Agent MUST NOT dispatch massive goals to sub-agents (e.g., "Refactor this module"). It MUST slice the work into `<YYYY-MM-DD>_<slug>_tasks.md`.
- **Parallel Dispatch:** The Orchestrator Agent MUST dispatch tasks to sub-agents, acting as the scheduler.
- The Agent delegates work to Sub-agents using high-frequency, short-lifecycle prompts. When dispatching, the Agent MUST use the contract schema defined in [subagent_contract_schema.md](../wiki/schema/subagent_contract_schema.md) to format the prompt.
- **Delegation Logging (MUST):** Persist each dispatched sub-agent contract prompt into `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_delegation_<id>.md` so deterministic gates can validate contract compliance.
- **Verification Gate:** The Agent MUST verify the sub-agent's return output against the contract schema before dispatching the next micro-task. Sub-agents are treated as "typewriters", not architects.
- State blast radius and dependencies assessment in the scope check.

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
python3 .claude/scripts/gates/migration_gate.py --sql-dir <path>
```
FAIL → block Archive. Bypass requires `bypass_justification.md` with DBA sign-off note.

**Extra constraint:** Data WAL write-back is MANDATORY in Archive (even if schema diff is small).

---

### Scenario C — Breaking API Change

**Trigger:** Removing or renaming a public endpoint, changing request/response schema in a backward-incompatible way, or modifying auth/permission strategy on an existing endpoint.

**Routing:** Profile `STANDARD`, risk `HIGH` (forced).

**Required gates (post-hook):**
```
python3 .claude/scripts/gates/api_breaking_gate.py --task-brief .claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md
```
FAIL → block Implement phase. The Agent MUST document the migration guide in `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` before proceeding.

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
python3 .claude/scripts/gates/dependency_gate.py --pom <pom.xml>
```
FAIL → block Archive. Bypass requires `bypass_justification.md` with compatibility evidence (test output or changelog excerpt).

---

## Context Funnel — Forward Navigation

Two symmetric protocols:
- **Forward (navigation)**: how the Agent collects context without blind searching.
- **Reverse (write-back)**: how the Agent writes stable knowledge back to the wiki during `Archive`.

### Rule 0: Direct Read when scope is explicit (MUST)
When the user provides an explicit scope (file path, directory, class/method, or pasted snippet) and the goal is learning:
- Read the target directly first.
- Use the wiki funnel only if background context is still needed after the direct read.
- Do NOT start with a Knowledge Graph drill-down for this scenario.

### Rule 0.5: Local Search Pre-flight (SHOULD, before manual drill-down)
When scope is NOT explicit, run local search tools BEFORE opening wiki or code files.
These tools are pure local — zero network calls, zero token cost.

**Wiki semantic search (BM25):**
```bash
python3 .claude/scripts/local_intel/wiki_search.py --query "<intent keywords>" --top 3
```
- Returns ranked wiki document paths with excerpts.
- Use the top result as the starting point instead of `KNOWLEDGE_GRAPH.md → index.md` drill-down.
- Still counts toward wiki budget when you actually READ the returned file.
- Skip if the query is too vague (< 3 content words); fall back to Rule 1.

**Code impact query (before writing Focus Card):**
```bash
python3 .claude/scripts/local_intel/code_index.py --impact-of <target_file>
python3 .claude/scripts/local_intel/code_index.py --who-calls <MethodName>
python3 .claude/scripts/local_intel/code_index.py --what-touches-table <table_name>
```
- Use to enumerate callers/importers of the changed file BEFORE writing the Allowed Scope list.
- Does NOT consume code budget (it reads the index file, not source files directly).
- Requires `code_index.py --build` to have been run. If index absent: skip and fall back to grep.

**Failure memory query (at session start for Change intent):**
```bash
python3 .claude/scripts/local_intel/failure_memory.py query --intent Change --phase <phase>
```
- Returns top-5 similar past failures to warn the agent before it repeats them.
- Output is advisory only — does NOT block execution.

### Rule 0.1: Budget Awareness (SHOULD)
Before any heavy navigation, be aware of soft budget guides. No need to output a preflight block.

**Soft Guides (not hard ceilings):**
- Wiki budget: ~5 distinct wiki documents
- Code budget: ~12 distinct workspace files
- Web Search budget: ~4 distinct external searches
- Same-file pagination reads do NOT consume additional budget.

**If you're approaching these limits without converging:** STOP and ask human. No escalation ceremony — just ask.

### Rule 1: Start at the root (MUST)
Context collection MUST begin by reading:
- [KNOWLEDGE_GRAPH.md](../wiki/KNOWLEDGE_GRAPH.md)

### Rule 2: Drill down via indexes (MUST)
1. In `KNOWLEDGE_GRAPH.md`, identify the correct domain index (e.g., [domain/index.md](../wiki/wiki/domain/index.md)).
2. Read that `index.md`.
3. Follow the link to the specific document you need.

### Rule 3: Fallback search is last resort (MAY)
Only when the index tree cannot locate the concept, search within `wiki/wiki/`.

### Rule 4: Budgeted Navigation (Simplified)

#### 4.1 Counting Rules
- Wiki budget: one unit per distinct wiki markdown file read.
- Code budget: one unit per distinct workspace file read.
- Pagination of the same file does NOT count.

#### 4.2 Example-First (Code Read Default)
For `Change` intent, attempt to locate a correct in-repo example before broad reading.
- First 2 code reads SHOULD capture one end-to-end example (typically `Controller + Service` or `Entity + Mapper/XML`).
- Only if the example is missing, conflicting, or insufficient: ask human for direction.

#### 4.3 Saturation Gate — Stop Reading When Any Is Met
- **Template acquired**: any 2 of (route shape, DTO validation style, service entry pattern, mapper/SQL pattern, table field pattern)
- **Integration point acquired**: a concrete usage example of the dependency
- **Executable chain acquired**: a known-good call chain exists; remaining work is a mechanical extension

#### 4.4 When to Stop and Ask Human
- Wiki reads not adding DB/API/permissions/flow constraints → shift to code.
- Wiki appears outdated or contradictory → trust code, note the drift.
- If you're near budget limits without converging → STOP and ask human.

### Rule 5: Stuck? Ask Human (MUST)
If budgets are exhausted or you're not converging: STOP and ask human directly. No escalation card template needed — just state:
- What you've confirmed (2-3 bullets)
- What you're missing (1 sentence)
- What you need from the human (1 question or request)

Set the intent row in `launch_spec_*.md` to `WAITING_APPROVAL`.

---

## Context Funnel — Write-back Rules

Write-back eligibility is defined above (by profile and flags).

**Profile split:**
- **PATCH**: No WAL write-back. Wiki refresh deferred to milestone or `@wiki-update`.
- **STANDARD**: Full WAL write-back as described below.

**Protocol (STANDARD only):**
1. Read [KNOWLEDGE_GRAPH.md](../wiki/KNOWLEDGE_GRAPH.md) to find the correct mount point.
2. Do NOT edit shared `index.md` files directly.
3. Write a WAL fragment into the target domain `wal/` directory.
   - Example (API): `../wiki/wiki/api/wal/YYYYMMDD_feature_x_api_append.md`
   - Example (Data/DB): `../wiki/wiki/data/wal/YYYYMMDD_feature_x_db_schema.md` (DO NOT write `.sql` files into the project root `sql/` directory).
4. Merge and splitting are performed in a low-conflict window (by human or via `python3 .claude/scripts/wiki/wiki_compactor.py`).
5. If an index exceeds the hard size limit: it MUST be split (see `writeback-policy.md`).

**Few-Shot Example (DB Change Archive):**
When generating a new table or altering a schema, the Agent MUST NOT drop a raw `.sql` file in the project root.
*Correct behavior:* Create a Markdown file `.claude/wiki/wiki/data/wal/20260419_add_tenant_asset_table.md` containing the DDL code blocks and ER mapping notes.

---

## Hard Constraints

- Links inside `.claude/` MUST use relative paths from the current file.
- If expertise is unclear: consult [skill-index](../skills/skill-index/SKILL.md).
- Every `index.md` MUST provide a 1–2 sentence summary for each linked child document.
