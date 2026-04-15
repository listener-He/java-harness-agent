# LLM Wiki Knowledge Graph (Root Index)

This file is the root of the wiki. Use it to navigate by drilling down through indexes. Do not guess paths.

## Hard Rules (MUST)
- You MUST start navigation from this file, then drill down via `index.md` files.
- You MUST NOT jump directly to random documents by guessing paths.
- Any new stable knowledge MUST be attached to this tree (via the correct domain).

## 0. Project Entry
- **[AGENTS.md](../../AGENTS.md)**: the single entry point (routing, funnel, lifecycle, write-back).

## 1. Philosophy & Templates
- **[Purpose](purpose.md)**: why this system exists and what it optimizes for.
- **[OpenSpec Schema](schema/openspec_schema.md)**: the contract template for proposals and designs.
- **[Skills Index](../skills/trae-skill-index/SKILL.md)**: available specialist skills.

## 2. Active Domains (Drill-down Indexes)
- **[Domain](wiki/domain/index.md)**: business vocabulary, states, invariants.
- **[API](wiki/api/index.md)**: exposed APIs and contracts.
- **[Data](wiki/data/index.md)**: database tables, indexes, ER notes.
- **[Architecture](wiki/architecture/index.md)**: architecture decisions, security baseline, ADRs.
- **[Specs](wiki/specs/index.md)**: active `openspec.md` documents.
- **[Testing](wiki/testing/index.md)**: testing standards and evidence requirements.
- **[Preferences](wiki/preferences/index.md)**: project-specific constraints, security rules, and do-not-do lists. If any file exceeds 500 lines, it MUST be split.

## 3. Cold Storage
- **[Archive](archive/index.md)**: extracted or obsolete documents kept for traceability.
