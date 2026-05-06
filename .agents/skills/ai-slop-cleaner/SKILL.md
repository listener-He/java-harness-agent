---
name: ai-slop-cleaner
description: "Clean AI-generated code slop with a regression-safe, deletion-first workflow and optional reviewer-only mode. Removes dead code, merges duplicates, reduces complexity without changing behavior. TRIGGER when: user says \"deslop\", \"anti-slop\", \"AI slop\", or wants to clean up bloated, repetitive, or over-abstracted code, or as Phase 5 of the AI engineering pipeline (after self-improve completes)."
---

# AI Slop Cleaner

Clean AI-generated code slop without drifting scope or changing intended behavior.

## When to Use

Use this skill when:
- The user explicitly says `deslop`, `anti-slop`, or `AI slop`
- The request is to clean up or refactor code that feels noisy, repetitive, or overly abstract
- Follow-up implementation left duplicate logic, dead code, wrapper layers, boundary leaks, or weak regression coverage
- The user wants a reviewer-only anti-slop pass via `--review`
- The goal is simplification and cleanup, not new feature delivery
- As Phase 5 of the AI engineering pipeline (after self-improve completes evolution)

**Do NOT use** this skill when:
- The task is mainly a new feature build or product change
- The user wants a broad redesign instead of an incremental cleanup pass
- The request is a generic refactor with no simplification or anti-slop intent
- Behavior is too unclear to protect with tests or a concrete verification plan

## Execution Posture

- Preserve behavior unless the user explicitly asks for behavior changes.
- Lock behavior with focused regression tests first whenever practical.
- Write a cleanup plan before editing code.
- Prefer deletion over addition.
- Reuse existing utilities and patterns before introducing new ones.
- Avoid new dependencies unless the user explicitly requests them.
- Keep diffs small, reversible, and smell-focused.
- Stay concise and evidence-dense: inspect, edit, verify, and report.

## Instructions

### Step 1: Protect Current Behavior First

- Identify what must stay the same.
- Add or run the narrowest regression tests needed before editing.
- If tests cannot come first, record the verification plan explicitly before touching code.
- If eval-harness (Phase 3) has already defined evals and benchmarks, use them as the regression test suite.

### Step 2: Write a Cleanup Plan Before Code

- Bound the pass to the requested files or feature area.
- List the concrete smells to remove.
- Order the work from safest deletion to riskier consolidation.

### Step 3: Classify the Slop Before Editing

| Category | Signs |
|---|---|
| **Duplication** | Repeated logic, copy-paste branches, redundant helpers |
| **Dead code** | Unused code, unreachable branches, stale flags, debug leftovers |
| **Needless abstraction** | Pass-through wrappers, speculative indirection, single-use helper layers |
| **Boundary violations** | Hidden coupling, misplaced responsibilities, wrong-layer imports or side effects |
| **Missing tests** | Behavior not locked, weak regression coverage, edge-case gaps |

### Step 4: Run One Smell-Focused Pass at a Time

Execute passes in this order, re-running targeted verification after each:

1. **Pass 1: Dead code deletion** — Remove unused functions, unreachable branches, stale flags
2. **Pass 2: Duplicate removal** — Consolidate repeated logic, merge copy-paste branches
3. **Pass 3: Naming and error-handling cleanup** — Fix inconsistent names, improve error messages
4. **Pass 4: Test reinforcement** — Add missing tests for preserved behavior

Do not bundle unrelated refactors into the same edit set.

### Step 5: Run the Quality Gates

- Keep regression tests green.
- Run the relevant lint, typecheck, and unit/integration tests for the touched area.
- Run existing static or security checks when available.
- If eval-harness benchmarks exist, run them to confirm no regression.
- If a gate fails, fix the issue or back out the risky cleanup instead of forcing it through.

### Step 6: Close with an Evidence-Dense Report

Always report:
- **Changed files**: list of all modified files
- **Simplifications**: what was removed or consolidated
- **Behavior lock / verification run**: which tests were run and their results
- **Remaining risks**: known issues that were not addressed

## Review Mode (`--review`)

`--review` is a reviewer-only pass after cleanup work is drafted. It preserves explicit writer/reviewer separation.

In review mode:
1. Do **not** start by editing files.
2. Review the cleanup plan, changed files, and regression coverage.
3. Check specifically for:
   - Leftover dead code or unused exports
   - Duplicate logic that should have been consolidated
   - Needless wrappers or abstractions that still blur boundaries
   - Missing tests or weak verification for preserved behavior
   - Cleanup that appears to have changed behavior without intent
4. Produce a reviewer verdict with required follow-ups.
5. Hand needed changes back to a separate writer pass instead of fixing and approving in one step.

## Scoped File-List Usage

This skill can be bounded to an explicit file list when the caller already knows the safe cleanup surface.

- Good fit: user specifies exact files to clean
- Preserve the same regression-safe workflow even when the scope is a short file list
- Do not silently expand a changed-file scope into broader cleanup work unless the user explicitly asks for it

## Failure Strategy

| Situation | Action |
|---|---|
| Regression test fails after cleanup | Revert the specific change, log it, continue with next smell |
| Cannot determine if code is dead | Skip — do not delete uncertain code |
| Merge conflict in cleanup | Resolve conservatively, keeping both paths until tests clarify |
| No tests exist to lock behavior | Record verification plan explicitly, ask user before proceeding |
| Cleanup changes behavior unexpectedly | Revert immediately, document what went wrong |

## Pipeline Integration

This skill is Phase 5 of the AI engineering pipeline. It cleans up after self-improve's evolution rounds:

- **From eval-harness (Phase 3)**: use the benchmark suite as regression protection during cleanup
- **From self-improve (Phase 4)**: the code may have accumulated evolution residue (dead code paths, over-abstracted intermediate layers, duplicate boilerplate, inconsistent naming)
- **From architecture-decision-records (Phase 2)**: check ADRs before removing abstractions that may have been deliberately introduced

After ai-slop-cleaner completes, the pipeline delivers **production-grade code**.