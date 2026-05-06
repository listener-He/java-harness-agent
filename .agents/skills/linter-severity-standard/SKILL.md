---
name: "linter-severity-standard"
description: "Defines a shared FAIL/WARN/IGNORE severity rubric for repo gates to reduce useless retries while keeping hard blockers enforceable."
---

# Linter Severity Standard (FAIL / WARN / IGNORE)

This standard classifies gate checks into three severity levels to avoid repeated retries on minor issues while ensuring hard red lines remain blocking.

## 1) Severity Definitions

- FAIL: Must stop progress. Triggers `fail_hook`. Fix required before proceeding.
- WARN: Allowed to proceed, but must explain rationale and follow-up plan in the delivery (or explicitly accept the risk).
- IGNORE: Record only. Not a gate condition.

## 2) Standard Classification (Fixed Thresholds)

### 2.1 Wiki Graph (wiki_linter)

- FAIL
  - Dead Markdown links
- WARN
  - Orphan files (not referenced by any Markdown, and not index/purpose/root)
  - Oversized file warning (> 500 lines)

### 2.2 Contract Health Check (schema_checker)

- FAIL (Full Spec)
  - Missing critical modules: API contract / data model / acceptance criteria (BDD / AC)
- WARN (Full Spec)
  - Missing JSON examples (unless there is a clear justification: no API / no input / no output)
- FAIL (Slim Spec)
  - Missing required modules: change summary / blast radius / risk & rollback / verification & evidence

## 3) Relationship With Hooks

- The `Doc Consistency Gate` MUST follow script exit codes: any FAIL (non-zero) triggers `fail_hook`.
- WARN does not block, but the agent must output an explanation and next action.
