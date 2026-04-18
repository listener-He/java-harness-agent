---
name: "devops-testing-standard"
description: "Handles Testing and QA. Invoke during Phase 5 to ensure test coverage and validation based on Specifications."
---

# Phase 5: QA Test (Testing Standard)

**Focus**: Writing Unit/Integration Tests based on Specs and Validating Implementation.

## 📋 Testing Flow

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

2. **Write and Validate Tests**:
   - Based on the `openspec.md` created in Phase 2 (Propose), create or validate Test Classes.
   - **Service Tests**: Mock external dependencies. 
   - **Validation Tests**: Ensure JSR303 (`@Valid`) annotations trigger correctly.

3. **Data Isolation (CRITICAL)**:
   - You MUST ensure transaction rollback (`@Transactional`) or explicit data cleanup in `@AfterEach` after every test method.
   - **STRICTLY PROHIBITED**: Depending on the execution order of test methods. Tests must be fully independent and must not leave dirty data.

4. **Coverage Expectations (Quantified)**:
   - Every public method MUST have tests covering at least three scenarios:
     1. **Normal/Happy Path**: Valid inputs yielding expected outputs.
     2. **Exception Path**: Invalid inputs triggering Domain Exceptions.
     3. **Boundary/Edge Cases**: Empty lists, nulls, max lengths, data permission boundaries (e.g., user A attempting to access user B's data).

## 🎯 Outcomes
- Test files committed and passing (Green).
- Objective evidence produced for the QA phase.
- Ready for Phase 6: Archive.