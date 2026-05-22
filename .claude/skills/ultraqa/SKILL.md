---
name: ultraqa
description: "Structured QA cycling workflow: test → verify → fix → repeat until all ACs pass. Use when AC count ≥ 4 OR risk = HIGH. Requires an Evidence Mapping Table (AC ↔ Test ↔ Result). Mutually exclusive with ac-verify (which is the lightweight alternative for smaller cases). See .claude/rules/skill-precedence.md Zone C."
---

# UltraQA — Bounded QA Cycling (Repo-Aligned)

Run a bounded "verify → diagnose → fix → re-verify" loop until the stated quality goal is met or a safety limit is reached.

## Hard Compatibility Rules

- Respect repo anti-loop rules (compilation/test fix retries are bounded).
- Do not assume external state directories.
- Prefer existing project gates/commands; if unknown, use `ac-verify` to define a minimal evidence path.

---

## Step 0: Evidence Mapping Table (MUST — before any cycle runs)

Map each Acceptance Criterion from the `task_brief.md` to a specific test and expected result.
Do NOT start verification until this table is complete.

```markdown
| AC | Test Method | Expected | Actual | Status |
|---|---|---|---|---|
| Given X, when Y, then Z | `testMethodName()` in `FooTest.java` | [expected output] | (fill after run) | ⬜ PENDING |
```

Rules:
- Every AC from the Explorer phase MUST appear as a row.
- "Actual" and "Status" are filled during the cycle, not before.
- If a constraint from the brainstorming Constraint List has no corresponding test → add a row for it or explicitly note it is untestable (and why).
- Completion gate: ALL rows must show ✅ PASS before QA phase closes.

---

## Goal Definition

Supported goal types: `tests` | `build` | `lint` | `typecheck` | `custom`

If the user does not provide a goal type, treat it as `custom` and ask for the exact pass condition.

---

## Cycle (Max 3)

For cycle N:
1. Run the narrowest verification for the goal
2. If PASS: fill "Actual" + mark ✅ PASS in the Evidence Mapping Table
3. If FAIL:
   - Use `root-cause-debug` to identify root cause (no random fixes)
   - Apply the smallest fix
   - Re-run the same verification
   - Fill "Actual" with the failure signal

---

## Exit Conditions

- All Evidence Mapping Table rows show ✅ PASS → success
- Cycle limit reached → stop with best diagnosis + unfilled rows as next action items
- Same failure repeats twice → stop and ask for human guidance (avoid thrashing)

---

## Output Format

1. Evidence Mapping Table (complete, with Actual + Status filled)
2. Cycle-by-cycle results (PASS/FAIL + key failure signal)
3. Fixes applied (files touched)
4. Final evidence summary

---

## Related Skills

- [ac-verify](../ac-verify/SKILL.md): Single-pass verification and evidence reporting
- [root-cause-debug](../root-cause-debug/SKILL.md): Root-cause discipline when verification fails
