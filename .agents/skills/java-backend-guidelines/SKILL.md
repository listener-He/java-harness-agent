---
name: "java-backend-guidelines"
description: "Comprehensive Java guidelines. Enforces defensive programming, in-memory data assembly, standardized pagination wrappers, and Hutool usage. Invoke for code generation."
---

# Java Backend Development Guidelines

Strict guidelines extracted from the `business` module implementations.

## 1. 字典与关联数据组装 (In-Memory Data Assembly Strategy)
- **核心思想**：强烈推荐避免使用 SQL `JOIN` 进行简单的字典或跨域关联数据查询。为了实现微服务下的表域隔离并提升数据库性能，应采用内存组装策略（Anti-JOIN）。
- **规范要求**：在 Service 层将主数据查出后，批量提取外键 ID，去关联服务或表查询出所需数据（如 ID 到名称的映射），然后在内存中进行属性回填。这种流式处理模式能有效防止 N+1 查询问题，同时保持各业务域的边界纯粹。

## 2. 分页查询 (Standardized Pagination Wrapper)
- **核心思想**：为了屏蔽底层 ORM 框架（如 MyBatis-Plus）的分页实现细节，并强制将底层 Entity 统一转化为对外的 DTO/VO 结构，系统应采用标准化的分页包装器。
- **规范要求**：所有的分页查询必须通过统一的内部机制进行拦截与包装。在查询逻辑中处理完租户隔离、逻辑删除和条件过滤后，必须使用内置的转换机制（如 `conversion` 方法）优雅地输出纯净的业务视图对象。

## 3. 工具类与对象拷贝 (Utility Usage)
- **判空**：强制使用标准库的 `java.util.Objects.isNull()` 和 `Objects.nonNull()` 替代原生的 `obj == null` 判断。
- **对象映射**：强制使用 `cn.hutool.core.bean.BeanUtil.copyProperties(source, Target.class)`，避免手动 Setter。

## 4. 防御性编程思维 (Defensive Programming)
- **租户隔离**：所有查询和修改操作，**必须**带上 `.eq(Entity::getTenantId, accessUser.currentTenantId())`。
- **逻辑删除**：所有查询操作**必须**带上 `.eq(Entity::getIsDeleted, false)`。删除时使用更新 `is_deleted = true`。

## 5. 代码与注释风格 (Code Style)
- **Lombok**：实体类与 DTO 避免使用 `@Data`，统一使用 `@Getter` 和 `@Setter`。
- **注释**：类和方法必须有标准 Javadoc，包括 `@author`、`@date`、`@param`、`@return`。
- **链式编程**：充分利用 MyBatis-Plus 的 Lambda 链式调用（如 `ChainWrappers.lambdaUpdateChain()` 或 `super.lambdaQuery()`）。


