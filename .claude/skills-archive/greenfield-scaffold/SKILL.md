---
name: "greenfield-scaffold"
description: "Starting-from-scratch protocol for projects with no existing codebase. Replaces the standard Explorer phase's 'infer from existing code' logic with a forward-design sequence: domain model → API contract → DB schema → package structure → scaffold. TRIGGER when input-classifier emits Scenario=Greenfield or when there is no src/ directory."
---

# Greenfield Scaffold

When there is no existing codebase, the standard Context Funnel ("read what's already there") cannot apply. This skill defines the forward-design sequence.

**Trigger condition:** `input-classifier` emits `Scenario: Greenfield` OR `src/` directory does not exist.

---

## Phase 0: Scenario Adversarial Check (one round, before any design)

Run `adversarial-review` Category C with the **Greenfield frame**:
> "Assume the domain model has a fundamental entity boundary error. Which boundary decision, if wrong, will require the most invasive refactoring 6 months from now, and why?"

- CRITICAL finding → revise entity boundary before Phase 1.
- MINOR finding → record as a design assumption in the Domain Model document.
- One round only.

---

## Phase 1: Domain Model First

Before any API or DB decisions, define the core domain:

1. **Identify Domain Entities** from the requirements.
   - Each entity: name, core attributes, lifecycle states (if stateful), relationships.
   - Use Ubiquitous Language: name entities in the language of the business, not the database.

2. **Define Invariants** — what must ALWAYS be true about each entity?
   Example: "An Order must always have at least one OrderItem."

3. **Define Boundaries** — which entities belong to the same aggregate? Which are separate bounded contexts?

Output: Domain Model document (entity list + invariants + boundaries).

---

## Phase 2: API Contract

Design the API surface from the domain model, NOT from the database:

1. For each user-facing operation in the requirements: define the API endpoint.
2. Follow project API standards (`java-architecture-standards`): no path variables for non-ID lookups, standard response wrapper, error codes.
3. Draft request/response DTOs.
4. Mark which endpoints require auth, which are public.

Output: API contract section of `task_brief.md`.

---

## Phase 3: DB Schema

Design the schema FROM the domain model and API contract:

1. Each aggregate root → primary table.
2. Value objects → embedded columns (not separate tables) unless size requires it.
3. Apply project SQL standards (`mybatis-sql-standard`): index design, no implicit type conversion, explicit created_at/updated_at/is_deleted fields.
4. No JOIN-first design — design for the Anti-JOIN assembly pattern.

Output: DB schema section of `task_brief.md`.

---

## Phase 4: Package Structure

Define the package structure BEFORE writing any code:

```
com.<org>.<service>/
  ├── controller/       # Thin HTTP layer — no business logic
  ├── service/          # Business logic, @Transactional
  ├── mapper/           # MyBatis interfaces
  ├── entity/           # DB-mapped POJOs
  ├── dto/              # Request/Response DTOs
  ├── exception/        # Custom exceptions
  └── config/           # Spring configuration
```

State explicitly which packages will be created in this task vs. deferred.

---

## Phase 5: Scaffold + Verify

1. Generate the skeleton: package directories, empty classes with correct annotations.
2. Run `shift_left_hook` (compile) immediately after scaffold — confirm the empty structure compiles.
3. Proceed to feature implementation in the standard Implement phase.

---

## Key Differences from Standard Flow

| Standard | Greenfield |
|---|---|
| Explorer reads existing code | Explorer designs domain model from scratch |
| Propose refines existing patterns | Propose establishes ALL patterns |
| Constraint List from existing invariants | Constraint List from domain invariants |
| Wiki funnel finds domain knowledge | Domain knowledge comes from requirements only |
