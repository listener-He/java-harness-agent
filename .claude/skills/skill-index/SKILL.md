---
name: "skill-index"
description: "Central index and navigator for all workspace skills. Invoke when you need to find the right skill, understand skill relationships, or see the lifecycle phase map. The single entry point to the skill ecosystem."
---

# Skill Index — Central Navigator

Root node of the Skill Knowledge Graph. Navigate here to find the appropriate specialized skill.

---

## Quick Start — Common Scenarios

| Scenario | Skill sequence |
|---|---|
| **Any non-trivial input** (PRD / idea / bug report / security finding) | `requirement-intake` → route to appropriate skill below |
| Writing a new feature (from idea) | `requirement-intake` → `brainstorming` → `task-decomposition-guide` → `java-architecture-standards` → `test-driven-development` → `ultraqa` → `wal-documentation-rules` |
| Processing a PRD | `requirement-intake` → `product-manager-expert` (Ingestion Mode) → `task-decomposition-guide` → standard feature flow |
| Fixing a bug | `requirement-intake` → `systematic-debugging` → `test-driven-development` → `verify` |
| Refactoring | `cognitive-bias-checklist` → `blueprint` → `ai-slop-cleaner` → `code-review-checklist` |
| Greenfield (from scratch) | `requirement-intake` → `greenfield-scaffold` → `brainstorming` → standard feature flow |
| A→B migration | `requirement-intake` → `migration-planner` → standard STANDARD flow |
| Full pipeline (idea → delivery) | `ai-pipeline` (orchestrates all phases automatically) |
| Large epic / multi-domain | `task-decomposition-guide` → `dispatching-parallel-agents` → `verify` |
| Security or HIGH risk change | `security-review-checklist` → `code-review-checklist` → `verify` |
| Multi-stakeholder conflict | `requirement-intake` → `stakeholder-conflict-resolver` → `product-manager-expert` (Mode A) |
| Production incident / outage | `requirement-intake` → `incident-response` → `systematic-debugging` → post-mortem AIs into task queue |
| Knowledge preservation | `wal-documentation-rules` (Archive) + `remember` (lessons learned) |

---

## 0. Default Enabled Set

Default Enabled means: preferred for automatic invocation and daily workflow. Everything else is opt-in unless a mounted role checklist requires it.

