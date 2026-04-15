# AGENTS.md — 统一入口（人类 & Agent）

本文件只做一件事：把你带到“正确的入口”，并说明必须遵守的最小纪律。

## TL;DR（默认主路径）

1. 任何自然语言需求 → 先走【意图网关】。
2. 意图网关的第一动作 → 启动【知识漏斗】（从知识图谱根节点逐层下钻）。
3. 推进交付 → 严格按【生命周期】流转，并在【归档/WAL】阶段写回证据与知识。

## 1) 入口：意图网关（绝对入口）

- 读：[.agents/router/ROUTER.md](.agents/router/ROUTER.md)
- 用：`intent-gateway`（意图映射 + 上下文检索漏斗）与 skill ->`devops-lifecycle-master`（生命周期主控调度）

## 2) 第一动作：知识漏斗（禁止盲搜）

- 先读根：[.agents/llm\_wiki/KNOWLEDGE\_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md)
- 只允许沿 Index 逐层下钻；找不到再兜底搜索
- 细则：[.agents/router/CONTEXT\_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)

## 3) 交付：生命周期（先契约，后实现）

- 状态机与阶段：[.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md)
- 钩子与纠偏：[.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md)
- Propose 阶段必须产出 `openspec.md`（模板）：[.agents/llm\_wiki/schema/openspec\_schema.md](.agents/llm_wiki/schema/openspec_schema.md)
- 变更敏感度为 MEDIUM/HIGH 且未经过 Approval 等待点：禁止进入实现（Implement）；LOW 可跳过但需写明理由

## 4) 归档：WAL（防膨胀、可断点续传）

- 规则与并发写回：[.agents/workflow/ARCHIVE\_WAL.md](.agents/workflow/ARCHIVE_WAL.md)
- 原则：优先“提取知识 + 写 WAL 碎片”，避免并发改公共索引

## 5) 能力入口（不会选技能就来这里）

- 技能索引：[.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md)

## 团队协作约定（强制）

- 默认不提交运行态文件：`.agents/router/runs/` 与 `.agents/workflow/runs/`
- 团队只共享稳定产物：规范/模板/Wiki 索引与内容、必要的契约与交付文档；运行态与个人进度不作为团队事实源

## 硬纪律（最小集合）

- 禁止越级猜文件路径；必须从 Knowledge Graph 根节点逐层下钻
- 禁止上来全文盲搜；先 Funnel，再搜索
- 禁止在变更敏感度为 MEDIUM/HIGH 时跳过契约与 Approval 直接实现
- 失败必须回退修复；触发最大重试防线就停止并请求人类介入
- 完成必须归档：证据落盘 + WAL 写回
