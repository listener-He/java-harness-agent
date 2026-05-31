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
├── rules/                     # Routing, lifecycle, hooks, dispatch, safety, write-back, skill precedence, TaskList
│   ├── lifecycle.md           # Profiles + risk classification + phase details (Explorer → Propose → Review → Implement → QA → Archive) + per-phase gates and hooks (force-loaded via `@` import in CLAUDE.md)
│   ├── policy.md              # Hard constraints + commit policy + WAL write-back + agent dispatch (inline role adoption vs sub-agent)
│   ├── dispatch-template.md   # Canonical sub-agent prompt skeleton (mandatory for every dispatch)
│   ├── skill-precedence.md    # Conflict resolution when multiple MANDATORY skills target the same trigger window
│   └── tasklist-policy.md     # When to open Claude Code's built-in TaskList (whitelist: EPIC sub-tasks / AC ≥ 4 / Approval Gate / Emergency Hotfix audit anchors)
├── agents/                    # 14 agents — each .md has Claude Code frontmatter (name/description/tools/model) and is invokable via the Agent tool
│   ├── ambiguity-gatekeeper.md   # GATE on ambiguous input — enforce definition-of-ready (clear scope + testable outcome + explicit AC) before AC transcription. Returns [Status]: PASS|FAIL; FAIL carries [Must-Ask Questions]. Phase: Phase 1 Step B (Idea/Feedback/Compliance/Security).
│   ├── requirement-engineer.md   # Translate raw Idea/Feedback/Compliance/Security input → testable Given/When/Then ACs + structured Must-Ask question list. Does NOT call AskUserQuestion (no such tool on sub-agents). Phase: Phase 1 Explorer.
│   ├── system-architect.md       # Design system architecture BEFORE any code — high-level interactions, schema, API contracts, irreversible decisions captured as ADRs. Acts as Foreman in EPIC (slices large work into INVEST micro-tasks). Phase: Phase 2 Propose (HIGH risk / Scenario EPIC / GREENFIELD / B2).
│   ├── triage-reviewer.md        # ★ NEW (T9): semantic second-opinion sub-agent (Haiku) for prompts where keyword-based evidence is ambiguous on a HIGH-sensitivity surface. EXPLICIT dispatch only — main agent decides when to call. Returns [Semantic Review] {refined_hint, reason, confidence}.
│   ├── lead-engineer.md          # Implement per task_brief Machine Section — translate Allowed Scope + ACs + Hard Constraints into compilable Java/Maven changes following TDD (RED→GREEN→REFACTOR). Main agent prefers inline for MEDIUM with AC ≤ 3 + single domain. Phase: Phase 4 Implement.
│   ├── java-build-resolver.md    # Diagnose Java/Maven build failures (mvn compile / test-compile / javac). Returns [Root Cause] + [Suggested Fix] block; main agent applies the fix and re-runs (max 2 dispatches per same root cause). Model: haiku. Phase: Phase 4 on compile failure.
│   ├── test-runner.md            # Run JUnit/Surefire tests scoped to changed modules, parse output, return AC-id → test method → PASS|FAIL|SKIP mapping + minimal failure excerpts. Does NOT modify code. Model: haiku. Phase: Phase 5 QA when AC ≥ 4 OR risk = HIGH.
│   ├── database-reviewer.md      # Review MyBatis mapper XML / *Mapper.java / migration SQL against mybatis-sql-standard (anti-JOIN, ${} injection, audit columns, leftmost-prefix, N+1, manual tenant_id filter). HIGH/MEDIUM findings block Archive. Phase: Phase 5 QA when mapper/SQL changes.
│   ├── code-reviewer.md          # Review newly written code (diff) for correctness, performance, security, maintainability — fresh-context inspection in isolated sub-agent. NOT for design review (use system-architect) or SQL review (use database-reviewer). Phase: after Phase 4 Implement, MEDIUM/HIGH STANDARD.
│   ├── security-sentinel.md      # Scan for secret leakage + authorization-bypass risks via deterministic scripts. Pure tool runner — no subjective security review. HIGH-confidence hit BLOCKS Archive. Phase: QA → Archive gate + Scenario A (Emergency Hotfix).
│   ├── knowledge-extractor.md    # Extract stable knowledge from completed code changes into WAL fragments. Writes ONLY user-elected dimensions (Domain/API/Rules/Data/Architecture) via h-archive Step 3b. Model: haiku. Phase: Phase 6 Archive.
│   ├── documentation-curator.md  # Author documentation grounded in real source — README, API/Javadoc, migration guide, runbook, ADR explainer, capabilities matrix. Every claim traceable to a file path or commit. Model: haiku. Phase: on user request ("write docs", "draft README", capabilities matrix).
│   ├── librarian.md              # Maintain wiki health: **Compact** (merge WAL fragments into stable indexes + GC) and **Distill** (scan + plan + human-approved deletion). Phase: Maintenance (user requests wiki consolidation / stale-knowledge cleanup).
│   └── knowledge-architect.md    # Split oversized wiki index files (> 3000 lines per wiki_linter.py cap) into focused sub-documents + rewrite original as a lean routing graph. Phase: Maintenance (triggered by linter overflow).
├── commands/                    # 24 user-invokable slash commands (h- prefix, avoid Claude Code built-in collision)
│   ├── h-help.md                # ★ NEW (T10/R5): scenario-driven catalog of all /h-* commands grouped by use case (new work / in-progress / debugging / delivery / knowledge / collaboration). Onboarding entry.
│   ├── h-from-ticket.md         # GitHub/Jira/Linear ticket → task_brief skeleton + launch_spec row (runs ambiguity-gatekeeper + input-classifier)
│   ├── h-decompose.md           # PRD/EPIC pre-validation → task-decomposition-guide → N brief skeletons → DAG bound to launch_spec
│   ├── h-brief.md               # Schema-compliant task_brief + bidirectional launch_spec binding
│   ├── h-design.md              # Dispatch system-architect with strict Source Documents → write ≥2 ADRs (HIGH) → fill brief §8/§9
│   ├── h-research.md            # Scaffold RESEARCH profile report skeleton (7 sections per schema); --scope quick|deep drives §3 findings quota; bind launch_spec at RES/Research/IN_PROGRESS
│   ├── h-context-check.md       # ★ NEW (P6): pull-model context probe — recent events + recurring failures + active task + dirty diff + active insights. Replaces the pre-P2 [triage-evidence]/[failure-memory] auto-injection that was push-modeled.
│   ├── h-resume.md              # Read-only: locate IN_PROGRESS task + restore Machine Section + report Next Action
│   ├── h-status.md              # Global queue snapshot — list all launch_spec rows (PENDING/IN_PROGRESS/WAITING_APPROVAL/DONE/FAILED) with parallelizable next steps
│   ├── h-fix-bug.md             # Ticket/manual → root-cause-debug Phase 1 (MUST complete) → launch_spec row at correct risk level; p1/p2 triggers h-incident
│   ├── h-gates.md               # Phase/scenario-aware gate suite + failure_memory recording (post-P3: scope_guard / migration / dependency moved HERE from per-edit hook)
│   ├── h-archive.md             # Plan Deviation Reflection → knowledge-extractor → archive brief → wiki_linter → mark DONE
│   ├── h-collab.md              # Generate cross-team deliverable (api/process/data/integration/custom) + collab state file + COLLAB marker in launch_spec
│   ├── h-collab-update.md       # Log external feedback → update deliverable → --signoff removes COLLAB marker; BLOCKED state recorded only
│   ├── h-evolve.md              # ★ NEW (P7): turn a high-confidence insight → concrete rule-change proposal. 5 per-kind templates (gate refinement / wiki scope template / archive / threshold loosening / behavior review). --apply requires AskUserQuestion Yes.
│   ├── h-publish-insight.md     # ★ NEW (R1): manually bridge local insight → git-tracked team knowledge doc under .claude/wiki/insights/<date>_<id>_<slug>.md. Solves "learning is single-machine local" pain. NEVER auto-fires.
│   ├── h-pr.md                  # secrets_linter + scope_guard → gh pr create → write PR URL into task_brief; launch_spec stays IN_PROGRESS with `| PR #<n>` Artifact marker
│   ├── h-test-handoff.md        # Generate QA-team handoff doc from a code change or bug fix — reproduction steps, impact scope, recommended test scope, rollback, open questions
│   ├── h-ci.md                  # Fetch CI run data → classify failures (compile/test/security/coverage) → failure_memory + routing recommendation
│   ├── h-release.md             # Pre-release gates (queue/tree/branch/secrets) → WAL changelog → mvn versions:set → tag + push; --dry-run supported
│   ├── h-distill.md             # Wiki cleanup — librarian scan → user-approved plan → execute deletions/merges
│   ├── h-distill-from-code.md   # Reconcile wiki claims against current code (bounded scope, not WAL flow)
│   ├── h-reflect.md             # Session reflection — multi-select lessons (incident/wiki/failure/success/memory) → reset session_stats counters
│   └── h-incident.md            # Wrap ingest_incident.py + write incident .md from TEMPLATE (enforces the "Reminder for Future LLM" smell test)
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
│   ├── schema/                # Contract templates (task_brief, subagent_contract, research_report)
│   ├── incidents/             # Production incident records (committed; surfaced by incident_hint)
│   ├── insights/              # ★ NEW (R1): team-published insights (via /h-publish-insight). Bridges local Insight Layer → team knowledge
│   ├── archive/               # Completed task_briefs + research reports (cold storage)
│   └── wiki/                  # Domain, API, Data, Architecture, Specs, Testing, Reviews, Preferences
├── scripts/
│   ├── gates/                                  # 21 deterministic gate scripts (block / warn / pass)
│   │   ├── _severity.py                        # Severity classification helper (internal)
│   │   ├── _severity_audit.py                  # Severity output audit harness
│   │   ├── ambiguity_gate.py                   # Input-ambiguity probe (UserPromptSubmit hook)
│   │   ├── api_breaking_gate.py                # Public API breaking-change check (Scenario C)
│   │   ├── bypass_audit_gate.py                # Audit attempts to bypass safety (--no-verify, etc.)
│   │   ├── comment_linter_java.py              # Java comment-style enforcement
│   │   ├── consistency_gate.py                 # Cross-file consistency check
│   │   ├── delivery_capsule_gate.py            # Delivery package validation
│   │   ├── dependency_gate.py                  # pom.xml dependency check (Scenario E)
│   │   ├── impact_gate.py                      # Change blast-radius assessment
│   │   ├── linter.py                           # Generic linter runner
│   │   ├── migration_gate.py                   # SQL migration check (Scenario B1/B2)
│   │   ├── research_report_gate.py             # research_report.md validation (Phase R3 gate)
│   │   ├── run.py                              # Gate suite runner
│   │   ├── scope_guard.py                      # Allowed-Scope enforcement (PreToolUse hook + /h-gates)
│   │   ├── secrets_linter.py                   # Secret-leak scan (PostToolUse hook + pre-PR + pre-release)
│   │   ├── skill_index_linter.py               # SKILL.md index consistency check
│   │   ├── subagent_return_gate.py             # Validate sub-agent structured-return format
│   │   ├── task_brief_gate.py                  # task_brief.md structural validation (Propose→Implement)
│   │   ├── wal_template_gate.py                # WAL fragment template compliance
│   │   └── writeback_gate.py                   # Archive WAL presence check (supports --accept-stub for None)
│   ├── harness/                                # 11 runtime entry points (Claude Code hooks + engine) — all hooks post-P2 are pure sensors except pre_tool_use (secrets-only block)
│   │   ├── engine.py                           # Central runtime: gate dispatch + severity aggregation
│   │   ├── find_active_task_brief.py           # Locate active task_brief from launch_spec IN_PROGRESS row
│   │   ├── pre_tool_use_hook.py                # PreToolUse[Edit|Write]: ONLY secrets_linter --content-stdin (blocks on HIGH-conf secret). Scope_guard moved to /h-gates. CLAUDE_SECRETS_BYPASS=1 emergency override.
│   │   ├── post_tool_use_hook.py               # PostToolUse[Edit|Write]: pure sensor — emit edit_post event + bump session_stats. (Pre-P2 was 5 parallel subprocesses; now in-process.)
│   │   ├── post_read_hook.py                   # PostToolUse[Read]: usage_tracker bump on .claude/wiki/** + .claude/skills/** + emit read event
│   │   ├── user_prompt_submit_hook.py          # UserPromptSubmit: pure sensor — emit prompt event (+ user_correction event when prompt opens with correction/frustration phrase). NO inline context push (post-P2).
│   │   ├── subagent_stop_hook.py               # SubagentStop: extract last-assistant text (3-shape transcript aware) + emit subagent_return event. Gate validation moved to /h-gates.
│   │   ├── stop_hook.py                        # Stop: emit turn_end event + throttled [insight-reminder] (high-conf insight set changed) + [scope-check-reminder] (dirty count > 5)
│   │   ├── notification_hook.py                # ★ NEW (#4): append notifications.jsonl + opt-in macOS bell via CLAUDE_NOTIFY_SOUND=1
│   │   ├── pre_compact_hook.py                 # ★ NEW (#4): snapshot active task_brief / launch_spec rows / HEAD / commits to last_compact_snapshot.json (retention 20) + inject [pre-compact-snapshot] recovery hint
│   │   └── test_subagent_stop_hook.py          # ★ NEW (c64f69c): 12-case regression test for SubagentStop payload extraction across 3 transcript shapes (run after Claude Code upgrades)
│   ├── local_intel/                            # 15 zero-cost local intelligence tools
│   │   ├── code_index.py                       # Java symbol index + --impact-of caller enumeration
│   │   ├── failure_memory.py                   # Gate failure ledger (query / record / summary). Post-T7: rotation when > 5MB OR oldest > 90d
│   │   ├── session_stats.py                    # Per-session counters (edits / failures) feeding /h-reflect threshold
│   │   ├── reflect_threshold.py                # /h-reflect threshold heuristic (queried, not auto-fired)
│   │   ├── incident_hint.py                    # Per-path incident lookup (on-demand, post-P2 not auto-pushed)
│   │   ├── ingest_incident.py                  # Incident raw-fact ingestion + emit template prompt
│   │   ├── skill_hint.py                       # Per-path SKILL.md anti-pattern hint (on-demand)
│   │   ├── triage_probe.py                     # Evidence collector: 5 signals (blast/failure/ambiguity/keywords/intent) + 1 advisory profile_hint. Post-P2 is an explicit CLI tool, NOT auto-injected.
│   │   ├── usage_tracker.py                    # .claude/wiki/** and .claude/skills/** file-access counters (ghost fragment detection for distill)
│   │   ├── turn_health_check.py                # Per-turn observability (uncompiled / drift / dirty-pile)
│   │   ├── wiki_search.py                      # BM25 search over .claude/wiki/
│   │   ├── event_writer.py                     # ★ NEW (P1): single append(kind, **fields) API for events.jsonl (Sensor layer L1 — events.jsonl@10MB rotate)
│   │   ├── events_query.py                     # ★ NEW (P1): events.jsonl query CLI — --kind / --file / --since / --last / --aggregate-by-{kind,file} / --json
│   │   ├── insight_writer.py                   # ★ NEW (P7): insights.jsonl writer (Insight Layer L2 — append + dedup by kind+summary hash + mark_status + query_active)
│   │   └── insight_detector.py                 # ★ NEW (P7+T8+T9): 5 pure-function detectors — recurring_failure_cluster / co_edit_cluster (age filter + union-find dedup) / decayed_knowledge / override_drift / user_correction (prior_actions bound)
│   ├── tools/                                  # 6 helper scripts (one-shot operations)
│   │   ├── archive_session_artifacts.py        # Move task_brief from runs/ to wiki/archive/
│   │   ├── bootstrap.py                        # First-time project bootstrap
│   │   ├── brief_from_decomposition.py         # Generate per-subtask brief skeletons from decomposition
│   │   ├── import_external_skills.py           # Import skills from an external source
│   │   └── librarian_gc.py                     # Wiki GC orchestrator (called by `librarian` Compact flow)
│   └── wiki/                                   # 9 wiki maintenance scripts
│       ├── compactor.py                        # Merge WAL fragments into main wiki
│       ├── distill_threshold.py                # Compute staleness threshold for distill
│       ├── distill.py                          # Extract + delete stale or duplicate knowledge files
│       ├── graph_checker.py                    # Knowledge graph link integrity
│       ├── pref_tag_checker.py                 # Preference tag consistency
│       ├── schema_checker.py                   # Schema validation for wiki documents
│       ├── wiki_compactor.py                   # Wiki-level compaction orchestrator
│       ├── wiki_linter.py                      # Wiki health (dead links, overlength caps, islands)
│       └── zero_residue_audit.py               # Audit zero-residue cleanups (after distill)
├── workflow/
│   ├── agent_matrix.json      # Agent-to-phase mount table
│   ├── EXAMPLES.md            # Walkthrough of a STANDARD task
│   └── artifacts/             # Artifact templates
├── runs/                      # Runtime artifacts — MUST be git-ignored
│   ├── launch-specs/                          # Per-day task queue (launch_spec_*.md)
│   ├── task-briefs/                           # Active per-task contracts (moved to wiki/archive on Archive)
│   ├── collabs/                               # Cross-team deliverable state files (paired with COLLAB launch_spec marker)
│   ├── reports/                               # Active research_report drafts (moved to wiki/archive on Archive)
│   ├── qa-handoffs/                           # /h-test-handoff outputs
│   ├── cache/                                 # local_intel caches (code_index, wiki BM25)
│   └── local_intel/                           # ★ Sensor layer sidecars (post-P1 + P7 added)
│       ├── events.jsonl                       # Unified event stream — schema in .claude/wiki/wiki/architecture/events_jsonl_schema.md
│       ├── insights.jsonl                     # ★ NEW (P7): pattern-recognition outputs — schema insights_layer_schema.md
│       ├── failure_memory.json                # Gate failure ledger
│       ├── notifications.jsonl                # ★ NEW (#4): Claude Code UI notification log
│       ├── last_compact_snapshot.json         # ★ NEW (#4): most recent PreCompact snapshot
│       ├── compact_snapshots/                 # ★ NEW (#4): 20-retention PreCompact history
│       ├── last_reminders.json                # ★ NEW (T10): throttle state for [insight-reminder] + [scope-check-reminder]
│       └── .usage/                            # ★ Per-file read counters (post_read_hook → ghost fragment detection)
└── settings.json              # Permissions and hooks configuration (8 hook events registered)
```

> ⚠️ **Git-ignore requirement — `.claude/runs/`**
>
> The `.claude/runs/` directory holds **per-session runtime workspace**: active `task_brief.md` files, `launch_spec_*.md` task queues, distill plans, research drafts, and `local_intel` cache indexes (BM25, code-index, failure-memory). These are ephemeral, machine-specific, and frequently rewritten by hooks — they MUST NEVER be committed.
>
> This repository's `.gitignore` already lists:
> ```gitignore
> ### Runtime artifacts (not committed) ###
> .claude/runs/
> ```
>
> When you fork this repo or copy the framework into a new project, **verify your `.gitignore` keeps that line**. Committed `runs/` artifacts cause: cross-machine state pollution, leaked PII from local sessions, and merge conflicts on every `task_brief.md` edit.
>
> Archive flow: completed task briefs are moved (via `archive_session_artifacts.py`) from `.claude/runs/task-briefs/` into `.claude/wiki/archive/`, which **is** committed. Only the archived snapshot enters git history; the active workspace never does.

---

## Architecture — 4-Layer Sensor / Insight / Policy / Enforce

As of P2–P7 (refactor commits in May–June 2026), the harness is organized as four cleanly separated layers. Each layer has a single responsibility and is owned by a specific kind of artifact.

```
┌───────────────────────────────────────────────────────────────────────────┐
│ L1 SENSOR     hooks → events.jsonl + failure_memory + usage_tracker        │
│                pure observation; all 8 Claude Code hooks emit events only  │
│                (silent stdout, no inline context push); cost ~30-70ms/hook │
├───────────────────────────────────────────────────────────────────────────┤
│ L2 INSIGHT    insight_detector → insights.jsonl                            │
│                5 pure-function detectors over Sensor data:                 │
│                  • recurring_failure_cluster                               │
│                  • co_edit_cluster      (24h age filter + union-find dedup)│
│                  • decayed_knowledge    (incidents + usage_tracker)        │
│                  • override_drift       (env_bypass events)                │
│                  • user_correction      (prior_actions_5min bound)         │
├───────────────────────────────────────────────────────────────────────────┤
│ L3 POLICY     agent + /h-context-check + /h-evolve + /h-publish-insight    │
│                on-demand pull: agent reads Sensor + Insight when it needs  │
│                context; decides profile / scope / next action              │
├───────────────────────────────────────────────────────────────────────────┤
│ L4 ENFORCE    PreToolUse secrets pre-check + /h-gates --phase ...          │
│                THE ONLY blocking layer; 1 hook (secrets, irreversible      │
│                red line) + agent-invoked phase-boundary gate suite         │
└───────────────────────────────────────────────────────────────────────────┘
```

**Design rules** (the "thou shalt nots"):

- L1 Sensor hooks NEVER block, NEVER inject inline context (except PreToolUse secrets → exit 2 on HIGH-confidence pattern, the single carved-out red line)
- L2 Insight detector NEVER modifies configuration files; produces insights only — humans/agents act on them via /h-evolve (rule change) or /h-publish-insight (team knowledge share)
- L3 Policy is the agent + slash commands — the "smart" layer that combines pulled evidence with conversation context to decide
- L4 Enforce phase-boundary gates fire when the agent explicitly invokes /h-gates --phase <implement|qa|archive>, NOT per-edit

**Why the pull model** (post-P2 design):

| Before P2 | After P2 |
|---|---|
| Hooks pushed 4 context blocks per prompt ([failure-memory] / [triage-evidence] / [ambiguity] / [wiki-distill]) | Hooks emit events to events.jsonl; agent pulls via /h-context-check |
| ~310ms UserPromptSubmit + ~330ms PostToolUse per Edit | ~60ms + ~70ms |
| 100-500 tokens injected per prompt → cache miss | 0 tokens by default → cache stays warm |
| Scope_guard fired per-edit (interrupted mid-flow refactors) | Scope_guard runs at /h-gates --phase implement (phase-boundary) |
| Recurring failures pushed on every prompt regardless of relevance | Agent decides when to query failure_memory |

**Single push-back exception** (minimal, throttled, only when actionable): stop_hook emits one-line `[insight-reminder]` when active high-confidence insight SET changes, plus `[scope-check-reminder]` when dirty files > 5. Both throttled via `last_reminders.json`.

---

## Workflow Process (STANDARD)

The STANDARD lifecycle implements a **PDD → BDD → SDD/SPEC → TDD → BDD** closed loop:

- **PDD (Plan-Driven Development)** at the front: task dependencies, parallelism constraints, and success metrics are declared before any code exists
- **BDD (Behavior-Driven Development)** at both ends: Explorer writes executable specs in `Given/When/Then` format; QA verifies behavior against those same specs
- **SDD/SPEC (Specification-Driven Development)** throughout: every phase is anchored to the `task_brief.md` contract
- **TDD (Test-Driven Development)** at the core: failing tests derived from ACs drive implementation

```
         ┌── PDD ──┐  ┌──── BDD ────┐                                     ┌──── BDD ────┐
         │deps+par  │  │ exec spec    │                                     │ behavior     │
         │ DAG      │  │ Given/When/  │    ┌── SDD (contract-driven) ──┐    │ AC↔test↔result│
         ▼          ▼  ▼              ▼    ▼                            ▼   ▼              ▼
