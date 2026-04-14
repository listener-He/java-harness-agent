# ⚙️ 规范域索引 (Schema Index)

本域维护所有全局性、通用性的研发契约模板与流程规则。
当需要了解“该输出什么格式的文档”时，请查阅本域。

## 快速开始（推荐阅读顺序）
1. 阅读 **契约模板**：明确后端研发在 Propose 阶段应交付的文档格式与字段粒度，保证后续实现与回归可落地。
2. 阅读 **流程与守卫**：明确这些契约在生命周期中的“冻结点、拦截点、纠偏点”分别在哪里，避免设计与实现跑偏。

## 契约模板（Schema）
- **[OpenSpec 契约模板 (OpenSpec Schema)](/.trae/llm_wiki/schema/openspec_schema.md)**：后端提案统一格式。*如需并行协作*，其中的 API Contract 与 Acceptance Criteria 可作为前端/QA 的可选交接物（包含 JSON Example 与 Given/When/Then）。

## 流程与守卫（跨域索引）
本域不重复写流程正文，但提供“从契约到执行”的关键挂载点：
- **[意图网关 (Intent Gateway)](/.trae/intent/intent-gateway.md)**：把需求拆成意图队列（launch_spec），定义交接与并发语义（顺序无关性）。
- **[知识漏斗 (Context Funnel)](/.trae/intent/context-funnel.md)**：契约的正向读取与反向写回（Archive 写回索引的打法）。
- **[生命周期 (Lifecycle)](/.trae/harness/lifecycle.md)**：Phase 3.5 为“契约冻结与广播”发令枪；冻结后前端/QA Agent 可启动并行工作。
- **[生命周期 (Lifecycle)](/.trae/harness/lifecycle.md)**：Phase 3.5 为“契约冻结与广播”发令枪；若项目需要前端/QA 并行推进，则以该节点作为正式交接点。
- **[钩子守卫 (Hooks)](/.trae/harness/hooks.md)**：guard/fail/loop 等纠偏机制（Max Retries、领域边界、HITL）。

## 链接规范（统一标准）
- 本知识库内所有索引链接优先使用从项目根出发的绝对路径（如 `/.trae/llm_wiki/...`），避免相对路径造成断头链接。

## 流程规则
- 流程规则不在 schema/index.md 内展开，请以“流程与守卫（跨域索引）”中的挂载点为准。
