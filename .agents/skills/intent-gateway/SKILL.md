---
name: "intent-gateway"
description: "意图网关技能：接收自然语言需求，执行上下文检索漏斗，并发分发到对应意图的生命周期中。作为整个框架的入口被调用。"
---

# 🧠 Intent Gateway Skill (意图网关)

**Focus**: 需求理解 (Requirement Understanding)、自主检索下钻 (Agentic Drill-down Search)、多流程调度 (Multi-Flow Orchestration)。

这是本架构的**中枢调度技能**。当你需要启动一个新需求或分析一个复杂的跨域任务时，**必须首先调用本技能**。

---

## 🛡️ 触发机制 (TRIGGER CONDITION)
- 任何新的特性开发、需求分析、重构任务，都必须从本技能开始。
- 严禁绕过本技能直接编写代码或设计规范。

## 📋 意图网关执行协议 (Gateway Execution Protocol)

### 步骤 1：启动自主检索漏斗 (The Context Funnel)
**规则：绝不盲目加载全局知识，必须沿着 Sitemap 逐层下钻。**
1. **强制动作**：使用 `Read` 工具读取 `.agents/llm_wiki/KNOWLEDGE_GRAPH.md`。
2. **分析**：根据用户的需求（例如：“增加一个销售排行榜”），判断需要哪些领域的知识。
3. **下钻**：使用 `Read` 工具读取选定领域的索引文件（例如 `.agents/llm_wiki/wiki/domain/index.md` 和 `.agents/llm_wiki/wiki/api/index.md`）。
4. **精读**：在局部索引中找到具体的文档链接后，如果认为必要，再次使用 `Read` 工具读取具体文档的内容。
5. **记忆提取**：在结束探索前，必须读取 `.agents/llm_wiki/wiki/preferences/index.md`，了解本项目的禁忌和偏好。

### 步骤 2：意图映射与冲突检测 (Intent Mapping & Conflict Resolution)
根据用户输入，将任务映射到一个或多个意图（意图词表详见 `.agents/router/ROUTER.md`）。
- 例如：“帮我理一下这个需求，然后出个表结构设计”，对应意图为 `[Explore.Req, Propose.Data]`。
- 例如：“代码体检/架构评审”，对应意图为 `[Audit.Codebase]`（只读）。
- 例如：“规范是什么/某文档怎么理解”，对应意图为 `[QA.Doc]`（默认只读，必要时可选 `QA.Doc.Actionize`）。
- **冲突检测**：如果判定并发执行会导致同一个文件（如某个 `index.md`）的写入冲突，必须安排串行执行，或建立独立的 Session 沙箱。

### 步骤 3：可选发车：生成启动计划 (Optional Launch Plan)
仅当满足以下条件之一时，才生成 `launch_spec.md` 并进入 Harness 生命周期：
- 用户明确要“做需求/改代码/出方案并落地”，且意图队列包含 `Explore.Req`、`Propose.*`、`Implement.*`、`QA.Test` 等生命周期意图
- 用户在 `QA.Doc` 的 Actionize Gate 明确同意，将其升级为 `QA.Doc.Actionize`

严格只读意图（如 `Audit.Codebase`、默认的 `QA.Doc`）只交付报告/答案，不生成 `launch_spec.md`，不写回 Wiki。

### 步骤 4：交付与流转 (Handoff)
- 结束本技能的执行，并在回复中告知用户：
  > "意图网关分析完毕。已根据 Sitemap 检索并装配了上下文。"
  > "若已发车：启动计划已生成，接下来进入 Harness 生命周期的 `[目标阶段名称]`。"