Input ─→ Explorer ─→ Propose ─→ Review ─→ [Approval] ─→ Implement ─→ QA ─→ Archive
          │              │          │                        │          │        │
        Req. clarify  Arch. design  Design review        TDD impl    Test verify  Knowledge
          │              │          │                        │          │        │
          ▼              ▼          ▼    ▼                  ▼          ▼        ▼
       Spec Gap     task_brief  Plan   Approved        Red→Green   Evidence   WAL
       + AC list    +deps+par   Review Contract         →Refactor   Mapping    +Deviation
```

### Phase 1: Explorer — Requirement Clarification + BDD Spec Writing

| Item | Detail |
|------|--------|
| **Roles** | `ambiguity-gatekeeper` (pre-gate), `requirement-engineer`, `system-architect` (Propose) |
| **Skills** | `input-classifier`, `brainstorming`, `product-manager-expert`, `task-decomposition-guide` |
| **Activities** | ① `input-classifier` inline: classify raw input → emit `[Intake]` block with `Input-Type` and `Route` |
| | ② **Idea/Feedback/Compliance/Security inputs**: dispatch `ambiguity-gatekeeper` first — FAIL blocks until input is tightened; PASS → dispatch `requirement-engineer` |
| | ③ **Specification Inference**: `Current: [X]. Required: [Y]. Delta: [Z]` — the gap is the true scope |
| | ④ **BDD — AC-as-Tests Translation (MUST)**: convert every requirement to `Given [precondition], when [action], then [observable, measurable result]` — vague language ("handle correctly", "work properly") is BLOCKED |
| | ⑤ Impact analysis: `code_index.py --impact-of <target>` → identify hidden dependencies |
| | ⑥ Adversarial review Category A (HIGH only): "are we solving the right problem?" |
| **Output** | Spec Gap + AC list (Given/When/Then) + Hidden Scope → feeds into task_brief Machine Section |

### Phase 2: Propose — Architecture Design & Specification

| Item | Detail |
|------|--------|
| **Roles** | `system-architect` |
| **Skills** | `brainstorming`, `java-architecture-standards`, `task-decomposition-guide`, `decision-frameworks`, `cognitive-bias-checklist` |
| **Activities** | ① **PDD — Plan as First-Class Artifact**: Declare task dependencies, draw dependency graph (DAG) when ≥3 tasks; set parallelism constraints (soft limit: 3) |
| | ② Generate ≥2 design alternatives (HIGH: ADR format with Pros/Cons/Failure Conditions) |
| | ③ Select approach → emit **Constraint List** (binding decisions for all downstream work) |
| | ④ Define **Allowed Scope** — explicit file whitelist that constrains implementation |
| | ⑤ Write `task_brief.md` — the **universal contract**: |
| | &nbsp;&nbsp;&nbsp; • Machine Section (English): Allowed Scope + ACs + Task Dependencies + Hard Constraints |
| | &nbsp;&nbsp;&nbsp; • Human Section (written in Chinese): WHAT / WHY + HOW + open items pending confirmation |
| **Output** | `task_brief.md` — single artifact shared by all agents and humans |

### Phase 3: Review — Design Review

| Item | Detail |
|------|--------|
| **Roles** | `system-architect` |
| **Skills** | `code-review-checklist`, `java-architecture-standards`, `adversarial-review` (HIGH), `spec-quality-checklist` |
| **Activities** | ① Review design against project standards and architecture constraints |
| | ② **Plan Review Checklist (PDD)**: Completeness → Consistency → Feasibility → Risk Coverage → Dependency Soundness (≥3 tasks) |
| | ③ Adversarial critique Category B (HIGH only): "are we solving it the right way?" — ONE round |
| | ④ **Approval Gate** (HIGH only): present Human Section in business language → wait for explicit sign-off |
| | ⑤ CRITICAL finding → rollback to Phase 2. MINOR → annotate ACs, proceed |
| **Output** | Approved `task_brief.md` (HIGH) or FYI summary (MEDIUM) |

### Phase 4: Implement — TDD-Driven Implementation

| Item | Detail |
|------|--------|
| **Roles** | `lead-engineer` (scope_guard.py PreToolUse hook enforces Allowed Scope) |
| **Skills** | `test-driven-development`, `java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `impl-plan` |
| **Activities** | ① Read `task_brief.md` Machine Section — Allowed Scope + ACs + Hard Constraints |
| | ② **RED**: Write failing tests derived from ACs (must see test failure before writing code) |
| | ③ **GREEN**: Implement within Allowed Scope — `scope_guard.py` enforces boundary |
| | ④ **REFACTOR**: Apply coding style, extract magic numbers, ensure SOLID compliance |
| | ⑤ Shift-left: `mvn compile` + `secrets_linter.py` after every change (max 2 retries) |
| | ⑥ **YIELD**: Stop and ask human for permission to proceed to QA |
| **Output** | Modified source files, passing tests, compile-clean |

