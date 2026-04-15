---
name: "trae-skill-index"
description: "The Central Knowledge Graph Index for all workspace skills. Invoke when you need to find a specific skill or understand the relationships between different skills."
---

# Trae Skill Index (技能知识图谱总目录)

**Focus**: Central Index (全局索引), Knowledge Graph Navigation (知识图谱导航), Skill Discovery (技能发现).

This is the root node of the Skill Knowledge Graph. Use this index to navigate to the appropriate specialized skills.

## 🗺️ Skill Categories (技能分类)

### 0. 🚪 Entry & Routing (入口与路由)
- **[intent-gateway](../intent-gateway/SKILL.md)**: 意图网关技能：接收自然语言需求，执行上下文检索漏斗，并发分发到对应意图的生命周期中。

### 1. 🎯 Business & Product (业务与产品)
- **[product-manager-expert](../product-manager-expert/SKILL.md)**: Expert PM skill for requirements research, validation, PRD generation, and prototyping.
- **[prd-task-splitter](../prd-task-splitter/SKILL.md)**: Analyzes PRDs to automatically generate structured development task lists, time estimates, dependencies, and PRD health checks.

### 2. 🔄 DevOps Lifecycle (研发全生命周期)
- **[devops-lifecycle-master](../devops-lifecycle-master/SKILL.md)**: MANDATORY MASTER orchestration skill for DevOps Lifecycle.
- **[devops-requirements-analysis](../devops-requirements-analysis/SKILL.md)**: Handles PDD & SDD phase.
- **[devops-system-design](../devops-system-design/SKILL.md)**: Handles System Architecture & Data Modeling (FDD & SDD).
- **[devops-task-planning](../devops-task-planning/SKILL.md)**: Handles Task Planning.
- **[devops-testing-standard](../devops-testing-standard/SKILL.md)**: Handles TDD phase.
- **[devops-feature-implementation](../devops-feature-implementation/SKILL.md)**: Handles feature code implementation (FDD).
- **[devops-review-and-refactor](../devops-review-and-refactor/SKILL.md)**: Handles code review and feature modification.
- **[devops-bug-fix](../devops-bug-fix/SKILL.md)**: Handles Bug Fixing.

### 3. ☕ Java Backend Standards (Java 后端规范)
- **[global-backend-standards](../global-backend-standards/SKILL.md)**: The MASTER index skill for all backend development.
- **[java-engineering-standards](../java-engineering-standards/SKILL.md)**: Enforces strict layer architecture, pojo sub-packages, and business design rules.
- **[java-backend-api-standard](../java-backend-api-standard/SKILL.md)**: Enforces backend API design standards.
- **[java-backend-guidelines](../java-backend-guidelines/SKILL.md)**: Comprehensive Java guidelines (defensive programming, etc.).
- **[java-data-permissions](../java-data-permissions/SKILL.md)**: Guides data permissions.
- **[utils-usage-standard](../utils-usage-standard/SKILL.md)**: Utilities Usage Standard (核心工具类使用规范)。
- **[error-code-standard](../error-code-standard/SKILL.md)**: Guides the usage of system error codes.
- **[mybatis-sql-standard](../mybatis-sql-standard/SKILL.md)**: Enforces strict MyBatis SQL writing standards.
- **[java-javadoc-standard](../java-javadoc-standard/SKILL.md)**: Enforces the project's strict Javadoc commenting style.
- **[checkstyle](../checkstyle/SKILL.md)**: Enforces strict Java checkstyle rules.

### 4. 🛠️ Utilities & Checklists (工具与检查单)
- **[code-review-checklist](../code-review-checklist/SKILL.md)**: MANDATORY Code Review Checklist.
- **[api-documentation-rules](../api-documentation-rules/SKILL.md)**: API接口文档规范。
- **[database-documentation-sync](../database-documentation-sync/SKILL.md)**: 数据库文档同步规范。
- **[oss-module](../aliyun-oss/SKILL.md)**: OSS对象存储模块。

### 5. 🕸️ Meta Skills (元技能)
- **[skill-graph-manager](../skill-graph-manager/SKILL.md)**: MANDATORY mechanism for managing the bidirectional Skill Knowledge Graph.

---

## 🔗 关联技能 (Related Skills)
- [skill-graph-manager](../skill-graph-manager/SKILL.md): Manages this index file and maintains the graph connections.
