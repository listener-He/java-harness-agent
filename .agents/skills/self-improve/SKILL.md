---
name: self-improve
description: "Repo-aligned evolutionary improvement loop with tournament selection. Generates multiple candidate plans, implements and verifies them, then keeps the best result. Requires explicit approval gates for iteration."
---

# Self-Improve — Tournament-Style Improvement (Repo-Aligned)

Generate multiple candidate improvement plans, implement them one at a time, verify against eval criteria, and keep the best result.

## Hard Compatibility Rules

- Follow `AGENTS.md` lifecycle and Approval Gate. No silent long-running loops.
- No external state directories, no implicit git worktrees/branches. Keep changes in the current working tree.
- Iteration is bounded:
  - Max 2 compilation/test fix retries per repo rules
  - Max 3 candidate plans per iteration
  - Max 2 iterations unless the user explicitly approves more

## When to Use

- User asks to “optimize”, “improve”, “iterate until good”, or “run self-improve”
- `eval-harness` has defined objective evidence (commands + pass/fail criteria)

## Protocol

### Step 0 — Preconditions

- Confirm objective, scope boundary, and acceptance criteria exist (prefer `eval-harness` output).
- Confirm the files allowed to change.

### Step 1 — Produce Candidate Plans (N=2..3)

For each plan:
- One testable hypothesis
- Specific file targets
- Verification commands (reusing eval-harness)
- Expected risk level and rollback (what to revert if it fails)

### Step 2 — Execute One Plan at a Time

For each candidate, in order:
- Implement minimal changes for the hypothesis
- Run verification commands
- Record outcome as PASS/FAIL with evidence

### Step 3 — Select Winner

- Winner is the plan that best satisfies acceptance criteria with lowest risk.
- If all candidates fail, produce a concise root-cause analysis and propose a re-plan (do not keep stacking fixes).

### Step 4 — Iteration Gate

If acceptance criteria not met:
- Propose exactly one next iteration (new hypothesis or re-plan)
- Ask the user to approve continuing (no infinite loops)

## Output Format

- Baseline evidence (if available)
- Candidate list (hypothesis + files + verification)
- Result table (candidate → PASS/FAIL → evidence)
- Winner summary (what changed and why)
