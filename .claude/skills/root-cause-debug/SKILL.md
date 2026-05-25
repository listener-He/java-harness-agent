---
name: root-cause-debug
description: "Investigates root cause before any fix via Hierarchical Localization. TRIGGER: bug / test failure / runtime exception. NOT FOR: build failures (use java-build-resolver); fixes before Phase 1."
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## Quick Triage (Merged from `debug`)

When the user is confused about “what is failing”, do a quick evidence-first triage before deep investigation:

1. Identify the exact failure signal (error line, stack trace, failing assertion, unexpected output)
2. Collect the narrowest local evidence (logs, failing command output, minimal reproduction steps)
3. State what is known vs unknown (separate symptoms from hypotheses)
4. Choose the smallest next probe that can confirm/deny one hypothesis

## Hierarchical Localization Protocol (MUST run before Phase 1)

Before reading ANY file, localize to the smallest scope:

```
Level 1 — Module: Which package/module boundary is implicated?
  Signal: error package, import chain, module name in stack trace
  → Narrow to 1–2 candidate packages before reading files.

Level 2 — File: Which specific class/file?
  Use: code_index.py --who-calls <method> or --symbol <ClassName>
  → Narrow to ≤3 candidate files.

Level 3 — Method: Which method/function?
  Read ONLY the candidate files. Find the method boundary.
  → Narrow to 1 method before reading its body.

Level 4 — Line: Exact location.
  Read the method body. Identify the exact line.
```

**Stop rule:** Do not descend to the next level until the current level is resolved.
**Budget rule:** Each level costs ≤2 code budget units. Total: ≤8 (within standard budget).

---

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   **WHEN system has multiple components (CI → build → signing, API → service → database):**

   **BEFORE proposing fixes, add diagnostic instrumentation:**
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   **Example (multi-layer system):** log presence/shape of data without printing secret values.

   **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)

5. **Trace Data Flow**

   **WHEN error is deep in call stack:**

   **Quick version:**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code in same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing pattern, read reference implementation COMPLETELY
   - Don't skim - read every line
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?
   - What assumptions does it make?

### Phase 3: Hypothesis Falsification (MUST — before any fix)

**Falsify before fixing.** A hypothesis that cannot be falsified is not a root cause — it is a guess.

**Protocol:**

1. **State the Hypothesis**
   Exact form: `"Root cause is [X] because [Y]."`
   Bad: "I think the null check is missing."
   Good: "Root cause is that `OrderService.createOrder()` does not validate `userId` before calling `userRepository.findById()`, causing NPE when `userId` is null."

2. **Derive a Falsifiable Prediction**
   `"If the hypothesis is true, then [observable condition Z] should hold."`
   Example: "If true, then removing the `userId != null` guard should make the test fail at line 127."

3. **Test the Prediction (without fixing)**
   Run the failing test in current state. Confirm the prediction is observable.
   If the prediction does NOT hold → the hypothesis is WRONG. Return to Phase 1.

4. **Only THEN: fix the root cause**
   The fix must target the exact cause stated in the hypothesis. No bundled changes.

5. **Counterfactual Verification (MUST after fix)**
   - Step A: Run the originally failing test → MUST pass.
   - Step B: Revert ONLY the fix → the test MUST fail again.
   - If Step B doesn't fail: the fix is not the actual cause. Investigate further.
   This two-step confirms causality, not just correlation.

**When hypothesis fails twice with different root causes:** STOP. The contract or architecture may be wrong. Roll back to Propose phase.

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - Automated test if possible
   - One-off test script if no framework
   - MUST have before fixing
   - Use the `test-driven-development` skill for writing proper failing tests

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?

## Dedicated Bug-Fix Framing (Merged from `devops-bug-fix`)

When the user request is explicitly “fix the bug” (not feature work), keep the flow narrow:

1. Diagnose & isolate (root cause hypothesis with evidence)
2. Reproduce with a failing test when possible (or a precise manual repro)
3. Implement the smallest fix that addresses the root cause
4. Verify with the reproduction + a small regression set
5. Run `code-review-checklist` before delivery

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 2: Return to Phase 1, re-analyze with new information
   - **If ≥ 2: STOP and question the architecture (step 5 below)**
   - Don't stack retries without new evidence

5. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new shared state/coupling/problem in different place
   - Fixes require "massive refactoring" to implement
   - Each fix creates new symptoms elsewhere

   **STOP and question fundamentals:**
   - Is this pattern fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we refactor architecture vs. continue fixing symptoms?

   **Discuss with your human partner before attempting more fixes**

   This is NOT a failed hypothesis - this is a wrong architecture.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 1+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 2+ fixes failed:** Question the architecture (see Phase 4.5)

## your human partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 1+ failures) | 2+ failures = architectural problem. Question pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Related Skills

- **test-driven-development** - Create a failing reproduction before fixing
- **verify** - Produce evidence before claiming completion
- **decision-frameworks** - When root cause points to a structural/architectural choice
- **code-review-checklist** - Final self-review before delivery

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common
