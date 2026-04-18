# AGENTS.md — Entry Map & Core Directives

This file is the single entry point. It contains essential navigation and hard constraints for the Agent.

## 🚨 Hard Safety Constraints (MUST FOLLOW)
- **Budget Limits**: Max 3 Wiki docs, Max 8 Code files per exploration. You MAY use a `<Confidence_Assessment>` to request an elastic extension if close to a breakthrough. If limits are fully exhausted, STOP and use the Escalation Protocol. Do not guess paths or perform runaway searches. ([CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md))
- **Approval Gate**: For MEDIUM/HIGH risk changes, you MUST STOP after creating the spec and wait for human approval (`WAITING_APPROVAL`) before writing any code. ([LIFECYCLE.md](.agents/workflow/LIFECYCLE.md))
- **Anti-Looping**: Max 3 retries for any failing script, test, or linter. If exceeded, STOP and ask the human. You MAY use `bypass_justification.md` to downgrade trivial script failures to WARN. ([HOOKS.md](.agents/workflow/HOOKS.md))
- **Scope Guard**: Do not modify files outside the agreed `focus_card.md` scope without explicit permission.

## 🧭 Initial Action Guidelines

### 第一步：意图确认（MUST，每次任务必须输出）

收到任务后，在任何操作前，先输出一行意图确认：

```
[Intent Check] 识别为 @{profile} | 风险 {LOW/MEDIUM/HIGH} | 意图 {Learn/Change/DocQA/Audit} | 触发原因：{信号词或判断依据}
```

示例：
```
[Intent Check] 识别为 @standard | 风险 HIGH | 意图 Change | 触发原因：关键词"数据库 Migration"→ 自动升级 HIGH
[Intent Check] 识别为 @patch | 风险 LOW | 意图 Change | 触发原因：单点 NPE 修复，影响 1 个方法
[Intent Check] 识别为 @read | 风险 N/A | 意图 Learn | 触发原因：用户未要求修改任何文件
```

用户可以纠正这一行，纠正后按新 profile 执行；否则自动继续。

### 第二步：路由与导航
- **Direct Read**: 用户提供了明确的文件路径或类名 → 直接读取，不从 Wiki Funnel 开始
- **Root Drill-down**: 探索业务域时 → 从 [KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md) 开始向下钻取
- **Resumability**: 会话恢复时 → 先读 `router/runs/launch_spec_*.md` 恢复状态

## 🗂 Single Sources of Truth (SSOT)
- Routing, profiles, shortcuts (`@read`, `@patch`, `@standard`): [.agents/router/ROUTER.md](.agents/router/ROUTER.md)
- Navigation and write-back methodology: [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)
- Lifecycle phases and hooks: [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md), [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md)
- Role mounting + gates: [.agents/workflow/ROLE_MATRIX.md](.agents/workflow/ROLE_MATRIX.md)

## 📚 Essential Pointers
- **Wiki Root Index**: [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md)
- **Specialist Skills Index**: [.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md) (Use this when you need specific expertise)
- **Project Red Lines & Preferences**: [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md)
- **Delivery Schema Template**: [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md)

## 🛑 Team Rule
- **Do not commit runtime state or caches**. The following directories MUST be ignored and never committed:
    - `.agents/router/runs/`
    - `.agents/workflow/runs/`
    - `.agents/events/drift_queue/`
    - Python caches: `__pycache__/`, `*.pyc`
    - Project build & IDE: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`
- **Only commit stable artifacts**: (e.g., source code, `openspec.md`, deliveries, and `wal/` fragments).
