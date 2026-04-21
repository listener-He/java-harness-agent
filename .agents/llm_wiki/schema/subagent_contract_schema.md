# Sub-Agent Contract Schema

This document defines the minimal, executable contract (Contract Header) used by the Main Agent to dispatch micro-tasks to Sub-Agents (e.g., Trae, Qoder, search). 
Because Sub-Agents are stateless "typewriters" and do not inherit the Main Agent's roles, skills, or global context, they MUST be constrained by this explicit contract to prevent context bloat, scope drift, and hallucinations.

## Universal Envelope (MANDATORY)
Whenever the Main Agent delegates a task to a Sub-Agent, the prompt MUST begin with this envelope:

```md
# Sub-Agent Contract

## 0) Task
- Phase: <EXPLORE | PLAN | IMPLEMENT>
- Objective (1 sentence): <...>

## 1) Scope (Hard Boundary)
- Allowed files/dirs (whitelist): <...>
- Forbidden: Anything outside whitelist

## 2) Non-negotiable Constraints
- No new dependencies/frameworks unless explicitly allowed.
- No secrets / tokens / private data in output.
- No comments added unless explicitly allowed.
- Follow existing code style and patterns; prefer minimal diffs.
- If uncertain: ask exactly 1 clarifying question; do not guess.

## 3) Inputs Provided
- Must-read context (max 3 items): <file/snippet/URL...>
- Assumptions you may use: <...>

## 4) Output Format (MANDATORY)
Return exactly these sections in Markdown:

## Result
- Status: <OK|NEEDS_CLARIFICATION|BLOCKED|RISK_FOUND>
- Summary: <3-6 bullets>

## Details
<phase-specific content required below>

## Self-Check
- Scope respected: ✅/❌
- New deps introduced: ✅/❌
- Secrets leaked: ✅/❌
- Style/patterns reused: ✅/❌
- Risks (1-3 bullets): <...>
- 1 Clarifying Question (only if needed): <...>
```

## Phase-Specific Appendices
The Main Agent MUST append ONE of the following blocks to the `## Details` section of the envelope instructions, depending on the Phase of the delegated task.

### A. EXPLORE / SEARCH (For codebase scanning)
```md
## Details Requirements:
- Search findings: <List of relevant files/symbols>
- Context summary: <Brief explanation of how the findings relate to the objective>
```

### B. PLAN (For proposing micro-task solutions, no code generation)
```md
## Details Requirements:
- Proposed Approach: <Describe the implementation plan>
- Files to touch: <Exact list of files that will be modified>
- Trade-offs: <Pros/cons>
```

### C. IMPLEMENT (For writing code / generating patches)
```md
## Details Requirements:
- File changes: 
  - <path>: <intent>
- Patch:
  ```lang
  <Full file content or minimal diff>
  ```
- Edge cases considered: <2-4 bullets>

Hard rule: Touch only the explicitly allowed files. If extra files are needed, set Status=NEEDS_CLARIFICATION.
```
