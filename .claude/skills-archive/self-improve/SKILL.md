---
name: self-improve
description: “Repo-aligned evolutionary improvement loop with tournament selection. Anchored to eval-harness baseline_score — every iteration must produce a measurable score delta. Plateau detection triggers external-research after 2 consecutive no-gain iterations. Requires explicit approval gates. TRIGGER when user says 'optimize', 'improve', 'iterate until good', or as Phase 4 of the AI engineering pipeline.”
---

# Self-Improve — Eval-Anchored Tournament Improvement

Generate candidate improvement plans, implement one at a time, measure score delta against the eval-harness baseline, keep the best result. Stop when acceptance criteria are met or plateau is detected.

## Hard Compatibility Rules

- Follow `CLAUDE.md` lifecycle and Approval Gate. No silent long-running loops.
- No external state directories, no implicit git worktrees/branches. Keep changes in the current working tree.
- Iteration is bounded:
  - Max 2 compilation/test fix retries per repo rules
  - Max 3 candidate plans per iteration
  - Max 2 consecutive no-gain iterations before mandatory plateau protocol
  - Max 5 total iterations unless the user explicitly approves more

## When to Use

- User asks to “optimize”, “improve”, “iterate until good”, or “run self-improve”
- `eval-harness` has produced a `baseline_score` — this is mandatory, not optional

## Score Tracking (MUST maintain across iterations)

Every iteration MUST update the score ledger:

```
| Iteration | Candidate | Score | Delta vs Baseline | Delta vs Prev | Status |
|---|---|---|---|---|---|
| 0 (baseline) | — | {baseline_score} | 0 | — | BASELINE |
| 1 | Plan A | {score} | {+/-X} | {+/-X} | WINNER/FAIL |
| 2 | Plan B | {score} | {+/-X} | {+/-X} | WINNER/FAIL |
```

**Delta rules:**
- `Delta vs Baseline` = current_score − baseline_score (must be positive to count as improvement)
- `Delta vs Prev` = current_score − previous_best_score
- A score equal to the previous best is NOT an improvement — it is a plateau tick

## Protocol

### Step 0 — Preconditions (HARD FAILURE if not met)

1. **Eval baseline REQUIRED**: Read `<slug>_baseline.json` from `.claude/runs/task-briefs/`. Extract `baseline_score`. If file does not exist → STOP: “Run eval-harness first. No baseline_score to anchor improvement to.”
2. **Frozen benchmark**: The evaluation command and scoring formula MUST NOT change between iterations. Any benchmark change requires a new baseline run and resets the ledger.
3. **Scope boundary confirmed**: Read task_brief Allowed Scope if present. All file targets MUST be within scope.
4. **Acceptance criteria explicit**: Must be a concrete threshold — e.g., “score ≥ 90” or “all AC rows ✅ PASS”. “Looks better” is blocked.

Initialize score ledger with baseline row.

### Step 1 — Produce Candidate Plans (N=2..3)

For each candidate plan:
- One falsifiable hypothesis: “Changing X will improve score by approximately Y because Z”
- Specific file targets (within Allowed Scope)
- Verification command (from eval-harness — frozen, do not modify)
- Expected score after the change (make a prediction before running)
- Rollback: which files to revert if the candidate fails

### Step 2 — Execute One Candidate at a Time

For each candidate, in order:
1. Implement minimal changes for the hypothesis
2. Run the frozen verification command
3. Record actual score
4. Update score ledger (Delta vs Baseline + Delta vs Prev)
5. If compilation fails → fix and re-run. **MAX 2 RETRIES**. If still failing → mark candidate FAIL, do not continue fixing.

### Step 3 — Select Winner

- Winner: highest score that improves on baseline, with lowest risk.
- If multiple candidates improve on baseline: pick highest score.
- If no candidate improves on baseline: this iteration counts as a **plateau tick**.
- If all candidates FAIL (compile error, not score): produce root-cause analysis, do not select a winner, proceed to Step 4.

### Step 4 — Plateau Detection

After each iteration, check:

```
Consecutive no-gain iterations: {count}
Plateau threshold: 2
```

| State | Action |
|---|---|
| score ≥ acceptance threshold | **DONE** — report final results, do not iterate further |
| no-gain count < 2 | Propose one next iteration hypothesis. Ask user to approve. |
| no-gain count = 2 (plateau) | **Plateau Protocol** — see below. Do NOT ask to continue normal iteration. |

### Plateau Protocol (mandatory at no-gain count = 2)

Report to user:
```
[Plateau Detected]
Iterations: {N}
Best score achieved: {score} (baseline: {baseline_score}, delta: {+/-X})
Acceptance threshold: {threshold}
Gap remaining: {threshold - best_score}
Approaches tried: {list of hypothesis families}

Options:
1. Invoke external-research (recommended) — search for new techniques
2. Revise acceptance threshold (if target was too aggressive)
3. Abandon — accept current best as final
```

Wait for human decision. Do NOT silently continue iterating.

If user selects option 1: invoke `external-research` (Mode 1: Pipeline Plateau), passing `approaches_tried`, `current_score`, `target_score`. After external-research returns ideas, restart from Step 1 with the new hypotheses. Plateau counter resets.

### Step 5 — Iteration Approval Gate

If iteration is approved by user to continue (Step 4, no-gain count < 2):
- Apply the winner's changes permanently
- Increment iteration counter
- Return to Step 1 with updated score ledger

**Hard stop at iteration 5** unless user explicitly extends the budget.

## Output Format

End of each iteration — report:

```
=== Iteration {N} Results ===

Score ledger:
{updated ledger table}

Winner: {candidate name or NONE}
Change applied: {yes/no}
Files modified: {list}
Evidence: {verification command output excerpt}

Next: {DONE | Continue — pending approval | Plateau Protocol triggered}
```
