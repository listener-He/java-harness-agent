---
name: "error-code-standard"
description: "Guides the usage of system error codes. Invoke when generating or modifying code that throws BusinessException or returns ApiResponse.failed to select or create appropriate ErrorCodes."
---

# Error Code Standard (异常状态码使用规范)

**CRITICAL: You MUST read and follow this guide before generating ANY code that returns an error response (`ApiResponse.failed`) or throws a business exception (`new BusinessException`).**

This project uses a highly abstracted, behavior-driven 4-digit ErrorCode system. We do **NOT** create a new enum for every specific error message (e.g., no separate codes for "phone number error" vs. "email error"). Instead, we reuse abstract codes and override the `message`.

## 🧠 Decision Flow: How to choose an ErrorCode

When you need to return an error, follow these steps:

### 1. Analyze the Error Scenario
Ask yourself: What type of error is this?
- Is it a **system/infrastructure** error (e.g., 404 Not Found, 401 Unauthorized)? -> Go to **SystemErrorCode** (0~999).
- Is it a **technical failure** (e.g., external API failed)? -> Go to **BizErrorCode 1xxx**.
- Is it a **hard rule/validation** failure (e.g., empty param, duplicate data)? -> Go to **BizErrorCode 2xxx**.
- Is it a **business logic/state** failure (e.g., quota exceeded, dependency exists)? -> Go to **BizErrorCode 3xxx**.
- Does the frontend need to **do something specific** (e.g., redirect, pop up a strong modal)? -> Go to **BizErrorCode 4xxx**.

### 2. Map to Existing Codes
Check the existing dictionaries in `SystemErrorCode.java` and `BizErrorCode.java`. 
**Always try to reuse an existing code by overriding the message.**

#### Common Reusable Mappings:
- **Parameter Validation (Empty, Format Error, Limit Exceeded)**:
  - Code: `BizErrorCode.PARAM_INVALID` (2001)
  - Example: `new BusinessException(BizErrorCode.PARAM_INVALID, "手机号格式不正确")`
- **Data Duplication (Name exists, Phone exists)**:
  - Code: `BizErrorCode.DATA_DUPLICATED` (2002)
  - Example: `new BusinessException(BizErrorCode.DATA_DUPLICATED, "部门名称已存在")`
- **Dependency Exists (Cannot delete because children exist)**:
  - Code: `BizErrorCode.HAS_DEPENDENCY` (3003)
  - Example: `new BusinessException(BizErrorCode.HAS_DEPENDENCY, "该部门下存在员工，不允许删除")`
- **Invalid State (Cannot modify because already started/finished)**:
  - Code: `BizErrorCode.INVALID_STATE` (3002)
  - Example: `new BusinessException(BizErrorCode.INVALID_STATE, "排班已开始，无法修改")`
- **Resource Quota (Limit reached)**:
  - Code: `BizErrorCode.QUOTA_EXCEEDED` (3001)
  - Example: `new BusinessException(BizErrorCode.QUOTA_EXCEEDED, "公司数量已达上限")`
- **Rate Limit (Too frequent)**:
  - Code: `BizErrorCode.RATE_LIMIT` (2003)
  - Example: `new BusinessException(BizErrorCode.RATE_LIMIT, "请勿频繁发送验证码")`

### 3. When to Create a NEW Code (Rare!)
You should **ONLY** create a new code in `BizErrorCode.java` if:
1. The error requires a **completely new frontend interaction** (e.g., 4xxx series).
2. The error represents a **completely new abstract category** of business failure that cannot be grouped under existing codes (e.g., if we introduce a new abstract concept like "Geographical Restriction").

If you must create one, follow the 4-digit numbering rule:
- `1xxx`: General Technical
- `2xxx`: Rule / Validation
- `3xxx`: Business Logic
- `4xxx`: Interaction (Frontend actions)

## 💻 Code Generation Rules

### 1. Throwing Exceptions
ALWAYS prefer the dynamic message constructor of `BusinessException`:
```java
// Good: Reusing abstract code, specific message
throw new BusinessException(BizErrorCode.DATA_DUPLICATED, "角色名称已存在");

// Bad: Using generic failed for everything
throw new BusinessException("角色名称已存在"); // Defaults to 3000

// Bad: Creating a new enum DEPT_NAME_EXIST just for this
```

### 2. Returning ApiResponse.failed (in Controllers or Services)
```java
// Good
return ApiResponse.failed(BizErrorCode.PARAM_INVALID.getCode(), "结束时间不能早于开始时间");

// Bad: Hardcoding numbers
return ApiResponse.failed(2001, "结束时间不能早于开始时间");
```
