---
name: "mybatis-sql-standard"
description: "Enforces strict MyBatis SQL writing standards, database table design boundaries, and data modeling structures. Focuses on performance, anti-JOIN strategies, index utilization, implicit type conversion prevention, and robust table schemas."
---

# SYSTEM DIRECTIVE: MyBatis SQL & Database Design Standard

## 🎯 Core Objective
This skill dictates the absolute rules for designing database tables, modeling data structures, and writing SQL queries in a MyBatis/MyBatis-Plus environment. The fundamental philosophies are:
1. **Application-Level Assembly over Database-Level JOINs**
2. **Defensive Data Modeling with Strict Boundaries**
3. **Maximum Index Efficiency & Query Predictability**

---

## 🏗 1. Table Design & Data Modeling Boundaries

### 1.1 Strict Bounded Contexts (Microservice-Ready)
**Rule:** Tables must be designed as if they are in separate microservices, even within a monolith.
- **No Foreign Keys (FK):** Physical Foreign Keys are STRICTLY PROHIBITED. Use logical relationships (e.g., storing `user_id` as a `BIGINT`).
- **Domain Isolation:** Do not create God-Tables. Split wide tables vertically. E.g., `user_core` (auth/login) vs `user_profile` (avatar/bio) vs `user_settings` (preferences).
- **JSON for Schema-less Data:** Use `JSON` data types for highly dynamic, non-searchable attributes (e.g., `extra_properties`, `form_snapshots`). Do NOT extract them into EAV (Entity-Attribute-Value) anti-pattern tables unless they require indexing.

### 1.2 Standardized Base Columns
**Rule:** EVERY business table MUST include the following 8 standard audit and control fields:
- `id` (BIGINT, Primary Key, Snowflake/Auto-increment)
- `tenant_id` (BIGINT, NOT NULL, default 0 - for data isolation/multi-tenancy)
- `create_time` (DATETIME, NOT NULL, default CURRENT_TIMESTAMP)
- `update_time` (DATETIME, NOT NULL, default CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
- `create_by` (BIGINT, NOT NULL, creator's ID)
- `update_by` (BIGINT, NOT NULL, updater's ID)
- `is_deleted` (TINYINT, NOT NULL, default 0 - for soft deletes, 0=normal, 1=deleted)
- `version` (INT, NOT NULL, default 0 - for Optimistic Locking)

---

## ⚡ 2. Anti-JOIN Strategy (Application-Level Assembly)

**Rule:** Offload computational and assembly pressure from the DB to the Application layer.
- **Single Table Preference:** 95% of business queries MUST be single-table queries.
- **Prohibited JOINs:** NEVER use `JOIN` purely to fetch dictionary names, enumerations, or redundant fields from a related table (e.g., joining `dept` just to get `dept_name` using `dept_id`).
  - **✅ POSITIVE EXAMPLE (App-Level Assembly):**
    Query `User` list first. Extract `dept_id`s. Query `Dept` table `WHERE id IN (...)`. Assemble in memory using Functional Utilities.
  - **❌ NEGATIVE EXAMPLE (DB-Level JOIN):**
    `SELECT u.*, d.dept_name FROM user u LEFT JOIN dept d ON u.dept_id = d.id` (Banned).
- **Allowed JOIN Exceptions:** You may use `JOIN` ONLY WHEN the filtering (`WHERE`) or sorting (`ORDER BY`) strictly depends on the joined table's columns AND data volume is strictly controlled.
- **Deep Pagination & Large IN Clauses (OOM Protection):** When assembling data in memory, if the first query returns a massive number of IDs (e.g., >1000), you MUST NOT pass them all into an `IN (...)` clause at once. You must use `Lists.partition(ids, 500)` to batch the queries, or rely on proper pagination to limit the initial dataset.

---

## 🔍 3. Index Design & Implicit Conversion Prevention

**Rule:** Every query must hit an index. Full table scans are treated as critical bugs.

### 3.1 Implicit Type Conversion (The Silent Killer)
**Rule:** SQL query parameters MUST perfectly match the database column types.
- **String vs Numeric:** If the DB column is `VARCHAR`, the Java parameter MUST be `String`. If DB is `BIGINT`, Java MUST be `Long`.
- **❌ NEGATIVE EXAMPLE:** `WHERE order_sn = 123456789` (DB is `VARCHAR(32)`). This forces the DB to cast the column to INT, disabling the index.
- **Function on Indexed Columns:** NEVER use functions on the left side of the operator.
  - **❌ NEGATIVE EXAMPLE:** `WHERE DATE(create_time) = '2023-01-01'` (Index disabled).
  - **✅ POSITIVE EXAMPLE:** `WHERE create_time >= '2023-01-01 00:00:00' AND create_time < '2023-01-02 00:00:00'`.

### 3.2 Composite Index (Leftmost Prefix Rule)
**Rule:** Design composite indexes based on query frequency and selectivity.
- **Tenant First:** For multi-tenant systems, `tenant_id` is almost always the first column in a composite index (e.g., `idx_tenant_status (tenant_id, status)`).
- **Range Query Truncation:** In a composite index, the first range condition (`>`, `<`, `BETWEEN`, `LIKE`) stops the index matching for subsequent columns.
  - **Best Practice:** Put equality checks (`=`, `IN`) first, range checks last.

---

## 💻 4. MyBatis / MyBatis-Plus Coding Standards

### 4.1 LambdaQueryWrapper First
**Rule:** For single-table queries, mandate the use of `LambdaQueryWrapper` over hardcoded XML to prevent magic strings.
- **✅ POSITIVE EXAMPLE:**
  ```java
  wrapper.eq(User::getTenantId, tenantId)
         .eq(ObjectUtil.isNotNull(status), User::getStatus, status)
         .orderByDesc(User::getCreateTime);
  ```

### 4.2 XML Dynamic SQL Safety
**Rule:** When XML is necessary (complex conditions, allowed JOINs), strict safety rules apply.
- **Null/Empty Checks:** ALWAYS use `<if test="param != null and param != ''">` for Strings, and `<if test="param != null">` for objects/collections.
- **The Absolute Ban on `${}`:** NEVER use `${}` for parameter injection due to SQL Injection risks.
  - **❌ NEGATIVE EXAMPLE:** `ORDER BY ${sortColumn} ${sortOrder}` (Critical Security Risk).
  - **✅ POSITIVE EXAMPLE:** Use Java Enums to map safe strings, or `<choose>` / `<if>` blocks in XML.
- **IN Clause Protection:** If an `IN` collection (`<foreach collection="list" item="id" open="(" separator="," close=")">`) can exceed 1000 items, it MUST be partitioned in Java before calling MyBatis.
- **No `SELECT *`:** Explicitly declare only the required columns, especially bypassing large `TEXT` or `JSON` fields unless explicitly requested.

---

## 🛡 5. Tenant Isolation Guarantee
**Rule:** Rely on the global Tenant Interceptor; do NOT duplicate conditions.
- The system uses MyBatis-Plus `TenantLineInnerInterceptor`. It will automatically append `tenant_id = ?` to all queries and updates.
- **DO NOT** manually add `.eq(User::getTenantId, tenantId)` or `WHERE tenant_id = #{tenantId}` in your code or XML. This causes redundant SQL (e.g., `tenant_id = 1 AND tenant_id = 1`) and potential syntax errors.
- Only manually append the tenant condition if you have explicitly bypassed the interceptor via `@InterceptorIgnore(tenantLine = "true")`.