---
name: "devops-bug-fix"
description: "Handles Bug Fixing. Invoke for diagnosing, reproducing, and fixing production or testing defects."
---

# DevOps General: Dedicated Bug Fix (独立Bug修复)

**Focus**: Standardized Bug Resolution. Diagnose -> Reproduce (Test) -> Fix -> Verify.

Do NOT mix this with standard feature development. This is a dedicated flow for fixing bugs.

## 📋 Steps

1. **Diagnose & Isolate**:
   - Analyze the error log, stack trace, or user report.
   - Use `Grep` and `Read` tools to inspect the suspected code.
   - Identify the root cause. If it involves a specific business domain, invoke the corresponding business skill.

2. **Reproduce via Test (TDD Approach)**:
   - **CRITICAL**: Before changing the implementation, write a Unit Test or Integration Test that explicitly reproduces the bug (it should fail).
   - If the bug is too complex to mock, clearly document the reproduction steps.

3. **Implement the Fix**:
   - Modify the code. Ensure you follow `checkstyle` and `global-backend-standards`.
   - Ensure the fix does not break the **Open-Closed Principle** (avoid breaking existing consumers).

4. **Verify**:
   - Run the reproduction test (it should now pass).
   - Run the broader test suite for the module to ensure no regressions.

## 🎯 Outcomes
- Root cause analysis documented.
- A passing test that reproduces the bug.
- The fixed implementation.