### Phase 5: QA — Test Verification + BDD Behavior Validation

| Item | Detail |
|------|--------|
| **Roles** | `code-reviewer` |
| **Skills** | `java-testing-standards`, `code-review-checklist`, `ultraqa`, `security-review-checklist` (HIGH) |
| **Activities** | ① Ensure compile is clean (`shift_left_hook`) |
| | ② Run test suite → verify all ACs pass |
| | ③ **BDD — Evidence Mapping Table** (AC ≥ 4 or HIGH risk): every Given/When/Then AC mapped to test method → expect → actual → status — ensures every behavior declared in Phase 1 is verified |
| | ④ Code review: N+1 checks, boundary conditions, magic numbers, SOLID compliance |
| | ⑤ MAX 2 retries on failure → 3rd failure: STOP, ask human |
| **Output** | Test evidence, review report (all ACs PASS) |

### Phase 6: Archive — Knowledge Persistence

| Item | Detail |
|------|--------|
| **Roles** | `knowledge-extractor`, `documentation-curator` |
| **Skills** | `wal-documentation-rules`, `ac-verify` |
| **Activities** | ① Extract stable knowledge from completed task_brief |
| | ② Write **WAL fragments** into domain directories: `api/wal/`, `data/wal/`, `domain/wal/` |
| | ③ **Plan Deviation Reflection (PDD)**: Compare planned vs actual — scope drift, dependency accuracy, plan invalidations, AC coverage; write `plan_deviation.md` for significant deviations |
| | ④ Move `task_brief.md` to `wiki/archive/` (cold storage) |
| | ⑤ Dispatch next PENDING task from `launch_spec.md` if queue not empty |
| **Output** | WAL fragments (domain + api + rules; data if schema changed), plan deviation record, archived task_brief |

