# 意图网关 (Intent Gateway)

## 🎯 定位
意图网关是整个智能研发架构的**绝对入口**与**循环起点**。
通过调用核心入口技能 `[intent-gateway](/.trae/skills/intent-gateway/SKILL.md)` 与主控调度技能 `[devops-lifecycle-master](/.trae/skills/devops-lifecycle-master/SKILL.md)`，网关负责接收自然语言需求，执行上下文检索漏斗，并将任务拆解为可流转的意图队列，分配到对应的生命周期中。

## 🚦 第一动作：启动知识漏斗 (Context Funnel)
**绝对禁止盲搜全文！** 当接收到任何需求时，大模型（Agent）必须：
1. 强制第一步：阅读 `[sitemap.md](/.trae/llm_wiki/sitemap.md)`。
2. 遵循 `[context-funnel.md](/.trae/intent/context-funnel.md)` 中的“逐层下钻”策略，获取业务和架构上下文。
3. 可选探索：如果遇到复杂的领域不知道调用什么能力，使用 `[trae-skill-index](/.trae/skills/trae-skill-index/SKILL.md)` 检索当前可用的专有专家技能。

## 🧩 第二动作：意图映射与队列组装
在掌握足够上下文后，将需求拆解为**标准意图的组合（任务队列）**。
例如：“新增接口并提供测试”，应拆解为 `[Propose.API] -> [Implement.Code] -> [QA.Test]` 串行队列。

| 意图代码 | 触发场景 | 对应生命周期阶段 | 关联核心技能 (Skills) | 并发规则 (Concurrency) |
|---|---|---|---|---|
| `Explore.Req` | 需求分析与任务拆分 | Explorer | `[product-manager-expert](/.trae/skills/product-manager-expert/SKILL.md)`, `[prd-task-splitter](/.trae/skills/prd-task-splitter/SKILL.md)` | 串行 |
| `Propose.API` | 新增/修改接口与架构 | Propose -> Review | `[devops-system-design](/.trae/skills/devops-system-design/SKILL.md)` | 顺序无关 (可与 Data 并发) |
| `Propose.Data`| 新增/修改数据库表或索引 | Propose -> Review | `[devops-system-design](/.trae/skills/devops-system-design/SKILL.md)` | 顺序无关 (可与 API 并发) |
| `Implement.Code` | 编写业务逻辑代码 / 修复 Bug | Implement -> QA | `[devops-feature-implementation](/.trae/skills/devops-feature-implementation/SKILL.md)`, `[devops-bug-fix](/.trae/skills/devops-bug-fix/SKILL.md)` | 必须等待 Propose 结束 |
| `QA.Test` | 编写测试用例 / 代码审查 | QA | `[devops-testing-standard](/.trae/skills/devops-testing-standard/SKILL.md)` | 必须等待 Implement 结束 |

> **💡 并发规则说明**：鉴于 Agent 的流转特性，此处的“并发（可与 xxx 并发）”指的是**顺序无关性**。Agent 依然会按照队列串行执行，但在执行完 `Propose.API` 写回索引时，不会与接着执行的 `Propose.Data` 产生文件锁或逻辑冲突。

## 🚀 第三动作：生成启动计划 (Launch Spec) 与发车
> **⚠️ 引擎 SOP 纪律 (Standard Engine)**：大模型（Agent）是整个流程的“智能主控引擎”。在生成任务队列并发车时，你有充分的灵活性：

1. **队列持久化**：你必须在 `/.trae/intent/catalog/` 下生成 `launch_spec_{timestamp}.md`，并使用 Markdown 任务列表（如 `- [ ] Propose.API`）记录意图队列。
2. **状态流转驱动**：你可以直接使用内置的文件编辑工具（如 `Write` 或 `SearchReplace`）将队列里的 `[ ]` 更新为 `[x]`，来推进你的执行状态。
3. **辅助工具（可选）**：如果遇到极度复杂、需要精确重试控制的任务，你可以调用辅助脚本 `python .trae/scripts/harness/engine.py init "..."` 让脚本帮你托管状态机。

随后，大模型自主进入 Harness Lifecycle（参考 `[lifecycle.md](/.trae/harness/lifecycle.md)`）开启流水线。在结束每一轮 Archive 阶段后，大模型**必须主动回溯读取** `launch_spec.md` 的状态，以决定是执行下一个意图，还是结束工作向用户汇报。
