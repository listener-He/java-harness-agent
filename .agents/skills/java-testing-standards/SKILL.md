---
name: "java-testing-standards"
description: "MANDATORY MASTER skill for Java Testing & QA. Enforces test isolation, mock guidelines, and the 3-scenario coverage rule (Happy Path, Exception, Edge Cases)."
---

# Java Unit & Integration Testing Standards

> **Trigger:** Invoke this skill during the **QA Phase** or whenever asked to write or refactor JUnit tests.

## 🧪 1. Test Architecture & Skeletons
If a module-specific testing guide (`src/test/java/.../README.md`) exists, follow it. Otherwise, strictly adhere to the Spring Boot testing skeleton:

```java
@SpringBootTest
@ActiveProfiles("test") // CRITICAL: Always bind to the test profile to avoid hitting prod/dev DBs
public class YourServiceTest {

    // 1. Mock external dependencies (e.g., Feign clients, third-party APIs)
    @MockBean
    private ExternalApiService externalApiService;

    // 2. Inject the service under test
    @Autowired
    private YourService yourService;

    @AfterEach
    public void tearDown() {
        // 3. Explicitly clean up test data if @Transactional is not sufficient
    }
}
```

## 🧹 2. Data Isolation (CRITICAL RED LINE)
- **Zero Dirty Data:** You MUST ensure transaction rollback (`@Transactional`) is applied to the test class, or explicitly clean up inserted data in an `@AfterEach` method.
- **Independent Execution:** Tests MUST be fully independent. It is **STRICTLY PROHIBITED** to write tests that depend on the execution order of other test methods.

## 📊 3. The 3-Scenario Coverage Rule
Every public business method MUST have tests covering at least the following three dimensions:
1. **Happy Path:** Valid inputs yielding expected outputs and database state changes.
2. **Exception Path:** Invalid inputs correctly triggering the expected `DomainException` (e.g., duplicate unique keys, invalid statuses). Use `assertThrows`.
3. **Boundary/Edge Cases:** Empty lists, null parameters, maximum string lengths, and **Data Permission Boundaries** (e.g., verifying that User A attempting to access User B's data throws an access denied exception).

## 🛡️ 4. Validation Testing
- When testing Controllers or input boundaries, explicitly verify that `jakarta.validation` (`@Valid`, `@NotNull`, `@Size`) constraints trigger the correct field error responses before reaching the Service layer.
