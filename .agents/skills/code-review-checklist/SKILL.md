---
name: "code-review-checklist"
description: "MANDATORY Code Review Checklist. Evaluates code against ALL project standards. Invoke AFTER writing/modifying code and BEFORE finalizing response. Automatically fix and re-evaluate until all checks pass."
---

# Code Review (CR) Checklist & Self-Correction Loop

**CRITICAL RULE**: Whenever you add or modify code, you MUST mentally or explicitly run through this checklist. If the code fails ANY check, you MUST automatically fix the code and re-evaluate until it fully passes. Do not return unverified/failing code to the user.

## 🔄 The Self-Correction Loop Protocol
1. **Evaluate**: After making edits, immediately run the code against the checklist below.
2. **Fix**: If any rule is violated (e.g., you used `@Autowired` instead of `@RequiredArgsConstructor`), immediately use editing tools to fix it.
3. **Re-evaluate**: Run the checklist again on the fixed code.
4. **Pass**: Only end your turn when all checks pass 100%. At the end of your response, output a brief "CR Checklist Report" confirming compliance or detailing what was automatically fixed.

## 📋 The Ultimate CR Checklist

### 1. API & Controller Design (`java-backend-api-standard`)
- [ ] **NO `@PathVariable`**: All parameters must use `@RequestBody` or `@RequestParam`.
- [ ] **URL Verbs**: Endpoint URLs must end with action verbs (e.g., `/add`, `/update`, `/delete`, `/page`, `/list`).
- [ ] **Resource Lock**: Write operations (add/update/delete) MUST have `@ResourceLock`.
- [ ] **Validation**: DTOs MUST use `@Validated` or `@Valid`.
- [ ] **Return Type**: Controllers MUST directly return the Service's `ApiResponse` for write operations, or `ApiResponse.success(data)` for reads.

### 2. Checkstyle & Formatting (`checkstyle`)
- [ ] **Indentation**: 4 spaces used? (NO tabs).
- [ ] **Braces**: K&R style used? (Opening brace on the same line, closing on a new line).
- [ ] **Imports**: NO wildcard imports (`.*`)? Correct grouping order used?
- [ ] **Javadoc**: Do all new/modified classes and public methods have Javadoc (`@author`, `@date` as `yyyy-MM-dd`, `@param`, `@return`)?
- [ ] **Injection**: Is `@RequiredArgsConstructor` used for constructor injection? (NO `@Autowired` on fields).
- [ ] **Naming**: `UpperCamelCase` for classes, `lowerCamelCase` for methods/variables, proper POJO suffixes (`Request`, `Response`).

### 3. Service Logic & Data Assembly (`java-backend-guidelines`)
- [ ] **Anti-JOIN Assembly**: Did you use in-memory data assembly strategy to fetch names/dictionaries instead of SQL JOINs?
- [ ] **Pagination**: Did you use the standardized pagination wrapper for pagination?
- [ ] **Null Checks**: Did you use `Objects.isNull()` or `Objects.nonNull()` instead of `obj == null`?
- [ ] **Bean Copy**: Did you use `cn.hutool.core.bean.BeanUtil` for object mapping?

### 4. Alibaba Code Guidelines & Business Logic
- [ ] **NO DB in Loops**: Are there ANY database operations (CRUD) inside a `for` or `while` loop? (MANDATORY FIX: Refactor to batch queries `in()` and memory mapping).
- [ ] **NO RPC in Loops**: Are there ANY Feign or external API calls inside a loop? (MANDATORY FIX: Refactor to batch API calls).
- [ ] **Business Boundaries**: Does the logic respect domain boundaries? (e.g., `UserService` should not directly modify `Order` tables; it should call `OrderService`).
- [ ] **Transaction Scope**: Is `@Transactional` only wrapping the necessary database operations? (Keep heavy computations or RPC calls OUTSIDE the transaction).
- [ ] **Magic Numbers**: Are there any unexplained magic numbers/strings in the code? (Replace with Enums or Constants).

### 5. Database & SQL Performance (`mybatis-sql-standard`)
- [ ] **Tenant Isolation**: Is `.eq(Entity::getTenantId, tenantId)` the VERY FIRST condition in the query? (MANDATORY)
- [ ] **Logical Delete**: Is `.eq(Entity::getIsDeleted, false)` included?
- [ ] **No `SELECT *`**: Are specific columns queried instead of `*` in XML?
- [ ] **Index Friendly**: Are there NO functions on the left side of `=` in the `WHERE` clause? (e.g., no `DATE(create_time) = ?`).
- [ ] **Type Matching**: Do Java parameter types perfectly match DB column types to prevent implicit conversion?

### 6. Error Handling (`error-code-standard`)
- [ ] **Abstract Error Codes**: Did you reuse abstract domain codes (e.g., `PARAM_INVALID`, `DATA_DUPLICATED`, `HAS_DEPENDENCY`) instead of creating new ones?
- [ ] **Dynamic Messages**: Did you override the message? (e.g., `new DomainException(AbstractErrorCode.DATA_DUPLICATED, "角色名称已存在")`).
- [ ] **No Generic Fails**: Did you avoid throwing generic DomainException without an abstract code if a more specific one exists?

## 📝 Output Format Requirement
At the end of your task, append a short checklist summary. Example:
> **✅ CR Checklist Report:**
> - Evaluated code against checkstyle, error codes, and API standards.
> - *Self-correction*: Found a wildcard import (`import java.util.*;`) and replaced it with explicit imports.
> - All checks passed.
