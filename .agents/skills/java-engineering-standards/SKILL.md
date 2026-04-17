---
name: "java-engineering-standards"
description: "Enforces strict layer architecture, pojo sub-packages, and business design rules. Invoke when setting up new modules, refactoring, or defining business logic flow."
---

# Java Engineering & Architecture Standards

This skill dictates the project's strict architectural layering and business logic distribution rules based on the `business` module implementation.

## 1. 架构分层规范 (Architecture Layering)

**常规情况下，代码严格限制为以下三层结构：**
- **Controller (控制层)**：负责对外暴露 API，接收 HTTP 请求，参数校验，提取 `AccessUser` 用户上下文。
  - 对于**读操作**（查询详情、分页等），Controller 负责调用 Service，并将结果用 `ApiResponse.success(data)` 封装。
  - 对于**写操作**（新增、修改、删除、启停等），Controller **直接返回** Service 层的执行结果（如 `return service.add(request);`）。
- **Service (业务层)**：负责核心业务逻辑的处理、事务管理、权限校验。
  - **写操作方法**允许且建议直接返回 `ApiResponse<Void>` 或 `ApiResponse<T>`，以便于在业务校验失败时优雅地使用 `ApiResponse.failed("错误信息")` 阻断流程，避免滥用异常。
  - **读操作方法**必须返回原始的 DTO/VO 或 `PageData<T>`。
- **Mapper (数据层)**：只负责与数据库的直接交互（MyBatis-Plus），禁止包含业务逻辑。

## 2. 领域对象规范 (POJO Directory Structure)

所有的实体和传输对象必须放在模块下的 `pojo` 目录，并严格划分子包：
- **`pojo.request`**：用于接收前端参数的 DTO（如 `XXXAddRequest`, `XXXQueryRequest`）。
- **`pojo.response`**：用于返回给前端的 VO 数据（如 `XXXResponse`, `XXXInfoResponse`）。
- **`pojo.entity`**：数据库映射实体类。
- **`pojo.constants`**：模块内的枚举和常量（如 `XXXType`，需实现 `BaseEnum` 接口）。

## 3. 实体类通用字段 (Entity Audit Fields)
所有数据库 Entity 必须包含以下通用防腐字段，并且在业务代码中严格处理：
- `id`, `tenant_id` (租户ID), `create_time`, `update_time`, `create_by`, `update_by`, `is_deleted`。

## 4. 命名规范 (Naming Conventions)
- **接口命名 (Interface Naming)**：绝对禁止使用 `I` 作为接口名的前缀（例如：禁止使用 `IUserService`，必须直接使用 `UserService`）。
- **实现类命名 (Implementation Naming)**：实现类必须以 `Impl` 结尾（例如：`UserServiceImpl`）。
- **实体类命名 (Entity Naming)**：数据库映射类必须以 `Entity` 结尾（例如：`UserEntity`）。