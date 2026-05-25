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

Non-blocking; user intent wins. The block is for audit only — prevents silent escalations and surfaces over-eager Vibe usage.

## Commit Policy

**Never commit:**
- `.claude/runs/` (launch-specs, active task_briefs)
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit:** source code, archived task briefs (`.claude/wiki/archive/`), archived research reports (`.claude/wiki/archive/reports/`), archived collab deliverables (`.claude/wiki/archive/collabs/`), and `.claude/**/wal/` fragments.

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

## Anti-Bloat: Per-directory Line Limits

| Path prefix | Cap |
|---|---|
| (default) | 3000 |
| `.claude/wiki/archive/reports/` | 10000 |

Python source of truth: `.claude/scripts/wiki/wiki_linter.py` (`DEFAULT_MAX_LINES`, `PATH_LINE_CAPS`).

On overflow:
1. Split content into focused sub-documents per topic
2. Rewrite original `index.md` as a lean routing graph
3. Update `KNOWLEDGE_GRAPH.md` if top-level structure changed
4. Research reports approaching 10000 → split per schema "Size limit" (main + evidence appendix)

Gate: `python3 .claude/scripts/wiki/wiki_linter.py` — FAIL on dead links OR cap exceeded.

## Extraction Rules

- Do NOT directly edit shared `index.md` files during automated runs. Write to `wal/` fragments.
- WAL fragments are merged later by the Librarian (via `@gc`).
- **STANDARD: WAL write-back is user-elected.** `h-archive` scans diff → suggests dimensions (Domain / API / Rules / Data / Architecture) → multi-select. Only chosen dimensions written. **None** is valid (writes a stub recording the decision). HIGH+None requires a one-line justification; MEDIUM+None does not. The question itself is mandatory — silent zero-WAL is not allowed.
- PATCH tasks: no WAL required, no question asked. Wiki refresh deferred to `@wiki-update`.
- New tables/schemas go into WAL data domain (`wiki/data/wal/`) as Markdown with DDL code blocks — NOT as root `.sql` files.

## RESEARCH Profile Write-back

| Rule | Value |
|---|---|
| WAL default | Skip (report itself is the knowledge artifact) |
| Archive-time WAL question | Mandatory single AskUserQuestion; user MUST pick Skip or Extract |
| Extract cap | ≤ 2 dimensions per research task; > 2 → use STANDARD follow-up instead |
| Extract trigger | Research surfaced stable reusable facts independent of §5 Recommendations |
| `signals_yellow` effect | Amplifies §3 evidence rigor (≥ 10 entries), does NOT change WAL default |

---

# Part 3 — Agent Invocation & Dispatch

Pick by isolation needs, not ceremony.

| Mechanism | What it really is | When to use |
|---|---|---|
| **Inline role adoption** | Main agent reads a role's `.md` and follows its instructions in the current conversation. No isolation, no tool boundary. | Architecture design or implementation that needs the full project context (CLAUDE.md + rules + wiki). |
| **Sub-agent dispatch** (`Agent` tool) | Claude Code spawns a fresh agent with its own context and the role's `tools` allowlist. Receives only the prompt you give it. | Well-scoped, bounded work: code review, scope guard, doc updates, knowledge extraction, secret scans. |

Roles live in [.claude/agents/](../agents/). The `Agent` tool picks one by name; check its `tools:` frontmatter for capabilities.

### Inline preference for small STANDARD-MEDIUM tasks

STANDARD-MEDIUM with **AC count ≤ 3 AND single domain AND no cross-cutting concerns** → prefer inline `lead-engineer`: main agent reads `.claude/agents/lead-engineer.md` and acts as that role. Allowed Scope / ACs / Hard Constraints stay in scope via the active task_brief.

Dispatch (not inline) when ANY of:
- AC count ≥ 4
- Multi-domain OR HIGH risk
- Role is `code-reviewer` or `adversarial-review` (**never inline**)
- Role is `knowledge-extractor`, `requirement-engineer`, `system-architect`, or `security-sentinel`

When in doubt, dispatch.

## Dispatch payload (sub-agents)

**MANDATORY:** build every sub-agent dispatch prompt from [dispatch-template.md](dispatch-template.md). Missing required section → sub-agent returns `[Status]: ESCALATE`; main agent re-dispatches.

## Handoff (Standard mode)

When work crosses sessions or roles:

1. Incoming agent reads `.claude/runs/launch-specs/launch_spec_*.md`
2. Finds the `IN_PROGRESS` row
3. Loads the `task_brief.md` listed in its Artifact column
4. Resumes from the Phase in the launch spec

## Special Scenarios — Foreman Pattern (EPIC)

For EPIC tasks (≥3 domains), the main agent acts as Foreman:
- MUST slice work into micro-tasks (one task_brief per slice)
- MUST delegate each slice to a sub-agent via dispatch
- MUST NOT write code directly — only review sub-agent outputs and integrate

See `.claude/skills/task-decomposition-guide/SKILL.md` (active) for the slicing protocol.