---

## Maintenance Workflows (Non-Code Operations)

When the user requests pure knowledge/wiki maintenance (compact, extract, scan, split, GC), the task routes to the **MAINTENANCE** profile — no code phases, no task_brief, no compile checks.

### WAL Compaction (GC)

**Trigger**: phrases like "compact wiki", "merge fragments", "run GC", "wiki consolidation"

| Step | Action | Role |
|------|--------|------|
| ① Aggregate | `librarian_gc.py --aggregate` — collect all unmerged WAL fragments | `librarian` |
| ② Merge | Merge aggregated knowledge into correct domain index files | `librarian` |
| ③ Clean | `librarian_gc.py --clean` — delete merged fragments | `librarian` |
| ④ Check | If any file exceeds 3000 lines → trigger Document Split | `knowledge-architect` |
| **Gate** | `wiki_linter.py` — no dead links | — |

### Wiki Refresh

**Trigger**: phrases like "extract knowledge", "persist to wiki", "refresh knowledge base", "milestone WAL flush"

| Step | Action | Role |
|------|--------|------|
| ① Diff | `git diff` to identify recent changes since last update | `knowledge-extractor` |
| ② Extract | Extract stable knowledge into WAL fragments: [Domain], [API], [Rules] (+ [Data] if schema) | `knowledge-extractor` |
| ③ Write | Write fragments into `wiki/domain/wal/`, `wiki/api/wal/`, etc. | `knowledge-extractor` |
| **Gate** | `writeback_gate.py` (3 required sections) + `wiki_linter.py` | — |

