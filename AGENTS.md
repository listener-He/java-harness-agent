# AGENTS.md — Single Entry Point

This file exists for one reason: route any human or agent to the correct starting point and define the minimal non-negotiable rules.

## TL;DR (Default Path)
1. Any natural-language request -> start at the Intent Gateway.
2. The first action is always the Context Funnel (drill down from the root index).
3. Deliver work via the Lifecycle, and write back evidence/knowledge during Archive (WAL).

## 1) Entry: Intent Gateway (MUST)
- Read: [.agents/router/ROUTER.md](.agents/router/ROUTER.md)
- Use: `intent-gateway` (routing + context funnel) and `devops-lifecycle-master` (lifecycle orchestration)

## 2) First Action: Context Funnel (DO NOT blind search)
- Start at the root: [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md)
- Drill down via indexes; use fallback search only when the index tree cannot locate the concept
- Rules: [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)

## 3) Delivery: Lifecycle (Contract-first, then implement)
- Lifecycle: [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md)
- Hooks: [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md)
- Propose MUST produce `openspec.md` (template): [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md)
- If risk level is MEDIUM/HIGH and Approval has not happened, DO NOT enter implementation; LOW may skip, but you MUST state why

## 4) Archive: WAL (Anti-bloat, resumable)
- WAL rules: [.agents/workflow/ARCHIVE_WAL.md](.agents/workflow/ARCHIVE_WAL.md)
- Principle: extract stable knowledge as WAL fragments; avoid direct edits to shared indexes

## 5) Skills
- Skills index: [.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md)

## Team Collaboration Rules (MUST)
- Do not commit runtime state: `.agents/router/runs/` and `.agents/workflow/runs/`
- Only commit stable artifacts: rules/templates/wiki content, and necessary contracts/delivery docs; personal runtime progress is not a shared source of truth

## Hard Rules (Minimal Set)
- Do not guess paths; always drill down from the Knowledge Graph root
- Do not start with full-text search; use the funnel first
- Do not skip Contract + Approval for MEDIUM/HIGH risk changes
- On failure: roll back and fix; if max retries is hit, stop and ask for human intervention
- On completion: archive and write back objective evidence + stable knowledge
