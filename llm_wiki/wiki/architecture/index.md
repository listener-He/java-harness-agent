# 架构决策与设计 (Architecture & ADRs)

> **⚠️ Agent 纪律**：在进行模块拆分、技术选型、重大中间件引入时，必须在此查阅或新增 ADR (Architecture Decision Record)。

## 1. 核心基线与守卫 (Baselines & Guards)
- **安全与合规基线**：`[../preferences/security_rules.md]` - 所有新增代码的底线要求。
- *(其他全局拓扑、部署架构占位)*

## 2. 架构决策记录 (ADRs)

| 决策号 (ADR #) | 标题 (Title) | 状态 (Status) | 结论摘要 |
|---|---|---|---|
| *(示例) ADR-001* | 选用 JWT 作为无状态 Auth 方案 | ✅ Accepted | 降低 Redis 依赖，配合网关层验签 |

---

## 3. 归档与提取规则 (Extraction SOP)
如果在 `Propose` 阶段进行了**影响全局的架构选型或模块边界定义**，在 `Archive` 时必须将其写回 ADR 列表。

### 写回块模板 (Append Template)
```markdown
| ADR-{XXX} | {技术选型标题} | ✅ Accepted | {一句话为什么这么选} |
```
