---
name: "devops-testing-standard"
description: "Handles TDD phase. Invoke BEFORE writing feature code to write failing unit tests based on Specifications."
---

# DevOps Phase 3 (Early): Test-Driven Development (TDD)

**Focus**: Writing Unit/Integration Tests based on Specs (SDD & TDD).

## 📋 TDD Flow

1. **Understand Test Architecture**:
   - Refer to the module testing guides (e.g., `src/test/java/.../README.md`) for the standard project testing template.
   - **Fallback Skeleton**: If the README is missing, use a standard Spring Boot test structure:
     ```java
     @SpringBootTest
     @ActiveProfiles("test")
     public class YourServiceTest {
         // @MockBean for external dependencies
         // @Autowired for the service under test
         
         @AfterEach
         public void tearDown() {
             // Explicitly clean up test data if not using @Transactional
         }
     }
     ```

2. **Write Failing Tests (Red)**:
   - Based on the SDD Spec and API Prototype, create Test Classes.
   - **Service Tests**: Mock external dependencies. 
   - **Validation Tests**: Ensure JSR303 (`@Valid`) annotations trigger correctly.

3. **Data Isolation (CRITICAL)**:
   - You MUST ensure transaction rollback (`@Transactional`) or explicit data cleanup in `@AfterEach` after every test method.
   - **STRICTLY PROHIBITED**: Depending on the execution order of test methods. Tests must be fully independent and must not leave dirty data.

4. **Coverage Expectations (Quantified)**:
   - Every public method MUST have tests covering at least three scenarios:
     1. **Normal/Happy Path**: Valid inputs yielding expected outputs.
     2. **Exception Path**: Invalid inputs triggering `BusinessException`.
     3. **Boundary/Edge Cases**: Empty lists, nulls, max lengths, data permission boundaries (e.g., user A attempting to access user B's data).

## 🎯 Outcomes
- Failing Test files committed.
- Ready for Implementation (`devops-feature-implementation`) to make them pass (Green).