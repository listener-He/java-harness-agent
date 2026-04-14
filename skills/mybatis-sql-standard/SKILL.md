---
name: "mybatis-sql-standard"
description: "Enforces strict MyBatis SQL writing standards. Focuses on performance, anti-JOIN strategies, index utilization, and implicit type conversion prevention. Invoke when writing or reviewing Mapper XML or LambdaQuery."
---

# MyBatis SQL Writing & Database Performance Standards

This skill defines the strict rules for writing SQL queries within the project, specifically tailored for MyBatis / MyBatis-Plus environments. The core philosophy is **Application-Level Joins over Database-Level Joins** and **Maximum Index Efficiency**.

## 1. 连表与聚合规范 (Anti-JOIN Strategy)

**核心原则：能不连表，坚决不连表。把计算和组装压力放在应用层，而不是数据库。**

- **单表优先**：绝大多数业务查询必须是单表查询。
- **禁止无意义的 JOIN**：仅仅为了获取字典名称、外键关联表的某个冗余字段（如通过 `dept_id` 获取 `dept_name`），**绝对禁止使用 JOIN**。必须在 Service 层使用 `Complete.start().build().over()` 工具类进行应用层内存组装。
- **允许 JOIN 的特例**：
  - **条件过滤强依赖**：当查询条件（WHERE）或排序（ORDER BY）强依赖于另一张表的字段时，允许使用 JOIN。
  - **性能评估**：即使满足上述特例，如果关联表数据量极大，也应优先考虑在应用层分步查询（先查 A 表 ID 集合，再用 `IN` 查 B 表）。

## 2. 索引与隐式转换防范 (Index & Type Conversion)

隐式类型转换是导致索引失效（Index Invalidation）的头号杀手。

- **类型严格匹配**：SQL 的查询条件类型必须与数据库字段类型**完全一致**。
  - 如果数据库字段是 `VARCHAR`，传入的参数必须是 `String`，严禁传入 `Integer` 或 `Long`。
  - 如果数据库字段是 `BIGINT`，传入的参数必须是 `Long`，严禁传入 `String`。
- **避免在索引列上使用函数**：禁止在 WHERE 条件的等号左侧对索引列进行任何函数操作（如 `DATE(create_time) = '2023-01-01'`），这会导致全表扫描。
- **避免隐式字符集转换**：在进行 JOIN 时（虽然不推荐），必须确保关联条件的两个字段字符集（Charset）和排序规则（Collation）完全一致。

## 3. 联合索引使用规范 (Composite Index Rules)

- **最左前缀原则 (Leftmost Prefix Rule)**：在编写 WHERE 条件时，条件的顺序必须尽量贴合联合索引的创建顺序。
  - 示例：如果存在联合索引 `idx_tenant_dept_status (tenant_id, dept_id, status)`，则查询条件必须包含 `tenant_id` 才能触发索引。
- **范围查询截断**：联合索引中，一旦遇到范围查询（`>`, `<`, `BETWEEN`, `LIKE`），其右侧的列将无法使用索引。
  - **最佳实践**：将等值查询（`=`、`IN`）的条件放在前面，范围查询放在最后。

## 4. MyBatis / MyBatis-Plus 编写规范

- **LambdaQueryWrapper 优先**：简单的单表查询，强制使用 MyBatis-Plus 的 `lambdaQuery()` 链式调用，避免硬编码字段名。
- **XML 动态 SQL**：
  - 必须使用 `<if test="... != null and ... != ''">` 进行条件判空。
  - **禁止使用 `${}`**：除非是动态表名或动态排序字段（需严格白名单校验），否则必须使用 `#{}` 防止 SQL 注入。
  - **避免大表 `IN` 查询**：如果 `IN` 集合的数量可能超过 1000 个，必须在应用层进行分批处理（Partitioning），防止 SQL 语句过长和内存溢出。
- **`select *` 限制**：
  - 严禁在 XML 中写死 `SELECT *`。
  - 在大表查询中，只 `SELECT` 业务真正需要的字段（特别是包含大文本、JSON 字段时）。

## 5. 租户隔离的底层保证 (Tenant Isolation)

- 在手写 XML SQL 时，**不要忘记加上租户隔离条件**。
- `WHERE tenant_id = #{tenantId}` 应该是绝大多数业务表查询的第一个条件（通常也是联合索引的第一个字段）。

## 6. 绝对禁止的语法
- *${}* 语法 绝对禁止使用，必须使用 *#{}* 语法。 如需实现 order by 动态排序，请使用 *<if test="">* 语法。自定义类型对应的字段来实现而不是使用 *${}* 语法。
