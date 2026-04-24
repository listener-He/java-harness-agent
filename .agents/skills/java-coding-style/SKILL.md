---
name: "java-coding-style"
description: "MANDATORY MASTER skill for Java coding style. Enforces Checkstyle (4 spaces, K&R braces), strict Javadoc templates, utility class boundaries, and functional programming patterns (In-Memory JOIN, Cursor Batching)."
---

# Java Coding Style & Utility Standards

> **Trigger:** You MUST read and follow this guide when writing, formatting, or reviewing ANY Java code to ensure structural and stylistic consistency.

## 💅 1. Formatting & Naming Conventions
**BASE RULE:** This project strictly enforces a combination of **Google Java Style** and **Sun Code Conventions**. When in doubt about formatting, default to Google Java Style.

- **Indentation:** ALWAYS use **4 spaces**. NEVER use tabs.
- **Line Wrapping:** Wrap before the `.` operator for chained methods (e.g., Stream API, MyBatis wrappers).
- **Braces (K&R Style):**
  - Opening brace `{` on the **same line**.
  - Closing brace `}` on a **new line**.
  - ALWAYS use braces for `if`, `else`, `for`, `while` (no single-line omissions).
- **Imports:** NO wildcard imports (`import java.util.*;` is strictly forbidden).
- **Naming:**
  - Classes/Interfaces: `UpperCamelCase`. Implementations MUST use the `Impl` suffix.
  - Methods/Variables: `lowerCamelCase`.
  - Constants: `UPPER_SNAKE_CASE`.

---

## 📝 2. Javadoc & Comments Standard
EVERY public element MUST have Javadoc. Do not use single-line `//` for structural comments.

**Class-Level Javadoc (Required for all Controllers, Services, Entities):**
```java
/**
 * 一句话描述该类的核心作用 (One-line description)
 *
 * @author HeHui
 * @date 2026-03-31
 */
```

**Method-Level Javadoc (Required for all public methods):**
```java
/**
 * 方法功能描述 (Method description)
 *
 * @param request    请求入参描述
 * @param accessUser 当前登录用户上下文
 *
 * @return {@link ApiResponse}<{@link Void}>
 */
```

**Field-Level Javadoc (Required for ALL Entity/DTO/VO fields):**
```java
/**
 * 账户状态 0停用 1正常 (Must explain enum/dictionary values)
 */
private Integer accountStatus;
```

**Inline Comments:** Use `// 1. 步骤说明` to divide complex logic blocks inside methods.

---

## 🛠️ 3. Utility Classes & Anti-Reinvention
- **Discovery First:** NEVER reinvent the wheel. Always prefer established libraries (`cn.hutool.*`, `org.apache.commons.*`) or existing project utilities (`*Util`, `*Helper`).
- **Strict Boundaries:** Custom utility classes MUST be stateless: `public final class` with a `private` default constructor. All methods MUST be `static`.
- **Acyclic Dependencies:** Utility classes MUST NOT import business-level components (e.g., `UserService` or Entities).

---

## 🚀 4. Functional Programming & High-Performance Patterns
When writing complex data processing logic, you MUST use functional programming paradigms (`Function`, `Consumer`, `BiConsumer`) to abstract control flows.

### Pattern A: In-Memory Data Assembly (Anti-JOIN)
Avoid nested `for`-loops when assembling cross-domain data. Parameterize the behavior:
```java
public static <T, K, V> void assembleData(
        List<T> source,
        Function<T, K> keyExtractor,
        Function<List<K>, Map<K, V>> valueLoader,
        BiConsumer<T, V> resultSetter) {
    // 1. Extract Keys -> 2. Load Values in Batch -> 3. Iterate and Set
}
```

### Pattern B: High-Volume Cursor Batching (Anti-LIMIT/OFFSET)
STRICTLY PROHIBITED to load massive datasets into memory at once or use deep pagination (`LIMIT offset, size`). MUST use Cursor/IDX-based batch processing:
```java
public static <T, C extends Comparable<C>> void processInBatches(
        C initialCursor,
        int batchSize,
        BiFunction<C, Integer, List<T>> fetcher, // Query: WHERE id > cursor ORDER BY id ASC LIMIT batchSize
        Function<T, C> cursorExtractor,          // Extract cursor from the last element
        Consumer<List<T>> batchConsumer          // Consume the batch
) {
    C currentCursor = initialCursor;
    while (true) {
        List<T> batch = fetcher.apply(currentCursor, batchSize);
        if (batch == null || batch.isEmpty()) break;
        batchConsumer.accept(batch);
        currentCursor = cursorExtractor.apply(batch.get(batch.size() - 1));
    }
}
```
