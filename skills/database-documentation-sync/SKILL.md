---
name: "database-documentation-sync"
description: "数据库文档同步规范。修改数据库表结构（SQL或Entity）时，必须同步更新对应的表文档、模块描述文档中的表清单和ER图。"
---

# 数据库文档同步规范

当修改数据库表结构时，必须同步更新相关文档，确保代码与文档一致。

## 1. 文档位置

| 文档类型 | 路径 |
|---------|------|
| 表定义文档 | `.trae/docs/db/{表名}.md` |
| 建表SQL | `src/main/resources/sql/{模块名}_tables.sql` |
| 模块描述 | `.trae/docs/module_description/{模块名}.md` |

## 2. 修改场景与同步要求

### 2.1 新增表

当新增数据库表时，必须完成以下同步：

1. **创建表定义文档** `.trae/docs/db/{表名}.md`
   - 表说明
   - 字段定义（字段名、类型、必填、说明）
   - 索引定义
   - 建表SQL

2. **更新建表SQL文件** `src/main/resources/sql/{模块名}_tables.sql`
   - 添加 CREATE TABLE 语句

3. **更新模块描述文档** `.trae/docs/module_description/{模块名}.md`
   - 在「数据表清单」章节添加表引用
   - 在「表关系图」章节更新 ER 图

### 2.2 修改表字段

当修改表字段（增加/删除/修改）时，必须完成以下同步：

1. **更新表定义文档** `.trae/docs/db/{表名}.md`
   - 修改字段定义表格
   - 更新建表SQL

2. **更新建表SQL文件** `src/main/resources/sql/{模块名}_tables.sql`
   - 修改对应的 CREATE TABLE 语句

3. **更新Entity实体类**（如果存在）
   - 同步字段和注解

### 2.3 修改表索引

当修改表索引时，必须完成以下同步：

1. **更新表定义文档** `.trae/docs/db/{表名}.md`
   - 修改索引定义章节
   - 更新建表SQL

2. **更新建表SQL文件** `src/main/resources/sql/{模块名}_tables.sql`
   - 修改对应的索引语句

### 2.4 删除表

当删除数据库表时，必须完成以下同步：

1. **删除表定义文档** `.trae/docs/db/{表名}.md`

2. **更新建表SQL文件** `src/main/resources/sql/{模块名}_tables.sql`
   - 删除对应的 CREATE TABLE 语句

3. **更新模块描述文档** `.trae/docs/module_description/{模块名}.md`
   - 从「数据表清单」章节移除表引用
   - 更新「表关系图」章节的 ER 图

4. **删除Entity实体类**（如果存在）

## 3. 表定义文档模板

```markdown
# {表名}

## 表说明

{表的用途和说明}

## 字段定义

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | BIGINT | 是 | - | 主键 |
| tenant_id | BIGINT | 是 | - | 租户ID |
| ... | ... | ... | ... | ... |
| create_date | DATETIME | 是 | CURRENT_TIMESTAMP | 创建时间 |
| update_date | DATETIME | 是 | CURRENT_TIMESTAMP | 更新时间 |
| is_deleted | TINYINT | 是 | 0 | 逻辑删除标记 |

## 索引定义

| 索引名 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| PRIMARY | id | 主键 | 主键索引 |
| idx_{表名}_{字段} | {字段} | 普通 | {说明} |

## 建表SQL

\`\`\`sql
CREATE TABLE `{表名}` (
    ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{表注释}';
\`\`\`
```

## 4. 模块描述文档更新示例

### 数据表清单章节

```markdown
| 表名 | 说明 | 详细定义 |
|-----|------|----------|
| {表名} | {说明} | [{表名}.md](../db/{表名}.md) |
```

### 表关系图章节

使用文本形式的 ER 图，展示表之间的关联关系：

```
table_a (N) ──────┐
      │           │
      ▼           ▼
table_b (1)   table_c (1)
      │
      ▼
table_d (N)
```

## 5. 检查清单

修改数据库结构后，确认以下事项：

- [ ] 表定义文档已更新
- [ ] 建表SQL已更新
- [ ] 模块描述文档的表清单已更新
- [ ] 模块描述文档的ER图已更新（如有关系变化）
- [ ] Entity实体类已同步
- [ ] 相关Mapper/接口文档已同步
