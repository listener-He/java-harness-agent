---
name: "java-backend-guidelines"
description: "Comprehensive Java guidelines. Enforces defensive programming, Complete assembly, CustomPage pagination, and Hutool usage. Invoke for code generation."
---

# Java Backend Development Guidelines

Strict guidelines extracted from the `business` module implementations.

## 1. 字典与关联数据组装 (`Complete` 工具类)
- **绝对禁止**使用 SQL `JOIN` 进行简单的字典或关联数据查询。
- **必须**使用 `com.jiuyu.framework.function.complete.Complete` 工具类在 Service 层组装数据。
- 示例：
  ```java
  Complete.start(responseList)
      .build(EntityResponse::getCompanyId, EntityResponse::setCompanyName, subCompanyService::getNameMap)
      .then()
      .build(EntityResponse::getDeptId, EntityResponse::setDeptName, deptService::getDeptNameMap)
      .then()
      .over();
  ```

## 2. 分页查询 (`CustomPage` 工具类)
- 分页查询**必须**使用 `CustomPage.execute` 包装 MyBatis-Plus 的 `lambdaQuery()`。
- 示例：
  ```java
  PageData<Entity> pageData = CustomPage.execute(request, (page, req) -> {
      return super.lambdaQuery()
          .eq(Entity::getTenantId, accessUser.currentTenantId())
          .eq(Entity::getIsDeleted, false)
          .like(EmptyUtil.isNotEmpty(req.getName()), Entity::getName, req.getName())
          .orderByDesc(Entity::getId)
          .page(page);
  });
  // 转换 VO
  PageData<EntityResponse> responsePage = pageData.conversion(emp -> BeanUtil.copyProperties(emp, EntityResponse.class));
  ```

## 3. 工具类与对象拷贝 (Utility Usage)
- **判空**：强制使用 `EmptyUtil.isEmpty()` 和 `EmptyUtil.isNotEmpty()`。
- **对象映射**：强制使用 `cn.hutool.core.bean.BeanUtil.copyProperties(source, Target.class)`，避免手动 Setter。

## 4. 防御性编程思维 (Defensive Programming)
- **租户隔离**：所有查询和修改操作，**必须**带上 `.eq(Entity::getTenantId, accessUser.currentTenantId())`。
- **逻辑删除**：所有查询操作**必须**带上 `.eq(Entity::getIsDeleted, false)`。删除时使用更新 `is_deleted = true`。

## 5. 代码与注释风格 (Code Style)
- **Lombok**：实体类与 DTO 避免使用 `@Data`，统一使用 `@Getter` 和 `@Setter`。
- **注释**：类和方法必须有标准 Javadoc，包括 `@author`、`@date`、`@param`、`@return`。
- **链式编程**：充分利用 MyBatis-Plus 的 Lambda 链式调用（如 `ChainWrappers.lambdaUpdateChain()` 或 `super.lambdaQuery()`）。

## 6. 分布式锁 (Distributed Lock)
- **工具类**：LockTemplate
- **示范1**： `lockTemplate.execute(lockKey, 1, TimeUnit.SECONDS, () -> {...});`
