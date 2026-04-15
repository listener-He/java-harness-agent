# 测试策略与证据落盘标准 (Testing & Evidence)

> **⚠️ Agent 纪律**：本目录不存放测试代码本身，而是定义系统级的测试策略、质量门禁规范，以及每一次需求/Bug 修复后，测试证据（Test Evidence）应该如何落盘。

## 1. 核心测试策略 (Core Strategies)
*描述系统关键模块如何测试。*
- **单元测试 (Unit Testing)**：业务核心 Service 逻辑必须包含单元测试。优先采用 Mockito 等框架进行依赖隔离。
- **集成测试 (Integration Testing)**：关键 DAO 层（Mapper）与 Controller 层，应包含连通性测试。

## 2. 测试证据落盘标准 (Test Evidence Schema)
> **强制要求**：在 `QA Test` 阶段结束时，或者修完 Bug 后，大模型必须按照以下格式生成一份名为 `test_evidence_{特性名}.md` 的客观证据，以供 `post_hook` 或 `fail_hook` 校验，并最终在 `Archive` 时归档。

### 证据模板 (Evidence Template)
```markdown
# 测试证据: {特性或Bug名称}

## 1. 执行环境与命令
- **测试命令**: `mvn test -Dtest=...`
- **代码覆盖范围**: `[影响面清单里的类或方法]`

## 2. 客观日志摘要 (Log Snippet)
- *(粘贴核心测试通过的日志片段，证明测试确实运行且全绿)*
- **失败重试次数**: `N`

## 3. 覆盖的边界用例 (Covered Edge Cases)
- `[Pass]` 测试了并发重复提交，返回 409。
- `[Pass]` 测试了非本租户 ID 查询，返回 403。
- `[Pass]` 测试了正常流程 (Happy Path)。

## 4. 覆盖率指标 (Coverage Metrics) - 可选
- 行覆盖率 (Line Coverage): XX%
- 分支覆盖率 (Branch Coverage): XX%
```

## 3. 历史测试报告与证据索引 (Test Reports)
*（此处由 Archive 阶段的 Agent 自动追加归档的测试证据链接）*

### 2026 年
- 暂无记录
