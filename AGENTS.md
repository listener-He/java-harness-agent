# AGENTS.md — Entry Map & Core Directives

This file is the single entry point. It contains essential navigation and hard constraints for the Agent.

## 🚨 Hard Safety Constraints (MUST FOLLOW)
- **Budget Limits**: Max 3 Wiki docs, Max 8 Code files per exploration. You MAY use a `<Confidence_Assessment>` to request an elastic extension if close to a breakthrough. If limits are fully exhausted, STOP and use the Escalation Protocol. Do not guess paths or perform runaway searches. ([CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md))
- **Approval Gate**: For MEDIUM/HIGH risk changes, you MUST STOP after creating the spec and wait for human approval (`WAITING_APPROVAL`) before writing any code. ([LIFECYCLE.md](.agents/workflow/LIFECYCLE.md))
- **Anti-Looping**: Max 3 retries for any failing script, test, or linter. If exceeded, STOP and ask the human. You MAY use `bypass_justification.md` to downgrade trivial script failures to WARN. ([HOOKS.md](.agents/workflow/HOOKS.md))
- **Scope Guard**: Do not modify files outside the agreed `focus_card.md` scope without explicit permission.

## 🧭 Initial Action Guidelines
- **Direct Read**: If the user provides an explicit file path, class, or code snippet, read it directly first. Do NOT start with the Wiki Funnel.
- **Root Drill-down**: If exploring a domain without an explicit scope, ALWAYS start at [KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md) and follow the links downward.
- **Resumability**: On session resume, ALWAYS read `router/runs/launch_spec_*.md` first to restore state.

## 🗂 Single Sources of Truth (SSOT)
- Routing, profiles, shortcuts (`@read`, `@patch`, `@standard`): [.agents/router/ROUTER.md](.agents/router/ROUTER.md)
- Navigation and write-back methodology: [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)
- Lifecycle phases and hooks: [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md), [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md)
- Role mounting + gates: [.agents/workflow/ROLE_MATRIX.md](.agents/workflow/ROLE_MATRIX.md)

## 📚 Essential Pointers
- **Wiki Root Index**: [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md)
- **Specialist Skills Index**: [.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md) (Use this when you need specific expertise)
- **Project Red Lines & Preferences**: [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md)
- **Delivery Schema Template**: [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md)

## 🛑 Team Rule
- **Do not commit runtime state or caches**. The following directories MUST be ignored and never committed:
    - `.agents/router/runs/`
    - `.agents/workflow/runs/`
    - `.agents/events/drift_queue/`
    - Python caches: `__pycache__/`, `*.pyc`
    - Project build & IDE: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`
- **Only commit stable artifacts**: (e.g., source code, `openspec.md`, deliveries, and `wal/` fragments).
