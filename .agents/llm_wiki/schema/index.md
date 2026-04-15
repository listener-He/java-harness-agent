# Schema Index

This domain contains global contract templates and the minimal links you need to apply them correctly in the lifecycle.

This file is intentionally English-only to maximize agent execution reliability.

## Quick Start (Recommended)
1. Read the contract template to learn the required document structure.
2. Read the process links to learn where the contract is checked, frozen, and enforced.

## Templates
- **[OpenSpec Schema](openspec_schema.md)**: the proposal contract. It can also carry optional handoff sections (API contract + acceptance criteria) when collaboration is needed.

## Process Links (Do not duplicate rules here)
- **[Router](../../router/ROUTER.md)**: map requests into an intent queue (`launch_spec`).
- **[Context Funnel](../../router/CONTEXT_FUNNEL.md)**: forward navigation + reverse write-back rules.
- **[Lifecycle](../../workflow/LIFECYCLE.md)**: the contract freeze point (Approval Gate) and phase responsibilities.
- **[Hooks](../../workflow/HOOKS.md)**: guard/fail/loop constraints (max retries, domain boundary, HITL).

## Link Rules
- Links inside this repo MUST use relative paths from the current file. Do not hardcode `.agents/` into relative links.
