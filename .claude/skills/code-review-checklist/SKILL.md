---
name: "code-review-checklist"
description: "Inline self-review checklist for TRIVIAL/LOW (PATCH) changes — evaluates code against project standards AFTER writing and BEFORE finalizing. For MEDIUM/HIGH (STANDARD) changes, the code-reviewer sub-agent supersedes this skill; do NOT run both. See .claude/rules/skill-precedence.md Zone B."
---

# Code Review (CR) Checklist & Self-Correction Loop

**CRITICAL RULE**: Whenever you add or modify code, you MUST mentally or explicitly run through this checklist. If the code fails ANY check, you MUST automatically fix the code and re-evaluate until it fully passes. Do not return unverified/failing code to the user.

## 🔄 The Self-Correction Loop Protocol
1. **Evaluate**: After making edits, immediately run the code against the checklist below.
2. **Fix**: If any rule is violated, immediately use editing tools to fix it.
3. **Re-evaluate**: Run the checklist again on the fixed code.
4. **Anti-Infinite-Loop (Max Retries: 3)**: You MUST NOT retry fixing the same rule more than 3 times. If a rule cannot be satisfied due to an architectural conflict, STOP, output a `bypass_justification.md` explaining the conflict, and ask the human for guidance.
5. **Pass**: End your turn when all checks pass (or are safely bypassed). Output a brief "CR Checklist Report" confirming compliance or detailing what was fixed/bypassed.

## 📋 The Ultimate CR Checklist

### 1. API & Controller Design (`java-backend-api-standard`)
- [ ] **NO `@PathVariable`**: All parameters must use `@RequestBody` or `@RequestParam`.
- [ ] **URL Verbs**: Endpoint URLs must end with action verbs (e.g., `/add`, `/update`, `/delete`, `/page`, `/list`).
- [ ] **Resource Lock**: Write operations (add/update/delete) MUST have `@ResourceLock`.
- [ ] **Validation**: DTOs MUST use `@Validated` or `@Valid`.
- [ ] **Return Type & Exceptions**: Service layer should return `ApiResponse` for simple/independent validations. However, if the operation requires **transaction rollback** or is deeply nested, the Service MUST throw a `DomainException` to guarantee data consistency. Controllers catch or return these accordingly.

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
- [ ] **Tenant Isolation**: Rely on MyBatis-Plus `TenantLineInnerInterceptor`. DO NOT manually append `.eq(Entity::getTenantId, tenantId)` unless explicitly ignoring the interceptor.
- [ ] **Logical Delete**: Is `.eq(Entity::getIsDeleted, false)` included?
- [ ] **No `SELECT *`**: Are specific columns queried instead of `*` in XML?
- [ ] **Index Friendly**: Are there NO functions on the left side of `=` in the `WHERE` clause? (e.g., no `DATE(create_time) = ?`).
- [ ] **Type Matching**: Do Java parameter types perfectly match DB column types to prevent implicit conversion?

### 6. Error Handling (`error-code-standard`)
- [ ] **Abstract Error Codes**: Did you reuse abstract domain codes (e.g., `PARAM_INVALID`, `DATA_DUPLICATED`, `HAS_DEPENDENCY`) instead of creating new ones?
- [ ] **Dynamic Messages**: Did you override the message? (e.g., `new DomainException(AbstractErrorCode.DATA_DUPLICATED, "Role name already exists")`).
- [ ] **No Generic Fails**: Did you always provide a specific error message when reusing an abstract code? (e.g., `new DomainException(AbstractErrorCode.PARAM_INVALID, "Specific reason here")`).

## 📝 Output Format Requirement
At the end of your task, append a short checklist summary. Example:
> **✅ CR Checklist Report:**
> - Evaluated code against checkstyle, error codes, and API standards.
> - *Self-correction*: Found a wildcard import (`import java.util.*;`) and replaced it with explicit imports.
> - All checks passed.

## Review Workflow (Merged)

### Requesting Review (Merged from `requesting-code-review`)

Use a review request to catch issues early and create an evidence-backed handoff.

- Evidence first, then review
- Run this checklist yourself before requesting review
- Share a review packet:
  - What changed (1–3 bullets)
  - Scope boundary (in-scope paths only)
  - Verification evidence (commands/tests run + outcome)
  - Remaining risks / known gaps

### Receiving Feedback (Merged from `receiving-code-review`)

Treat feedback as technical input to verify, not an order to blindly implement.

Response pattern:
1. Read the feedback end-to-end
2. Restate the technical requirement (or ask clarifying questions)
3. Verify against codebase reality
4. Evaluate whether it is sound for this codebase
5. Respond with technical acknowledgment or reasoned pushback
6. Implement one item at a time and re-verify after each change

Red flags:
- Implementing before understanding
- Bundling multiple fixes without verification
- Accepting suggestions that conflict with repo workflow gates
