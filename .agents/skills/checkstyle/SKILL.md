---
name: "checkstyle"
description: "Enforces strict Java checkstyle rules combining Google and Sun standards, adapted for the org and rbac modules. Invoke when generating, reviewing, or refactoring Java code to ensure style compliance."
---

# Java Checkstyle Standard (Java 代码规范)

**CRITICAL: You MUST strictly adhere to this checkstyle guide when writing or modifying ANY Java code in this workspace.**

This standard is synthesized from Google Java Style and Sun Code Conventions, heavily adapted based on the `com.jiuyu.governance.business.org` and `rbac` module architectures.

## 1. Formatting & Indentation (格式与缩进)
- **Indentation**: ALWAYS use **4 spaces**. NEVER use tabs.
- **Line Wrapping**: Keep lines under 120 characters. For chained methods (e.g., MyBatis Plus `LambdaQueryWrapper` or Stream API), wrap before the `.` operator and indent by 4 or 8 spaces.
- **Braces (K&R Style)**:
  - Opening brace `{` goes on the **same line** as the declaration.
  - Closing brace `}` goes on a **new line** by itself.
  - ALWAYS use braces for `if`, `else`, `for`, `while`, even if the body is a single line.
- **Whitespace**:
  - Add a space before opening braces `{` (e.g., `if (condition) {`).
  - Add a space after keywords `if`, `for`, `while`, `catch` before the parenthesis `(`.
  - Add spaces around binary operators (`=`, `+`, `&&`, `==`, etc.).

## 2. Naming Conventions (命名规范)
- **Packages**: All lowercase, dot-separated (e.g., `com.jiuyu.governance.business.org`).
- **Classes/Interfaces**: `UpperCamelCase`.
  - Interfaces should be adjectives or nouns.
  - Implementations MUST use the `Impl` suffix (e.g., `DeptServiceImpl`).
- **Methods/Variables**: `lowerCamelCase`.
- **Constants**: `CONSTANT_CASE` (all uppercase with underscores).
- **POJO Suffixes**:
  - Requests: `XxxRequest` (e.g., `DeptAddRequest`).
  - Responses: `XxxResponse` (e.g., `DeptResponse`).
  - Entities: No suffix, pure nouns (e.g., `Dept`, `Employee`).

## 3. Imports (导包规范)
- **NO Wildcard Imports**: Never use `import java.util.*;`. Explicitly import classes.
- **Grouping Order**:
  1. Standard Java (`java.*`, `javax.*`)
  2. Spring / Jakarta (`org.springframework.*`, `jakarta.*`)
  3. Third-party libraries (`cn.hutool.*`, `com.baomidou.*`)
  4. Internal framework (`com.jiuyu.framework.*`)
  5. Current project (`com.jiuyu.governance.*`)
- Separate each group with a single blank line.

## 4. Javadoc & Comments (注释规范)
- **Class Javadoc**: EVERY class and interface MUST have a class-level Javadoc including a description, `@author`, and `@date` (format: `yyyy-MM-dd` or `yyyy-MM-dd HH:mm`).
  ```java
  /**
   * 部门业务接口
   *
   * @author HeHui
   * @date 2026-03-31
   */
  ```
- **Method Javadoc**: All public methods (especially in Controllers and Services) MUST have Javadoc explaining the purpose, `@param`, and `@return`.
- **Inline Comments**: Use `//` for single-line comments. Place the comment on a separate line ABOVE the code it describes, not at the end of the line.

## 5. OOP & Best Practices (面向对象与最佳实践)
- **Lombok**: Extensively use Lombok to reduce boilerplate. Explicitly forbid `@Data` on Entity and DTO classes, mandate `@Getter` and `@Setter` instead. Use `@RequiredArgsConstructor` for dependency injection, and `@Slf4j` for logging.
- **Dependency Injection**: ALWAYS use Constructor Injection via Lombok's `@RequiredArgsConstructor`. NEVER use `@Autowired` on fields.
- **Validation**: Use `@Valid` or `@Validated` on Controller method parameters.
- **Magic Numbers**: Avoid magic numbers or strings. Extract them to `private static final` constants or Enums.

## 6. Enforcement Checklist
Before outputting code, verify:
- [ ] No tab characters (4 spaces only).
- [ ] No wildcard imports (`.*`).
- [ ] K&R braces used correctly.
- [ ] Javadoc present on classes and public methods.
- [ ] Constructor injection used instead of field injection.
