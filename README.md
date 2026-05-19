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
├── rules/                     # Routing, lifecycle, dispatch, hooks, safety, write-back
│   ├── routing.md             # Profiles, risk classification, special scenarios, shortcuts
│   ├── lifecycle.md           # Phase details (Explorer → Propose → Review → Implement → QA → Archive)
│   ├── dispatch.md            # Agent invocation (inline role adoption vs sub-agent dispatch) + handoff
│   ├── hooks.md               # Per-phase gate checklist; settings.json defines auto-fired hooks
│   ├── safety-constraints.md  # Hard constraints, commit policy
│   └── writeback-policy.md    # WAL fragment write-back, anti-bloat rules
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
├── skills/                          # 29 skills auto-loaded by Claude Code on every session
│   ├── skill-index/                 # Central navigator (active set + archive references)
│   ├── adversarial-review/          # One-round isolated critique (HIGH-risk Review)
│   ├── ai-slop-cleaner/             # Regression-safe cleanup: dead code, duplicates, over-abstraction
│   ├── architecture-decision-records/ # Capture architectural decisions as structured ADRs
│   ├── brainstorming/               # Explore idea/requirement into design with ADR-format alternatives
│   ├── code-review-checklist/       # Mandatory pre-delivery code review against all project standards
│   ├── cognitive-bias-checklist/    # Prevent hallucinations and overconfidence during design decisions
│   ├── decision-frameworks/         # SWOT, 5-Why, First Principles for root cause and architecture selection
│   ├── java-architecture-standards/ # Mandatory: 3-Layer arch, API design, POJO, anti-JOIN, error codes
│   ├── java-coding-style/           # Mandatory: Checkstyle, Javadoc, utility class boundaries, functional patterns
│   ├── java-testing-standards/      # Mandatory: test isolation, mock guidelines, 3-scenario coverage rule
│   ├── linter-severity-standard/    # FAIL/WARN/IGNORE severity rubric for gate scripts
│   ├── local-code-intelligence/     # Zero-cost local tools: BM25 wiki search, symbol index, failure memory
│   ├── mybatis-sql-standard/        # Anti-JOIN, index utilization, implicit type conversion prevention
│   ├── product-manager-expert/      # PRD generation and PRD ingestion → technical requirements + AC
│   ├── remember/                    # Classify discovered knowledge into correct persistence layer
│   ├── requirement-intake/          # Normalize raw input (PRD, idea, bug) into structured intent+scope+AC
│   ├── security-review-checklist/   # Secrets, authZ, IDOR, data exposure, dependency safety checklist
│   ├── skill-creator/               # Create or update SKILL.md for repeatable workflows
│   ├── skill-graph-manager/         # Mandatory: maintain bidirectional Skill Knowledge Graph
│   ├── spec-quality-checklist/      # Self-correction gate for AI-generated docs before Python gate scripts
│   ├── stakeholder-conflict-resolver/ # Detect and resolve mutually exclusive stakeholder requirements
│   ├── systematic-debugging/        # Mandatory root-cause investigation before any fix
│   ├── task-decomposition-guide/    # Decompose large PRDs/EPICs via INVEST criteria and Vertical Slicing
│   ├── test-driven-development/     # Write failing tests from ACs before implementation
│   ├── ultraqa/                     # Structured QA loop with Evidence Mapping Table (AC ↔ Test ↔ Result)
│   ├── verify/                      # End-to-end AC verification with pass/fail evidence before Archive
│   ├── wal-documentation-rules/     # Mandatory: extract stable knowledge into WAL fragments at Archive
│   └── writing-plans/               # Decompose spec into checkpoint-driven implementation plan
├── skills-archive/                  # 12 lower-frequency skills — NOT auto-loaded; referenced inline by the rule/agent that needs them
│   ├── ai-pipeline/                 # Full AI engineering pipeline orchestrator (Scenario PIPELINE)
│   ├── blueprint/                   # Multi-session, multi-agent construction plan (Scenario EPIC)
│   ├── deepinit/                    # New-repo deep init: hierarchical CLAUDE.md (Scenario GREENFIELD)
│   ├── dispatching-parallel-agents/ # Parallel sub-agent dispatch (Scenario EPIC)
│   ├── eval-harness/                # Formal AC eval / pass@k benchmarks (Scenario PIPELINE)
│   ├── external-research/           # CVE / compliance / plateau research (Scenarios D, PIPELINE)
│   ├── greenfield-scaffold/         # From-scratch protocol (Scenario GREENFIELD)
│   ├── incident-response/           # Production triage + post-mortem (Scenario A)
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
| **Roles** | `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard` |
| **Skills** | `requirement-intake`, `brainstorming`, `product-manager-expert`, `task-decomposition-guide` |
| **Activities** | ① Classify input via intent signal matrix → determine risk level (TRIVIAL/LOW/MEDIUM/HIGH) |
| | ② **Specification Inference**: `Current: [X]. Required: [Y]. Delta: [Z]` — the gap is the true scope |
| | ③ **BDD — AC-as-Tests Translation (MUST)** : convert every requirement to `Given [precondition], when [action], then [observable, measurable result]` — vague language ("handle correctly", "work properly") is BLOCKED |
| | ④ Impact analysis: `code_index.py --impact-of <target>` → identify hidden dependencies |
| | ⑤ Adversarial review Category A (HIGH only): "are we solving the right problem?" |
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
| **Skills** | `test-driven-development`, `java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `writing-plans` |
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
| **Skills** | `wal-documentation-rules`, `verify` |
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
