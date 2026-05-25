---
name: "task-decomposition-guide"
description: "Decomposes PRDs / EPICs into INVEST subtasks via Vertical Slicing. TRIGGER: Explorer/Propose with EPIC/PRD or multi-task scope. NOT FOR: single-task spec (use impl-plan); design (use brainstorming)."
---

# Task Decomposition & Orchestration Guide

> **Trigger:** Invoke this guide when analyzing a PRD (Product Requirements Document) or breaking down a massive feature/refactoring (`Scenario EPIC`).

This skill transforms a monolithic requirement into an actionable, structured execution plan (`<YYYY-MM-DD>_<slug>_tasks.md`) that multiple Sub-Agents (or developers) can execute without stepping on each other's toes or blowing up the context window.

---

## 🔍 0. Pre-Decomposition: Scope Validation

**Before splitting anything:**

### 0a. PRD Input — Run product-manager-expert first
If the input is a PRD (multi-requirement document), do NOT decompose directly.
1. Run `product-manager-expert` Mode A (PRD Ingestion) to extract + validate requirement units.
2. Use the validated, conflict-free requirement list as input to this skill.
3. Reason: decomposing an unvalidated PRD embeds hidden conflicts into the task graph.

### 0b. EPIC Scenario — Run adversarial check first
If the input is a single large feature (EPIC), run `adversarial-review` Category C with the **EPIC frame**:
> "Assume the task decomposition has a hidden sequential dependency that makes parallel execution impossible. Which two tasks, and what shared state forces the ordering?"

- CRITICAL finding → resolve the dependency structure before finalizing the task graph.
- MINOR finding → annotate affected tasks with `[Dep-Risk]` in the output.
- One round only.

### 0c. Complexity Estimation via Code Impact
If `code_index.json` is built, run `code_index.py --impact-of <target_file>` for the primary change file.
Use the impact count to calibrate effort estimates:
- impact ≤ 5 files → Simple (2h)
- impact 6–15 files → Medium (4h)
- impact > 15 files → Complex (8h+) — consider further vertical slicing.

---

## 🎯 1. The INVEST Quality Gate (Strict Criteria)
Before finalizing any subtask breakdown, you MUST ensure EVERY generated task satisfies the Agile **INVEST** principles:
- **I (Independent):** Can this task be worked on without waiting for 3 other tasks to finish? Minimize blocking dependencies.
- **N (Negotiable):** Does the task define the *what* and *why*, leaving the *how* (implementation details) up to the executing agent/developer?
- **V (Valuable):** Does completing this task deliver a tangible slice of business value or a verifiable technical outcome?
- **E (Estimable):** Is the scope clear enough to estimate the effort (e.g., Simple ~2h, Medium ~4h, Complex ~8h+)?
- **S (Small):** Is it small enough to fit within a single LLM context window or be completed in a few days? If it feels like an Epic itself, split it again.
- **T (Testable):** Does it have explicit, verifiable Acceptance Criteria (AC)?

## 🧭 1.5 Subtask Type Classification (run before Vertical Slicing)

Every generated subtask MUST carry `Type ∈ {Change, Research}`. This drives the downstream entry command, risk column, and DAG dependency rule.

### Classification rules (first match wins)

| Signal | Type |
|---|---|
| User text contains "先调研再实现" / "先评估再决定" / "先看看再…" two-stage structure | Split into 2 subtasks: Research first, Change second, Change `Depends On` Research |
| Subtask goal verb in research set (analyze / research / evaluate / assess / feasibility / 调研 / 分析 / 评估 / 可行性) AND no Change verb | Research |
| Subtask has measurable code/file outcome (endpoint / DB column / class) | Change |
| Subtask has only "want to know X" / "compare A vs B" outcome | Research |
| Default | Change |

### Per-Type schema (extends INVEST output)

| Field | Change | Research |
|---|---|---|
| Effort | Simple / Medium / Complex | quick / deep (drives §3 quota) |
| Acceptance Criteria | Given/When/Then ACs | report §1 Question + §3 quota |
| Artifact | task_brief.md | research_report.md |
| Risk literal | LOW / MEDIUM / HIGH | RES |

### DAG rule: Research → Change ordering

When a Research subtask R produces §5 Recommendations with `If chosen, run: ...` next-step options, downstream Change subtask C MUST list R in its `Depends On`. C's task_brief §1 Context inherits R's §5.chosen option verbatim when work resumes.

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
3. **Asynchronous Handoff:** Use disk storage for handoffs. Have Task N write its output to `.claude/runs/task-briefs/intermediate_<task_id>.md`, and instruct Task N+1 to read that file.

## 📋 4. Output Template (`<YYYY-MM-DD>_<slug>_tasks.md`)
Always output a highly readable Markdown report containing an Overview Panel and the Task Breakdown.

**1. 📊 Overview Panel**
- Total Subtasks: X
- Total Estimated Effort: Y hours
- PRD Health/Risk Warning: (Flag vague requirements, missing NFRs, or high-risk third-party integrations here).

**2. 📦 Task Breakdown**
Per-subtask format (all fields MUST be present; Type drives the rest):

```markdown
### 📋 Task [ID]: [Task Name]
- **Goal:** [One sentence — business value or research question]
- **Type:** Change | Research
- **Subtype:** [Change: Vertical Slice | Technical Chore | Migration] | [Research: quick | deep]
- **Effort:** [Change: Simple (2h) | Medium (4h) | Complex (8h+)] | [Research: quick | deep]
- **Dependencies:** [blocking Task IDs or 'None']
- **Acceptance Criteria (Testable):**
  - [ ] [Change: Given/When/Then AC] | [Research: §1 Question answerable with §3 ≥ <quota> findings]
- **Handoff Artifact:** [Change: task_brief.md or intermediate spec] | [Research: research_report.md]
```
