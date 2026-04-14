# OpenSpec 契约模板 (OpenSpec Schema)

> **Agent 纪律**：在 Phase 2 (Propose) 阶段，所有生成的设计文档必须严格遵守此模板，并存放在 `/.trae/llm_wiki/wiki/specs/` 目录下。生成完毕后，必须同时在 `/.trae/llm_wiki/wiki/specs/index.md` 中补充链接与摘要。

---

## 1. 需求背景 (Context)
- **业务目标**：一句话说明为什么要加这个功能。
- **影响面清单 (Scope of Change)**：列出本次特性将新增或修改的模块/包/关键类（为 Review 和 QA 提供客观 Checklist）。
- **依赖知识**：列出在推演该方案时，阅读了哪些前置 Wiki（必须附带绝对或相对路径链接）。
  - 例如：`depends_on: [../wiki/domain/index.md]`

## 2. 领域模型变更 (Domain Model)
*(如果无变更，请写“无”)*
- 新增或修改的名词解释。
- 状态机的变迁图或枚举值变更。

## 3. API 契约 (API Contract) - 【前端 Agent 交接物】
*(如果无变更，请写“无”。此部分必须高度结构化，确保前端 Agent 可直接解析生成 TS Interface 或 Mock 数据)*
- **接口路径**：`POST /api/v1/...`
- **Header/Auth**：是否需要 Token，是否有特殊请求头。
- **入参 (Request)**：
  - 必须提供精确的字段类型、是否必填、校验规则。
  - 必须提供一段标准的 JSON Example。
- **出参 (Response)**：
  - 必须提供完整的 JSON 返回结构（包括错误码结构）。

## 4. 数据模型变更 (Data Model)
*(如果无变更，请写“无”)*
- 表名、新增字段、类型、默认值、索引设计。

## 5. 核心业务逻辑 (Business Logic)
- **步骤拆解**：Step-by-step 描述代码实现逻辑。
- **异常处理**：可能抛出的异常分支与降级处理（Error Handling）。

## 6. 非功能红线 (Non-Functional Constraints) - 【Review 与安全交接物】
*(为了防止大模型在实现时超规格发挥，请显式定义以下约束；如果无，写“无”)*
- **安全与权限 (Security)**：接口是否对外部越权防护？是否有数据权限隔离策略 (Data Permission Strategy)？
- **并发与幂等 (Concurrency & Idempotency)**：是否需要加锁？幂等键 (Idempotency Key) 是什么？
- **禁止模式 (Forbidden Patterns)**：在实现时绝对不能做什么（例如：禁止在 for 循环中 RPC/DB 查询、禁止连表查询、禁止抛出宽泛异常等）。
- **回滚动作 (Rollback Steps)**：如果发生部分失败，需要执行哪些回滚动作（补偿事务/状态回退）。

## 7. 测试验收标准 (Acceptance Criteria) - 【QA Agent 交接物】
*(此部分必须使用结构化语言，供 QA Agent 编写自动化 E2E 或接口测试脚本)*
- **核心正常流 (Happy Path)**：Given / When / Then 格式描述。
- **异常边界流 (Edge Cases)**：如参数越界、并发超卖、权限不足时的预期阻断行为。
- **单元测试要求**：后端代码需要覆盖的核心分支与 Assert 校验点。