### Document Split

**Trigger**: Any wiki file exceeds 3000 lines, or phrases like "split document", "index too large"

| Step | Action | Role |
|------|--------|------|
| ① Check | Verify file exceeds 3000-line limit; abort if not | `knowledge-architect` |
| ② Deduplicate | Remove repeated entries within the bloated file | `knowledge-architect` |
| ③ Split | Split into focused sub-documents by topic | `knowledge-architect` |
| ④ Rewrite | Rewrite original as a lean routing index with links | `knowledge-architect` |
| **Gate** | `wiki_linter.py` — no dead links, no file still exceeds 3000 | — |

### Project Scan

**Trigger**: phrases like "scan project", "audit codebase", "analyze code structure"

| Step | Action | Role |
|------|--------|------|
| ① Index | `code_index.py --build` — rebuild symbol index | Explorer (inline) |
| ② Search | `wiki_search.py` — surface relevant wiki context | Explorer (inline) |
| ③ Memory | `failure_memory.py query` — surface past failures | Explorer (inline) |
| ④ Report | Produce structured scan report (directories, modules, key symbols, risks) | Explorer (inline) |

---

## Slash Commands

User-invokable shortcuts that wrap multi-step lifecycle flows into single invocations. All project commands use the `h-` prefix (harness) to avoid collision with Claude Code built-ins (`/init`, `/review`, `/security-review`, etc.). Commands live under `.claude/commands/<name>.md` and are loaded automatically — invoke as `/h-<name> [args]`.

