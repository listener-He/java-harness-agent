---
name: impl-plan
description: "Decompose a spec or requirements into a checkpoint-driven, bite-sized implementation plan before touching any code. TRIGGER during Propose phase after brainstorming selects a design option and task scope is known. Output saved to .claude/runs/task-briefs/<slug>_plan.md."
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase. Document everything they need to know: which files to touch for each task, code, testing, docs to check, and how to verify. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Save plans to:** `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_plan.md`

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS
````

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD

## Plan Review Loop

After writing the complete plan:

1. Have a reviewer pass validate: scope, dependencies, verification steps, and risk gates.
2. If issues found: fix the plan and re-review (max 3 iterations)
3. If approved: proceed to execution handoff

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 3 iterations, surface to human for guidance
- Reviewers are advisory — explain disagreements if you believe feedback is incorrect

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_plan.md`. Two execution options:**

**1. Agent-driven (Recommended)** - Dispatch one agent per task with checkpoints and tight scope boundaries

**2. Inline Execution** - Execute tasks in this session with checkpoints (see checklist below)

**Which approach?"**

**If Agent-driven chosen:**
- Use `dispatching-parallel-agents` to split independent tasks
- Keep a strict scope boundary per task

**If Inline Execution chosen:**
- Follow the Inline Execution Checklist below

## Inline Execution Checklist (Merged from `executing-plans`)

When executing a written plan in this session:

1. Load the plan file and review it critically (identify gaps or risky steps)
2. If critical concerns exist: stop and raise them before starting execution
3. Execute tasks in order:
   - Mark the task in-progress
   - Follow the plan’s verification steps for that task
   - Mark completed only after verification evidence exists
4. Stop immediately when:
   - A blocker appears (missing dependency, failing verification, unclear instruction)
   - The same failure repeats (avoid thrashing; switch to `root-cause-debug`)
5. Completion protocol:
   - Run `code-review-checklist`
   - Run `ac-verify` to produce an evidence summary
   - Enter Archive phase and write WAL if required

## Related Skills

- **verify** - Evidence before completion
- **root-cause-debug** - Root-cause discipline when execution fails
