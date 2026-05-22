---
name: "migration-planner"
description: "A→B system migration protocol where the core requirement is behavioral equivalence, not new features. Generates an equivalence test suite BEFORE migration begins. Migration is done when equivalence tests pass. TRIGGER when input-classifier emits Scenario=Migration or when the request is 'migrate from X to Y'."
---

# Migration Planner

System migration is different from feature development: **the requirement is behavioral equivalence, not new behavior.**

A migration is complete when: every behavior that existed in A is preserved in B, and the equivalence test suite passes.

---

## Phase 0: Scenario Adversarial Check (one round, before any analysis)

Run `adversarial-review` Category C with the **Migration frame**:
> "Assume behavioral equivalence cannot be fully verified by automated tests. Which business-critical behavior is most likely to silently diverge between A and B, and how would a user first notice?"

- CRITICAL finding → design a manual verification protocol for that behavior before proceeding.
- MINOR finding → add it to the equivalence test suite as a priority test case.
- One round only.

---

## Phase 1: Behavior Inventory (MUST — before any migration code)

Enumerate what System A currently does:

1. **API Behavior Inventory**
   - For each endpoint: input → output mapping (including error cases).
   - Use existing integration tests, API documentation, or trace logs as evidence.
   - Do NOT rely on code reading alone — behavior is what the system does, not what the code says.

2. **Data Contract Inventory**
   - What data does A store? In what format?
   - What are the implicit constraints (nullability, enum values, max lengths)?
   - What data must be preserved exactly? What can be transformed?

3. **Failure Mode Inventory**
   - What errors does A return, and under what conditions?
   - Equivalence includes error behavior, not just happy paths.

Output: `<YYYY-MM-DD>_<slug>_behavior_inventory.md`

---

## Phase 2: Equivalence Test Suite (MUST — before migration code)

Write tests that verify B behaves identically to A:

```
For each behavior in the inventory:
  - Write a test that runs against BOTH A and B
  - Assert: output(A, input) == output(B, input)
```

**Test types:**
- **Golden file tests**: capture A's actual output as golden files; B must match.
- **Differential tests**: run same input against both; diff the outputs.
- **Contract tests**: assert the response schema is identical.

These tests will initially FAIL (B doesn't exist yet). That is correct — they define the migration target.

Output: Equivalence test suite (committed alongside migration code).

---

## Phase 3: Migration Execution

Implement B in the standard STANDARD lifecycle. But:
- **Definition of done**: equivalence tests PASS, not "code is written".
- **Do NOT delete A** until equivalence tests pass AND a canary period completes.
- Maintain A and B in parallel until fully validated.

**Incremental migration (preferred over big-bang):**
1. Migrate one behavior group at a time.
2. Run equivalence tests after each group.
3. Only migrate the next group when the previous is green.

---

## Phase 4: Cutover + Cleanup

1. Run full equivalence test suite — all must pass.
2. Run A and B in parallel (shadow mode or canary) for a defined period.
3. Monitor divergence: any case where A and B return different results is a migration bug.
4. After canary period with zero divergence: decommission A.
5. Archive behavior inventory as wiki documentation for B.

---

## Key Constraint

**The equivalence test suite is the acceptance criteria.** Do NOT accept a migration as complete based on code review alone. The tests must run and pass.

If the requirements include new behavior ON TOP of migration: separate the migration task (equivalence first) from the new behavior task (feature development after migration). Do not mix them.
