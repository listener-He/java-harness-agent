---
name: "error-code-standard"
description: "Guides the usage of system error codes and domain exceptions. Invoke when generating or modifying code that throws domain exceptions or returns unified error responses."
---

# Error Code Standard (异常状态码与契约设计规范)

**CRITICAL: You MUST read and follow this guide before generating ANY code that returns an error response or throws a business domain exception.**

This project uses a highly abstracted, behavior-driven Error Code system and a Unified API Response format. We do **NOT** create a new enum for every specific error message (e.g., no separate codes for "phone number error" vs. "email error"). Instead, we reuse abstract codes and override the `message` dynamically.

## 🧠 Core Ideas & Design

### 1. Unified API Response Format
All interactions between the frontend and backend must strictly adhere to a Unified Response format. This ensures that the frontend can consistently parse the `code`, `message`, and `data` fields.
- **Read Operations**: Controllers must wrap query results in a unified success response.
- **Write Operations**: Services should ideally return the unified response structure directly, allowing validation failures to return a failure response cleanly without always throwing exceptions.

### 2. Domain-Driven Exceptions
Instead of using standard Java exceptions (like `IllegalArgumentException`) for business rule violations, the system uses a centralized Domain Exception concept.
- **Behavior-Driven**: The domain exception represents a violation of business rules or state.
- **Dynamic Messages**: You should instantiate the domain exception with a highly abstracted error code (e.g., "Data Duplicated") and dynamically pass the specific error message (e.g., "Role name already exists").

### 3. Categorized Abstract Error Codes
Error codes are designed as abstract categories rather than specific instances. When an error occurs, you map it to the closest abstract category:
- **1xxx Series (Technical Failures)**: External API failures, timeouts, etc.
- **2xxx Series (Hard Rules & Validation)**: Empty parameters, format errors, duplicate data (e.g., "Name exists", "Phone exists"), rate limits.
- **3xxx Series (Business Logic & State)**: Quota exceeded, invalid state (e.g., "Cannot modify because already started"), dependency exists (e.g., "Cannot delete because children exist").
- **4xxx Series (Interaction Prompts)**: Errors that require specific frontend actions (e.g., redirect to login, pop up a strong confirmation modal).

## 💻 Code Generation Rules

### 1. Throwing Exceptions
ALWAYS prefer reusing abstract error codes and providing specific messages when throwing domain exceptions:
```java
// Good: Reusing abstract code, specific message
throw new DomainException(AbstractErrorCode.DATA_DUPLICATED, "角色名称已存在");

// Bad: Creating a new enum DEPT_NAME_EXIST just for this specific scenario
```

### 2. Returning Unified Error Responses
When returning a failure from a Controller or Service without throwing an exception, always use the unified response builder and reference the abstract error code:
```java
// Good
return ApiResponse.failed(AbstractErrorCode.PARAM_INVALID.getCode(), "结束时间不能早于开始时间");

// Bad: Hardcoding numbers
return ApiResponse.failed(2001, "结束时间不能早于开始时间");
```
