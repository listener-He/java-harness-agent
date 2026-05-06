---
name: brainstorming
description: You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
---

# Brainstorming Ideas Into Designs

Help turn an idea into a design that fits this repo’s workflow gates.

<HARD-GATE>
Do NOT write or modify implementation code until a design/spec has been presented and approved (per this repo’s Approval Gate rules).
</HARD-GATE>

## Hard Compatibility Rules

- Use `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_openspec.md` as the design/spec artifact.
- Keep all scope boundaries explicit (in-scope paths + out-of-scope paths).
- Do not assume external spec templates, extra reviewer prompts, or auto-commit behavior.

## Protocol

1. Explore current repo context (standards, constraints, existing patterns)
2. Ask clarifying questions (prefer 1–3 high-impact questions)
3. Propose 2–3 approaches with trade-offs and recommendation
4. Present the design/spec in the OpenSpec format
5. Stop for approval before any implementation work

## Optional Visual Support

If the topic is inherently visual (UI, diagrams), use the browser-based workflow; otherwise keep it text-first.
