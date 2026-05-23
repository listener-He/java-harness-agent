# Schema Index

This domain contains global contract templates and the minimal links you need to apply them correctly in the lifecycle.

This file is intentionally English-only to maximize agent execution reliability.

## Quick Start (Recommended)
1. Read the contract template to learn the required document structure.
2. Read the process links to learn where the contract is checked, frozen, and enforced.

## Templates
- **[Task Brief Schema](task_brief_schema.md)**: the proposal contract for STANDARD/PATCH profiles. May carry optional handoff sections (API contract + acceptance criteria) when collaboration is needed.
- **[Research Report Schema](research_report_schema.md)**: the report contract for RESEARCH profile (analysis / feasibility / baseline). 7-section structure with evidence-pointer enforcement.

Sub-agent dispatch contract (Claude Code internal `Agent` tool) lives in [../../rules/dispatch-template.md](../../rules/dispatch-template.md), not under `schema/`.

## Process Links (Do not duplicate rules here)
- **[Routing + Lifecycle + Hooks](../../rules/lifecycle.md)**: profiles, phase responsibilities, Approval Gate, and guard/fail/loop constraints (max retries, domain boundary, HITL).
- **[Policy](../../rules/policy.md)**: safety constraints, commit policy, WAL write-back, and sub-agent dispatch rules.

## Link Rules
- Links inside this repo MUST use relative paths from the current file. Do not hardcode `.claude/` into relative links.