| Skill | Lifecycle Phase(s) | Primary Role |
|---|---|---|
| [brainstorming](../brainstorming/SKILL.md) | Explorer / Propose | Requirement Engineer |
| [task-decomposition-guide](../task-decomposition-guide/SKILL.md) | Propose / Review | System Architect |
| [writing-plans](../writing-plans/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |
| [systematic-debugging](../systematic-debugging/SKILL.md) | Implement / QA | Lead Engineer / Code Reviewer |
| [test-driven-development](../test-driven-development/SKILL.md) | Implement | Lead Engineer |
| [verify](../verify/SKILL.md) | QA / Archive | Code Reviewer / Knowledge Extractor |
| [code-review-checklist](../code-review-checklist/SKILL.md) | QA | Code Reviewer |
| [wal-documentation-rules](../wal-documentation-rules/SKILL.md) | Archive | Knowledge Extractor |
| [skill-graph-manager](../skill-graph-manager/SKILL.md) | Any (skills change) | Skill Graph Curator |
| [java-architecture-standards](../java-architecture-standards/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |
| [java-coding-style](../java-coding-style/SKILL.md) | Implement | Lead Engineer |
| [java-testing-standards](../java-testing-standards/SKILL.md) | QA | Code Reviewer |
| [mybatis-sql-standard](../mybatis-sql-standard/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |

---

## 0.1 Role-Required (Not Default Enabled)

These are invoked because mounted roles explicitly require them (see `.claude/agents/`).

| Skill | Required By Roles |
|---|---|
| [cognitive-bias-checklist](../cognitive-bias-checklist/SKILL.md) | Requirement Engineer, System Architect, Devil's Advocate |
| [spec-quality-checklist](../spec-quality-checklist/SKILL.md) | Requirement Engineer, System Architect, Documentation Curator |
| [decision-frameworks](../decision-frameworks/SKILL.md) | System Architect, Devil's Advocate, Ambiguity Gatekeeper |
| [linter-severity-standard](../linter-severity-standard/SKILL.md) | Code Reviewer |

---

## 0.2 Lifecycle Phase Map (Change / STANDARD)

This is the “happy path” routing aligned with mounted roles.

| Phase | Mounted Role(s) | Skills |
|---|---|---|
| Pre-Explorer | — | **requirement-intake** (for non-trivial inputs) |
| Explorer | Requirement Engineer | brainstorming → (cognitive-bias-checklist) → (spec-quality-checklist) |
| Explorer (Greenfield) | Requirement Engineer | **greenfield-scaffold** → brainstorming |
| Explorer (Migration) | Requirement Engineer | **migration-planner** Phase 1-2 |
| Propose / Review | System Architect | **brainstorming** (≥2 ADR alternatives) → task-decomposition-guide → decision-frameworks → (cognitive-bias-checklist) |
| Implement | Lead Engineer + Focus Guard | writing-plans → java-architecture-standards/java-coding-style/mybatis-sql-standard → systematic-debugging/test-driven-development |
| QA | Code Reviewer | code-review-checklist → java-testing-standards → **ultraqa** (Evidence Mapping Table) → (security-review-checklist for HIGH risk) |
| Archive | Knowledge Extractor | wal-documentation-rules → verify (evidence summary) |

---

## 1. Business & Product

| Skill | Purpose |
|---|---|
| [requirement-intake](../requirement-intake/SKILL.md) | **Front door.** Classifies ANY raw input (PRD, idea, bug, signal, security, compliance) into normalized intent+AC format before routing. Run first for all non-trivial inputs. |
| [product-manager-expert](../product-manager-expert/SKILL.md) | Two modes: (A) PRD Ingestion — process existing PRD into AC + implementation queue; (B) PRD Generation — research and write a new PRD. |
| [task-decomposition-guide](../task-decomposition-guide/SKILL.md) | MANDATORY MASTER skill for decomposing large PRDs or EPIC scenarios into manageable subtasks. Enforces Agile INVEST criteria and Vertical Slicing. |
| [greenfield-scaffold](../greenfield-scaffold/SKILL.md) | Starting-from-scratch protocol: domain model → API contract → DB schema → package structure → scaffold. Use when there is no existing codebase. |
| [migration-planner](../migration-planner/SKILL.md) | A→B migration protocol with behavioral equivalence testing. Generates equivalence test suite BEFORE migration code. |
| [stakeholder-conflict-resolver](../stakeholder-conflict-resolver/SKILL.md) | Detects and resolves mutually exclusive requirements from multiple stakeholders. Produces conflict map + resolution record. |
| [incident-response](../incident-response/SKILL.md) | Production emergency triage (severity → blast radius → mitigation) + root cause investigation + post-mortem with 5-Why chain and Action Items. |

---

## 2. Engineering Pipeline

| Skill | Purpose |
|---|---|
| [ai-pipeline](../ai-pipeline/SKILL.md) | End-to-end AI engineering pipeline orchestrator (blueprint → decisions → eval → improve → cleanup). |
| [blueprint](../blueprint/SKILL.md) | Convert a goal into an executable step plan with dependency awareness. |
| [architecture-decision-records](../architecture-decision-records/SKILL.md) | Capture architecture decisions as ADR documents. |
| [eval-harness](../eval-harness/SKILL.md) | Two modes: (A) early-phase AC definition at Explorer; (B) pipeline benchmark harness with pass@k metrics. |
| [external-research](../external-research/SKILL.md) | Four trigger modes: pipeline plateau / security CVE / compliance / competitor benchmarking. |
| [self-improve](../self-improve/SKILL.md) | Eval-anchored tournament loop: tracks score delta per iteration, plateau detection at 2 no-gain iterations triggers external-research. |
| [ai-slop-cleaner](../ai-slop-cleaner/SKILL.md) | Regression-safe cleanup bounded by task_brief Allowed Scope. Step 0 enforces scope gate before any analysis. |

---

## 3. Java Backend Standards

| Skill | Purpose |
|---|---|
| [java-architecture-standards](../java-architecture-standards/SKILL.md) | MANDATORY MASTER skill for Java backend architecture, API design, and engineering rules. |
| [java-coding-style](../java-coding-style/SKILL.md) | MANDATORY MASTER skill for Java coding style, strict Javadoc templates, utility class boundaries, and functional programming patterns. |
| [java-testing-standards](../java-testing-standards/SKILL.md) | MANDATORY MASTER skill for Java Testing & QA, test isolation, mock guidelines, and the 3-scenario coverage rule. |
| [mybatis-sql-standard](../mybatis-sql-standard/SKILL.md) | Anti-JOIN strategy, type conversion prevention, leftmost prefix index rules, no `SELECT *`. |

---

## 4. QA, Debugging & Review

| Skill | Purpose |
|---|---|
| [adversarial-review](../adversarial-review/SKILL.md) | One-round isolated critique, scenario-specific adversarial frame. Hard 1-round limit. For MEDIUM/HIGH risk Review phase. |
| [brainstorming](../brainstorming/SKILL.md) | Explore intent, requirements, and design before any creative work. |
| [systematic-debugging](../systematic-debugging/SKILL.md) | Systematic investigation before proposing fixes. |
| [test-driven-development](../test-driven-development/SKILL.md) | Write tests first, then implement; enforce 3-scenario coverage. |
| [ultraqa](../ultraqa/SKILL.md) | Test → verify → fix → repeat QA loop until acceptance passes. |
| [verify](../verify/SKILL.md) | Verification-before-completion: evidence-driven validation. |
| [code-review-checklist](../code-review-checklist/SKILL.md) | **MANDATORY** code review checklist — run before every code delivery. |
| [cognitive-bias-checklist](../cognitive-bias-checklist/SKILL.md) | Cognitive bias checklist for deep analysis and architectural design. |
| [decision-frameworks](../decision-frameworks/SKILL.md) | Decision frameworks (SWOT, 5-Why, Decision Matrix) for complex scenarios. |
| [spec-quality-checklist](../spec-quality-checklist/SKILL.md) | Flexible quality gate checklist for AI self-correction on docs/specs. |
| [wal-documentation-rules](../wal-documentation-rules/SKILL.md) | **MANDATORY** documentation capture during Archive phase (API, Domain, Data WAL). |
| [security-review-checklist](../security-review-checklist/SKILL.md) | Security checklist for HIGH risk changes: secrets, authZ, IDOR, data exposure. |
| [linter-severity-standard](../linter-severity-standard/SKILL.md) | Linter severity levels (FAIL / WARN / IGNORE) and bypass justification protocol. |

---

## 5. Workflow & Collaboration

| Skill | Purpose |
|---|---|
| [dispatching-parallel-agents](../dispatching-parallel-agents/SKILL.md) | Dispatch parallel agents for independent tasks. |
| [using-git-worktrees](../using-git-worktrees/SKILL.md) | Use git worktrees for isolated development. |
| [writing-plans](../writing-plans/SKILL.md) | Write an implementation plan before coding. |
| [release](../release/SKILL.md) | Analyze repo release rules and guide release steps. |
| [deepinit](../deepinit/SKILL.md) | Deep initialization: generates hierarchical CLAUDE.md files + machine-readable `context_brief.md` for downstream skill consumption. |
| [remember](../remember/SKILL.md) | Extract and persist reusable project knowledge. |
| [local-code-intelligence](../local-code-intelligence/SKILL.md) | Three pure-local tools: BM25 wiki search, Java symbol index, failure memory. Zero-cost context before file navigation. |

---

## 6. Meta Skills

| Skill | Purpose |
|---|---|
| [skill-creator](../skill-creator/SKILL.md) | Create new skills and validate skill format. |
| [skill-graph-manager](../skill-graph-manager/SKILL.md) | **MANDATORY** mechanism for managing the bidirectional Skill Knowledge Graph. Invoke when adding or modifying skills. |

---

## Related

- [skill-graph-manager](../skill-graph-manager/SKILL.md): maintains this index and the graph connections.
- [skill-creator](../skill-creator/SKILL.md): use when creating a new skill — it will prompt you to register here.
