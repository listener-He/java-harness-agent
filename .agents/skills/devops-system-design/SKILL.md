---
name: "devops-system-design"
description: "Handles System Architecture & Data Modeling (FDD & SDD). Invoke when designing database tables, ER diagrams, data models, and architectural extensibility."
---

# DevOps Phase 2: System Architecture & Data Modeling (FDD & SDD)

**Focus**: Technical breakdown, System Architecture, and Data Modeling.

## 🛡️ GUARDRAILS (边界守卫) - STRICTLY ENFORCED
- **NO JAVA CODING**: You are prohibited from generating Java implementations (Controllers, Services, Tests) during this phase.
- **ALLOWED OUTPUTS**: Only Markdown documents, Mermaid diagrams, and SQL `CREATE TABLE` scripts are permitted.

## 📋 Design Dimensions

### 1. Data Structure & ER Design
- **Tables**: Define SQL `CREATE TABLE` statements with precise data types (`varchar`, `tinyint`, `bigint`).
- **Standard Columns**: All tables MUST have `id` (bigint primary key), `tenant_id` (bigint), `create_time` (datetime), `update_time` (datetime), `create_by` (bigint), `update_by` (bigint), `version` (int), `is_deleted` (tinyint).
- **Relationships**: Design logical foreign keys (do NOT use physical DB foreign keys). Draw Mermaid ER diagrams.

### 2. Architectural Extensibility & Business Boundaries
- **Modularity**: Ensure the design separates concerns based on the business rules injected in Phase 1.
- **Interfaces**: Define the abstract Service interfaces (Markdown or minimal Java Interface stubs only) that this feature will expose.

### 3. Large Data Volume & Performance Considerations
- **Query Scenarios & Indexing**: List the main query scenarios. Explain your reasoning for how proposed indexes (e.g., compound indexes, leftmost prefix rule) cover these scenarios.
- **Data Assembly Strategy**: Plan for application-level in-memory mapping / Anti-JOIN assembly. 
- **Caching Strategy**: *If* the architecture includes a cache layer (Redis/Caffeine) and data is read-heavy, design the cache keys, eviction policies, and consistency mechanisms.

### 4. Specification Synchronization (SDD)
- Update or create the database documentation (invoke `database-documentation-sync`).
- Update or create the API documentation (invoke `api-documentation-rules`).

## 🎯 Outcomes
- `schema.sql` or Liquibase/Flyway scripts.
- Mermaid ER Diagrams & Index Reasoning.
- Stop here. Do not write feature code. Prompt the user to proceed to Phase 3: `devops-task-planning`.