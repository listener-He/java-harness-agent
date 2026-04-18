# LLM Wiki Knowledge Graph (Root Index)

This file is the root of the wiki. Use it to navigate by drilling down through indexes. Do not guess paths.

## Hard Rules (MUST)
- *Note: All paths are relative to the directory of this KNOWLEDGE_GRAPH.md file.*
- You MUST start navigation from this file, then drill down via `index.md` files. Read maximum 1-2 index files per step, analyze, and then decide the next exact file to read.
- You MUST NOT jump directly to random documents by guessing paths.
- Any new stable knowledge MUST be attached to this tree (via the correct domain). When updating knowledge, the agent MUST update `KNOWLEDGE_GRAPH.md` or the relevant domain `index.md` first to ensure no orphan docs are created.

## 0. Project Entry
- **[AGENTS.md](../../AGENTS.md)**: the single entry point (routing, funnel, lifecycle, write-back).

## 1. Philosophy & Templates
- **[Purpose](purpose.md)**: why this system exists and what it optimizes for.
- **[OpenSpec Schema](schema/openspec_schema.md)**: the contract template for proposals and designs.
- **[Skills Index](../skills/trae-skill-index/SKILL.md)**: available specialist skills.

## 2. Active Domains (Drill-down Indexes)
- **[Domain](wiki/domain/index.md)**: Business vocabulary, states, invariants. *(e.g., Auth, Payment, User states)*
- **[API](wiki/api/index.md)**: Exposed APIs and contracts. *(Format: Markdown tables with Method, Path, Auth)*
- **[Data](wiki/data/index.md)**: Database tables, indexes, ER notes. *(Format: Markdown tables with Store Type, Retention)*
- **[Architecture](wiki/architecture/index.md)**: Architecture decisions, security baseline, ADRs. *(Format: ADR tracking list)*
- **[Specs](wiki/specs/index.md)**: Active `openspec.md` documents. *(Ongoing or recently closed proposals)*
- **[Testing](wiki/testing/index.md)**: Testing standards and evidence requirements. *(Contains objective evidence links)*
- **[Reviews](wiki/reviews/index.md)**: Review artifacts, PR design reviews, audit reports. *(Status tracking)*
- **[Preferences](wiki/preferences/index.md)**: Project-specific constraints, security rules, and do-not-do lists. *(Tags: `[Security]`, `[DB]`, etc. If any file exceeds 500 lines, it MUST be split).*

## 3. Cold Storage
- **[Archive](archive/index.md)**: extracted or obsolete documents kept for traceability.
