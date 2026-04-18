# Testing Index — 测试标准与证据

> 测试分层要求、测试数据规范、覆盖率基线、已知不稳定测试、测试证据索引。

## 硬规则 (MUST)
- QA 阶段**必须**生成 `test_evidence_{feature}.md` 文件，作为 Archive 的强制输入。
- 新发现的不稳定测试（Flaky）**必须**追加至本文件，不得忽略。
- 覆盖率下降超过 5% 时，`fail_hook` 触发，回滚至 Implement 阶段。

---

## 1. 测试分层要求 (Test Layers)

| Profile | 单元测试要求 | 集成测试要求 | 证据要求 |
|---------|------------|------------|---------|
| PATCH   | 覆盖修改路径的正/异常分支 | 可选（复杂修改建议做） | 测试命令 + 通过日志摘要 |
| STANDARD | 新增代码行覆盖率 ≥ 80% | 主流程 + 边界场景必须 | CI 报告 + 覆盖率截图 |
| STANDARD HIGH | 同上 + 安全/权限专项测试 | 必须含租户隔离测试 | 同上 + 安全测试报告 |

---

## 2. 测试证据模板 (Evidence Template)

每次 QA 阶段结束后，**必须**输出以下格式的证据文件：

```markdown
# Test Evidence: {feature_or_bug_name}

## 1. 环境 & 命令
- 测试命令: `mvn test -Dtest=OrderServiceTest,OrderControllerTest`
- 覆盖范围: [修改涉及的类/方法列表]

## 2. 客观日志（最小通过证据）
[粘贴测试通过的关键日志行]

## 3. 覆盖的用例
- [Pass] 正常流程: 创建订单成功
- [Pass] 异常流程: 库存不足返回 4001
- [Pass] 权限边界: 跨租户访问返回 403
- [Pass] 幂等性: 重复提交返回已有订单

## 4. 覆盖率（如可获取）
- 行覆盖率: XX%
- 分支覆盖率: XX%

## 5. 失败重试次数
- 重试次数: 0（超过 3 次触发 fail_hook）
```

---

## 3. 测试数据规范 (Test Data)

| 场景 | 准备方式 | 清理策略 | 注意事项 |
|------|----------|----------|----------|
| *(示例) 多租户隔离测试* | *@Sql 插入 tenant_id=1 和 tenant_id=2 的数据* | *@Transactional 自动回滚* | *禁止使用生产 tenant_id* |
| *(示例) 权限测试* | *MockMvc + @WithMockUser* | *无状态，无需清理* | *需覆盖有权限/无权限两种 case* |

---

## 4. 已知不稳定测试 (Flaky Tests)

| 测试类 | 不稳定原因 | 当前处理方式 | 状态 | 登记日期 |
|--------|----------|------------|------|----------|
| *(示例) OrderAsyncServiceTest* | *依赖消息队列时序，偶发超时* | *增大 await 超时时间为 5s* | *观察中* | *2026-03-01* |

---

## 5. 覆盖率基线 (Coverage Baselines)

| 模块 | 行覆盖率 | 分支覆盖率 | 趋势 | 最后更新 |
|------|----------|------------|------|----------|
| *(示例) order-service* | *82%* | *74%* | *↑* | *2026-04-01* |

---

## Archive Extraction SOP

Archive 阶段：
- 将 `test_evidence_{feature}.md` 移入"测试证据索引"并追加链接
- 发现新 Flaky 测试 → 追加至"已知不稳定测试"
- 覆盖率有变化 → 更新"覆盖率基线"

WAL 写入路径：`wal/YYYYMMDD_{topic}_testing_append.md`
WAL 格式参考：[wal/WAL_FORMAT.md](wal/WAL_FORMAT.md)

**触发条件**：任何 PATCH/STANDARD 任务完成后，**必须**写回 testing WAL（至少包含证据文件链接）。

---

## 6. 测试证据索引 (Evidence Index)

*(Archive 阶段自动追加)*

### 2026
- 暂无条目
