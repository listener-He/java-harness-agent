# Preferences Index — 项目偏好与红线

> 团队已确认的正/反模式、硬约束、安全基线、历史决策。
> Agent 在任何架构设计或代码修改前，**必须**先读取本文件。

## 硬规则 (MUST)
- 本文件中的规则由 `guard_hook` 强制执行；违反即触发 `fail_hook` 回滚。
- 新发现的反模式（来自 Review 评分、线上事故、代码审查）**必须**在 Archive 阶段追加至本文件。
- 超过 500 行时**必须**拆分子文件，本文件只保留路由链接。

---

## 1. 反模式 (NEVER DO)

| 类别 | 禁止行为 | 禁止原因 | 错误示例 | 正确替代 |
|------|----------|----------|----------|----------|
| 性能 | 循环内查询数据库 | N+1 问题，轻则慢查询，重则拖垮 DB | `for(id in ids) { repo.findById(id); }` | `repo.findAllById(ids)` 批量查询 |
| 安全 | 硬编码密钥/密码 | 密钥泄露、无法轮转 | `String key = "abc123secret"` | 使用环境变量 `${SECRET_KEY}` |
| 数据 | SELECT * | 字段耦合、索引失效、带宽浪费 | `SELECT * FROM order` | 显式列出所需字段 |
| 架构 | Controller 直接调 Mapper | 跳过业务层，绕过事务/权限控制 | `@Autowired OrderMapper` in Controller | 必须通过 Service 层 |
| 稳定性 | 吞掉异常返回 null | 掩盖错误，上层 NPE | `catch(Exception e) { return null; }` | 向上抛出或抛 BizException |
| 权限 | 不加租户过滤 | 跨租户数据泄露 | `SELECT * FROM order WHERE id=?` | 必须加 `AND tenant_id=?` |

---

## 2. 必须模式 (ALWAYS DO)

| 类别 | 模式 | 原因 | 示例 |
|------|------|------|------|
| 异常 | 业务异常用 BizException | 统一错误码，前端可处理 | `throw new BizException(ErrorCode.ORDER_NOT_FOUND)` |
| 权限 | 默认开启租户隔离 | 数据安全基线 | MyBatis 拦截器自动注入 tenant_id |
| 接口 | 非查询接口考虑幂等 | 防重提交导致数据重复 | 唯一键 / 幂等 Token |
| 日志 | 关键操作记录操作日志 | 审计追踪 | 使用 `@OperationLog` 注解 |
| 事务 | 跨表写操作加 @Transactional | 原子性保证 | Service 方法上加注解 |

---

## 3. 安全基线 (Security Baseline)

→ 详见 [security_rules.md](security_rules.md)（硬约束，违反必须阻断）

**摘要**：
- 禁止硬编码密钥
- 所有 API 默认需要认证和租户隔离
- 禁止 MyBatis `${}` 字符串拼接（SQL 注入风险）
- 导出接口必须限流和行数上限

---

## 4. 团队决策记录 (Team Decisions)

| 决策 | 背景 | 结论 | 决策人 | 日期 |
|------|------|------|--------|------|
| *(示例) 禁止使用 @Transactional(readOnly=true)* | *误用导致写操作无事务保护* | *统一用默认事务，由 DBA 优化读性能* | *架构组* | *2026-03-01* |

---

## 5. Code Review 高频发现 (Recurring Findings)

| 发现 | 严重度 | 类别 | 修复模式 | 累计次数 |
|------|--------|------|----------|----------|
| *(示例) Service 方法未捕获 NPE* | *WARN* | *稳定性* | *Optional 包装 或 前置 null 判断* | *0* |

---

## Archive Extraction SOP

- Review 评分 ≤ 5 分 → 提取根因为反模式，追加至"反模式"表
- Review 评分 ≥ 8 分 → 提取最佳实践，追加至"必须模式"表
- 线上事故 / 重大发现 → 追加至"团队决策记录"
- Code Review 高频问题 → 追加至"高频发现"表

WAL 写入路径：`wal/YYYYMMDD_{topic}_preferences_append.md`
WAL 格式参考：[wal/WAL_FORMAT.md](wal/WAL_FORMAT.md)

**触发条件**：Archive 时发现新的反模式/最佳实践/团队决定，或用户在 Review 评分后提出改进建议，**必须**写回本维度。

---

## WAL Pending（待合并）

*(compactor 合并后此处自动清空)*
