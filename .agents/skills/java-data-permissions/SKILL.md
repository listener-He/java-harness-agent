---
name: "java-data-permissions"
description: "Guides data permissions (Query filtering vs Action validation via @BeforePermission). Invoke when writing APIs requiring authorization."
---

# Java Data Permissions Guidelines

## 1. 操作验证：@BeforePermission (Action Validation)
用于需要对特定目标数据执行操作（增删改、单条详情查询）的场景，校验用户是否有权限操作该数据。

- **使用位置**：Controller 或 Service 层的方法上。
- **单维度校验**：
  ```java
  @BeforePermission(type = OauthConstant.TEAM, dataId = "#request.id")
  public ApiResponse<Void> update(...)
  ```
- **多维度联合校验**（用于新增等涉及多个层级的操作）：
  ```java
  @BeforePermission.Multiple({
      @BeforePermission(type = OauthConstant.COMPANY, dataId = "#request.companyId"),
      @BeforePermission(type = OauthConstant.DEPT, dataId = "#request.deptId", ignoreEmpty = true)
  })
  public ApiResponse<Void> add(...)
  ```

## 2. 列表过滤：数据隔离 (Query Filtering)
对于分页 (`/page`) 和下拉列表 (`/options`) 接口，不要使用 `@BeforePermission`，而应该在查询参数 DTO 中包含相关维度的 ID 集合，并在 `lambdaQuery` 中过滤：

- 示例：
  ```java
  .and(EmptyUtil.isNotEmpty(req.getCompanyIds()) && EmptyUtil.isNotEmpty(req.getDeptIds()), c -> {
      c.in(EmptyUtil.isNotEmpty(req.getCompanyIds()), Entity::getCompanyId, req.getCompanyIds())
       .or().in(EmptyUtil.isNotEmpty(req.getDeptIds()), Entity::getDeptId, req.getDeptIds());
  })
  ```

## 3. 租户绝对隔离 (Tenant Isolation)
- **最高优先级**：无论任何权限策略，所有查询和更新的条件中**永远必须**优先包含当前用户的租户 ID 校验：`.eq(Entity::getTenantId, accessUser.currentTenantId())`。