# STANDARD Task — Multi-Turn Rhythm Example

A concrete walkthrough showing how a STANDARD task flows across turns, respecting Human-in-the-Loop gates.

---

## Scenario: Add a new REST endpoint `POST /orders/{id}/cancel`

**Risk level:** MEDIUM (new external API, core business path change)
**Profile:** STANDARD
**Approval Gate:** No (MEDIUM = FYI only, no gate)

---

## Turn 1 — Explorer

**Human:** "Add a cancel endpoint for orders. Only the order owner can cancel, and only when status is PROCESSING."

**Agent actions:**
1. Runs `requirement-intake` → emits `[Intake] Input-Type: Feature / Profile: STANDARD / Scenario: Standard`
2. Runs `pre_hook` → loads `java-architecture-standards`, reads wiki preferences
3. Runs `wiki_search.py --query "order cancel status"` → finds `domain/index.md` with OrderStatus enum
4. **Specification Inference:**
   - Current: OrderService has `updateStatus()` but no cancel-specific method
   - Required: cancel endpoint with ownership check + status guard
   - Delta: new controller method + service method + permission check
5. **AC-as-Tests Translation:**
   - AC-001: `Given order owner, status=PROCESSING → POST /orders/{id}/cancel → HTTP 200, status=CANCELLED`
   - AC-002: `Given non-owner → HTTP 403`
   - AC-003: `Given status=DONE → HTTP 409, error code ORD_004`
6. **AC-Driven Impact Check:** `code_index.py --impact-of OrderService.java` → no hidden callers for cancel

**Agent output to human:**
```
[Intent: Change | Profile: STANDARD | Risk: MEDIUM]
→ Phase: Explorer

Gap: OrderService has no cancel method.
Need: cancelOrder(orderId, userId) with ownership + status guard.
AC: 3 testable criteria.
Proceeding to Propose.
```

---

## Turn 2 — Propose + Review + FYI

**Agent actions:**
1. **Brainstorming** generates 2 alternatives:
   - Option A: New `cancelOrder()` in OrderService (direct)
   - Option B: Generic `transitionStatus()` state machine method
   - Selects Option A (simpler, lower blast radius for this scope)
   - Emits Constraint List: "No direct DB writes in controller; use existing DomainException hierarchy"
2. **Review** (MEDIUM): `code-review-checklist` + `java-architecture-standards` — PASS
3. Writes `2026-05-17_order-cancel_task_brief.md` with endpoint contract, service signature, error codes, AC list, Allowed Scope
4. Immediately writes `task_brief.md` path into `launch_spec.md` Artifact column

**Agent output to human (FYI — no gate):**
```
[Propose + Review complete]

Design: POST /orders/{id}/cancel
- Service: OrderService.cancelOrder(Long orderId, Long userId)
- Auth: token userId must equal order.userId
- Guard: status must be PROCESSING (DONE/FAILED → ORD_004)
- Allowed Scope: OrderController.java, OrderService.java

Spec: .claude/runs/task-briefs/2026-05-17_order-cancel_task_brief.md
(FYI — proceeding to Implement unless you object)
```

---

## Turn 3 — Implement

**Agent actions:**
1. `→ Scope: OrderController + OrderService. Role: @Lead Engineer + @Focus Guard. Confidence: HIGH`
2. Reads `task_brief.md` Machine Section: Allowed Scope + AC + Hard Constraints
3. Implements: `OrderController.cancelOrder()` → `OrderService.cancelOrder()` → uses existing `OrderMapper`
4. Runs `shift_left_hook` → `mvn compile` passes
5. **STOP (Yield)**

**Agent output to human:**
```
[Implement complete — compile OK]
Modified: OrderController.java, OrderService.java
Awaiting permission to proceed to QA.
```

---

## Turn 4 — Human: "Proceed to QA"

**Agent actions (QA):**
1. Runs unit tests: `mvn test -pl src/test/...OrderServiceTest`
2. Produces Evidence Mapping Table (3 ACs → table required)

```
| AC | Test Method | Expected | Actual | Status |
| AC-001: owner+PROCESSING → 200 | cancelOrder_ownerProcessing | HTTP 200 | HTTP 200 | PASS |
| AC-002: non-owner → 403 | cancelOrder_nonOwner | HTTP 403 | HTTP 403 | PASS |
| AC-003: DONE → 409 | cancelOrder_doneStatus | HTTP 409 ORD_004 | HTTP 409 ORD_004 | PASS |
```

All rows PASS. QA passes.

---

## Turn 5 — Archive

**Agent actions:**
1. Writes WAL fragments: `20260517_order_cancel_api_append.md` + `20260517_order_cancel_rules_append.md`
2. Moves `task_brief.md` to `llm_wiki/archive/`

**Agent output to human:**
```
→ Phase: Archive. Role: @Knowledge Extractor
WAL written: api + rules. Task brief archived.
```

---

## Key Observations

- **5 turns** for a MEDIUM task: Explorer → Propose/Review → Implement → **YIELD** → QA → Archive
- **1 explicit stop**: Implement Yield (Turn 3→4) — no Approval Gate for MEDIUM
- **Single artifact**: `task_brief.md` is the only task-level file — no brake snapshot, no delivery capsule, no explore report
- **Evidence Mapping Table** makes QA objective — no "I think it works"
- **HIGH risk** adds: Approval Gate (after Propose), one ADR per actual irreversible decision linked from §8 (or explicit "mechanical" note if none), adversarial-review Category B
- **Multi-assistant handoff**: Design/Review/Archive by strong-reasoning assistant → Implement by strong-codegen assistant
