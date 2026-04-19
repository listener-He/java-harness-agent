---
name: "java-engineering-standards"
description: "Enforces strict layer architecture, POJO sub-packages, and business design rules. Invoke when setting up new modules, refactoring, or defining business logic flow."
---

# Java Engineering & Architecture Standards

Dictates the project's strict architectural layering and business logic distribution rules.

---

## 1. Architecture Layering (3 Layers, Strictly Enforced)

### Controller (API Layer)
- Responsibility: expose HTTP endpoints, receive requests, validate parameters, extract `AccessUser` context.
- **Read operations** (query / pagination): call Service, wrap result in a Unified Response structure.
- **Write operations** (add / update / delete / toggle): call Service, directly return the Unified Response structure returned by the Service.

### Service (Business Layer)
- Responsibility: core business logic, transaction management, permission validation.
- **Read methods**: MUST return raw DTO/VO or `PageData<T>` — not a Unified Response wrapper.
- **Write methods (Return vs. Throw Exception)**:
  - **Return `ApiResponse<T>`**: Use this when the operation is independent, explicitly known to the caller (e.g., direct Controller call), and DOES NOT require rolling back a database transaction.
  - **Throw `DomainException`**: Use this for non-query operations where module call depth is deep, OR **when transaction rollback is sensitive/required**. Throwing an exception is the standard and safest way to trigger `@Transactional` rollback.

### Mapper (Data Layer)
- Responsibility: direct database interaction via MyBatis-Plus only.
- MUST NOT contain any business logic.

---

## 2. POJO Directory Structure

All entities and transfer objects MUST be placed under the module's `pojo` directory, split into sub-packages:

| Sub-package | Contains | Naming example |
|---|---|---|
| `pojo.request` | DTOs for receiving frontend parameters | `XXXAddRequest`, `XXXQueryRequest` |
| `pojo.response` | VOs returned to the frontend | `XXXResponse`, `XXXInfoResponse` |
| `pojo.entity` | Database-mapped entity classes | `XXXEntity` |
| `pojo.constants` | Module-scoped enums and constants (MUST implement `BaseEnum`) | `XXXType` |

---

## 3. Entity Audit Fields (MUST Include)

Every database Entity MUST contain the following standard anti-corruption fields:

| Field | Type | Purpose |
|---|---|---|
| `id` | Long / String | Primary key |
| `tenant_id` | Long | Tenant isolation — always filter at DB level |
| `create_time` | LocalDateTime | Creation timestamp |
| `update_time` | LocalDateTime | Last update timestamp |
| `create_by` | Long | Creator user ID |
| `update_by` | Long | Last updater user ID |
| `is_deleted` | Integer (0/1) | Soft-delete flag |

---

## 4. Naming Conventions

| Element | Rule | Example (correct) | Example (forbidden) |
|---|---|---|---|
| Interface | No `I` prefix | `UserService` | `IUserService` |
| Implementation class | Suffix `Impl` | `UserServiceImpl` | `UserService` (as class) |
| Entity class | Suffix `Entity` | `UserEntity` | `User` |
| Enum / constant class | Suffix `Type` or `Enum` | `OrderType` | `OrderStatus` (ambiguous) |
| Methods (camelCase) | lowerCamelCase | `getUserById` | `GetUserById` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` | `maxRetryCount` |

---

## 5. Cross-cutting Rules

- **No interface prefix `I`**: absolutely forbidden. Interfaces use the plain role name.
- **Tenant isolation**: every list query MUST filter by `tenant_id` at the DB level (or via `@BeforePermission`). Never trust caller-provided tenant context without server-side enforcement.
- **Soft delete**: use `is_deleted = 0` filter; NEVER hard-delete domain records.
- **Transaction scope**: transactions MUST be confined to the Service layer. Controllers and Mappers MUST NOT own transactions.
