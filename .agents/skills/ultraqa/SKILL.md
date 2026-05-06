---
name: ultraqa
description: QA cycling workflow - test, verify, fix, repeat until goal met
---

# ultraqa

# UltraQA — Bounded QA Cycling (Repo-Aligned)

Run a bounded “verify → diagnose → fix → re-verify” loop until the stated quality goal is met or a safety limit is reached.

## Hard Compatibility Rules

- Respect repo anti-loop rules (compilation/test fix retries are bounded).
- Do not assume external state directories.
- Prefer existing project gates/commands; if unknown, use `verify` to define a minimal evidence path.

## Goal Definition

Supported goal types:
- tests
- build
- lint
- typecheck
- custom (explicit success criteria)

If the user does not provide a goal type, treat it as `custom` and ask for the exact pass condition.

## Cycle (Max 3)

For cycle N:
1. Run the narrowest verification for the goal
2. If PASS: stop and report evidence
3. If FAIL:
   - Use `systematic-debugging` to identify root cause (no random fixes)
   - Apply the smallest fix
   - Re-run the same verification

## Exit Conditions

- Goal met → success report with evidence
- Cycle limit reached → stop with best diagnosis + next recommended action
- Same failure repeats twice → stop and ask for human guidance (avoid thrashing)

## Output Format

- Goal and verification command(s)
- Cycle-by-cycle results (PASS/FAIL + key failure signal)
- Fixes applied (files touched)
- Final evidence summary

## Related Skills

- [verify](../verify/SKILL.md): Single-pass verification and evidence reporting
- [systematic-debugging](../systematic-debugging/SKILL.md): Root-cause discipline when verification fails
