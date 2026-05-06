---
name: "trae-skill-index"
description: "Central index for all workspace skills. Invoke when you need to find a specific skill or understand the relationships between skills."
---

# Trae Skill Index — Central Knowledge Graph

Root node of the Skill Knowledge Graph. Navigate here to find the appropriate specialized skill.

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

These are invoked because mounted roles explicitly require them (see `.agents/workflow/ROLE_MATRIX.md`).

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
| Explorer | Requirement Engineer | brainstorming → (cognitive-bias-checklist) → (spec-quality-checklist) |
| Propose / Review | System Architect + Devil's Advocate | task-decomposition-guide → decision-frameworks → (cognitive-bias-checklist) → (spec-quality-checklist) |
| Implement | Lead Engineer + Focus Guard | writing-plans → java-architecture-standards/java-coding-style/mybatis-sql-standard → systematic-debugging/test-driven-development |
| QA | Code Reviewer | code-review-checklist → java-testing-standards → verify/ultraqa |
| Archive | Knowledge Extractor | wal-documentation-rules → verify (evidence summary) |

---

## 1. Business & Product

| Skill | Purpose |
|---|---|
| [product-manager-expert](../product-manager-expert/SKILL.md) | Requirements research, validation, PRD generation, and prototyping. |
| [task-decomposition-guide](../task-decomposition-guide/SKILL.md) | MANDATORY MASTER skill for decomposing large PRDs or EPIC scenarios into manageable subtasks. Enforces Agile INVEST criteria and Vertical Slicing. |

---

## 2. Engineering Pipeline

| Skill | Purpose |
|---|---|
| [ai-pipeline](../ai-pipeline/SKILL.md) | End-to-end AI engineering pipeline orchestrator (blueprint → decisions → eval → improve → cleanup). |
| [blueprint](../blueprint/SKILL.md) | Convert a goal into an executable step plan with dependency awareness. |
| [architecture-decision-records](../architecture-decision-records/SKILL.md) | Capture architecture decisions as ADR documents. |
| [eval-harness](../eval-harness/SKILL.md) | Evaluation-driven development harness: pass/fail criteria and regression suites. |
| [external-research](../external-research/SKILL.md) | Inject actionable improvements via external research when stuck. |
| [self-improve](../self-improve/SKILL.md) | Tournament-style improvement loop until baseline passes. |
| [ai-slop-cleaner](../ai-slop-cleaner/SKILL.md) | Regression-safe cleanup of AI-generated code without behavior change. |

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
| [brainstorming](../brainstorming/SKILL.md) | Explore intent, requirements, and design before any creative work. |
| [systematic-debugging](../systematic-debugging/SKILL.md) | Systematic investigation before proposing fixes. |
| [test-driven-development](../test-driven-development/SKILL.md) | Write tests first, then implement; enforce 3-scenario coverage. |
| [ultraqa](../ultraqa/SKILL.md) | Test → verify → fix → repeat QA loop until acceptance passes. |
| [verify](../verify/SKILL.md) | Verification-before-completion: evidence-driven validation. |
| [code-review-checklist](../code-review-checklist/SKILL.md) | **MANDATORY** code review checklist — run before every code delivery. |
| [cognitive-bias-checklist](../cognitive-bias-checklist/SKILL.md) | Cognitive bias checklist for deep analysis and architectural design. |
| [decision-frameworks](../decision-frameworks/SKILL.md) | Decision frameworks (SWOT, 5-Why, Decision Matrix) for complex scenarios. |
| [spec-quality-checklist](../spec-quality-checklist/SKILL.md) | Flexible quality gate checklist for AI self-correction on docs/specs. |
| [wal-documentation-rules](../wal-documentation-rules/SKILL.md) | MANDATORY documentation capture during the Archive phase (API and Database). |
| [linter-severity-standard](../linter-severity-standard/SKILL.md) | Linter severity levels (FAIL / WARN / IGNORE) and bypass justification protocol. |

---

## 5. Workflow & Collaboration

| Skill | Purpose |
|---|---|
| [dispatching-parallel-agents](../dispatching-parallel-agents/SKILL.md) | Dispatch parallel agents for independent tasks. |
| [using-git-worktrees](../using-git-worktrees/SKILL.md) | Use git worktrees for isolated development. |
| [writing-plans](../writing-plans/SKILL.md) | Write an implementation plan before coding. |
| [release](../release/SKILL.md) | Analyze repo release rules and guide release steps. |
| [deepinit](../deepinit/SKILL.md) | Deep initialization: generate layered AGENTS-style docs for a repo. |
| [remember](../remember/SKILL.md) | Extract and persist reusable project knowledge. |

---

## 6. Meta Skills

| Skill | Purpose |
|---|---|
| [skill-creator](../skill-creator/SKILL.md) | Create new skills and validate skill format. |
| [skill-graph-manager](../skill-graph-manager/SKILL.md) | **MANDATORY** mechanism for managing the bidirectional Skill Knowledge Graph. Invoke when adding or modifying skills. |

---

## Related

- [skill-graph-manager](../skill-graph-manager/SKILL.md): maintains this index and the graph connections.
