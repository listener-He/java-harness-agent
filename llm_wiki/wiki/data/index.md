# 数据模型索引 (Data Models Index)

> **⚠️ Agent 纪律**：本文件是系统所有表结构、ER 图、核心索引策略的【路由网】。严禁大模型通过硬搜全局代码来猜测表结构。

## 1. 核心业务表清单 (Core Tables)

| 表名 (Table Name) | 实体摘要 (Entity Purpose) | 核心字段提示 | 变更文档来源 |
|---|---|---|---|
| *(示例) sys_user* | 存储用户核心信息与凭证 | `id, username, tenant_id(索引)` | `[user_table.md]` |

---

## 2. 归档与提取规则 (Extraction SOP)
在 `Archive` 阶段的 `post_hook` 中，Agent 必须将 `openspec.md` 中的表变更动作【追加】到上述表格中。

### 写回块模板 (Append Template)
```markdown
| {Table Name} | {一句话说明表的用途} | `{核心字段及特殊索引}` | `[{特性文档名}]` |
```

> **防膨胀提醒**：超过 50 个表时，按模块（如 `auth_tables.md`, `trade_tables.md`）拆分并仅保留一级链接。
