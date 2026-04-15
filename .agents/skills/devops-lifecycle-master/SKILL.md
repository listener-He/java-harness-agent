---
name: "devops-lifecycle-master"
description: "MANDATORY MASTER orchestration skill for DevOps Lifecycle. Invoke IMMEDIATELY when starting any task from requirements to review (PDD, FDD, SDD, TDD)."
---

# DevOps Lifecycle Master (PDD, FDD, SDD, TDD)

**CRITICAL: You MUST read and follow this guide before starting any new feature, design, modification, or bug fix in this repository.**

This project employs a harness full-process DevOps automation methodology. We adopt a strict **3-Layer Architecture** (Project Level -> Feature Level -> General Level) with embedded **Guardrails (边界守卫)** to prevent hallucinations and premature coding.

## 🛡️ Core Mechanism: Guardrails (边界守卫)
- **STRICT ISOLATION**: Do NOT write code during Phase 1 (Requirements) and Phase 2 (Design). Code generation is ONLY allowed in Phase 4 (Implementation) and Bug Fix.
- **CONTEXT INJECTION**: Do NOT rely on LLM memory. You MUST invoke `Skill` to load relevant business domain rules BEFORE making design decisions.

---

## 🧭 Layer 1: Feature Development (功能级循环)
For developing a new feature or complex module, you MUST execute these phases sequentially through the Intent Gateway:

### Phase 0: Intent Gateway & Context Funnel (意图分发与检索)
- **Task**: Understand user intent, drill-down through the `KNOWLEDGE_GRAPH.md`, and orchestrate the multi-flow launch plan.
- **Skill to Invoke**: `intent-gateway`
- **Guardrail**: Strictly NO CODING. Only output the `launch_spec.md` plan.

### Phase 1: Requirements & Business Alignment (Explorer)
- **Task**: Clarify requirements, define prototypes, and load business rules based on the gateway's context.
- **Skill to Invoke**: `devops-requirements-analysis`
- **Guardrail**: Strictly NO CODING. Only output Markdown specifications (`explore_report.md`).

### Phase 2: Tech Design & Architecture (Propose)
- **Task**: Output the standardized `openspec.md` covering API, Data, Architecture.
- **Skill to Invoke**: `devops-system-design`
- **Guardrail**: Only output Markdown and SQL `CREATE TABLE` scripts. Must follow `openspec_schema.md`.

### Phase 3: Technical Review (Review)
- **Task**: Check the proposed `openspec.md` against standards, boundaries, and preferences.
- **Skill to Invoke**: `devops-review-and-refactor`
- **Guardrail**: Must pass all checks before implementation. Failures loop back to Propose.

### Phase 4: Task Planning (任务规划)
- **Task**: Break down the design into actionable steps using the `TodoWrite` tool.
- **Skill to Invoke**: `devops-task-planning`
- **Guardrail**: Prevent monolithic code generation. Divide and conquer.

### Phase 5: Implementation & QA (Implement & Test)
- **Task**: Execute the Todo list. Write tests first, then write robust code.
- **Skills to Invoke**: `devops-testing-standard` & `devops-feature-implementation`
- **Guardrail**: Code must strictly match `openspec.md`. Test failures loop back to Implement.

### Phase 6: Knowledge Archiving & Evaluation (Archive)
- **Task**: Extract knowledge to `llm_wiki`, move spec to `archive`, collect user evaluation (1-10) and update `preferences/index.md`.
- **Action**: Follow the `Archive` hook protocols in `workflow/HOOKS.md`.

---

## 🧭 Layer 2: General & Maintenance (通用运维级)
For anytime tasks (fixing bugs, reviewing code, or micro-changes):

### Option A: Dedicated Bug Fix
- **Task**: Diagnose, write tests to reproduce, fix, and verify.
- **Skill to Invoke**: `devops-bug-fix`

### Option B: Code Review & Refactoring
- **Task**: Modify existing features safely, check against baseline standards.
- **Skill to Invoke**: `devops-review-and-refactor`

### Option C: 🚀 Fast Track (Hotfix Mode)
- **Condition**: Only for trivial tasks (e.g., typo fix, single line change).
- **Action**: You MAY skip Layer 1 phases and jump directly to Implementation or Review.