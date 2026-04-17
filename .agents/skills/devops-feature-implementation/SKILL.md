---
name: "devops-feature-implementation"
description: "Handles feature code implementation. Invoke in Phase 4 to write Java code according to the approved contract."
---

# Phase 4: Implement (Feature Implementation)

**Focus**: Elegant, Robust Implementation to satisfy Specs (`openspec.md`).

## 🚨 Strict Rules (MANDATORY)
- **Checkstyle Invocation**: You MUST invoke the `checkstyle` skill for ALL new and modified code.

## 📋 Implementation Directives

### 1. Code Elegance (Concrete Rules)
Do not over-design. In this repository, "Elegance" concretely means:
- Route to and strictly follow `checkstyle` (4 spaces, K&R braces, naming conventions).
- Prefer **composition over inheritance**.
- Keep methods **short and focused** (ideally < 50 lines). Extract complex logic into private helper methods.
- **No Magic Values**: Extract all magic numbers and strings to `private static final` constants or Enums.

### 2. Modifying Legacy Code (Open-Closed Principle)
- When a new feature requires changes to existing legacy classes, evaluate the impact carefully.
- Prefer creating a **new adapter class, strategy implementation, or extending via interfaces** rather than heavily modifying a stable, old class.
- If modifying an old class is unavoidable, ensure existing unit tests pass before adding new logic.

### 3. Robustness & Scale
- **Exceptions**: Use `BusinessException` with appropriate error codes (See `error-code-standard`).
- **Defensive Checks**: Validate inputs (`@Valid`) and enforce business rules early in the service layer.
- **High Performance**: Follow `mybatis-sql-standard` (Anti-JOIN, batching). No DB queries or RPC calls inside loops.
- **Concurrency & Isolation**: Use `@ResourceLock` on modifying endpoints. Filter by `tenant_id` at the DB level or use `@BeforePermission`.

## 🎯 Outcomes
- Java code (Controller, Service, Mapper, POJO) completed according to the contract.
- Code elegantly structured, scalable, and secure.
- Ready for Phase 5: QA Test.