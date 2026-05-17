---
name: eval-harness
description: "Formal evaluation framework with two operating modes: (A) Early-phase AC Definition — usable at Explorer phase to translate requirements into executable pass/fail criteria before any code is written; (B) Pipeline Evaluation — Phase 3 of the AI engineering pipeline (after blueprint and ADR, before self-improve) to set up benchmarks and measure reliability with pass@k metrics. TRIGGER for either mode: when requirements need to be translated to testable assertions, or when setting up evaluation benchmarks."
---

# Eval Harness Skill

A formal evaluation framework with two modes: early-phase AC definition (Explorer) and pipeline benchmark evaluation (ai-pipeline Phase 3).

## When to Activate

**Mode A — Early-phase AC Definition (Explorer phase):**
- Requirements have been captured but Acceptance Criteria are not yet in `Given/When/Then` executable form
- Use this mode as part of Explorer's AC-as-Tests Translation step (LIFECYCLE.md Step 6)
- Output: structured AC table that can seed both the task_brief and the pipeline eval definitions

**Mode B — Pipeline Evaluation (ai-pipeline Phase 3):**
- Setting up eval-driven development (EDD) for AI-assisted workflows
- Defining pass/fail criteria for task completion
- Measuring agent reliability with pass@k metrics
- Creating regression test suites for prompt or agent changes
- Benchmarking performance across model versions
- As Phase 3 of the AI engineering pipeline (after blueprint and ADR, before self-improve)

## Philosophy

Eval-Driven Development treats evals as the "unit tests of AI development":
- Define expected behavior BEFORE implementation
- Run evals continuously during development
- Track regressions with each change
- Use pass@k metrics for reliability measurement

## Mode A: Early-phase AC Definition

Use at Explorer phase when requirements are captured but ACs are not yet executable.

### Step A1: Extract requirement units from context

For each requirement in scope, extract the behavior being promised.

### Step A2: Translate to AC table

```markdown
| # | Requirement | Given | When | Then | Grader Type | Pass Threshold |
|---|---|---|---|---|---|---|
| AC-001 | User can register | no account exists for email | POST /auth/register | HTTP 201 + account row in DB | code (HTTP status + DB query) | pass@1 |
| AC-002 | Duplicate email rejected | account exists for email | POST /auth/register | HTTP 409 + error code REG_001 | code (HTTP status + body.code) | pass^3 |
```

**Vague language blocklist** — any AC containing these words MUST be rewritten before proceeding:
`correct`, `properly`, `appropriately`, `handle`, `reasonable`, `good`, `work`

### Step A3: Output

Write the AC table to `task_brief.md` under `## Acceptance Criteria`. Also write to eval_harness artifact if the pipeline will run:
```
<YYYY-MM-DD>_<slug>_eval_harness.md  ← AC table + grader types seeded
```

The Mode B steps below then fill in benchmark scripts against these ACs.

---

## Mode B: Pipeline Evaluation

### Step 1: Define Evals (Before Coding)

Create an eval definition artifact under `.claude/runs/task-briefs/` (e.g., `<YYYY-MM-DD>_<slug>_eval_harness.md`):

```markdown
## EVAL DEFINITION: feature-xyz

### Capability Evals
1. Can create new user account
2. Can validate email format
3. Can hash password securely

### Regression Evals
1. Existing login still works
2. Session management unchanged
3. Logout flow intact

### Success Metrics
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
```

### Step 2: Choose Grader Types

#### Code-Based Grader (preferred)
Deterministic checks using code:
```bash
grep -q "export function handleAuth" src/auth.ts && echo "PASS" || echo "FAIL"
npm test -- --testPathPattern="auth" && echo "PASS" || echo "FAIL"
npm run build && echo "PASS" || echo "FAIL"
```

#### Model-Based Grader
Use an LLM to evaluate open-ended outputs:
```markdown
[MODEL GRADER PROMPT]
Evaluate the following code change:
1. Does it solve the stated problem?
2. Is it well-structured?
3. Are edge cases handled?
4. Is error handling appropriate?

Score: 1-5 (1=poor, 5=excellent)
Reasoning: [explanation]
```

#### Human Grader
Flag for manual review:
```markdown
[HUMAN REVIEW REQUIRED]
Change: Description of what changed
Reason: Why human review is needed
Risk Level: LOW/MEDIUM/HIGH
```

