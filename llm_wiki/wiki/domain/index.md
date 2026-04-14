# 领域模型与业务字典 (Domain Model & Dictionary)

> **⚠️ Agent 纪律**：本索引存储全系统的【统一语言 (Ubiquitous Language)】。大模型在 `Explorer` 和 `Propose` 阶段，必须参考此处的名词解释，防止业务理解偏差。

## 1. 核心概念与状态机 (Core Concepts & State Machines)

| 概念 (Concept) | 一句话定义 (Definition) | 状态机/枚举/规则详情页 |
|---|---|---|
| *(示例) Opportunity* | 销售商机，代表一个潜在的成单机会 | `[opportunity_states.md]` |

---

## 2. 归档与提取规则 (Extraction SOP)
如果在 `openspec.md` 中定义了**全新的名词、角色、枚举值或状态流转**，在 `Archive` 阶段必须将其提取到本索引。

### 写回块模板 (Append Template)
```markdown
| {业务名词} | {1-2句话定义与业务边界} | `[{详细说明文档}]` |
```

> **防膨胀提醒**：名词超过 30 个时，按业务线拆分为独立的 `dictionary_xxx.md`。
