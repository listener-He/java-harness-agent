---
name: "java-javadoc-standard"
description: "Enforces the project's strict Javadoc commenting style. Invoke when generating or updating classes, methods, or fields to ensure consistency with the existing codebase."
---

# Java Javadoc Commenting Standard

This skill dictates the strict Javadoc commenting style used throughout the project. It is based on the analysis of existing core modules (`rbac`, `org`).

## 1. 类级别注释 (Class-Level Comments)

所有的 Java 类（Controller, Service, Impl, Entity, DTO, VO 等）都必须包含标准的 Javadoc 块。
- **必须包含**：一句话描述该类的核心作用。
- **必须包含**：`@author` (默认使用 `HeHui`，除非指定其他人)。
- **必须包含**：`@date` (格式为 `yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm`)。
- **格式示例**：
  ```java
  /**
   * 企业端-人员管理
   *
   * @author HeHui
   * @date 2026-03-18 17:23
   */
  @RestController
  public class EmployeeController { ... }
  ```
- **对于 Entity/DTO/VO 简单的类**：允许只写类名描述（可以省略作者和日期，但推荐保留），如：
  ```java
  /**
   * 人员实体类
   */
  ```

## 2. 方法级别注释 (Method-Level Comments)

**所有对外暴露的方法**（Controller 中的接口方法、Service 接口中的方法、Service 实现类中的非覆盖方法）必须包含完整的 Javadoc。
- **必须包含**：一句话描述该方法的作用（如 "新增人员"、"分页查询人员"）。
- **必须包含**：`@param` 描述所有的入参。对于复杂的 `AccessUser`，统一描述为 "访问用户" 或 "当前登录用户上下文"。
- **必须包含**：`@return` 描述返回值。使用 `{@link ClassName}` 进行链接。
- **空行规范**：描述与 `@param` 之间留一个空行；`@param` 与 `@return` 之间留一个空行。
- **格式示例**：
  ```java
  /**
   * 新增人员
   *
   * @param request    请求入参
   * @param accessUser 访问用户
   *
   * @return {@link ApiResponse }<{@link Void }>
   */
  ```
- **接口实现方法 (`@Override`)**：如果在接口层已经写了详细的注释，实现类 (`Impl`) 中可以省略大段 Javadoc，直接使用 `/** ... */` 简写或者直接省略，除非内部逻辑极其复杂需要用 `<p>1. 校验...<br>2. 保存...</p>` 分步说明。

## 3. 字段级别注释 (Field-Level Comments)

Entity, DTO (Request), VO (Response) 中的**所有字段**都必须有注释。
- **格式**：统一使用多行 Javadoc `/** ... */` 格式，**禁止**使用单行注释 `//`。
- **内容**：精简地描述字段的中文含义。如果是枚举或状态值，必须在注释中注明字典值（如 `0停用 1正常`）。
- **格式示例**：
  ```java
  /**
   * 所属公司ID
   */
  private Long companyId;

  /**
   * 账户状态 0停用 1正常
   */
  private Integer accountStatus;
  ```

## 4. 复杂逻辑的内部注释 (Inline Comments)

在 Service 的复杂实现方法中，提倡使用数字编号的行级注释来划分逻辑块，使得代码一目了然：
```java
// 1. 校验手机号/工号是否已存在
boolean exists = ...;

// 2. 转换实体
Employee employee = BeanUtil.copyProperties(request, Employee.class);

// 3. 落库保存
this.save(employee);
```