### Onboarding & Discovery

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-help [--scenario <kw>]` | Any | Print scenario-driven catalog of all `/h-*` commands grouped by use case | New user / rusty user / not sure which command fits |
| `/h-context-check [--prompt "<text>"] [--brief-only] [--no-events] [--no-insights]` | Any | Pull-model context probe: recent events + recurring failures + active task + dirty diff + active insights. Replaces post-P2 push-model auto-injection. | Phase start / unsure state / about to /h-pr or /h-archive |

### Intake & Planning

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-from-ticket <source> [<slug>]` | Explorer entry | Fetch GitHub/Jira/Linear ticket → `input-classifier` + `ambiguity-gatekeeper` → task_brief skeleton + launch_spec row at Explore phase | Ticket-driven development; maps ticket fields to brief sections; `ticket_ref`/`ticket_url` in frontmatter for PR auto-close |
| `/h-decompose <slug> <prd-path>` | Explorer → Propose | PRD/EPIC pre-validation → task-decomposition-guide → N brief skeletons → DAG bound to launch_spec | EPIC/PRD spanning ≥3 domains; need INVEST-compliant slicing |
| `/h-brief <slug>` | Propose entry | Schema-compliant task_brief + 1 launch_spec row | Single STANDARD task starting from a known scope |
| `/h-design [slug]` | Propose design | Dispatch system-architect with strict Source Documents contract; write ≥2 ADRs (HIGH); fill brief §8/§9 | HIGH/EPIC needs design alternatives; MEDIUM needs 1 explicit option |
| `/h-research <slug> [--scope quick\|deep]` | RESEARCH entry | Scaffold `research_report.md` skeleton (7 sections per schema) + bind to launch_spec at `RES`/`Research`/`IN_PROGRESS`; `--scope` drives §3 quota (5 vs 15 findings) | Analysis / feasibility / baseline investigation; `[triage]` suggested RESEARCH; deliverable is a report, not code |

### Daily Development

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-resume` | Any | Read-only: locate IN_PROGRESS task + restore Machine Section context + report Next Action; detects COLLAB-blocked state | Resuming an interrupted session |
| `/h-status [--all] [--days <N>] [--slug <prefix>]` | Any | Read-only: list all launch_spec rows grouped by status (IN_PROGRESS / WAITING_APPROVAL / PENDING parallelizable / PENDING blocked / DONE / FAILED); compute Next Action from priority chain | Global queue view when you've forgotten what's in flight, before `/h-release` (which requires queue clean), or for backlog triage |
| `/h-fix-bug [<issue-url>] [--priority p1|p2|p3]` | Explorer | GitHub issue or manual input → `failure_memory` query → `root-cause-debug` Phase 1 (MUST complete before any fix) → launch_spec row; p1/p2 triggers `h-incident` and is restricted from inline-PATCH path | Bug reports from QA or production; priority determines risk level and whether incident file is created |
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
| `/h-pr [slug]` | After QA | `secrets_linter` + `scope_guard` pre-gates → `gh pr create` with Human Section + AC checklist; PR URL written back to task_brief; launch_spec row stays `IN_PROGRESS` with `\| PR #<n>` Artifact marker (mirrors COLLAB pattern); auto-closes ticket if `ticket_url` in frontmatter | Creating a PR for a completed STANDARD task |
| `/h-test-handoff [slug] [--bug-fix] [--commits <range>] [--ticket <ref>]` | After QA (pre-merge or pre-release) | Read task_brief + git diff + (incident file if bug-fix) → emit a QA briefing covering reproduction, impact surfaces, positive/negative test cases, regression risks, out-of-scope, rollback plan, open questions → `.claude/runs/qa-handoffs/<date>_<slug>_qa_handoff.md` | Handing the change to QA when test team is separate from dev; pre-merge sanity for high-risk changes |
| `/h-ci [--run-id <id>] [--from-file <log>]` | After push | Fetch CI run data → classify failures by type/severity → `failure_memory` recording → routing recommendation (flake check / fix task / alert) | Analyzing CI failures after a push or as post-PR feedback |
| `/h-release <version> [--dry-run]` | Release | Pre-release gates (queue completeness, clean tree, release branch, secrets) → WAL changelog → `mvn versions:set` → `mvn test` → tag + push; `--dry-run` prints all intended actions without git operations | Cutting a release version |

### Production

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-incident <source> <slug>` | Anytime | Wrap `ingest_incident.py` + write structured incident `.md` from TEMPLATE; enforces `## 提醒未来 LLM` smell test | Real production fact (Sentry/Jira/oncall/post-mortem) entering memory |

### Knowledge & Self-Evolution

★ Post-P7 (June 2026): the Insight Layer turns observed patterns into actionable proposals. These commands bridge **observation → policy change** (always human-approved).

| Command | Phase | Effect | When to use |
|---------|-------|--------|-------------|
| `/h-evolve [--insight-id <id>] [--auto-pick] [--apply]` | Anytime | Turn an active insight into a concrete rule-change proposal. 5 per-kind templates (gate refinement / wiki scope template / archive / threshold loosening / behavior review). `--apply` requires `AskUserQuestion` Yes. | An active high-confidence insight is worth acting on as a harness rule / wiki / hook change |
| `/h-publish-insight --insight-id <id> [--slug <kebab>] [--dry-run]` | Anytime | Manually bridge a local insight → git-tracked team knowledge doc under `.claude/wiki/insights/<date>_<id>_<slug>.md`. Solves "learning is single-machine local" pain. **NEVER auto-fires.** | An insight is worth sharing with the team (vs. only acting on locally) |
| `/h-distill` | Maintenance | Wiki cleanup — `librarian` scan → user-approved plan → execute deletions/merges | Stale wiki nudge / explicit "clean up wiki" request |
| `/h-distill-from-code` | Anytime | Reconcile wiki claims against current code (bounded scope, not WAL flow) | Suspect wiki is out of sync with source |
| `/h-reflect` | End of session | Multi-select lessons (incident/wiki/failure/success/memory) → reset session_stats counters | Reflect-threshold hint OR explicit session retrospective |

