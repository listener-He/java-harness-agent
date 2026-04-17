---
name: "devops-review-and-refactor"
description: "Handles review and modification. Invoke in Phase 3 to review the proposed contract against engineering standards, or when refactoring."
---

# Phase 3: Review (Review & Refactor)

**Focus**: Contract Review, Safe Modification, Continuous Quality, Automated Review.

## 📋 1. Safe Feature Modification (Refactoring Flow)
When asked to modify or refactor existing code, follow this flow:
1. **Identify Regression Tests**: Locate or write tests covering the existing behavior.
2. **Review Dependencies**: Check what other modules rely on this code.
3. **Implement & Verify**: Make the change and ensure regression tests pass.

## 📋 2. Automated Review (The CR Checklist)
Before proceeding to the Approval Gate and Implementation, run a self-correction loop on the proposed `openspec.md` and related context. 

**Context Gathering (CRITICAL)**:
- Before reviewing, you MUST use `Read` or `Glob` tools to inspect relevant context (e.g., `pom.xml`, base classes, utility classes, DB structure) to prevent hallucinations. Do not assume a utility class exists without verifying it.

### 🔍 Architectural & Performance Checks
- [ ] **Business Boundary**: Does the code stay within its domain? (Calls other services instead of direct cross-domain DB access).
- [ ] **Data Model**: Are new tables compliant (`tenant_id`, `is_deleted`)?
- [ ] **Performance Baseline**: Compare performance metrics if available (e.g., Did the interface response time increase? Are there N+1 queries?).

### 🔍 Abstracted Standards Compliance
- [ ] **Code Style & Formatting**: Check against the `checkstyle` skill (formatting, annotations, Javadoc, no magic values).
- [ ] **API & Naming**: Check against the `java-backend-api-standard` skill (verb URLs, no `@PathVariable`).
- [ ] **Database & SQL**: Check against the `mybatis-sql-standard` skill (Anti-JOIN, tenant isolation, loop safety).
- [ ] **Error Handling**: Check against the `error-code-standard` skill.

## 🎯 Outcomes
- A final "Review Report" detailing the checks and context gathered.
- If review passes, ready for Approval Gate.
- If review fails, trigger `fail_hook` and roll back to Phase 2: Propose.