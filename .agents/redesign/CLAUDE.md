# CLAUDE.md - Agent 工作指南

> 这是唯一入口文件。大多数任务只需读这一个文件。

## 工作模式

| 模式 | 适用场景 | 流程 |
|------|----------|------|
| `@quick` | 单文件改动、文档更新、明确的小修复 | 直接做 |
| `@standard` | 常规开发任务 (默认) | 理解 → 执行 → 可选归档 |
| `@careful` | 数据库/权限/配置/跨模块重构 | 理解 → 设计spec → 审批 → 执行 → 归档 |

**不确定用哪个？用 `@standard`，系统会自动检测是否需要升级。**

---

## 搜索原则

### 直接读取优先
如果用户给了明确的文件路径或类名，**直接读取**，不要先翻知识库。

### 搜索自检 (防止无限搜索)
每次读取文件后，快速自问：
1. 这次读取是否解答了我的疑问？
2. 我是否还需要继续搜索？

**停止信号**：
- 连续 3 次读取没有新收获 → 停止搜索，用已有信息开始执行
- 发现自己在反复读同样的文件 → 停止，总结已知信息
- 感觉越搜越迷茫 → 停止，向用户确认方向

### 背景知识
如果需要项目背景，先看 `.agents/context/QUICK_REF.md`（一页纸速查）。

---

## 代码规范 (核心)

### 分层架构
```
Controller (入口)
    ↓ 调用
Service (业务逻辑)
    ↓ 调用
Mapper (数据访问)
```
- 禁止 Controller 直接调用 Mapper
- 禁止 Service 之间循环依赖
- 跨域调用通过 RPC/Feign，不直接依赖

### 命名规范
- 类名: 大驼峰 + 后缀明确 (OrderService, OrderDTO, OrderVO, OrderEntity)
- 方法名: 小驼峰，动词开头 (createOrder, findByUserId)
- 常量: 全大写下划线 (MAX_RETRY_COUNT)

### 异常处理
```java
// 业务异常 - 明确的业务规则违反
throw new BizException(ErrorCode.ORDER_NOT_FOUND, "订单不存在: " + orderId);

// 系统异常 - 向上抛，由全局处理器捕获
// 不要 catch Exception 然后返回 null
```

### SQL 规范
- 禁止 `SELECT *`，明确列出字段
- 禁止在循环中执行 SQL，使用批量查询
- WHERE 条件必须走索引
- 大表查询必须分页

### 权限
- 默认开启租户隔离
- 敏感操作需要权限注解: `@RequiresPermission("order:delete")`
- 跳过租户隔离需要明确标注: `@SkipTenant`

---

## 风险检测 (自动)

以下情况会自动触发 `@careful` 模式：

| 触发条件 | 原因 |
|----------|------|
| 修改 `*Mapper.xml` | 数据库操作变更 |
| 修改 `*Permission*.java` / `*Auth*.java` | 权限逻辑变更 |
| 修改 `application*.yml` | 配置变更 |
| 新增/修改 SQL 文件 | 数据库结构变更 |
| 单次修改超过 10 个文件 | 大范围重构 |

检测到以上情况时，请：
1. 暂停编码
2. 输出简要的 spec 草案
3. 等待用户确认后继续

---

## 常用工具类

```java
// 字符串
StringUtils.isBlank(str)
StringUtils.defaultIfBlank(str, "default")

// 集合
CollectionUtils.isEmpty(list)
CollectionUtils.isNotEmpty(list)

// 日期
DateUtils.parseDate(str, "yyyy-MM-dd")
DateUtils.formatDate(date, "yyyy-MM-dd HH:mm:ss")

// 当前用户
SecurityUtils.getUserId()
SecurityUtils.getTenantId()
SecurityUtils.getUsername()

// Bean 拷贝
BeanUtils.copyProperties(source, target)
```

---

## 详细规范 (按需)

只在需要时查阅，不要预加载：

| 场景 | 文件 |
|------|------|
| 分层架构详解 | `.agents/skills/java-engineering-standards/SKILL.md` |
| API 设计规范 | `.agents/skills/java-backend-api-standard/SKILL.md` |
| MyBatis SQL 规范 | `.agents/skills/mybatis-sql-standard/SKILL.md` |
| 数据权限详解 | `.agents/skills/java-data-permissions/SKILL.md` |
| 错误码规范 | `.agents/skills/error-code-standard/SKILL.md` |

---

## 知识回写 (可选)

完成任务后，如果发现了值得记录的知识，可以回写：

**业务知识** → `.agents/context/domain/wal/YYYYMMDD_主题_append.md`
**工程规范** → `.agents/context/standards/wal/YYYYMMDD_主题_append.md`

格式示例：
```markdown
# 订单状态机补充说明

- PENDING_PAYMENT 状态下可取消
- PAID 状态下取消需要触发退款流程
- SHIPPED 状态下不可取消
```

**不强制回写**，只有确实有价值的新发现才需要记录。

---

## @careful 模式 Spec 模板

```markdown
# Spec: {功能名称}

## 概述
一句话描述: 做什么、为什么

## 风险评估
- 等级: HIGH / MEDIUM
- 原因: (为什么是高风险)

## 变更范围
- 新增文件:
- 修改文件:
- 删除文件:

## 设计要点
1. ...
2. ...
3. ...

## 验证计划
- [ ] 单元测试:
- [ ] 手动验证:

---
[ ] 用户确认可以执行
```

---

## 禁止事项

1. **禁止无限搜索** - 连续 3 次无收获就停止
2. **禁止硬编码密钥** - 使用环境变量或配置中心
3. **禁止循环查库** - 批量查询 + 内存组装
4. **禁止 SELECT *** - 明确列出字段
5. **禁止跨层调用** - Controller 不能直接调 Mapper
6. **禁止吞异常** - 不要 catch 后返回 null
7. **禁止跳过租户隔离** - 除非明确标注 @SkipTenant
