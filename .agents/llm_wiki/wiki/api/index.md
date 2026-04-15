# API 契约索引 (API Contracts Index)

> **⚠️ Agent 纪律**：本索引是系统所有对外暴露接口的【路由网】。在 `Archive` 阶段，Agent 必须将 `openspec.md` 中的接口签名提取并【追加】到本文件对应的子域表格中。

## 1. 核心域接口汇总 (Core Domain APIs)

| 接口 (Method Path) | 功能摘要 | 文档链接 | 写回时间 |
|---|---|---|---|
| *(示例) POST /api/v1/user/login* | 用户登录并下发 Token | `[user_api.md]` | 2026-04-14 |

---

## 2. 归档与提取规则 (Extraction SOP)
在 `Archive` 阶段，Agent 必须按照以下【写回块模板】进行操作：

### 写回块模板 (Append Template)
```markdown
| {Method} {Path} | {一句话摘要} | `[{特性文档名}]` | {YYYY-MM-DD} |
```

> **防膨胀提醒**：如果本表格超过 50 行，Agent 必须主动按业务模块（如 `user/`, `trade/`）拆分子目录 index。
