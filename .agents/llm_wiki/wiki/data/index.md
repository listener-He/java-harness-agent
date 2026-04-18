# Data Index — 数据模型

> 数据库表结构、索引策略、ER 关系、Schema 变更历史、性能注意事项。
> Agent **禁止**通过扫描全量代码猜测表结构，必须以本文件为准，再按需校验 Mapper XML。

## 硬规则 (MUST)
- Archive 阶段，**必须**从 `openspec.md` 提取表变更追加到本文件。
- Schema 破坏性变更（字段删除/重命名/类型变更）**必须**填写"Schema 决策记录"并注明回滚方案。
- 表数量超过 50 时，**必须**按模块拆分（如 `auth_tables.md`、`trade_tables.md`）。
- Migration SQL **必须**能在测试库验证通过后才允许进入 Archive。

---

## 1. 表清单 (Tables)

| 表名 | 中文名 | 所属模块 | 核心字段 | 关键索引 | 关联表 | 数量级 | 备注 |
|------|--------|----------|----------|----------|--------|--------|------|
| *(示例) sys_user* | *用户表* | *auth* | *id, tenant_id, username, status* | *idx_tenant_username (tenant_id, username)* | *sys_role* | *百万级* | *软删除，is_deleted 标记* |

---

## 2. Schema 决策记录

| 决策 | 背景 | 选择 | 未选方案 | 可回滚 | 日期 |
|------|------|------|----------|--------|------|
| *(示例) 用户表按 tenant_id 分库* | *单表预计超 1 亿行* | *按 tenant_id hash 分 16 库* | *按时间分表* | *否，上线后不可逆* | *2026-03-01* |

---

## 3. Migration 记录

| 版本号 | 文件名 | 变更摘要 | 是否可回滚 | 回滚 SQL / 方案 | 执行日期 |
|--------|--------|----------|------------|----------------|----------|
| *(示例) V1.2.0* | *V1.2.0__add_order_status.sql* | *order 表新增 status 字段* | *是* | *ALTER TABLE order DROP COLUMN status* | *2026-04-01* |

---

## 4. 敏感数据地图 (Sensitive Data)

| 表 | 字段 | 敏感级别（L1-L3） | 存储方式 | 脱敏规则 |
|----|------|------------------|----------|----------|
| *(示例) sys_user* | *phone* | *L2* | *AES 加密* | *展示时掩码 138****8888* |

---

## 5. 性能注意事项 (Performance)

| 表 / 查询场景 | 问题描述 | 解决方案 | 状态 | 发现日期 |
|--------------|----------|----------|------|----------|
| *(示例) order 按 create_time 范围查询* | *全表扫描，单次 3s+* | *增加 (tenant_id, create_time) 联合索引* | *已上线* | *2026-03-15* |

---

## Archive Extraction SOP

Archive 阶段从 `openspec.md` 提取：
- 新增/变更表 → 追加至"表清单"
- Schema 设计决策 → 追加至"Schema 决策记录"
- Migration 文件 → 追加至"Migration 记录"
- 涉及敏感字段 → 追加至"敏感数据地图"
- 发现慢查询 → 追加至"性能注意事项"

WAL 写入路径：`wal/YYYYMMDD_{topic}_data_append.md`
WAL 格式参考：[wal/WAL_FORMAT.md](wal/WAL_FORMAT.md)

**触发条件**：修改 `*Mapper.xml`、`*.sql`、`*Migration*.java`、`*Entity.java`（新增字段）时，**必须**写回本维度 WAL。

---

## WAL Pending（待合并）

*(compactor 合并后此处自动清空)*
