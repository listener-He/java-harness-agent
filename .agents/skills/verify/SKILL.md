---
name: verify
description: Verify that a change really works before you claim completion. Use when the user wants confidence that a feature, fix, or refactor actually works.
---

# Verify

## What This Does

Use this skill to turn “it should work” into concrete, observable evidence.

## When to Use

- User asks to verify correctness (e.g., “verify”, “make sure it works”)
- After implementing a feature, bugfix, or refactor
- Before declaring completion or handing off work

## Protocol

1. Identify the exact behavior(s) that must be proven
2. Prefer existing tests and existing gates
3. If coverage is missing, run the narrowest direct verification available
4. If automation is insufficient, provide a minimal manual verification procedure and capture observable evidence
5. Report only what was actually verified

### Verification Order (Preferred)

1. Existing tests
2. Typecheck / build (if applicable)
3. Narrow, direct command checks
4. Manual or interactive verification (last resort)

### Rules

- Do not claim completion without evidence
- If verification fails, include the failure signal and what remains unverified
- If no realistic verification path exists, say so explicitly
- Prefer concise evidence summaries over noisy logs

## Output Format

- What was verified
- Commands/tests executed
- What passed
- What failed or remains unverified

## Related Skills

- [ultraqa](../ultraqa/SKILL.md): Use when you need a bounded “fail → diagnose → fix → re-verify” loop
- [systematic-debugging](../systematic-debugging/SKILL.md): Use when verification fails and you must find root cause before fixing
- [code-review-checklist](../code-review-checklist/SKILL.md): Run before delivery for self-review gates
