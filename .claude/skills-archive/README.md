# `skills-archive/` — Lazy-Loaded / Scenario-Conditional Skills (PERMANENT)

**This directory is NOT a graveyard.** The name `skills-archive` is misleading: every skill here is **actively referenced** by `.claude/rules/lifecycle.md` scenarios or by `.claude/commands/h-*.md`. They live here (rather than in `.claude/skills/`) because their trigger conditions are narrow — they fire on specific Scenarios (EPIC, RELEASE, GREENFIELD, B2, etc.) rather than on the daily PATCH/STANDARD flow.

## Why this directory is safe from automatic cleanup

The cleanup pipeline already excludes it, two ways:

1. **`distill.py execute`** (`.claude/scripts/wiki/distill.py:17-22`) refuses to `git rm` or modify anything **outside `.claude/wiki/wiki/`**. `skills-archive/` is at `.claude/skills-archive/`, so it's structurally out of scope. The script may *grep* this directory to count cross-references (it appears in `SCAN_ROOTS` on line 50), but reference-counting is read-only.
2. **`wiki_linter.py`** (`.claude/scripts/wiki/wiki_linter.py:14`) only scans `.claude/wiki/`. `skills-archive/` is not under that root, so the linter doesn't see it at all — no orphan warnings, no dead-link complaints.

So while no script explicitly says "skip skills-archive," the existing scope rules make it untouchable. This is by design.

## What the Librarian (`@gc` / `@distill` / `@librarian`) should do here

The Librarian agent (`.claude/agents/librarian.md`) drives `distill.py`. Because of guarantee #1 above, it physically cannot remove files in this directory. But it MAY surface a manual recommendation like "skill X here looks unreferenced; consider removing in a STANDARD task." That recommendation is informational — acting on it requires the path below.

## When to actually remove a skill from here

Only when ALL of the following hold:

1. Every reference in `lifecycle.md` AND every `.claude/commands/h-*.md` has been removed in the same change set.
2. A WAL Architecture fragment (under `.claude/wiki/wiki/architecture/wal/`) records why the skill became obsolete.
3. The removal goes through a STANDARD-profile task with explicit user approval — **never** via `@distill`, `@gc`, or any automated path.

The directory name (`skills-archive`) predates the "permanent vs deprecated" distinction. Renaming to e.g. `skills-conditional/` would be more honest, but it ripples through every `lifecycle.md` Scenario reference and every `h-*.md` command. Until that ripple is paid for in a dedicated task, this README is the single source of truth: **PERMANENT**.

## Current load-bearing references (audit anchor)

| Skill | Referenced by |
|---|---|
| `incident-response/` | `lifecycle.md` Scenario A (Emergency Hotfix) |
| `blueprint/` | `lifecycle.md` Scenario EPIC (`system-architect` Propose phase) |
| `dispatching-parallel-agents/` | `lifecycle.md` Scenario EPIC (≥2 independent workstreams) |
| `migration-planner/` | `lifecycle.md` Scenario B2 (Mutating DDL) |
| `greenfield-scaffold/` | `lifecycle.md` Scenario GREENFIELD |
| `release/` | `lifecycle.md` Scenario RELEASE, `commands/h-release.md` |
| `linter-severity-standard/` | `commands/h-gates.md` severity aggregation contract |
| `external-research/` | `lifecycle.md` Scenario D (Performance Tuning, optional) |
| `ai-pipeline/`, `self-improve/`, `eval-harness/`, `deepinit/` | `lifecycle.md` Scenario PIPELINE |
| `using-git-worktrees/` | parallel-execution flows; consulted on demand |

Delete any directory above → expect breakage at the next Scenario trigger or `/h-gates` / `/h-release` invocation. Verify each row before pruning.
