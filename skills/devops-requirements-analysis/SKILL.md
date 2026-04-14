---
name: "devops-requirements-analysis"
description: "Handles PDD & SDD phase. Invoke when analyzing raw requirements, clarifying business boundaries, and outputting Markdown specifications."
---

# DevOps Phase 1: Requirements & Design (PDD & SDD)

**Focus**: Prototype-Driven Development (PDD), Specification-Driven Development (SDD), and Business Injection.

## 🛡️ GUARDRAILS (边界守卫) - STRICTLY ENFORCED
- **NO CODING ALLOWED**: You are strictly prohibited from generating any Java, XML, or configuration code during this phase. 
- **FOCUS**: Your only job right now is to clarify what needs to be built and output Markdown documentation.

## 📋 Steps

1. **Business Context Injection (CRITICAL)**:
   - Identify the business domain of the request.
   - You MUST explicitly invoke the corresponding business skill using the `Skill` tool to load the specific rules BEFORE proceeding.

2. **Understand & Clarify**:
   - Parse user requests or raw requirement docs.
   - Ask clarifying questions using `AskUserQuestion` if rules or boundaries are ambiguous.

3. **Prototype-Driven Development (PDD)**:
   - **Backend Prototype**: Draft the API Request/Response JSON structure that the frontend will consume.
   - **Flow Prototype**: Provide Mermaid flowcharts (sequence/activity diagrams) to visualize the interaction and user flow.

4. **Specification-Driven Development (SDD)**:
   - Generate a detailed Markdown Specification containing:
     - **Business Boundaries**: Clearly define what this module does and does *not* do. Avoid monolithic designs.
     - **Use Cases**: Describe happy paths and edge cases.
     - **Validation Rules**: Define all required fields, max lengths, regex, and unique constraints.
     - **Permissions**: Specify which user type (`@GovernanceUser`, etc.) and permission string is required.

5. **Non-Functional Requirements (NFRs)**:
   - **Performance Expectations**: Clearly define expected QPS and data volume magnitude.
   - **Strict Constraints**: State that looping over external APIs (RPC/Feign) and database CRUD operations is strictly prohibited.

## 🎯 Outcomes
- A complete Markdown Specification (including prototypes and NFRs).
- Stop here. Do not write code. Prompt the user to proceed to Phase 2: `devops-system-design`.