# Agent Invocation & Dispatch

Two ways to engage a role. Pick by isolation needs, not by ceremony.

| Mechanism | What it really is | When to use |
|---|---|---|
| **Inline role adoption** | Main agent reads a role's `.md` and follows its instructions in the current conversation. No isolation, no tool boundary. | Architecture design or implementation that needs the full project context (CLAUDE.md + rules + wiki). |
| **Sub-agent dispatch** (`Agent` tool) | Claude Code spawns a fresh agent with its own context and the role's `tools` allowlist. Receives only the prompt you give it. | Well-scoped, bounded work: code review, scope guard, doc updates, knowledge extraction, secret scans. |

Honest note: "inline role adoption" is just *you, reading a markdown file*. Claude Code doesn't enforce a special "mounted role" state — the discipline is yours. Sub-agent dispatch IS enforced by the harness.

Roles live in [.claude/agents/](../agents/). The `Agent` tool picks one by name; check its `tools:` frontmatter to know what it can do.

---

## Dispatch payload (sub-agents)

When you spawn a sub-agent, the prompt MUST be self-contained:

1. **Task contract** — the `task_brief.md` Machine Section (Allowed Scope + ACs + Hard Constraints), or an equivalent inline mini-contract for non-STANDARD tasks
2. **Inputs** — file paths, commit ranges, line numbers
3. **Expected output format**

The sub-agent only sees its own `.md` plus your prompt. It does NOT inherit CLAUDE.md, project rules, or memory.

---

## Handoff (Standard mode)

When work crosses sessions or roles:

1. Incoming agent reads `.claude/runs/launch-specs/launch_spec_*.md`
2. Finds the `IN_PROGRESS` row
3. Loads the `task_brief.md` listed in its Artifact column
4. Resumes from the Phase in the launch spec

The Machine Section is the universal contract — any role can act from it.

---

## Special Scenarios — Foreman Pattern (EPIC)

For EPIC tasks (≥3 domains), the main agent acts as Foreman:
- MUST slice work into micro-tasks (one task_brief per slice)
- MUST delegate each slice to a sub-agent via dispatch
- MUST NOT write code directly — only review sub-agent outputs and integrate

See `.claude/skills/task-decomposition-guide/SKILL.md` (active) for the slicing protocol.
