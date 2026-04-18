# SYSTEM DIRECTIVE: Utilities Usage & Design Standard

## 🎯 Core Objective
This skill defines the standard operating procedures for discovering, utilizing, and designing utility classes (`*Util`, `*Helper`) and common technical patterns. It prioritizes code reuse, strict boundary enforcement, functional programming paradigms, and high-performance data processing.

## 🛑 1. Discovery & Reuse First (Anti-Reinvention)
**Rule:** NEVER implement a new utility function before thoroughly searching the existing workspace and standard libraries.
- **Search Heuristics:** Always run semantic searches or use the `Glob` tool for `*Util.java`, `*Utils.java`, `*Helper.java`, or inspect `common`, `core`, `util` packages.
- **Standard Libraries Priority:** Default to established third-party libraries already in the project dependencies (e.g., `Guava`, `Apache Commons`, `Hutool`) for standard operations (e.g., `StringUtils.isNotBlank`, `CollectionUtils.isEmpty`).
- **Pattern Matching:** Analyze how similar business modules handle identical scenarios. Mimic existing proven patterns to maintain codebase consistency.

## 📐 2. Boundaries, Accessibility & Dependencies
**Rule:** If a custom utility is strictly necessary, it must adhere to rigid structural boundaries.
- **Statelessness:** Utilities MUST be purely stateless. Declare classes as `public final class` and explicitly define a `private` default constructor to prevent instantiation. All methods MUST be `public static` (or `package-private static`).
- **Dependency Isolation (Acyclic Dependencies):** Pure technical utilities (e.g., `DateUtil`, `StringUtil`) are STRICTLY PROHIBITED from importing business-level components (e.g., `UserService`, business entities, or domain-specific exceptions).
- **Accessibility Control:** Place global utilities in `common/utils`. Place module-specific utilities in `[module]/utils` and restrict their visibility to `package-private` where possible to prevent cross-domain contamination.

## 🧩 3. Functional Programming Mindset
**Rule:** Inject Java 8+ functional interfaces (`Function`, `Consumer`, `Predicate`, `Supplier`, `BiConsumer`) to abstract control flows and maximize reusability.
- **Memory-level Data Assembly (In-Memory JOIN):** Avoid hardcoded `for`-loops with intermediate `Map`s. Parameterize the key extraction, data loading, and result mapping behaviors.
- **Behavior Parameterization:** Abstract reusable skeletons (e.g., retry mechanisms, resource cleanup, logging wrappers) by passing behaviors as functions.
- **Code Generation Standard:**
  ```java
  public static <T, K, V> void assembleData(
          List<T> source,
          Function<T, K> keyExtractor,
          Function<List<K>, Map<K, V>> valueLoader,
          BiConsumer<T, V> resultSetter) {
      // Implementation: Extract Keys -> Load Values in Batch -> Iterate and Set
  }
  ```

## 🚀 4. High-Volume Data Batching (Cursor / IDX Pattern)
**Rule:** STRICTLY PROHIBITED to load massive datasets into memory at once (OOM risk) or use deep pagination `LIMIT offset, size` (Performance degradation). MUST use Cursor/IDX-based batch processing.
- **Cursor Concept:** Always track the unique identifier (e.g., `id`, `timestamp` - must be indexed) of the last processed record. Query using `WHERE id > :lastId ORDER BY id ASC LIMIT :batchSize`.
- **Streamlined Batch Consumer Skeleton:** Separate the data fetching strategy from the data consumption logic using functional interfaces.
- **Code Generation Standard:**
  ```java
  public static <T, C extends Comparable<C>> void processInBatches(
          C initialCursor,
          int batchSize,
          BiFunction<C, Integer, List<T>> fetcher, // Fetches data based on cursor and limit
          Function<T, C> cursorExtractor,          // Extracts the cursor from the last element
          Consumer<List<T>> batchConsumer          // Consumes the current batch
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

## 🏛 5. Design Patterns & Business Boundaries
**Rule:** Do not cram complex business logic into static utility classes. Use appropriate design patterns to maintain Domain-Driven Design (DDD) boundaries.
- **Strategy Pattern:** Replace extensive `if-else` or `switch` statements for business types with a common interface and Strategy Pattern (coupled with Factory or Spring IoC routing).
- **Template Method Pattern:** For standardized business workflows with varying localized steps, utilize the Template Method pattern or inject high-order functions to ensure the Open-Closed Principle (OCP).
- **Anti-Corruption Layer (ACL):** When integrating with complex external libraries or third-party APIs, establish an ACL or Adapter. Do not let external DTOs or specific exceptions bleed into the core business logic or utility layers.