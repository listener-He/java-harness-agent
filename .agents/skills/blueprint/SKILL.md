---
name: blueprint
description: "Turn a one-line objective into a step-by-step construction plan for multi-session, multi-agent engineering projects. Each step has a self-contained context brief so a fresh agent can execute it cold. Includes adversarial review gate, dependency graph, parallel step detection, anti-pattern catalog, and plan mutation protocol. TRIGGER when: user requests a plan, blueprint, or roadmap for a complex multi-PR task, or describes work that needs multiple sessions, or invokes the AI engineering pipeline. DO NOT TRIGGER when: task is completable in a single PR or fewer than 3 tool calls, or user says \"just do it\"."
---

# Blueprint — Construction Plan Generator

Turn a one-line objective into a step-by-step construction plan that any coding agent can execute cold.

## Hard Compatibility Rules

- Follow `AGENTS.md` lifecycle gates (spec first for MEDIUM/HIGH, Approval Gate, Archive/WAL).
- Write plans as runtime artifacts under `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_plan.md`.
- Do not assume git/gh/CI availability. Use repo-local evidence only.

## When to Use

- Breaking a large feature into multiple PRs with clear dependency order
- Planning a refactor or migration that spans multiple sessions
- Coordinating parallel workstreams across agents
- Any task where context loss between sessions would cause rework
- As Phase 1 of the AI engineering pipeline (blueprint → ADR → eval-harness → self-improve → ai-slop-cleaner)

**Do not use** for tasks completable in a single PR, fewer than 3 tool calls, or when the user says "just do it."

## How It Works

Blueprint runs a 5-phase pipeline:

1. **Research** — Reads project structure and existing workflow artifacts to gather context.
2. **Design** — Breaks the objective into one-PR-sized steps (3–12 typical). Assigns dependency edges, parallel/serial ordering, and rollback strategy per step.
3. **Draft** — Writes a self-contained Markdown plan file to `.agents/workflow/runs/`. Every step includes a context brief, task list, verification commands, and exit criteria — so a fresh agent can execute any step without reading prior steps.
4. **Review** — Delegates adversarial review to an agent against a checklist and anti-pattern catalog. Fixes all critical findings before finalizing.
5. **Register** — Saves the plan, updates memory index, and presents the step count and parallelism summary to the user.

Blueprint should stay tool-agnostic. If git workflows exist, they can be proposed, but do not hard-require them.

## Instructions

### Phase 1: Research

1. Read project structure (top-level directories, key READMEs)
2. Check for existing workflow artifacts under `.agents/workflow/runs/`
3. Check for existing ADR/WAL patterns under `.agents/llm_wiki/` when relevant
4. Gather constraints and standards from `AGENTS.md` and related SSOT documents when needed

### Phase 2: Design

1. Break the objective into discrete steps (3–12 steps)
2. For each step, determine:
   - **Dependencies**: which steps must complete first
   - **Parallel potential**: can this step run concurrently with others?
   - **Scope**: files and modules affected
   - **Rollback strategy**: how to undo if something goes wrong
3. Build a dependency graph identifying parallel vs serial steps

### Phase 3: Draft

Write the plan as a Markdown file to `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_plan.md` with this structure:

```markdown
# Plan: {Objective}

## Overview
{1-2 sentence summary}

## Dependency Graph
{ASCII or Mermaid diagram showing step dependencies}

## Parallelism Summary
- Serial steps: {count}
- Parallel groups: {count}
- Total steps: {count}

---

## Step 1: {Title}

### Context Brief
{Self-contained context so a fresh agent can execute this step without reading prior steps}

### Tasks
- [ ] {task 1}
- [ ] {task 2}

### Verification
{Commands to verify step completion}

### Exit Criteria
{Measurable conditions for step completion}

### Rollback
{How to undo changes if needed}

---

## Step 2: {Title}
...
```

### Phase 4: Review

1. Delegate an adversarial review to a search agent with a self-contained prompt and checklist
2. Review checklist:
   - Completeness: are all necessary steps included?
   - Dependency correctness: are dependencies accurate and minimal?
   - Anti-pattern detection: does the plan avoid known anti-patterns?
   - Cold-start viability: can each step be executed independently?
   - Verification adequacy: are exit criteria measurable?
3. Fix all critical findings before finalizing

### Phase 5: Register

1. Save the finalized plan file
2. Present summary to user:
   ```
   Blueprint complete: {N} steps, {P} parallel groups
   Plan saved to: .agents/workflow/runs/<YYYY-MM-DD>_<slug>_plan.md
   Next: Run architecture-decision-records to capture key decisions, then eval-harness to define success metrics.
   ```

## Anti-Pattern Catalog

Watch for and avoid these common planning anti-patterns:

| Anti-Pattern | Description | Fix |
|---|---|---|
| **God Step** | A single step that does too much | Split into smaller, focused steps |
| **Hidden Dependency** | Step depends on another but doesn't declare it | Make dependency explicit |
| **Vague Exit Criteria** | "It works" instead of measurable conditions | Add specific test commands or assertions |
| **Missing Rollback** | No way to undo if step fails | Add git branch or backup strategy |
| **Context Assumption** | Step assumes knowledge from prior steps | Add context brief |
| **Sequential Bias** | Steps marked serial when they could be parallel | Check for independent file sets |

## Plan Mutation Protocol

When the plan needs to change after creation:

| Operation | Protocol |
|---|---|
| **Split** | Replace step N with N.1, N.2; update dependencies |
| **Insert** | Add step between existing steps; renumber and update dependencies |
| **Skip** | Mark step as skipped with reason; update dependent steps |
| **Reorder** | Move step and update all dependency edges |
| **Abandon** | Mark entire plan as abandoned with reason |

All mutations must be recorded in the plan file with timestamp and reason.

## Pipeline Integration

This skill is Phase 1 of the AI engineering pipeline. After completing the blueprint:

1. **Phase 2**: Invoke the `architecture-decision-records` skill to capture architectural decisions made during planning
2. **Phase 3**: Invoke the `eval-harness` skill to define success metrics for the plan
3. **Phase 4**: Invoke the `self-improve` skill to automatically optimize implementation
4. **Phase 5**: Invoke the `ai-slop-cleaner` skill to clean up after evolution

## Examples

### Basic usage

User says: "migrate database to PostgreSQL"

Produces `plans/myapp-migrate-database-to-postgresql.md` with steps like:
- Step 1: Add PostgreSQL driver and connection config
- Step 2: Create migration scripts for each table
- Step 3: Update repository layer to use new driver
- Step 4: Add integration tests against PostgreSQL
- Step 5: Remove old database code and config

### Multi-agent project

User says: "extract LLM providers into a plugin system"

Produces a plan with parallel steps where possible (e.g., "implement Anthropic plugin" and "implement OpenAI plugin" run in parallel after the plugin interface step is done), and invariants verified after every step (e.g., "all existing tests pass", "no provider imports in core").
