# CLAUDE.md — Project Entry Point

Single entry point for AI coding assistants on this repo. Lazy-load everything else.

## Hard Rules (always apply)

1. **Anti-loop**: max 3 retries per gate/linter, max 2 for compile fixes. Exceed → STOP, ask human.
2. **Never commit**: `.claude/runs/`, `__pycache__/`, `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`. Only commit source, archived task_briefs (`.claude/wiki/archive/`), and `.claude/**/wal/` fragments.

Full safety/commit/artifact policy: [.claude/rules/policy.md](.claude/rules/policy.md).

## Behavioral Principles

These reduce common LLM coding mistakes. They bias toward caution over speed — for trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

### 5. Skill Files: Reference, Not Preflight Reading

**Skills are deep-dive references, not preflight reading.** The description for each skill in your system prompt is the daily navigation — for Zone A skills (`java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `test-driven-development`) the description already encodes the everyday rules you need.

- Don't ritualistically read every Zone A `SKILL.md` before Implement. The description has what you need 90% of the time.
- Open `SKILL.md` only when you face a **specific technical decision** the description doesn't answer (e.g., "what's the In-Memory JOIN helper signature", "should this be a composite index leftmost-prefix or a covering index").
- During Implement, the PostToolUse hook emits a `[skill-hint]` block when a known anti-pattern slips into a file. Treat the hint as a signal to consider opening that specific `SKILL.md`, not as a blocking gate.

### 6. Past Incidents: Read When the Hook Points You at Them

Production incident facts live under `.claude/wiki/incidents/<date>_<slug>.md`. They are surfaced two ways:

- **UserPromptSubmit:** the `[failure-memory]` block at turn start lists recent incidents (last 30 days + any with `status: watch`), each with a one-line "提醒未来 LLM" lesson. Skim them like you'd skim a standup digest.
- **PostToolUse:** when you edit a file referenced by a past incident, an `[incident-hint]` block injects a pointer. **Open that specific `.md`** — it has the actual root cause, fix, and what to avoid this time.

**Ingesting a new incident:** run `python3 .claude/scripts/local_intel/ingest_incident.py --help` — script saves the raw fact + prints a template; you write `.claude/wiki/incidents/<date>_<slug>.md` per the template. The `## 提醒未来 LLM` field is what every future session sees — write it well.

## Two Modes

| Mode | When | Flow |
|---|---|---|
| **Vibe** | LEARN, TRIVIAL, simple PATCH, "just do it" | Act directly. No task_brief, no Explorer, no WAL. |
| **Standard** | MEDIUM/HIGH risk, public API/DB/auth changes, EPIC | Explorer → Propose → Review → [Approval if HIGH] → Implement → QA → Archive |

### Vibe Eligibility (white-list, not fallback)

Enter Vibe ONLY if: probe ALL-GREEN or heuristic-skipped (see [lifecycle.md](.claude/rules/lifecycle.md) Step 0 + Risk Classification), OR explicit `@vibe`/`@patch`/`@quickfix`/`@learn`, OR diff < 3 lines obviously cosmetic. `@vibe`/`@patch` while probe shows red signals → emit `[Probe Override]` per [policy.md](.claude/rules/policy.md#probe-override).

Any other input enters at least **PATCH(LOW)** with a Slim Spec — one paragraph stating scope + AC before code. Force a mode with `@vibe` / `@patch` / `@standard` / `@learn`.

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
| Routing + lifecycle + hooks (profiles, phases, gates) | [.claude/rules/lifecycle.md](.claude/rules/lifecycle.md) |
| Safety + commit + WAL write-back + dispatch | [.claude/rules/policy.md](.claude/rules/policy.md) |
| Sub-agent dispatch prompt template (mandatory) | [.claude/rules/dispatch-template.md](.claude/rules/dispatch-template.md) |
| Skill precedence (conflict resolution for MANDATORY) | [.claude/rules/skill-precedence.md](.claude/rules/skill-precedence.md) |
| TaskList usage (when to open / granularity) | [.claude/rules/tasklist-policy.md](.claude/rules/tasklist-policy.md) |
| Role catalog | [.claude/agents/](.claude/agents/) |
| Active skill index (+ archive index) | [.claude/skills/skill-index/SKILL.md](.claude/skills/skill-index/SKILL.md) |
| Wiki root | [.claude/wiki/KNOWLEDGE_GRAPH.md](.claude/wiki/KNOWLEDGE_GRAPH.md) |
| Task brief schema | [.claude/wiki/schema/task_brief_schema.md](.claude/wiki/schema/task_brief_schema.md) |
