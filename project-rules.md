# 项目级规则入口 (Project Rules)

本文件是本仓库的**项目级规则入口**。任何 Agent（无论是否运行在 Trae）在执行任务前，必须先阅读本文件，再进入知识图谱进行逐层下钻。

> 约束目标：不剥夺大模型自主性，但用最小的“硬纪律”保证不跑偏、不膨胀、可断点续传。

## 1. 定位与边界
- 本体系以**后端开发**为主（需求分析、API/数据设计、实现、测试、归档沉淀）。
- 在需要全栈并行协作时，后端阶段会产出可供前端/QA 依赖的交付物，但这不是本体系的主目标。

## 2. 必须遵守的检索规则（知识漏斗）
1. 先读知识图谱根入口：[LLM Wiki Sitemap](llm_wiki/sitemap.md)。
2. 只允许沿着 Index 逐层下钻；当索引树找不到时，才允许兜底搜索。
3. 检索与写回的打法详见：[Context Funnel](intent/context-funnel.md)。

## 3. 生命周期（从需求到归档）
生命周期状态机详见：[Lifecycle](harness/lifecycle.md)。

必须遵守的关键点：
- **契约先行**：在 Propose 阶段必须产出符合契约模板的 `openspec.md`，模板见：[OpenSpec Schema](llm_wiki/schema/openspec_schema.md)。
- **人类防线（HITL）**：在进入 Implement 之前，必须经过 Approval 强拦截点（由人类确认是否进入实现）。
- **失败回退与防暴走**：任何测试/审查失败必须回退修复；同一阶段连续失败达到最大次数必须停止并请求人类介入。
- **归档与防膨胀**：完成后必须执行知识提取与归档，将不稳定的 Spec 提取为稳定的 API/Data/Domain 索引；超过 500 行必须拆分子索引。

## 4. Hooks 与纠偏机制
钩子与守卫详见：[Hooks](harness/hooks.md)。

核心纠偏点：
- `guard_hook`：规范守卫 + 领域边界守卫（跨域修改必须明确授权）。
- `fail_hook`：状态降级 + 最大重试防线（防止死循环修复）。
- `loop_hook`：队列消费与闭环推进（如果存在多意图队列）。

## 5. 可选的全栈交付物（仅在需要并行协作时）
当项目存在前端或 QA 并行时，后端 Agent 在 `openspec.md` 中必须提供：
- **前端交接物**：API Contract 的结构化字段 + JSON Example（便于生成 TS Interface/Mock）。
- **QA 交接物**：Acceptance Criteria（Given/When/Then）+ Edge Cases（便于生成自动化测试脚本）。

## 6. 能力入口（Skills）
当需要调用专有能力时，从技能索引开始： [Skill Index](skills/trae-skill-index/SKILL.md)。

## 7. 路径与链接规范（不出现“.trae”的可移植写法）
- 本仓库的规则与知识主要位于 `.trae/` 目录，但**在 Markdown 链接中统一使用相对路径**（如 `llm_wiki/sitemap.md`），避免链接里出现“.trae”。
- 原则：链接永远以“当前文件所在目录”为基准解析，保证在非 Trae 环境的 Markdown 阅读器中也能正确跳转。
