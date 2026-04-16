# AGENTS.md — Entry Map

This file is navigation only.

Single sources of truth (SSOT):
- Routing, profiles, shortcuts, launch/write-back switches: [.agents/router/ROUTER.md](.agents/router/ROUTER.md)
- Navigation and write-back methodology: [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)
- Lifecycle phases and hooks: [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md), [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md)
- Wiki root index: [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md)

Quick usage:
- Use the shortcut DSL (examples and flags are in ROUTER.md):
    - `@read` / `@learn` for read-only learning
    - `@patch` / `@quickfix` for small changes and bugfixes
    - `@standard` for full delivery lifecycle

Team rule:
- Do not commit runtime state: `.agents/router/runs/` and `.agents/workflow/runs/` (only commit stable artifacts).
