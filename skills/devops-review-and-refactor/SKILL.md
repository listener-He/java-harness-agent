---
name: "devops-review-and-refactor"
description: "Handles code review and feature modification. Invoke when reviewing code against specs or refactoring existing features with regression testing."
---

# DevOps Phase 4: Review, Modification & Refactoring

**Focus**: Safe Modification, Continuous Quality, Automated Review.

## 📋 1. Safe Feature Modification (Refactoring Flow)
When asked to modify or refactor existing code, follow this flow:
1. **Identify Regression Tests**: Locate or write tests covering the existing behavior.
2. **Review Dependencies**: Check what other modules rely on this code.
3. **Implement & Verify**: Make the change and ensure regression tests pass.

## 📋 2. Automated Code Review (The CR Checklist)
Before presenting any code or feature as "Done," run a self-correction loop. 

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
- A final "CR Checklist Report" output to the user detailing the checks and context gathered.