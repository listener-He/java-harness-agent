---
name: "task-decomposition-guide"
description: "MANDATORY MASTER skill for decomposing large PRDs or EPIC scenarios into manageable, verifiable, and parallelizable subtasks. Enforces Agile INVEST criteria and Vertical Slicing for LLM agents."
---

# Task Decomposition & Orchestration Guide

> **Trigger:** Invoke this guide when analyzing a PRD (Product Requirements Document) or breaking down a massive feature/refactoring (`Scenario EPIC`).

This skill transforms a monolithic requirement into an actionable, structured execution plan (`<YYYY-MM-DD>_<slug>_tasks.md`) that multiple Sub-Agents (or developers) can execute without stepping on each other's toes or blowing up the context window.

## 🎯 1. The INVEST Quality Gate (Strict Criteria)
Before finalizing any subtask breakdown, you MUST ensure EVERY generated task satisfies the Agile **INVEST** principles:
- **I (Independent):** Can this task be worked on without waiting for 3 other tasks to finish? Minimize blocking dependencies.
- **N (Negotiable):** Does the task define the *what* and *why*, leaving the *how* (implementation details) up to the executing agent/developer?
- **V (Valuable):** Does completing this task deliver a tangible slice of business value or a verifiable technical outcome?
- **E (Estimable):** Is the scope clear enough to estimate the effort (e.g., Simple ~2h, Medium ~4h, Complex ~8h+)?
- **S (Small):** Is it small enough to fit within a single LLM context window or be completed in a few days? If it feels like an Epic itself, split it again.
- **T (Testable):** Does it have explicit, verifiable Acceptance Criteria (AC)?

## 🔪 2. Decomposition Strategies (Vertical Slicing is King)

**❌ Anti-Pattern (Horizontal Slicing):**
Do NOT split tasks strictly by technical layers (e.g., Task 1: All DB tables, Task 2: All APIs, Task 3: All UI). This creates massive dependencies and delays value delivery.

**✅ Recommended Pattern (Vertical Slicing):**
Split tasks by business capability or user journey through the entire tech stack.
*Example (User Registration):*
- **Task 1:** Basic Email/Password Registration (DB schema + Auth API + basic UI form).
- **Task 2:** Social Login Integration (OAuth API + UI buttons).
- **Task 3:** Password Reset Flow.

### Alternative Strategies (For Technical Tasks):
- **By Phase (Migration):** Task 1: Schema changes, Task 2: Data sync script, Task 3: API cutover.
- **By Workflow (Debugging):** Task 1: Log extraction & analysis, Task 2: Root cause fix, Task 3: Regression test.

## 🤝 3. AI Orchestration & Data Handoff (Preventing Context Bloat)
When breaking down an EPIC for multiple Sub-Agents:
1. **Batch Processing:** Split massive files or datasets into chunks. Assign one chunk per subtask.
2. **Summarization over Raw Data:** Never pass raw logs or entire codebases between tasks. Task N MUST output a compressed summary (e.g., an interface contract) to pass to Task N+1.
3. **Asynchronous Handoff:** Use disk storage for handoffs. Have Task N write its output to `.agents/workflow/runs/intermediate_<task_id>.md`, and instruct Task N+1 to read that file.

## 📋 4. Output Template (`<YYYY-MM-DD>_<slug>_tasks.md`)
Always output a highly readable Markdown report containing an Overview Panel and the Task Breakdown.

**1. 📊 Overview Panel**
- Total Subtasks: X
- Total Estimated Effort: Y hours
- PRD Health/Risk Warning: (Flag vague requirements, missing NFRs, or high-risk third-party integrations here).

**2. 📦 Task Breakdown**
Use the following format for each task:

```markdown
### 📋 Task [ID]: [Task Name]
- **Goal:** [One sentence summary of the business value]
- **Type:** [Vertical Slice | Technical Chore | Migration]
- **Effort:** [Simple (2h) | Medium (4h) | Complex (8h+)]
- **Dependencies:** [List blocking Task IDs or 'None']
- **Acceptance Criteria (Testable):** 
  - [ ] Criteria 1 (e.g., API returns 200 with JWT)
  - [ ] Criteria 2 (e.g., DB record is created with correct tenant_id)
- **Handoff Artifact:** [What file/spec must this task produce for the next step? e.g., `intermediate_auth_spec.md`]
```
