---
name: "prd-task-splitter"
description: "Analyzes PRDs to automatically generate structured development task lists, time estimates, dependencies, and PRD health checks. Invoke when a PRD is ready for development planning."
---

# PRD Task Splitter (PRD智能任务拆解器)

**Focus**: PRD Health Check (PRD体检), Existing System Impact Assessment (现网影响评估), Task Breakdown (任务拆解 including NFRs), Role Assignment (角色分配), Time Estimation (工时估算), and Dependency Tracking (依赖推断).

This skill acts as your virtual **Tech Lead** or **Agile Scrum Master**. It bridges the gap between Product Management (PRD) and Development by transforming a static PRD document into an actionable, structured execution plan that accounts for both functional and non-functional requirements.

## 🛡️ GUARDRAILS (边界守卫) - STRICTLY ENFORCED
- **NO PRD WRITING**: Do not write or invent product requirements. Your job is to *analyze* existing PRDs.
- **NO CODE GENERATION**: Do not write actual code (Java, Vue, etc.) in this phase.
- **MANDATORY HEALTH CHECK**: You must evaluate the PRD quality before outputting the task list.

---

## 📋 The 6-Step Splitting Workflow

### Step 1: PRD Health Check & Risk Assessment (PRD体检与风险识别)
**Action**: Scan the provided PRD for quality and risks.
- **Quality Check**: Identify fuzzy/vague words (e.g., "optimize", "fast", "user-friendly"), missing Acceptance Criteria, missing Exception Flows, or missing Performance Metrics.
- **Risk Identification**: Highlight high-risk technical areas (e.g., Third-party payment/SMS integrations, complex data migrations, concurrency issues, security compliance).

### Step 2: Existing System Impact Assessment (现网影响评估)
**Action**: If this is an iteration or requirement change (not a greenfield project), evaluate its impact on existing systems.
- **Data Impact**: Will this change require altering existing database tables, migrating historical data, or running data patching scripts?
- **Process Impact**: Will this break existing downstream systems, APIs consumed by other teams, or current user workflows?
- **Compatibility**: Is backward compatibility required for older app versions or existing open API clients?

### Step 3: Module Identification (模块识别)
**Action**: Automatically identify the core functional and non-functional modules from the PRD (e.g., User System, Order Management, Security & Compliance, Monitoring).

### Step 4: Role-Based Task Breakdown (结构化任务拆解)
**Action**: Deconstruct each module into specific, actionable tasks assigned to different roles, ensuring Non-Functional Requirements (NFRs) are included:
- `[前端/Frontend]`: UI development, API integration, state management, bundle size optimization, accessibility (a11y).
- `[后端/Backend]`: API design, core business logic, caching strategies, rate limiting.
- `[数据库/Database]`: Table schema design, indexes, initial data, data migration scripts.
- `[运维/DevOps]`: CI/CD pipeline updates, infrastructure provisioning, monitoring/alerting setup, log aggregation.
- `[测试/QA]`: Unit tests, integration test cases, edge case validation, performance/load testing, security penetration testing.

### Step 5: Time Estimation (工时估算)
**Action**: Assign realistic effort estimates based on complexity.
- **Simple**: ~2 hours (e.g., basic CRUD API, simple UI component).
- **Medium**: ~4 hours (e.g., complex form validation, standard business logic, monitoring setup).
- **Complex**: ~8+ hours (e.g., third-party integration, complex algorithm, data migration, high-concurrency optimization).

### Step 6: Dependency Tracking (依赖推断)
**Action**: Establish the execution sequence to avoid blocked developers.
- Example: `Frontend Task A depends on Backend API Task B`.
- Example: `Backend Task B depends on Database Design Task C`.
- Example: `Data Migration Script depends on Database Design Task C`.

---

## 🚀 Output Format (输出报告规范)
Always output a highly readable Markdown report containing:

1. **📊 总览面板 (Overview Panel)**
   - 识别模块数 (Total Modules)
   - 拆解任务数 (Total Tasks)
   - 总工时估算 (Estimated Total Hours / Mandays)
   - PRD 体检评分及高危风险预警 (PRD Health Score & Risks)

2. **📦 任务拆解清单 (Task Breakdown by Module)**
   - *Example:*
     - **[数据库]** T01: 设计用户表及索引结构 `[简单-2h]`
     - **[后端]** T02: 实现手机号+验证码登录 API `[中等-4h]` *(依赖 T01)*
     - **[前端]** T03: 开发登录页面及交互 `[中等-4h]` *(依赖 T02)*
     - **[测试]** T04: 编写登录异常分支用例 `[简单-2h]`