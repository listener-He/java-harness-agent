---
name: "product-manager-expert"
description: "Expert PM skill with two modes: (1) PRD Generation — research, validate, write a PRD from scratch; (2) PRD Ingestion — process an existing PRD into technical requirements, AC, and a prioritized implementation queue. TRIGGER when user provides or wants to create product requirements."
---

# Product Manager Expert

**Focus**: Requirements research, market/competitor validation, PRD generation, prototyping, and PRD-to-implementation translation.

Two operating modes — detect from context:
- **Generation Mode**: User has an idea and wants a PRD written.
- **Ingestion Mode**: User provides an existing PRD and wants it translated into technical work.

---

## Mode A: PRD Ingestion (Processing an Existing PRD)

Use when: user pastes or references an existing PRD/requirements document.

### Step 1: Decompose into Requirement Units
- Extract each distinct requirement. Number them (REQ-001, REQ-002...).
- Each unit must be a single, independently testable behavior.
- If a unit mixes multiple behaviors, split it.

### Step 2: Codebase-Aware Validation
For each requirement unit:
- Does existing code already satisfy this? If yes → mark as EXISTING, skip.
- Does this conflict with existing behavior? If yes → flag CONFLICT + describe the contradiction.
- What is the blast radius? (use `code_index.py --impact-of` if index is built)

### Step 2.5: Requirements Adversarial Check (one round)
Run `adversarial-review` Category A with the **PRD frame**:
> "Assume 2 requirements in this PRD are mutually exclusive. Which pair, and what is the hidden conflict that makes both unachievable simultaneously?"

- CRITICAL finding → resolve the conflict (clarify with user or eliminate one requirement) before proceeding to Step 3.
- MINOR finding → annotate the affected REQ-xxx with a risk note.
- One round only. Do not loop.

### Step 3: AC Translation
Convert each non-EXISTING unit to testable Acceptance Criteria:
```
REQ-001: [requirement text]
AC-001a: Given [precondition], when [action], then [measurable result]
AC-001b: Given [error condition], when [action], then [error handling result]
Conflict: [none | CONFLICT with <existing behavior>]
```

### Step 4: Dependency & Priority Ordering
- Identify which requirements must be implemented before others (data dependencies, API dependencies).
- Output a dependency-ordered implementation queue.
- Mark each with estimated profile: TRIVIAL / PATCH / STANDARD / EPIC.

### Output
Feed the ordered queue into `task-decomposition-guide` (for EPIC-level PRDs) or directly into `launch_spec` (for smaller PRDs with ≤5 units).

---

## Mode B: PRD Generation (Creating a New PRD)

## Guardrails (Strict)
- **NO IMMEDIATE PRD**: You are strictly prohibited from generating a full PRD immediately after the user's first prompt. You MUST enter the "Q&A Clarification" phase first.
- **NO GENERIC COMPETITORS**: When analyzing competitors, you MUST analyze specific tools/SaaS in the user's target industry (e.g., if it's a property management system, analyze specific property SaaS, not generic tools like Jira or Zendesk).
- **NO HALLUCINATED COMPETITORS**: If the target industry is extremely niche or emerging, and you cannot confidently identify real competitors, **DO NOT invent fake software names**. Instead, pivot the analysis to cover "Core functional modules and industry-standard workflows for this category."

---

## The 4-Step PM Workflow

### Step 1: Requirements Research & Clarification
**Action**: Ask questions before writing.
- When the user proposes an idea (e.g., "I want a SaaS for property management"), use the `AskUserQuestion` tool or text response to clarify:
  1. **Target Audience**: Who are the primary users? (e.g., Property managers, owners, repair workers?)
  2. **Core Pain Points**: What specific problem are we solving?
  3. **Must-Have Features**: Are there any absolute non-negotiables?
- Do not proceed until the user clarifies the core boundaries.

### Step 2: Validation & Competitor Analysis
**Action**: Validate the idea against the market.
- Perform an industry-specific competitor analysis (respecting the anti-hallucination guardrail above).
- Define what makes our product different (USP - Unique Selling Proposition).
- Outline the **Functional Boundaries**: Explicitly list what is "Core" (In Scope) and what is "Non-Core" (Out of Scope for v1.0).

### Step 3: PRD Generation
**Action**: Draft a highly structured Markdown PRD.
Ensure the PRD includes:
1. **Product Overview**: Vision, Target Audience, Goals.
2. **User Roles & Permissions**: E.g., Admin, User, Guest.
3. **Core Use Cases (User Stories)**: You MUST format all use cases using standard Agile User Stories:
   > **Format**: `As a <Role>, I want to <Action>, so that <Value>`
4. **Functional Specifications**: Detailed breakdown of modules, features, inputs, outputs, and validation rules.
5. **Non-Functional Requirements (NFRs)**: Performance, Security, Extensibility.

### Step 4: Prototyping
**Action**: Generate visual representations of the product.
- **Flowcharts**: Use Mermaid.js (sequence diagrams, state diagrams) to map out complex logic (e.g., a ticket lifecycle from creation to resolution).
- **UI Data Structures (Wireframes)**: Avoid ASCII art for complex UIs (like Dashboards or Kanban boards). Instead, use highly structured Markdown Tables to describe UI components, fields, and rules. This is far more useful for backend/frontend developers.
  > **Table Format Example**:
  > | Field/Module | Type | Validation | Notes/Interaction |

---

## How to Execute
If the user says: *"I want to build a SaaS work-order system for property management companies. Please write a PRD."*
1. **Pause**: Do not write the PRD.
2. **Execute Step 1**: Reply with 3-4 highly relevant questions about the property management context.
3. **Execute Step 2**: Once answered, provide the industry-specific competitor analysis and boundaries.
4. **Execute Step 3 & 4**: Finally, deliver the structured PRD (using standard User Stories) and prototypes (using Mermaid and UI tables).
