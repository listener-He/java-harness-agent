# Java Harness Agent

An AI agent harness framework for structured, sustainable software engineering. It defines a set of rules, roles, skills, and lifecycle phases that guide coding assistants through development tasks — from requirement intake to code generation, testing, and knowledge archival.

[![简体中文](https://img.shields.io/badge/中文版-available-red.svg)](README_zh.md)

---

## What It Is

This repository is **not** a Java library or application. It is a protocol and toolset that sits between a human developer and an AI coding assistant. It constrains the assistant's behavior to produce correct, traceable, and reviewable engineering outcomes.

Entry point: **[CLAUDE.md](CLAUDE.md)** — read first on every session start.

---

## Structure

```
CLAUDE.md                      # Single entry point
.claude/
├── rules/                     # Routing, lifecycle, hooks, dispatch, safety, write-back, skill precedence
│   ├── lifecycle.md           # Profiles + risk classification + phase details (Explorer → Propose → Review → Implement → QA → Archive) + per-phase gates and hooks
│   ├── policy.md              # Hard constraints + commit policy + WAL write-back + agent dispatch (inline role adoption vs sub-agent)
│   ├── dispatch-template.md   # Canonical sub-agent prompt skeleton (mandatory for every dispatch)
│   └── skill-precedence.md    # Conflict resolution when multiple MANDATORY skills target the same trigger window
├── agents/                    # Role catalog — each .md has Claude Code frontmatter (name/description/tools/model) and is invokable via the Agent tool
│   ├── ambiguity-gatekeeper.md   # Gate: blocks work on vague input. Enforces "definition of ready" (action verb + target + measurable outcome). Stops runaway exploration >3 unconverging steps. Phase: before Explorer.
│   ├── requirement-engineer.md   # Translates raw user requests → testable ACs in Given/When/Then. Challenges vague adjectives ("fast", "better"). Defines happy path + 2 edge cases per requirement. Runs cognitive bias check before finalizing. Phase: Explorer.
│   ├── system-architect.md       # Designs the technical solution before code exists. Produces task_brief.md (Allowed Scope + ACs + Hard Constraints + Task DAG). HIGH risk: ≥2 ADR alternatives with Pros/Cons/Failure Conditions. Acts as Foreman in EPIC. Phase: Propose → Review.
│   ├── lead-engineer.md          # Translates task_brief Machine Section → compilable, tested code. Follows TDD: RED (failing test from AC) → GREEN (minimum code) → REFACTOR (clean up). Copies existing patterns, stays in Allowed Scope. Phase: Implement.
│   ├── focus-guard.md            # Scope enforcement gate. Ensures every file edit stays within task_brief Allowed Scope. Blocks out-of-scope changes; requests [Boundary Exception] for necessary cross-boundary edits. Does NOT review quality — only boundary compliance. Phase: Implement (guard).
│   ├── code-reviewer.md          # Tech-lead code inspection against 5-dimension rubric: Correctness, Security, Performance, Design & Maintainability, Style. Reports CRITICAL (blocks merge) / MAJOR / MINOR findings with file:line references. Phase: QA.
│   ├── knowledge-extractor.md    # Extracts stable knowledge from completed code → WAL fragments (Domain, API, Rules, Data). Categorizes changes, writes to wal/ directories. Does NOT edit shared index.md — merging is the Librarian's job. Phase: Archive.
│   ├── documentation-curator.md  # Updates user-facing docs (README, Javadoc, API docs) to reflect code changes. Handles new/changed/removed public APIs. Follows Javadoc standards (@param, @return, @throws). Scope excludes wiki/WAL. Phase: Archive.
│   ├── skill-graph-curator.md    # Maintains skill index consistency. Ensures every skill dir has SKILL.md and every SKILL.md is indexed. Detects dead links, duplicates, orphans. Runs skill_index_linter as gate. Phase: Archive.
│   ├── knowledge-architect.md    # Splits bloated wiki indexes when >500 lines. Deduplicates → groups by topic → creates focused sub-documents → rewrites parent as lean routing index. Updates KNOWLEDGE_GRAPH.md. Phase: Maintenance (triggered by GC overflow).
│   ├── librarian.md              # Wiki health maintainer. Aggregates scattered WAL fragments → merges into stable domain indexes → garbage-collects merged fragments. Invokes Knowledge Architect on index overflow. Trigger: @gc / @librarian. Phase: Maintenance.
│   └── security-sentinel.md      # Deterministic security gate. Runs automated scan (secrets_linter.py) for hardcoded credentials, tokens, keys. Reports objective pass/fail — no subjective security review. Triggered before every Archive + Scenario A (Emergency Hotfix).
├── commands/                    # User-invokable slash commands (h- prefix, avoid Claude Code built-in collision)
│   ├── h-from-ticket.md         # GitHub/Jira/Linear ticket → task_brief skeleton + launch_spec row (runs ambiguity-gatekeeper + input-classifier)
│   ├── h-decompose.md           # PRD/EPIC pre-validation → task-decomposition-guide → N brief skeletons → DAG bound to launch_spec
│   ├── h-brief.md               # Schema-compliant task_brief + bidirectional launch_spec binding
│   ├── h-design.md              # Dispatch system-architect with strict Source Documents → write ≥2 ADRs (HIGH) → fill brief §8/§9
│   ├── h-resume.md              # Read-only: locate IN_PROGRESS task + restore Machine Section + report Next Action
│   ├── h-fix-bug.md             # Ticket/manual → root-cause-debug Phase 1 (MUST complete) → launch_spec row at correct risk level; p1/p2 triggers h-incident
│   ├── h-gates.md               # Phase/scenario-aware gate suite + failure_memory recording
│   ├── h-archive.md             # Plan Deviation Reflection → knowledge-extractor → archive brief → wiki_linter → mark DONE
│   ├── h-collab.md              # Generate cross-team deliverable (api/process/data/integration/custom) + collab state file + COLLAB marker in launch_spec
│   ├── h-collab-update.md       # Log external feedback → update deliverable → --signoff removes COLLAB marker; BLOCKED state recorded only
│   ├── h-pr.md                  # secrets_linter + scope_guard → gh pr create → write PR URL into task_brief; launch_spec → WAITING_APPROVAL
│   ├── h-ci.md                  # Fetch CI run data → classify failures (compile/test/security/coverage) → failure_memory + routing recommendation
│   ├── h-release.md             # Pre-release gates (queue/tree/branch/secrets) → WAL changelog → mvn versions:set → tag + push; --dry-run supported
│   └── h-incident.md            # Wrap ingest_incident.py + write incident .md from TEMPLATE (enforces 提醒未来 LLM smell test)
├── skills/                          # 28 skills auto-loaded by Claude Code on every session
│   ├── skill-index/                 # Central navigator (active set + archive references)
│   ├── ac-verify/                   # End-to-end AC verification with pass/fail evidence before Archive
│   ├── adversarial-review/          # One-round isolated critique (HIGH-risk Review)
│   ├── ai-slop-cleaner/             # Regression-safe cleanup: dead code, duplicates, over-abstraction
│   ├── architecture-decision-records/ # Capture architectural decisions as structured ADRs
│   ├── brainstorming/               # Explore idea/requirement into design with ADR-format alternatives
│   ├── code-review-checklist/       # Mandatory pre-delivery code review against all project standards
│   ├── cognitive-bias-checklist/    # Prevent hallucinations and overconfidence during design decisions
│   ├── decision-frameworks/         # SWOT, 5-Why, First Principles for root cause and architecture selection
│   ├── impl-plan/                   # Decompose spec into checkpoint-driven implementation plan
│   ├── input-classifier/            # Classify raw input (PRD, idea, bug, ticket) into structured intent+scope+AC
│   ├── java-architecture-standards/ # Mandatory: 3-Layer arch, API design, POJO, anti-JOIN, error codes
│   ├── java-coding-style/           # Mandatory: Checkstyle, Javadoc, utility class boundaries, functional patterns
│   ├── java-testing-standards/      # Mandatory: test isolation, mock guidelines, 3-scenario coverage rule
│   ├── local-code-intelligence/     # Zero-cost local tools: BM25 wiki search, symbol index, failure memory
│   ├── mybatis-sql-standard/        # Anti-JOIN, index utilization, implicit type conversion prevention
│   ├── product-manager-expert/      # PRD generation and PRD ingestion → technical requirements + AC
│   ├── remember/                    # Classify discovered knowledge into correct persistence layer
│   ├── root-cause-debug/            # Mandatory root-cause investigation before any fix (Phase 1 must complete)
│   ├── security-review-checklist/   # Secrets, authZ, IDOR, data exposure, dependency safety checklist
│   ├── skill-creator/               # Create or update SKILL.md for repeatable workflows
│   ├── skill-graph-manager/         # Mandatory: maintain bidirectional Skill Knowledge Graph
│   ├── spec-quality-checklist/      # Self-correction gate for AI-generated docs before Python gate scripts
│   ├── stakeholder-conflict-resolver/ # Detect and resolve mutually exclusive stakeholder requirements
│   ├── task-decomposition-guide/    # Decompose large PRDs/EPICs via INVEST criteria and Vertical Slicing
│   ├── test-driven-development/     # Write failing tests from ACs before implementation
│   ├── ultraqa/                     # Structured QA loop with Evidence Mapping Table (AC ↔ Test ↔ Result)
│   └── wal-documentation-rules/     # Mandatory: extract stable knowledge into WAL fragments at Archive
├── skills-archive/                  # 13 lower-frequency skills — NOT auto-loaded; referenced inline by the rule/agent that needs them
│   ├── ai-pipeline/                 # Full AI engineering pipeline orchestrator (Scenario PIPELINE)
│   ├── blueprint/                   # Multi-session, multi-agent construction plan (Scenario EPIC)
│   ├── deepinit/                    # New-repo deep init: hierarchical CLAUDE.md (Scenario GREENFIELD)
│   ├── dispatching-parallel-agents/ # Parallel sub-agent dispatch (Scenario EPIC)
│   ├── eval-harness/                # Formal AC eval / pass@k benchmarks (Scenario PIPELINE)
│   ├── external-research/           # CVE / compliance / plateau research (Scenarios D, PIPELINE)
│   ├── greenfield-scaffold/         # From-scratch protocol (Scenario GREENFIELD)
│   ├── incident-response/           # Production triage + post-mortem (Scenario A)
│   ├── linter-severity-standard/    # FAIL/WARN/IGNORE severity rubric for gate scripts
│   ├── migration-planner/           # A→B migration with equivalence tests (Scenario B)
│   ├── release/                     # Pre-release validation + step-by-step (Scenario RELEASE)
│   ├── self-improve/                # Tournament loop with plateau detection (Scenario PIPELINE)
│   └── using-git-worktrees/         # Isolated worktrees for HIGH-risk parallel work (lead-engineer)
├── wiki/                      # Knowledge graph (file-system-based, no vector DB)
│   ├── KNOWLEDGE_GRAPH.md     # Root index
│   ├── purpose.md             # Design philosophy
│   ├── schema/                # Contract templates (task_brief, subagent_contract)
│   └── wiki/                  # Domain, API, Data, Architecture, Specs, Testing, Reviews, Preferences
├── scripts/
│   ├── gates/                 # Deterministic gate scripts (scope_guard, secrets_linter, etc.)
│   ├── wiki/                  # Wiki maintenance (compactor, linter, schema checker)
│   ├── tools/                 # Bootstrap, archive, GC helpers
│   ├── local_intel/           # Zero-cost local search (wiki_search, code_index, failure_memory)
│   └── harness/               # Engine
├── workflow/
│   ├── role_matrix.json       # Role-to-phase mount table
│   ├── EXAMPLES.md            # Walkthrough of a STANDARD task
│   └── artifacts/             # Artifact templates
├── runs/                      # Runtime artifacts (task-briefs, launch-specs, cache)
└── settings.json              # Permissions and hooks configuration
```

---

## Workflow Process (STANDARD)

The STANDARD lifecycle implements a **PDD → BDD → SDD/SPEC → TDD → BDD** closed loop:

- **PDD (Plan-Driven Development)** at the front: task dependencies, parallelism constraints, and success metrics are declared before any code exists
- **BDD (Behavior-Driven Development)** at both ends: Explorer writes executable specs in `Given/When/Then` format; QA verifies behavior against those same specs
- **SDD/SPEC (Specification-Driven Development)** throughout: every phase is anchored to the `task_brief.md` contract
- **TDD (Test-Driven Development)** at the core: failing tests derived from ACs drive implementation

```
         ┌── PDD ──┐  ┌──── BDD ────┐                                     ┌──── BDD ────┐
         │依赖+并行  │  │ 写可执行规格  │                                     │ 行为验证     │
         │ DAG      │  │ Given/When/  │    ┌── SDD (契约驱动) ──┐           │ AC↔测试↔结果 │
         ▼          ▼  ▼              ▼    ▼                     ▼           ▼              ▼
Input ─→ Explorer ─→ Propose ─→ Review ─→ [Approval] ─→ Implement ─→ QA ─→ Archive
          │              │          │                        │          │        │
          需求澄清     架构设计   设计审查                TDD实现    测试验证  知识沉淀
          │              │          │    │                  │          │        │
          ▼              ▼          ▼    ▼                  ▼          ▼        ▼
       Spec Gap     task_brief  Plan   Approved        Red→Green   Evidence   WAL
       + AC list    +依赖+并行  Review Contract         →Refactor   Mapping    +偏差回顾
```

### Phase 1: Explorer — 需求澄清 + BDD 规格编写

| Item | Detail |
|------|--------|
| **Roles** | `@Ambiguity Gatekeeper` (pre-gate), `@Requirement Engineer`, `@System Architect` (Propose) |
| **Skills** | `input-classifier`, `brainstorming`, `product-manager-expert`, `task-decomposition-guide` |
| **Activities** | ① `input-classifier` inline: classify raw input → emit `[Intake]` block with `Input-Type` and `Route` |
| | ② **Idea/Feedback/Compliance/Security inputs**: dispatch `ambiguity-gatekeeper` first — FAIL blocks until input is tightened; PASS → dispatch `requirement-engineer` |
| | ③ **Specification Inference**: `Current: [X]. Required: [Y]. Delta: [Z]` — the gap is the true scope |
| | ④ **BDD — AC-as-Tests Translation (MUST)**: convert every requirement to `Given [precondition], when [action], then [observable, measurable result]` — vague language ("handle correctly", "work properly") is BLOCKED |
| | ⑤ Impact analysis: `code_index.py --impact-of <target>` → identify hidden dependencies |
| | ⑥ Adversarial review Category A (HIGH only): "are we solving the right problem?" |
| **Output** | Spec Gap + AC list (Given/When/Then) + Hidden Scope → feeds into task_brief Machine Section |

### Phase 2: Propose — 架构设计与 Spec (Architecture Design & Specification)

| Item | Detail |
|------|--------|
| **Roles** | `@System Architect` |
| **Skills** | `brainstorming`, `java-architecture-standards`, `task-decomposition-guide`, `decision-frameworks`, `cognitive-bias-checklist` |
| **Activities** | ① **PDD — Plan as First-Class Artifact**: Declare task dependencies, draw dependency graph (DAG) when ≥3 tasks; set parallelism constraints (soft limit: 3) |
| | ② Generate ≥2 design alternatives (HIGH: ADR format with Pros/Cons/Failure Conditions) |
| | ③ Select approach → emit **Constraint List** (binding decisions for all downstream work) |
| | ④ Define **Allowed Scope** — explicit file whitelist that constrains implementation |
| | ⑤ Write `task_brief.md` — the **universal contract**: |
| | &nbsp;&nbsp;&nbsp; • Machine Section (English): Allowed Scope + ACs + Task Dependencies + Hard Constraints |
| | &nbsp;&nbsp;&nbsp; • Human Section (Chinese): 做什么/为什么 + 怎么做 + 待确认项 |
| **Output** | `task_brief.md` — single artifact shared by all agents and humans |

### Phase 3: Review — 设计审查 (Design Review)

| Item | Detail |
|------|--------|
| **Roles** | `@System Architect` |
| **Skills** | `code-review-checklist`, `java-architecture-standards`, `adversarial-review` (HIGH), `spec-quality-checklist` |
| **Activities** | ① Review design against project standards and architecture constraints |
| | ② **Plan Review Checklist (PDD)**: Completeness → Consistency → Feasibility → Risk Coverage → Dependency Soundness (≥3 tasks) |
| | ③ Adversarial critique Category B (HIGH only): "are we solving it the right way?" — ONE round |
| | ④ **Approval Gate** (HIGH only): present Human Section in business language → wait for explicit sign-off |
| | ⑤ CRITICAL finding → rollback to Phase 2. MINOR → annotate ACs, proceed |
| **Output** | Approved `task_brief.md` (HIGH) or FYI summary (MEDIUM) |

### Phase 4: Implement — TDD 驱动实现 (TDD-Driven Implementation)

| Item | Detail |
|------|--------|
| **Roles** | `@Lead Engineer`, `@Focus Guard` |
| **Skills** | `test-driven-development`, `java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `impl-plan` |
| **Activities** | ① Read `task_brief.md` Machine Section — Allowed Scope + ACs + Hard Constraints |
| | ② **RED**: Write failing tests derived from ACs (must see test failure before writing code) |
| | ③ **GREEN**: Implement within Allowed Scope — `scope_guard.py` enforces boundary |
| | ④ **REFACTOR**: Apply coding style, extract magic numbers, ensure SOLID compliance |
| | ⑤ Shift-left: `mvn compile` + `secrets_linter.py` after every change (max 2 retries) |
| | ⑥ **YIELD**: Stop and ask human for permission to proceed to QA |
| **Output** | Modified source files, passing tests, compile-clean |

### Phase 5: QA — 测试验证 + BDD 行为验证

| Item | Detail |
|------|--------|
| **Roles** | `@Code Reviewer` |
| **Skills** | `java-testing-standards`, `code-review-checklist`, `ultraqa`, `security-review-checklist` (HIGH) |
| **Activities** | ① Ensure compile is clean (`shift_left_hook`) |
| | ② Run test suite → verify all ACs pass |
| | ③ **BDD — Evidence Mapping Table** (AC ≥ 4 or HIGH risk): every Given/When/Then AC mapped to test method → expect → actual → status — ensures every behavior declared in Phase 1 is verified |
| | ④ Code review: N+1 checks, boundary conditions, magic numbers, SOLID compliance |
| | ⑤ MAX 2 retries on failure → 3rd failure: STOP, ask human |
| **Output** | Test evidence, review report (all ACs PASS) |

### Phase 6: Archive — 知识沉淀 (Knowledge Persistence)

| Item | Detail |
|------|--------|
| **Roles** | `@Knowledge Extractor`, `@Documentation Curator`, `@Skill Graph Curator` |
| **Skills** | `wal-documentation-rules`, `ac-verify` |
| **Activities** | ① Extract stable knowledge from completed task_brief |
| | ② Write **WAL fragments** into domain directories: `api/wal/`, `data/wal/`, `domain/wal/` |
| | ③ **Plan Deviation Reflection (PDD)**: Compare planned vs actual — scope drift, dependency accuracy, plan invalidations, AC coverage; write `plan_deviation.md` for significant deviations |
| | ④ Move `task_brief.md` to `wiki/archive/` (cold storage) |
| | ⑤ Dispatch next PENDING task from `launch_spec.md` if queue not empty |
| **Output** | WAL fragments (domain + api + rules; data if schema changed), plan deviation record, archived task_brief |

---

## Maintenance Workflows (Non-Code Operations)

When the user requests pure knowledge/wiki maintenance (整理, 提取, 扫描, 拆分, GC), the task routes to the **MAINTENANCE** profile — no code phases, no task_brief, no compile checks.

### WAL Compaction (GC)

**Trigger**: `@gc`, `@librarian`, or "整理 wiki", "合并碎片", "做 GC"

| Step | Action | Role |
|------|--------|------|
| ① Aggregate | `librarian_gc.py --aggregate` — collect all unmerged WAL fragments | `@Librarian` |
| ② Merge | Merge aggregated knowledge into correct domain index files | `@Librarian` |
| ③ Clean | `librarian_gc.py --clean` — delete merged fragments | `@Librarian` |
| ④ Check | If any file exceeds 500 lines → trigger Document Split | `@Knowledge Architect` |
| **Gate** | `wiki_linter.py` — no dead links | — |

### Wiki Refresh

**Trigger**: `@wiki-update`, `@milestone`, or "提取知识", "沉淀 wiki", "刷新知识库"

| Step | Action | Role |
|------|--------|------|
| ① Diff | `git diff` to identify recent changes since last update | `@Knowledge Extractor` |
| ② Extract | Extract stable knowledge into WAL fragments: [Domain], [API], [Rules] (+ [Data] if schema) | `@Knowledge Extractor` |
| ③ Write | Write fragments into `wiki/domain/wal/`, `wiki/api/wal/`, etc. | `@Knowledge Extractor` |
| **Gate** | `writeback_gate.py` (3 required sections) + `wiki_linter.py` | — |

### Document Split

**Trigger**: Any wiki file exceeds 500 lines, or "拆分文档", "index 太大"

| Step | Action | Role |
|------|--------|------|
| ① Check | Verify file exceeds 500-line limit; abort if not | `@Knowledge Architect` |
| ② Deduplicate | Remove repeated entries within the bloated file | `@Knowledge Architect` |
| ③ Split | Split into focused sub-documents by topic | `@Knowledge Architect` |
| ④ Rewrite | Rewrite original as a lean routing index with links | `@Knowledge Architect` |
| **Gate** | `wiki_linter.py` — no dead links, no file still exceeds 500 | — |

### Project Scan

**Trigger**: "扫描项目", "审计代码库", "分析代码结构"

| Step | Action | Role |
|------|--------|------|
| ① Index | `code_index.py --build` — rebuild symbol index | Explorer (inline) |
| ② Search | `wiki_search.py` — surface relevant wiki context | Explorer (inline) |
| ③ Memory | `failure_memory.py query` — surface past failures | Explorer (inline) |
| ④ Report | Produce structured scan report (directories, modules, key symbols, risks) | Explorer (inline) |

---

## Slash Commands

User-invokable shortcuts that wrap multi-step lifecycle flows into single invocations. All project commands use the `h-` prefix (harness) to avoid collision with Claude Code built-ins (`/init`, `/review`, `/security-review`, etc.). Commands live under `.claude/commands/<name>.md` and are loaded automatically — invoke as `/h-<name> [args]`.

### Intake & Planning

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-from-ticket <source> [<slug>]` | Explorer entry | Fetch GitHub/Jira/Linear ticket → `input-classifier` + `ambiguity-gatekeeper` → task_brief skeleton + launch_spec row at Explore phase | Ticket-driven development; maps ticket fields to brief sections; `ticket_ref`/`ticket_url` in frontmatter for PR auto-close |
| `/h-decompose <slug> <prd-path>` | Explorer → Propose | PRD/EPIC pre-validation → task-decomposition-guide → N brief skeletons → DAG bound to launch_spec | EPIC/PRD spanning ≥3 domains; need INVEST-compliant slicing |
| `/h-brief <slug>` | Propose entry | Schema-compliant task_brief + 1 launch_spec row | Single STANDARD task starting from a known scope |
| `/h-design [slug]` | Propose design | Dispatch system-architect with strict Source Documents contract; write ≥2 ADRs (HIGH); fill brief §8/§9 | HIGH/EPIC needs design alternatives; MEDIUM needs 1 explicit option |

### Daily Development

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-resume` | Any | Read-only: locate IN_PROGRESS task + restore Machine Section context + report Next Action; detects COLLAB-blocked state | Resuming an interrupted session |
| `/h-fix-bug [<issue-url>] [--priority p1|p2|p3]` | Explorer | GitHub issue or manual input → `failure_memory` query → `root-cause-debug` Phase 1 (MUST complete before any fix) → launch_spec row; p1/p2 triggers `h-incident` | Bug reports from QA or production; priority determines risk level and whether incident file is created |
| `/h-gates [--phase X] [--scenario Y]` | Phase boundary / pre-commit | Run all applicable gates (scope, secrets, task_brief, scenario B/C/E); record failures into failure_memory | Auditing full diff before phase transition or commit |
| `/h-archive` | Phase 6 | Plan Deviation Reflection → knowledge-extractor → archive brief → wiki_linter → mark launch_spec DONE | STANDARD task completion |

### Cross-Team Collaboration

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-collab <slug> [--type api\|process\|data\|integration\|custom]` | Between Propose and Implement | Generate structured deliverable from task_brief; type auto-inferred if omitted; creates collab state file + `COLLAB:<date>-<slug>` marker in launch_spec; external delivery is manual | Task requires external team alignment (frontend, third-party, QA, ops) before code is written |
| `/h-collab-update <slug> [--signoff] [--reviewer <name>]` | Anytime (cross-session) | Collect feedback (approved/questions/changes/blocker) → update deliverable → update collab state; `--signoff` removes COLLAB marker; BLOCKED state does not change launch_spec | After receiving external team response to a deliverable |

### Delivery

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-pr [slug]` | After QA | `secrets_linter` + `scope_guard` pre-gates → `gh pr create` with Human Section + AC checklist; PR URL written back to task_brief; launch_spec → WAITING_APPROVAL; auto-closes ticket if `ticket_url` in frontmatter | Creating a PR for a completed STANDARD task |
| `/h-ci [--run-id <id>] [--from-file <log>]` | After push | Fetch CI run data → classify failures by type/severity → `failure_memory` recording → routing recommendation (flake check / fix task / alert) | Analyzing CI failures after a push or as post-PR feedback |
| `/h-release <version> [--dry-run]` | Release | Pre-release gates (queue completeness, clean tree, release branch, secrets) → WAL changelog → `mvn versions:set` → `mvn test` → tag + push; `--dry-run` prints all intended actions without git operations | Cutting a release version |

### Production

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-incident <source> <slug>` | Anytime | Wrap `ingest_incident.py` + write structured incident `.md` from TEMPLATE; enforces `## 提醒未来 LLM` smell test | Real production fact (Sentry/Jira/oncall/post-mortem) entering memory |

Each command file is opinionated: hard step ordering, fixed STOP conditions, explicit Allowed Edit boundaries. See `.claude/commands/h-<name>.md` for the full contract per command.

---

## Daily Development Workflow

The command suite covers the full ticket-to-production loop. Each step is optional depending on the task's risk profile.

```
  [Ticket / Bug report]
        │
        ▼
  /h-from-ticket <url>          ← GitHub / Jira / Linear ticket → task_brief skeleton
  /h-fix-bug [<issue-url>]      ← Bug report → root-cause-debug → task_brief at right risk level
        │
        ▼ (STANDARD tasks)
  /h-decompose | /h-brief       ← Define scope, create task_brief
  /h-design [slug]              ← Architecture design, ADRs for HIGH risk
        │
        ▼ (if external team alignment needed)
  /h-collab <slug>              ← Generate deliverable (api/process/data/integration)
        ↕  ← share manually, then:
  /h-collab-update <slug>       ← Log feedback, apply changes, --signoff to unblock
        │
        ▼ (Implement)
  /h-resume                     ← Restore context after interruption
  /h-gates [--phase Implement]  ← Gate audit before phase transition
        │
        ▼ (Archive)
  /h-archive                    ← Plan Deviation Reflection → WAL → mark DONE
        │
        ▼ (Delivery)
  /h-pr [slug]                  ← Create PR (secrets + scope gates run first)
  /h-ci [--run-id <id>]         ← Analyze CI failures after push
        │
        ▼ (Release)
  /h-release <version>          ← Pre-release gates → changelog → tag + push
        │
        ▼ (Production)
  /h-incident <source> <slug>   ← Record real incident into failure_memory
```

**Cross-session continuity:** collab state (`runs/collabs/<date>_<slug>_collab.md`) and the `COLLAB:<slug>` marker in `launch_spec` persist across sessions. `/h-resume` detects the COLLAB marker and surfaces the pending deliverable state automatically.

---

## Execution Profiles

Every user request is classified into an **intent** and routed to a **profile**:

| Profile | Use case | Lifecycle | Write-back | Artifact |
|---------|----------|-----------|------------|----------|
| **LEARN** | Read/explain code | None | No | None |
| **PATCH** (TRIVIAL) | Typos, logging, null checks, single-domain bugfix (≤3 files, no public API/DB/auth change) | `Implement → QA → Archive` | No | None |
| **PATCH** (LOW) | Small bugfix spanning two related domains (4–6 files, still no public API/DB/auth change) | `Implement → QA → Archive` | No | None |
| **STANDARD** (MEDIUM) | Feature, new API, cross-module | Full 6-phase (no gate) | Yes (WAL) | `task_brief.md` |
| **STANDARD** (HIGH) | Core flow, DB schema, auth, breaking API | Full 6-phase + Approval Gate | Yes (WAL) | `task_brief.md` + ADR |
| **MAINTENANCE** | Wiki GC, knowledge extract, document split, project scan | Role-specific (see Maintenance Workflows) | Yes (WAL/merged) | WAL fragments, merged indexes, scan report |

---

## Key Mechanisms

| Mechanism | What It Does |
|-----------|-------------|
| **Behavioral Principles** | Four cross-cutting LLM rules in `CLAUDE.md` (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) — applied to every turn before mode/profile selection |
| **Context Funnel** | Structured navigation from root index → domain index → specific document; prevents blind searching |
| **Dependency Graph (DAG)** | Tasks declare upstream dependencies in `launch_spec.md`; dispatch is gated on dependency satisfaction |
| **Scope Guard** | Enforces that code changes stay within declared Allowed Scope |
| **Shift-Left Hook** | Runs compile after every code change; max 2 retries before human escalation |
| **Secrets Lint** | Scans changed files for secrets after every edit |
| **Plan Review Checklist** | Completeness, Consistency, Feasibility, Risk Coverage, Dependency Soundness — must pass before exiting Review (≥3 tasks) |
| **Plan Deviation Reflection** | Compare planned vs actual at Archive — scope drift, dependency accuracy, AC coverage |
| **Hook System** | pre_hook (phase entry), guard_hook (during edit), shift_left_hook (after edit), post_hook (phase exit), fail_hook (rollback), loop_hook (queue loop) |
| **Local Intelligence** | BM25 wiki search, Java symbol index, failure memory — zero-cost context before file navigation |
| **Gate Scripts** | Deterministic Python scripts that block or warn on quality/security/compliance issues |

---

## Quick Start

1. **Read [CLAUDE.md](CLAUDE.md)** — the single entry point.
2. The AI assistant will classify your request and route it to the correct profile.
3. For STANDARD tasks, the framework creates a `launch_spec.md` with task dependency graph and a `task_brief.md` as the shared contract between you and the assistant.
4. For HIGH risk changes, you will be asked for explicit approval before code is written.
5. After implementation, plan deviation is measured (PDD) and completed tasks have their knowledge extracted into the wiki for future sessions.

---

## Related Documentation

- [CLAUDE.md](CLAUDE.md) — project entry point
- [README_zh.md](README_zh.md) — Chinese version
- [.claude/workflow/EXAMPLES.md](.claude/workflow/EXAMPLES.md) — walkthrough of a STANDARD task
- [.claude/wiki/KNOWLEDGE_GRAPH.md](.claude/wiki/KNOWLEDGE_GRAPH.md) — knowledge graph root
- [.claude/skills/skill-index/SKILL.md](.claude/skills/skill-index/SKILL.md) — skill navigator
- [.claude/wiki/purpose.md](.claude/wiki/purpose.md) — design philosophy
