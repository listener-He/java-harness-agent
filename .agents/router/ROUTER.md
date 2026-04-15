# 意图网关 (Intent Gateway)

## 🎯 定位
意图网关是整个智能研发架构的**绝对入口**与**循环起点**。
通过调用核心入口技能 `[intent-gateway](../skills/intent-gateway/SKILL.md)` 与主控调度技能 `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)`，网关负责接收自然语言需求，执行上下文检索漏斗，并将任务拆解为可流转的意图队列，分配到对应的生命周期中。

## 🚦 第一动作：启动知识漏斗 (Context Funnel)
**绝对禁止盲搜全文！** 当接收到任何需求时，大模型（Agent）必须：
1. 强制第一步：阅读 `[KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)`。
2. 遵循 `[CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)` 中的“逐层下钻”策略，获取业务和架构上下文。
3. 可选探索：如果遇到复杂的领域不知道调用什么能力，使用 `[trae-skill-index](../skills/trae-skill-index/SKILL.md)` 检索当前可用的专有专家技能。

## 🧩 第二动作：意图映射与队列组装
在掌握足够上下文后，将需求拆解为**标准意图的组合（任务队列）**。
例如：“新增接口并提供测试”，应拆解为 `[Propose.API] -> [Implement.Code] -> [QA.Test]` 串行队列。

| 意图代码 | 触发场景 | 对应生命周期阶段 | 关联核心技能 (Skills) | 并发规则 (Concurrency) |
|---|---|---|---|---|
| `Explore.Req` | 需求分析与任务拆分 | Explorer | `[product-manager-expert](../skills/product-manager-expert/SKILL.md)`, `[prd-task-splitter](../skills/prd-task-splitter/SKILL.md)` | 串行 |
| `Audit.Codebase` | 代码体检 / 架构评审 / 风险扫描（只读） | Gateway (Read-only) | `[intent-gateway](../skills/intent-gateway/SKILL.md)`, `[devops-review-and-refactor](../skills/devops-review-and-refactor/SKILL.md)` | 串行 |
| `QA.Doc` | 基于 Wiki/需求文档的问答（只读） | Gateway (Doc QA) | `[intent-gateway](../skills/intent-gateway/SKILL.md)` | 串行 |
| `QA.Doc.Actionize` | 将问答结论动作化为可执行意图队列（需确认） | Gateway -> Lifecycle (HITL) | `[intent-gateway](../skills/intent-gateway/SKILL.md)`, `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)` | 串行 |
| `Propose.API` | 新增/修改接口与架构 | Propose -> Review | `[devops-system-design](../skills/devops-system-design/SKILL.md)` | 顺序无关 (可与 Data 并发) |
| `Propose.Data`| 新增/修改数据库表或索引 | Propose -> Review | `[devops-system-design](../skills/devops-system-design/SKILL.md)` | 顺序无关 (可与 API 并发) |
| `Implement.Code` | 编写业务逻辑代码 / 修复 Bug | Implement -> QA | `[devops-feature-implementation](../skills/devops-feature-implementation/SKILL.md)`, `[devops-bug-fix](../skills/devops-bug-fix/SKILL.md)` | 必须等待 Propose 结束 |
| `QA.Test` | 编写测试用例 / 代码审查 | QA | `[devops-testing-standard](../skills/devops-testing-standard/SKILL.md)` | 必须等待 Implement 结束 |

### 流程 1：只读审计（`Audit.Codebase`）
- 目标：对当前代码库做分析/评估，产出结构化审计报告与证据引用
- 只读约束：不改代码、不写 Wiki、不生成 launch spec、不进入 lifecycle
- 允许动作：只读检索与读取；允许运行测试/构建，但不得修改任何已跟踪文件
- 产出要求：每条结论必须带证据（文件路径 + 行号范围）与影响/建议

### 流程 2：Doc QA（`QA.Doc` / `QA.Doc.Actionize`）
- `QA.Doc`：按知识漏斗逐层下钻，输出带引用的答案（引用到 Wiki/需求段落，必要时补充代码引用）
- `QA.Doc.Actionize`：将问答结论转成“可执行意图队列”，必须先问一次是否发车；同意后才生成 launch spec 并进入生命周期

## 🚀 第三动作：生成启动计划 (Launch Spec) 与发车
> **⚠️ 引擎 SOP 纪律 (Standard Engine)**：大模型（Agent）是整个流程的“智能主控引擎”。在生成任务队列并发车时，你有充分的灵活性：

1. **队列持久化**：你必须在 `router/runs/` 下生成 `launch_spec_{timestamp}.md`，并使用“状态机表格”记录意图队列与当前阶段。
2. **状态流转驱动**：只更新表格中的 `Status/Phase/Failed_Reason` 字段，避免修改 Checkbox 造成的匹配失败与状态错乱。
3. **辅助工具（可选）**：如果需要严格记录失败次数与阶段流转，可调用 `python ../scripts/harness/engine.py init "..."` 生成并维护该文件。

随后，大模型自主进入 Harness Lifecycle（参考 `[LIFECYCLE.md](../workflow/LIFECYCLE.md)`）开启流水线。在结束每一轮 Archive 阶段后，大模型**必须主动回溯读取** `launch_spec.md` 的状态，以决定是执行下一个意图，还是结束工作向用户汇报。

### Launch Spec 模板（机器友好，支持断点续传）

状态枚举：`PENDING`, `IN_PROGRESS`, `DONE`, `WAITING_APPROVAL`, `FAILED`

```markdown
# 启动计划 (Launch Spec) - {YYYYMMDD_HHMMSS}

## 状态机 (State Machine)
| Intent | Status | Phase | Artifact/Log | Failed_Reason |
|---|---|---|---|---|
| Explore.Req | IN_PROGRESS | 1_Explorer | `explore_report.md` | - |
| Propose.API | PENDING | - | - | - |
| Implement.Code | PENDING | - | - | - |

## 断点续传 (Resume)
- 若会话中断/人类延迟回复，下一次被唤醒时第一动作先读本文件。
- 若存在 `WAITING_APPROVAL`：进入 Approval 等待点，读取对应 `openspec.md`，等待人类确认后将该行切回 `IN_PROGRESS` 并进入 Implement。
- 若存在 `FAILED`：停止自动推进，优先向人类报告 `Failed_Reason` 并请求介入。
```
