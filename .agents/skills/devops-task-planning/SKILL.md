---
name: "devops-task-planning"
description: "Handles Task Planning. Invoke in Phase 2 AFTER system design and BEFORE coding to break down the implementation into a Todo list."
---

# Phase 2: Propose (Task Planning)

**Focus**: Divide and Conquer. Preventing monolithic and chaotic code generation.

## 🛡️ GUARDRAILS (边界守卫) - STRICTLY ENFORCED
- **NO FEATURE CODING**: You are prohibited from writing the actual implementation code during this phase. 
- **TOOL REQUIREMENT**: You MUST use the `TodoWrite` tool to output your plan.

## 📋 Steps

1. **Review Architecture**:
   - Read the Markdown Specifications and SQL Schema generated in Phases 1 and 2.
   
2. **Breakdown Strategy**:
   - Deconstruct the feature into the smallest actionable, sequential steps.
   - **Example Sequence for Backend**:
     1. Update database schema / sync documentation.
     2. Create Entity and Mapper XML.
     3. Create Request/Response DTOs.
     4. Write Service Tests (TDD - Failing Tests).
     5. Implement Service Logic.
     6. Write Controller Tests (TDD).
     7. Implement Controller Endpoints.

3. **Execute TodoWrite**:
   - Invoke the `TodoWrite` tool. Set `merge: false` (or `true` if appending) and populate the `todos` array with the detailed breakdown.
   - Assign priorities (`high` for early steps, `medium` for later steps).

## 🎯 Outcomes
- A populated Todo list in the workspace.
- Stop here. Follow the LIFECYCLE.md and proceed to Phase 3: Review.