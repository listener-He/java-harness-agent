# OpenSpec Schema (Contract Template)

This is the required contract format for Phase 2 (Propose).

Rules:
- The proposal document MUST be stored under `.agents/llm_wiki/wiki/specs/`.
- After creating it, you MUST add a link + 1–2 line summary into `.agents/llm_wiki/wiki/specs/index.md`.

---

## Slim Spec (LOW risk only)

When the change is LOW risk, `openspec.md` MAY be downgraded to a Slim Spec to reduce review fatigue and documentation cost.

Hard rules:
- The document MUST include the marker `spec_mode: SLIM`.
- The document MUST contain all sections below.

```markdown
spec_mode: SLIM

# Change Summary
- What changed: one sentence
- Why: one sentence

# Scope of Change
- File/module list (paths only)

# Risk & Rollback
- Why LOW: one sentence
- Rollback steps: one sentence or a short list

# Verification & Evidence
- Local verification: build/test/manual steps you actually ran
- Evidence: logs/snippets/screenshots/links (if any)
```

## Standard Spec (MEDIUM/HIGH risk)

When the change is MEDIUM or HIGH risk, you MUST use the Standard Spec format.

Hard rules:
- The document MUST include the marker `spec_mode: STANDARD`.
- The document MUST contain all sections below (1 through 7).

```markdown
spec_mode: STANDARD

## 1. Context
- Business goal: one sentence.
- Scope of change: list modules/packages/key classes to be changed (objective checklist for review and QA).
- Dependencies: list the wiki documents you read (MUST include relative links).
  - Example: `depends_on: [../wiki/domain/index.md]`

## 2. Domain Model
If no change, write "None".
- New or updated terms.
- State machine changes or enum updates.

## 3. API Contract (Handoff)
If no change, write "None". This section MUST be highly structured.
- Endpoint: `POST /api/v1/...`
- Header/Auth: token required? special headers?
- Request:
  - Provide exact field types, required/optional, validation rules.
  - Provide a standard JSON example.
- Response:
  - Provide the full JSON response schema (including error response shape).

## 4. Data Model
If no change, write "None".
- Table name, new fields, types, defaults, indexes.

## 5. Business Logic
- Step-by-step behavior.
- Error handling and fallback branches.

## 6. Non-Functional Constraints (Hard Constraints)
If none, write "None".
- Security & permissions.
- Concurrency & idempotency.
- Forbidden patterns (DO NOT do).
- Rollback steps for partial failures.

## 7. Acceptance Criteria (Testing)
This section MUST use structured language suitable for automated tests.
- Happy path: Given / When / Then.
- Edge cases: invalid params, concurrency, permission denied, etc.
- Unit test requirements: key branches and asserts.
```