Each command file is opinionated: hard step ordering, fixed STOP conditions, explicit Allowed Edit boundaries. See `.claude/commands/h-<name>.md` for the full contract per command.

**Note — no `/h-implement` or `/h-qa`**: the Implement and QA phases are intentionally NOT wrapped in commands. Those phases are the core write-code / write-test / run-tests work that the LLM does directly under the active `task_brief` contract — there is no state transition or gate orchestration to wrap. The `h-*` commands cover entry/exit (`/h-from-ticket`, `/h-decompose`, `/h-brief`, `/h-pr`, `/h-test-handoff`, `/h-archive`), design (`/h-design`), research (`/h-research`), audit (`/h-gates`), status (`/h-resume`, `/h-status`), and special scenarios (`/h-fix-bug`, `/h-incident`, `/h-ci`, `/h-release`). Implement/QA happen in between, plain.

### Command Usage Guide

Read this section when stuck on **which command to invoke** or **what comes next**. Tables above describe what each command DOES; this section helps you decide WHICH one to RUN.

#### Entry Decision Tree — "What do I have on hand?"

| Starting point | Run |
|---|---|
| GitHub Issue / Jira / Linear ticket | `/h-from-ticket` |
| PRD / EPIC (multi-requirement doc) | `/h-decompose` |
| Bug (unknown root cause / error) | `/h-fix-bug` |
| "Research / evaluate / feasibility / analysis" | `/h-research` |
| Production incident (already resolved, record it) | `/h-incident` |
| CI failure (classify + route) | `/h-ci` |
| Requirement already discussed in conversation | `/h-brief` |
| Session interrupted / switching machines | `/h-resume` |
| Forgot what's in flight / global queue view | `/h-status` |
| Cutting a release tag | `/h-release` |

> **Vibe / Patch (TRIVIAL/LOW) does NOT take any `/h-*`.** Just say "fix X" — the agent handles it inline; no TaskList, no WAL, no brief. `/h-*` is for MEDIUM/HIGH/RESEARCH/EPIC structured channels only.

#### Phase Flow Chain — "I'm mid-task, what's next?"

```
Entry              Propose            Implement          Delivery       Archive
────────          ──────────          ──────────        ────────       ──────
/h-from-ticket  → /h-brief    →     (write code) →    /h-pr    →    /h-archive
/h-decompose      /h-design                            (open PR)     (move to wiki/archive,
/h-fix-bug        (HIGH forced)                                       write WAL, mark DONE)
                      │
                      └── /h-collab  ←→  /h-collab-update    (pluggable at any phase)
                                         (cross-team alignment)

Side tools (off the main chain, on-demand):
  /h-gates     run full gate suite (commit / phase boundary / pre-PR)
  /h-resume    recover one task's context after a session break
  /h-status    global queue snapshot (every task on one screen)
  /h-ci        ingest CI failure into the workflow
  /h-incident  record an already-resolved incident into wiki/incidents/
  /h-release   release (requires launch_spec queue empty)

RESEARCH path (no code):
  /h-research  →  (investigate §3 Findings)  →  /h-archive
```

##### Phase "what's next" quick judge

| Current state | Next |
|---|---|
| Just reached requirement agreement | `/h-from-ticket` (have issue) or `/h-brief` (from conversation) |
| `/h-brief` done, skeleton in place | `/h-design <slug>` (HIGH must run, MEDIUM iff `tech_arch`/`patterns` declared) |
| `/h-design` done, into Review | Inline review; HIGH → Approval Gate |
| Approval passed, writing code | No command needed — just code; use `/h-gates --phase implement` for compile/test orchestration |
| Code + tests pass | `/h-pr` |
| PR merged | `/h-archive` |
| Lost track of where I am | `/h-resume` (single task) or `/h-status` (everything) |

#### Disambiguation — Which command for similar-looking cases

| Use which | Distinguishing key |
|---|---|
| `h-brief` **vs** `h-from-ticket` | Requirement already clear from conversation → `h-brief`; pulling from GitHub/Jira/Linear → `h-from-ticket` |
| `h-brief` **vs** `h-decompose` | Single task → `h-brief`; multi-requirement PRD/EPIC → `h-decompose` |
| `h-fix-bug` **vs** `h-from-ticket` | Bug + unknown root cause → `h-fix-bug` (root-cause-first); ticket + known scope → `h-from-ticket` |
| `h-incident` **vs** `h-fix-bug` | Still investigating / fixing → `h-fix-bug`; already fixed, recording for future → `h-incident` |
| `h-design` **vs** natural Propose | MEDIUM/HIGH with declared `tech_arch`/`patterns` dimension → `h-design`; pure CRUD without architectural decision → skip |
| `h-research` **vs** `h-brief` | Deliverable is a **report** (decision input, no code) → `h-research`; deliverable is **code** → `h-brief` |
| `h-pr` **vs** `h-archive` | `h-pr` opens the PR (status stays IN_PROGRESS); `h-archive` closes the loop after merge (IN_PROGRESS → DONE) |
| `h-gates` **vs** PreToolUse hook | Hook is per-Edit tripwire (single file); `h-gates` is phase-boundary / pre-commit audit (full diff) |
| `h-collab` **vs** `h-collab-update` | First time creating cross-team doc → `h-collab`; logging external feedback → `h-collab-update` |
| `h-resume` **vs** `h-status` | `h-resume` = deep recovery of one task (loads task_brief Machine Section); `h-status` = shallow global scan (one row per task) — answers "how many tasks do I have, where are they stuck, which can run in parallel" |

#### Common Stuck Moments

**Q: Just finished describing a task — should I run `/h-brief` or just start?**
Check the `[triage]` block's `suggested:` value: VIBE/PATCH → just start; STANDARD-MEDIUM/HIGH → `/h-brief`; RESEARCH → `/h-research`. No `[triage]`? Ask: does this touch auth/migration/error codes, or > 5 files? If yes → `/h-brief`.

