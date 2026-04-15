# 🧠 偏好与禁忌索引 (Preferences & Anti-Patterns)

> **⚠️ Agent 纪律**：本域维护大模型（Agent）与人类开发者在此项目中的协作记忆、偏好与禁忌。
> **任何代码修改或架构设计前，强制查阅此域中的相关禁忌！**

## 1. 核心偏好 (Core Preferences)
*(暂无，等待首次 Archive 沉淀)*

## 2. 架构与编码禁忌 (Anti-Patterns & Security Rules)
> **防线：** `intent-gateway` 在 `pre_hook` 阶段必须加载本区块。如果在 `Propose` 或 `Implement` 阶段违反了以下规则，Review 阶段将直接触发 `fail_hook`。

### 2.1 安全红线 (Security Baseline)
- **密钥不落盘**：禁止将任何 API Key、Secret、密码明文硬编码在代码或 `application.yml` 中。必须使用环境变量或配置中心注入。
- **越权防护**：所有接口默认必须校验租户（Tenant）或用户权限，禁止出现可以直接通过 ID 遍历查询的接口（除非明确是公开接口）。
- **细则清单**：[security_rules.md](security_rules.md)

### 2.2 性能红线 (Performance Baseline)
- **禁止 N+1 查询**：禁止在 `for` 循环中执行数据库查询或外部 RPC 调用。必须使用批量查询（`IN` 语句）在循环外组装数据。
- **避免全表扫描**：所有涉及查询的业务表，查询条件必须命中索引。

## 3. 归档与提取规则 (Extraction SOP)
在 `Archive` 阶段，大模型必须请求人类进行 1-10 分打分。
- 如果人类评分 **≤ 5 分**，大模型必须提炼出导致低分的“反模式（Anti-Pattern）”，并按以下模板**追加**到上方的【架构与编码禁忌】中。
- 如果人类评分 **≥ 8 分**，提炼出被表扬的“最佳实践”，追加到【核心偏好】中。

### 写回块模板 (Append Template)
```markdown
- **{规则简述}**: {详细的禁止/推荐做法，以及为什么（低分原因复盘）}
```
