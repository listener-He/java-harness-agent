# Project Policy: Safety, Write-back & Dispatch

Single source of truth for: safety/commit rules, WAL write-back, agent invocation/dispatch. Merged from former `safety-constraints.md` + `writeback-policy.md` + `dispatch.md`.

---

# Part 1 — Safety Constraints & Commit Policy

## Hard Constraints

| Constraint | Rule |
|---|---|
| **Anti-loop** | Max 3 retries per script/linter. Max 2 retries for compile fixes. Exceed → STOP, ask human. |
| **Artifact Paths** | Runtime artifacts under `.claude/runs/`. Never in repo root. Archive phase moves task_brief to `wiki/archive/`. |
| **State Files** | Only two: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract). No brake_snapshot, no engine_state.json. |

<a id="probe-override"></a>
### Probe Override

When the user invokes `@vibe` / `@patch` / `@quickfix` but the `[triage]` block (from `triage_probe.py`, see [lifecycle.md Step 0](lifecycle.md#step-0--triage-probe-auto-injected-via-userpromptsubmit-hook)) reports any `signals_red`, the agent MUST print this block at turn start before any other output:

```
[Probe Override]
User invoked <shortcut>; ignoring probe signals:
  - <signal-1>
  - <signal-2>
Proceeding in <Vibe|Patch> at user's explicit request.
```

This is **non-blocking** — the user's declared intent wins. The block exists solely for auditability so silent escalations cannot happen and over-eager Vibe usage is visible in the transcript.

## Commit Policy

**Never commit:**
- `.claude/runs/` (launch-specs, active task_briefs)
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit:** source code, archived task briefs (`.claude/wiki/archive/`), and `.claude/**/wal/` fragments.

---

# Part 2 — Write-back Policy: WAL & Anti-Bloat

## Language Rule

- **Machine-facing** (code snippets, schemas, paths, script names): **English**
- **Human-facing** (explanations, rationale, context, summaries): **User's primary language** (Chinese for this project)

## WAL Fragment Naming

```
.claude/wiki/wiki/<domain>/wal/YYYYMMDD_<slug>_<category>.md
```

Domains: `domain/`, `api/`, `data/`, `preferences/`, `architecture/`

## Archive Location

Completed task_briefs move to: `.claude/wiki/archive/<YYYY-MM-DD>_<slug>_task_brief.md`

After extraction, replace the active `task_brief.md` in `runs/task-briefs/` with a pointer file:
```bash
python3 .claude/scripts/tools/archive_session_artifacts.py --slug <feature_slug>
```

## Anti-Bloat: 500-line Hard Limit

When any wiki index file exceeds 500 lines:
1. Split content into focused sub-documents per topic
2. Rewrite original `index.md` as a lean routing graph (links + 1-2 line summaries)
3. If top-level structure changes, update `KNOWLEDGE_GRAPH.md`

Gate: `python3 .claude/scripts/wiki/wiki_linter.py` — FAIL if dead links or any file > 500 lines.

## Extraction Rules

- Do NOT directly edit shared `index.md` files during automated runs. Write to `wal/` fragments.
- WAL fragments are merged later by the Librarian (via `@gc`).
- STANDARD tasks: WAL write-back is MANDATORY (Domain + API + Rules; Data if schema change).
- PATCH tasks: no WAL required. Wiki refresh deferred to `@wiki-update`.
- New tables/schemas go into WAL data domain (`wiki/data/wal/`) as Markdown with DDL code blocks — NOT as root `.sql` files.

---

# Part 3 — Agent Invocation & Dispatch

Two ways to engage a role. Pick by isolation needs, not by ceremony.

| Mechanism | What it really is | When to use |
|---|---|---|
| **Inline role adoption** | Main agent reads a role's `.md` and follows its instructions in the current conversation. No isolation, no tool boundary. | Architecture design or implementation that needs the full project context (CLAUDE.md + rules + wiki). |
| **Sub-agent dispatch** (`Agent` tool) | Claude Code spawns a fresh agent with its own context and the role's `tools` allowlist. Receives only the prompt you give it. | Well-scoped, bounded work: code review, scope guard, doc updates, knowledge extraction, secret scans. |

Honest note: "inline role adoption" is just *you, reading a markdown file*. Claude Code doesn't enforce a special "mounted role" state — the discipline is yours. Sub-agent dispatch IS enforced by the harness.

Roles live in [.claude/agents/](../agents/). The `Agent` tool picks one by name; check its `tools:` frontmatter to know what it can do.

## Dispatch payload (sub-agents)

**MANDATORY:** every sub-agent dispatch prompt MUST be built from the template at [dispatch-template.md](dispatch-template.md). Do NOT write dispatch prompts free-form — the template captures the contract, anti-loop limits, scope, and structured-return format that sub-agents otherwise wouldn't know about (they don't inherit CLAUDE.md / rules / memory).

Required sections, all present even if "none":
1. **Task Contract** — Allowed Scope + ACs + Hard Constraints (from `task_brief.md` Machine Section)
2. **Inputs** — file paths, commit ranges, line numbers
3. **Hard Limits** — anti-loop, scope discipline, no safety-bypass (verbatim from template)
4. **Expected Output** — the structured `[Status]: … [Files Changed]: …` block

Receiving sub-agents validate the prompt structure on entry. Missing section → return `[Status]: ESCALATE` with the missing-section name; the main agent must re-dispatch with the template. See [dispatch-template.md](dispatch-template.md) for the full skeleton and worked examples.

## Handoff (Standard mode)

When work crosses sessions or roles:

1. Incoming agent reads `.claude/runs/launch-specs/launch_spec_*.md`
2. Finds the `IN_PROGRESS` row
3. Loads the `task_brief.md` listed in its Artifact column
4. Resumes from the Phase in the launch spec

The Machine Section is the universal contract — any role can act from it.

## Special Scenarios — Foreman Pattern (EPIC)

For EPIC tasks (≥3 domains), the main agent acts as Foreman:
- MUST slice work into micro-tasks (one task_brief per slice)
- MUST delegate each slice to a sub-agent via dispatch
- MUST NOT write code directly — only review sub-agent outputs and integrate

See `.claude/skills/task-decomposition-guide/SKILL.md` (active) for the slicing protocol.
