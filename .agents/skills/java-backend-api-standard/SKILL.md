---
name: "java-backend-api-standard"
description: "Enforces backend API design standards (no path variables, standard verbs, ApiResponse formats). Invoke when creating Controllers or DTOs."
---

# Java Backend API Design Standard

This skill enforces the project's strict backend API design and data interaction specifications based on `business` module practices.

## 1. 接口路径与动词规范 (Endpoint Naming Convention)
- **统一风格**：接口路径统一使用小写字母，多单词用连字符 `-` 分隔。
- **操作动词后缀**：必须在路径末尾明确加上操作动词，保持扁平化：
  - `/add`：新增 (POST)
  - `/update`：修改 (POST)
  - `/delete`：删除 (POST，参数放 Body)
  - `/detail`：查询详情 (GET)
  - `/page`：分页查询 (POST)
  - `/options` 或 `/option`：下拉列表搜索查询 (GET)
  - `/enable` / `/disable`：状态启停操作 (POST)

## 2. 【强制】禁止使用 Path 变量传参 (NO Path Variables)
- **绝对不允许**在 URL 路径中使用动态变量传参（例如：~~`/delete/{id}`~~ 严格禁止）。
- 必须通过 **Query String**（GET 请求）或者 **Request Body**（POST 请求，`@RequestBody`）传递。

## 3. 防抖与并发控制 (Resource Lock)
- Controller 层的写操作接口，**必须**加上 `@ResourceLock` 注解防止重复提交。
- 示例：`@ResourceLock(prefix = "governance:module", key = "#request.id", message = "请勿频繁点击")`

## 4. 参数校验 (Validation)
- Controller 方法中的请求对象必须加上 `@Validated` 或 `@Valid` 注解。
- 请求 DTO 内部使用 `jakarta.validation.constraints` 注解，并且必须提供用户友好的 `message`（如 `@NotBlank(message = "请输入名称")`）。