**Q: `/h-brief` asks for risk — which do I pick?**
- **HIGH**: touches auth, schema-mutating DDL (ALTER / DROP / RENAME), lifecycle/policy/error codes, secrets. (Pure `CREATE TABLE` is NOT HIGH — it's B1/LOW.)
- **MEDIUM**: affects ≥ 7 files, OR touches public API/Controller, OR same failure pattern recurred ≥ 3 times.
- **LOW**: everything else.

**Q: `/h-brief` asks for dimensions — which keywords are allowed?**
Exactly 5: `api` (controller/Mapping/DTO), `data` (mapper/entity/SQL), `domain` (service/event/saga/business rules/state machine), `tech_arch` (new component/deployment/dependency), `patterns` (Strategy/Factory/Saga/Outbox/ACL). Single or multi-select; empty `[]` is legal for pure refactor.

**Q: Finished `/h-design`, what next?**
- MEDIUM → straight to Implement (write code), then `/h-pr` after compile + test pass
- HIGH → Approval Gate triggers first (manually confirm Human Section), THEN Implement
- Lost track of phase → `/h-resume` reloads launch_spec context

**Q: Forgot the slug.**
`/h-resume` prints current IN_PROGRESS slug. Or `/h-status` for the full list. Or `ls .claude/runs/task-briefs/`. Most commands also accept an empty `[slug]` and auto-fetch from launch_spec.

**Q: `/h-archive` says 'SLIM cannot run'.**
Step 1.5 guard: `spec_mode: SLIM` tasks don't take WAL flow. Manually `mv .claude/runs/task-briefs/<file> .claude/wiki/archive/`, then flip the launch_spec row `IN_PROGRESS` → `DONE`.

**Q: Command chain mentions `/h-collab` but we don't work cross-team.**
`/h-collab` is an optional side tool. **Ignore.** Only use when frontend / third-party / QA / ops need alignment before code is written.

#### Anti-Patterns

- **Don't use `/h-*` as a Vibe substitute.** Simple changes get "fix X"; don't wrap in `/h-brief --slim`.
- **Don't chain-call `/h-*` via shell.** They are LLM prompt templates, not callable functions. "Execute inline" means YOU (main agent) follow the Steps, not `Bash` runs.
- **Don't run `/h-archive` on a PATCH task.** Step 1.5 will reject.
- **Don't run `/h-research` without `[triage] suggested: RESEARCH`** (unless you explicitly invoke `@research`). It is mutually exclusive with `/h-brief`.
- **Run `/h-archive` on every IN_PROGRESS task BEFORE `/h-release`** — otherwise Gate A rejects the release.

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
| **RESEARCH** | Analysis / feasibility / baseline — deliverable is a report, not code | `Investigate → Synthesize → Archive` | Optional (default Skip; opt-in at archive) | `research_report.md` |
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
| **★ Sensor/Insight/Policy/Enforce 4-Layer** | Post-P2 architecture: hooks are pure sensors → insight_detector finds patterns → agent pulls evidence on demand via /h-context-check → /h-gates enforces at phase boundaries. ONE blocking hook (secrets pre-check) remains. See Architecture section above. |
| **★ Events Stream (`events.jsonl`)** | Unified append-only event log (8 kinds: prompt / edit_pre / edit_post / read / subagent_return / turn_end / notification / compact / env_bypass / user_correction). Queried via `events_query.py`. Schema versioned in wiki. |
| **★ Insight Layer (`insights.jsonl`)** | 5 pure-function detectors over Sensor data emit structured insights with confidence (low/medium/high) + status state machine (new → acknowledged → acted_on / published / dismissed). Append-only, dedup by kind+summary hash. |
| **★ /h-publish-insight → team knowledge** | Bridges single-machine Insight Layer → git-tracked `.claude/wiki/insights/` docs. Solves the "learning is local" team-collaboration pain. Always manual, never auto-fires. |
| **Scope Guard** | Post-P3: moved from per-Edit PreToolUse hook to `/h-gates --phase implement` (phase-boundary enforcement). Implicit allowlist exempts `.claude/runs/` + WAL + archive paths. |
| **Secrets Pre-Check** | PreToolUse hook scans about-to-be-written content; HIGH-conf pattern → exit 2 (block). Post-T10/R3: path-aware downgrade — `test/`, `fixtures/`, `*_test.*`, `*Test.java` patterns get FAIL → WARN demotion (still surfaced, not blocked). `CLAUDE_SECRETS_BYPASS=1` emergency override. |
| **Plan Review Checklist** | Completeness, Consistency, Feasibility, Risk Coverage, Dependency Soundness — must pass before exiting Review (≥3 tasks) |
| **Plan Deviation Reflection** | Compare planned vs actual at Archive — scope drift, dependency accuracy, AC coverage |
| **Throttled Push-Back Reminders** | Stop hook emits `[insight-reminder]` (high-conf insight set changed) + `[scope-check-reminder]` (dirty > 5 + last emit aged). Shared throttle state in `last_reminders.json` prevents per-turn noise. |
| **Hook System** | 8 hook events registered: PreToolUse[Edit\|Write] (secrets only) / PostToolUse[Edit\|Write] (sensor) / PostToolUse[Read] (sensor + usage_tracker) / UserPromptSubmit (sensor) / SubagentStop (sensor) / Stop (sensor + 2 throttled reminders) / Notification (jsonl log + opt-in bell) / PreCompact (state snapshot for recovery) |
| **PreCompact State Snapshot** | Before context compression: snapshot active task_brief / launch_spec / HEAD / recent commits to `last_compact_snapshot.json` (retention 20). Post-compact agent reads to resume context. |
| **Local Intelligence** | BM25 wiki search, Java symbol index, failure memory — zero-cost context. failure_memory rotates at >5MB or oldest > 90d. |
| **Gate Scripts** | 21 deterministic Python scripts in `scripts/gates/` that block or warn on quality/security/compliance issues. Invoked by `/h-gates --phase` at phase boundaries (NOT per-edit, post-P3). |
| **Insight Detector Detectors** | 5 detectors with thresholds tuned for low/medium/high confidence: count ≥ 3 / 5 / 10 within window. `co_edit_cluster` includes union-find subset dedup + 24h age filter (avoids self-noise during active dev). `user_correction` bound to `prior_actions_5min > 0` (filters opening-prompt false fires). |
| **Triage Reviewer (Haiku)** | Optional semantic second-opinion sub-agent for genuinely ambiguous prompts on HIGH-sensitivity surface. Explicit dispatch only (post-P6); pre-P6 was auto-triggered by `needs_semantic_review` flag, since removed. |

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
- [.claude/wiki/wiki/architecture/events_jsonl_schema.md](.claude/wiki/wiki/architecture/events_jsonl_schema.md) — events.jsonl schema (Sensor layer L1)
- [.claude/wiki/wiki/architecture/insights_layer_schema.md](.claude/wiki/wiki/architecture/insights_layer_schema.md) — insights.jsonl schema (Insight layer L2)
- [.claude/wiki/insights/README.md](.claude/wiki/insights/README.md) — team-published insights directory (from /h-publish-insight)
- [.claude/wiki/incidents/](.claude/wiki/incidents/) — production incident records
