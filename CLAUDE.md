# CLAUDE.md — Project Entry Point

Single entry point for AI coding assistants on this repo. Lazy-load everything else.

## Hard Rules (always apply)

1. **Anti-loop**: max 3 retries per gate/linter, max 2 for compile fixes. Exceed → STOP, ask human.
2. **Never commit**: `.claude/runs/`, `__pycache__/`, `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`. Only commit source, archived task_briefs (`.claude/wiki/archive/`), and `.claude/**/wal/` fragments.

Full safety/commit/artifact policy: [.claude/rules/safety-constraints.md](.claude/rules/safety-constraints.md).

## Two Modes

| Mode | When | Flow |
|---|---|---|
| **Vibe** (default) | LEARN, TRIVIAL, simple PATCH, "just do it" | Act directly. No task_brief, no Explorer, no WAL. |
| **Standard** | MEDIUM/HIGH risk, public API/DB/auth changes, EPIC | Explorer → Propose → Review → [Approval if HIGH] → Implement → QA → Archive |

Default to Vibe. Escalate to Standard only when the change touches **public API, DB schema, auth, error-code system, or ≥3 domains**. Force a mode with `@vibe` / `@patch` / `@standard` / `@learn`.

Standard mode composes PDD + SDD/SPEC + BDD + TDD — see [.claude/wiki/purpose.md](.claude/wiki/purpose.md).

## Session Start

1. Read this file. Lazy-load `.claude/rules/*.md` only when the task needs them.
2. Resuming an interrupted session: read `.claude/runs/launch-specs/launch_spec_*.md` and restore from Phase.
3. User provided concrete paths or snippets: read them directly.
4. Intent ambiguous: ask one clarifying question, then proceed.

Vibe-eligible request → act, no classification line.
Standard-required → emit one line before any output: `[Risk: HIGH | Scenario: B] → task_brief required`.

## Single Sources of Truth

| Topic | File |
|---|---|
| Routing, profiles, shortcuts, risk classification | [.claude/rules/routing.md](.claude/rules/routing.md) |
| Lifecycle phases + gates | [.claude/rules/lifecycle.md](.claude/rules/lifecycle.md) |
| Agent invocation & dispatch | [.claude/rules/dispatch.md](.claude/rules/dispatch.md) |
| Hooks | [.claude/rules/hooks.md](.claude/rules/hooks.md) |
| Safety + commit policy | [.claude/rules/safety-constraints.md](.claude/rules/safety-constraints.md) |
| WAL write-back + anti-bloat | [.claude/rules/writeback-policy.md](.claude/rules/writeback-policy.md) |
| Role catalog | [.claude/agents/](.claude/agents/) |
| Active skill index (+ archive index) | [.claude/skills/skill-index/SKILL.md](.claude/skills/skill-index/SKILL.md) |
| Wiki root | [.claude/wiki/KNOWLEDGE_GRAPH.md](.claude/wiki/KNOWLEDGE_GRAPH.md) |
| Task brief schema | [.claude/wiki/schema/task_brief_schema.md](.claude/wiki/schema/task_brief_schema.md) |
