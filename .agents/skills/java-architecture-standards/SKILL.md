---
name: "java-architecture-standards"
description: "MANDATORY MASTER skill for Java backend development. Enforces strict 3-Layer architecture, API design (No Path Variables), POJO structure, Anti-JOIN data assembly, and Error Code handling. Invoke before writing ANY Java code."
---

# Java Architecture & Engineering Standards

> **Trigger:** You MUST read and follow this guide before generating, refactoring, or reviewing ANY backend Java code (Controllers, Services, Entities, DTOs).

## 🚨 0. Absolute Red Lines (Non-Negotiable)
- **NO Path Variables:** Absolutely NO dynamic variables in URLs (e.g., `/delete/{id}` is FORBIDDEN). Pass parameters via Query String (GET) or Request Body (POST).
- **Tenant Isolation:** EVERY list query MUST filter by `tenant_id` at the DB level, or enforce isolation via the project's standard permission/interceptor mechanism. Never trust caller-provided tenant context without server-side enforcement.
- **Soft Delete Only:** Use `is_deleted = 0` filter for queries. NEVER hard-delete domain records. Update `is_deleted = 1` instead.
- **No `I` Prefix for Interfaces:** Interfaces use plain role names (e.g., `UserService`, not `IUserService`).

---

## 🌐 1. API & Controller Layer Design

**Responsibility:** Expose HTTP endpoints, receive requests, validate parameters.
- **Endpoint Naming:** Lowercase, hyphen-separated, MUST end with an action verb:
  - `/add`, `/update`, `/delete` (POST)
  - `/detail` (GET), `/page` (POST), `/options` (GET)
  - `/enable`, `/disable` (POST)
- **Idempotency (Resource Lock):** Write operations in Controllers MUST use `@ResourceLock` (e.g., `@ResourceLock(prefix = "governance:module", key = "#request.id", message = "Please do not click repeatedly")`).
- **Validation:** Use `@Validated` or `@Valid` on request objects. DTO fields MUST use `jakarta.validation.constraints` with user-friendly `message` attributes.
- **Return Types:**
  - **Read ops:** Call Service, wrap result in a Unified `ApiResponse<T>`.
  - **Write ops:** Call Service, directly return the Unified Response returned by the Service.

---

## ⚙️ 2. Service Layer & Business Logic

**Responsibility:** Core business logic, transaction management, exception handling.
- **Return Types:** Read methods MUST return raw DTO/VO or `PageData<T>` (not wrapped in ApiResponse).
- **Transactions & Exceptions (CRITICAL):**
  - **Throw `DomainException` (Preferred for Writes):** If the logic involves `@Transactional` database writes, you MUST throw a `DomainException` to guarantee rollback. Reuse abstract error codes and pass dynamic messages (e.g., `throw new DomainException(AbstractErrorCode.DATA_DUPLICATED, "Role name already exists");`). DO NOT create new enums for every specific error.
  - **Return `ApiResponse.failed()`:** Acceptable ONLY for surface-level validation (e.g., in Controller) where no transaction has started.
- **In-Memory Data Assembly (Anti-JOIN):** AVOID SQL `JOIN` for simple dictionary or cross-domain data. Query the main data, extract foreign keys, query the related service/table, and backfill properties IN MEMORY. This prevents N+1 and maintains domain isolation.
- **Standardized Pagination:** All pagination must go through internal wrappers to shield MyBatis-Plus details and output pure DTO/VO structures.

---

## 🗄️ 3. POJO & Data Modeling

**Directory Structure:** All entities/DTOs MUST be placed under the module's `pojo` directory:
- `pojo.request`: DTOs for receiving frontend parameters (e.g., `XXXAddRequest`).
- `pojo.response`: VOs returned to the frontend (e.g., `XXXResponse`).
- `pojo.entity`: Database-mapped classes (Suffix: `Entity`).
- `pojo.constants`: Module-scoped enums (Suffix: `Type` or `Enum`, MUST implement `BaseEnum`).

**Audit Fields:** EVERY database Entity MUST contain:
- `id` (PK), `tenant_id` (Isolation), `is_deleted` (Soft delete flag: 0/1)
- `create_time`, `update_time` (LocalDateTime)
- `create_by`, `update_by` (Creator/Updater ID)

---

## 🛠️ 4. Tooling & Code Style

- **Null Checks:** MANDATORY use of `java.util.Objects.isNull()` and `Objects.nonNull()`. DO NOT use `obj == null`.
- **Object Mapping:** MANDATORY use of `cn.hutool.core.bean.BeanUtil.copyProperties(source, Target.class)`. Avoid manual Setters.
- **Lombok:** Use `@Getter` and `@Setter` for Entities/DTOs. AVOID `@Data`. Use `@RequiredArgsConstructor` for dependency injection (Constructor Injection). NEVER use `@Autowired` on fields.
- **Javadoc:** Classes and methods MUST have standard Javadoc (`@author`, `@date`, `@param`, `@return`).
- **Chaining:** Utilize MyBatis-Plus Lambda chain wrappers (e.g., `lambdaUpdateChain()`, `lambdaQuery()`).

---

## 🤖 5. Agent Macros & Slash Commands
If the user invokes these commands, execute the corresponding behavior instantly based on the standards above:
- `/gen-api`: Generate Controller + Request/Response DTOs following the "NO Path Variable", "Verb Suffix URL", and `@ResourceLock` rules.
- `/gen-service`: Generate Service Impl returning `ApiResponse` for simple writes, or throwing `DomainException` for transactional operations. Use in-memory assembly for read queries.
- `/optimize-sql`: Review XML/LambdaQuery for JOINs. Rewrite them to application-level in-memory assembly (Anti-JOIN strategy).