### Step 3: Implement Benchmark Script

Create a benchmark script that outputs a score:

**Requirements:**
- **JSON output preferred**: Last line of stdout as `{"primary": 85.2, "sub_scores": {"dim_a": 0.92}}`
- **Deterministic**: Same code → same score (fixed seeds)
- **Fast**: Under 5 minutes ideally
- **Self-contained**: No external services
- **Honest**: Measures actual quality

Place the benchmark script in the target repo (e.g., `scripts/benchmark.py` or `benchmark.py`).
Must exit 0 on success, non-zero on error. Print score as last stdout line.

### Step 4: Validate Benchmark

Run the benchmark 3 times:
```
Run 1: {x}
Run 2: {y}
Run 3: {z}
Variance: {(max-min)/mean * 100}%
```
All 3 must complete. Variance must be < 5%.

### Step 5: Record Baseline

Save baseline as a run artifact under `.claude/runs/task-briefs/` (e.g., `<YYYY-MM-DD>_<slug>_baseline.json`):
```json
{ "baseline_score": 80.0, "recorded_at": "2026-05-02T12:00:00Z" }
```

### Step 6: Generate Report

```markdown
EVAL REPORT: feature-xyz
========================

Capability Evals:
  create-user:     PASS (pass@1)
  validate-email:  PASS (pass@2)
  hash-password:   PASS (pass@1)
  Overall:         3/3 passed

Regression Evals:
  login-flow:      PASS
  session-mgmt:    PASS
  logout-flow:     PASS
  Overall:         3/3 passed

Metrics:
  pass@1: 67% (2/3)
  pass@3: 100% (3/3)

Status: READY FOR REVIEW
```

## Eval Types

### Capability Evals
Test if the system can do something it couldn't before:
```markdown
[CAPABILITY EVAL: feature-name]
Task: Description of what should be accomplished
Success Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
  - [ ] Criterion 3
Expected Output: Description of expected result
```

### Regression Evals
Ensure changes don't break existing functionality:
```markdown
[REGRESSION EVAL: feature-name]
Baseline: SHA or checkpoint name
Tests:
  - existing-test-1: PASS/FAIL
  - existing-test-2: PASS/FAIL
  - existing-test-3: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

## Metrics

### pass@k
"At least one success in k attempts"
- pass@1: First attempt success rate
- pass@3: Success within 3 attempts
- Typical target: pass@3 > 90%

### pass^k
"All k trials succeed"
- Higher bar for reliability
- pass^3: 3 consecutive successes
- Use for critical paths

Recommended thresholds:
- Capability evals: pass@3 >= 0.90
- Regression evals: pass^3 = 1.00 for release-critical paths

## Eval Storage

Store eval artifacts in project:
```
.claude/
  workflow/
    runs/
      <YYYY-MM-DD>_<slug>_eval_harness.md   # Eval definition
      <YYYY-MM-DD>_<slug>_eval_run.log      # Optional eval run history
      <YYYY-MM-DD>_<slug>_baseline.json     # Optional baselines
```

## Eval Anti-Patterns

- Overfitting prompts to known eval examples
- Measuring only happy-path outputs
- Ignoring cost and latency drift while chasing pass rates
- Allowing flaky graders in release gates

## Pipeline Integration

This skill is Phase 3 of the AI engineering pipeline. It is the **prerequisite** for self-improve — without quantifiable evaluation, the tournament selection mechanism cannot judge which approach is better.

**Relationship with self-improve**: eval-harness is the "referee", self-improve is the "competition". If the referee is unfair or unclear, the competition is meaningless.

After completing eval-harness:
- **Phase 4**: Invoke the `self-improve` skill — it will use your eval definitions and benchmark commands
- The benchmark command and format you define here feed directly into self-improve's `settings.json`

## Best Practices

1. **Define evals BEFORE coding** - Forces clear thinking about success criteria
2. **Run evals frequently** - Catch regressions early
3. **Track pass@k over time** - Monitor reliability trends
4. **Use code graders when possible** - Deterministic > probabilistic
5. **Human review for security** - Never fully automate security checks
6. **Keep evals fast** - Slow evals don't get run
7. **Version evals with code** - Evals are first-class artifacts
