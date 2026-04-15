# Agent 入口 (AGENTS.md)

本文件是本仓库对**任何 Agent / 任何人类读者**的统一入口。无论你是否使用 Trae，本仓库的 Agent 体系都以此为“第一必读”。

## 必读顺序（强制）

1. 读知识图谱根入口：`.agents/llm_wiki/KNOWLEDGE_GRAPH.md`
2. 读路由与检索规则：`.agents/router/ROUTER.md` 与 `.agents/router/CONTEXT_FUNNEL.md`
3. 读工作流与纠偏：`.agents/workflow/LIFECYCLE.md` 与 `.agents/workflow/HOOKS.md`
4. 读归档与并发写回：`.agents/workflow/ARCHIVE_WAL.md`

---

# 项目级规则入口 (Project Rules)

本文件是本仓库的**项目级规则入口**。任何 Agent（无论是否运行在 Trae）在执行任务前，必须先阅读本文件，再进入知识图谱进行逐层下钻。

> 约束目标：不剥夺大模型自主性，但用最小的“硬纪律”保证不跑偏、不膨胀、可断点续传。

## 1. 定位与边界
- 本体系以**后端开发**为主（需求分析、API/数据设计、实现、测试、归档沉淀）。
- 在需要全栈并行协作时，后端阶段会产出可供前端/QA 依赖的交付物，但这不是本体系的主目标。

## 2. 必须遵守的检索规则（知识漏斗）
1. 先读知识图谱根入口：`.agents/llm_wiki/KNOWLEDGE_GRAPH.md`。
2. 只允许沿着 Index 逐层下钻；当索引树找不到时，才允许兜底搜索。
3. 检索与写回的打法详见：`.agents/router/CONTEXT_FUNNEL.md`。

## 3. 必须阅读的引擎流转规范（先学会怎么干活）
在理解“知识在哪”之后，必须立即理解“活怎么干”：
- 路由与队列：`.agents/router/ROUTER.md`
- 生命周期：`.agents/workflow/LIFECYCLE.md`
- 钩子与纠偏：`.agents/workflow/HOOKS.md`

## 4. 生命周期（从需求到归档）
生命周期状态机详见：`.agents/workflow/LIFECYCLE.md`。

必须遵守的关键点：
- **契约先行**：在 Propose 阶段必须产出符合契约模板的 `openspec.md`，模板见：`.agents/llm_wiki/schema/openspec_schema.md`。
- **人类防线（HITL）**：在进入 Implement 之前，必须经过 Approval 强拦截点（由人类确认是否进入实现）。
- **失败回退与防暴走**：任何测试/审查失败必须回退修复；同一阶段连续失败达到最大次数必须停止并请求人类介入。
- **归档与防膨胀**：完成后必须执行知识提取与归档，将不稳定的 Spec 提取为稳定的 API/Data/Domain 索引；超过阈值必须拆分子索引。

## 5. Hooks 与纠偏机制
钩子与守卫详见：`.agents/workflow/HOOKS.md`。

核心纠偏点：
- `guard_hook`：规范守卫 + 领域边界守卫（跨域修改必须明确授权）。
- `fail_hook`：状态降级 + 最大重试防线（防止死循环修复）。
- `loop_hook`：队列消费与闭环推进（如果存在多意图队列）。

## 6. 归档与并发写回（WAL）
归档与并发安全写回详见：`.agents/workflow/ARCHIVE_WAL.md`。

原则：
- Agent 在归档阶段优先“提取知识 + 写 WAL 碎片”，避免直接并发修改公共索引。
- 索引合并与清理由人类或可选脚本在低冲突窗口执行。

## 7. 可选的全栈交付物（仅在需要并行协作时）
当项目存在前端或 QA 并行时，后端 Agent 在 `openspec.md` 中必须提供：
- **前端交接物**：API Contract 的结构化字段 + JSON Example（便于生成 TS Interface/Mock）。
- **QA 交接物**：Acceptance Criteria（Given/When/Then）+ Edge Cases（便于生成自动化测试脚本）。

## 8. 能力入口（Skills）
当需要调用专有能力时，从技能索引开始：`.agents/skills/trae-skill-index/SKILL.md`。

## 9. 路径与链接规范
- 本仓库的 Agent 规则与知识统一收拢在 `.agents/`。
- 文档内链接优先使用相对路径，避免出现 `.agents/...`、硬编码绝对路径等导致的路径幻觉。

