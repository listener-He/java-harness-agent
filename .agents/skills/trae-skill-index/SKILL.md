---
name: "trae-skill-index"
description: "Central index for all workspace skills. Invoke when you need to find a specific skill or understand the relationships between skills."
---

# Trae Skill Index — Central Knowledge Graph

Root node of the Skill Knowledge Graph. Navigate here to find the appropriate specialized skill.

---

## 0. Entry & Routing

| Skill | Purpose |
|---|---|
| [intent-gateway](../intent-gateway/SKILL.md) | Routes any natural-language request into the correct intent and lifecycle profile. Start every new task here. |

---

## 1. Business & Product

| Skill | Purpose |
|---|---|
| [product-manager-expert](../product-manager-expert/SKILL.md) | Requirements research, validation, PRD generation, and prototyping. |
| [task-decomposition-guide](../task-decomposition-guide/SKILL.md) | MANDATORY MASTER skill for decomposing large PRDs or EPIC scenarios into manageable subtasks. Enforces Agile INVEST criteria and Vertical Slicing. |

---

## 2. DevOps Lifecycle

| Skill | Purpose |
|---|---|
| [devops-lifecycle-master](../devops-lifecycle-master/SKILL.md) | **MANDATORY** master orchestration skill. Invoke at the start of any feature, design, or bugfix task. |
| [devops-requirements-analysis](../devops-requirements-analysis/SKILL.md) | PDD & SDD phase — requirements analysis. |
| [devops-system-design](../devops-system-design/SKILL.md) | System architecture & data modeling (FDD & SDD). |
| [devops-task-planning](../devops-task-planning/SKILL.md) | Task breakdown and planning. |
| [devops-testing-standard](../devops-testing-standard/SKILL.md) | TDD phase — testing standards and evidence requirements. |
| [devops-feature-implementation](../devops-feature-implementation/SKILL.md) | Phase 4 — feature code implementation. |
| [devops-review-and-refactor](../devops-review-and-refactor/SKILL.md) | Code review and safe feature modification. |
| [devops-bug-fix](../devops-bug-fix/SKILL.md) | Structured bug diagnosis, reproduction, fix, and verification. |

---

## 3. Java Backend Standards

| Skill | Purpose |
|---|---|
| [global-backend-standards](../global-backend-standards/SKILL.md) | **MASTER index** for all backend code generation. Invoke before writing any Java/Spring/MyBatis code. |
| [java-architecture-standards](../java-architecture-standards/SKILL.md) | MANDATORY MASTER skill for Java backend architecture, API design, and engineering rules. |
| [java-coding-style](../java-coding-style/SKILL.md) | MANDATORY MASTER skill for Java coding style, strict Javadoc templates, utility class boundaries, and functional programming patterns. |
| [java-testing-standards](../java-testing-standards/SKILL.md) | MANDATORY MASTER skill for Java Testing & QA, test isolation, mock guidelines, and the 3-scenario coverage rule. |
| [mybatis-sql-standard](../mybatis-sql-standard/SKILL.md) | Anti-JOIN strategy, type conversion prevention, leftmost prefix index rules, no `SELECT *`. |

---

## 4. Utilities & Checklists

| Skill | Purpose |
|---|---|
| [code-review-checklist](../code-review-checklist/SKILL.md) | **MANDATORY** code review checklist — run before every code delivery. |
| [cognitive-bias-checklist](../cognitive-bias-checklist/SKILL.md) | Cognitive bias checklist for deep analysis and architectural design. |
| [decision-frameworks](../decision-frameworks/SKILL.md) | Decision frameworks (SWOT, 5-Why, Decision Matrix) for complex scenarios. |
| [spec-quality-checklist](../spec-quality-checklist/SKILL.md) | Flexible quality gate checklist for AI self-correction on docs/specs. |
| [wal-documentation-rules](../wal-documentation-rules/SKILL.md) | MANDATORY documentation capture during the Archive phase (API and Database). |
| [linter-severity-standard](../linter-severity-standard/SKILL.md) | Linter severity levels (FAIL / WARN / IGNORE) and bypass justification protocol. |
| [aliyun-oss](../aliyun-oss/SKILL.md) | OSS object storage module usage. |

---

## 5. Meta Skills

| Skill | Purpose |
|---|---|
| [skill-graph-manager](../skill-graph-manager/SKILL.md) | **MANDATORY** mechanism for managing the bidirectional Skill Knowledge Graph. Invoke when adding or modifying skills. |

---

## Related

- [skill-graph-manager](../skill-graph-manager/SKILL.md): maintains this index and the graph connections.
