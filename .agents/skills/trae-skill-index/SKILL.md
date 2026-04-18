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
| [prd-task-splitter](../prd-task-splitter/SKILL.md) | Analyzes PRDs to produce structured task lists, time estimates, and dependency maps. |

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
| [java-engineering-standards](../java-engineering-standards/SKILL.md) | Layer architecture, POJO sub-packages, entity audit fields, naming conventions. |
| [java-backend-api-standard](../java-backend-api-standard/SKILL.md) | API design rules (no `@PathVariable`, verb-suffix URLs, `@ResourceLock`, `@Validated`). |
| [java-backend-guidelines](../java-backend-guidelines/SKILL.md) | Defensive programming, in-memory data assembly, standardized pagination wrappers, `Objects` utility, `BeanUtil`. |
| [utils-usage-standard](../utils-usage-standard/SKILL.md) | Core utility class usage rules. |
| [error-code-standard](../error-code-standard/SKILL.md) | Unified error response, domain-driven exceptions, abstract error codes. |
| [mybatis-sql-standard](../mybatis-sql-standard/SKILL.md) | Anti-JOIN strategy, type conversion prevention, leftmost prefix index rules, no `SELECT *`. |
| [java-javadoc-standard](../java-javadoc-standard/SKILL.md) | Project Javadoc style enforcement. |
| [checkstyle](../checkstyle/SKILL.md) | K&R braces, 4-space indent, lowerCamelCase, strict Javadoc. |

---

## 4. Utilities & Checklists

| Skill | Purpose |
|---|---|
| [code-review-checklist](../code-review-checklist/SKILL.md) | **MANDATORY** code review checklist — run before every code delivery. |
| [api-documentation-rules](../api-documentation-rules/SKILL.md) | API interface documentation standards. |
| [database-documentation-sync](../database-documentation-sync/SKILL.md) | Database documentation sync rules. |
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
