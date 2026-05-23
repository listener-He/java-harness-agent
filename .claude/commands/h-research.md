---
description: Scaffold a research report (no code change) and bind to launch_spec
argument-hint: <slug> [--scope quick|deep]
---

Phase R1 entry for RESEARCH profile. Produces `research_report.md`; binds to `launch_spec`. NOT for code change — use task_brief command for that.

## Step 1 — Parse `$ARGUMENTS`

- `<slug>` (required, kebab-or-snake-case) — STOP if missing.
- `--scope quick|deep` (default `quick`) — drives §3 quota (quick ≥ 5 findings; deep ≥ 15).

If invoked after `[triage] suggested: RESEARCH` without a slug → propose one (≤ 4 words, kebab-case), confirm via `AskUserQuestion`, then proceed.

## Step 2 — Compute path

- Path: `.claude/runs/reports/<YYYY-MM-DD>_<slug>_research.md`
- File exists → STOP, do not overwrite.
- `mkdir -p .claude/runs/reports`.

## Step 3 — Render skeleton

Render per schema at `.claude/wiki/schema/research_report_schema.md`. Frontmatter:

```yaml
---
spec_mode: RESEARCH
scope: <quick|deep>
created: <YYYY-MM-DD>
slug: <slug>
---
```

All 7 sections (§1..§7) MUST be present. Bodies use this placeholder format:

```
<!-- TODO(h-research, R1|R2): <one-line instruction> -->
```

Per-section placeholder content (MUST follow):

| Section | Placeholder content |
|---|---|
| §1 Question | seed user goal verbatim; ≥ 20 chars; refine TODO if vague |
| §2 Method | TODO listing 3 starting moves (grep / read / WebSearch) |
| §3 Findings | TODO citing pointer-format whitelist + scope quota |
| §4 Analysis | TODO citing uncertainty markers (`[high confidence]` / `[inferred]` / `[speculative]`) |
| §5 Recommendations | TODO citing Option block template |
| §6 Open Questions | TODO citing Q / Why-blocked / Next template |
| §7 Evidence Index | TODO ("populate during R2 from §3 pointers") |

## Step 4 — Validate skeleton

```bash
python3 .claude/scripts/gates/research_report_gate.py --require <report path>
```

Skeleton is expected to FAIL at scaffold time. Acceptable FAIL messages:

- `§3 Findings: 0 entries`
- `§4 Analysis too thin`
- `§7 Evidence Index has no entries`

Unacceptable FAIL (revise once, then STOP):

- `frontmatter missing or wrong`
- `missing section(s)`
- `§1 Question too short` when user input ≥ 20 chars

Anti-loop: max 2 retries on skeleton issues.

## Step 5 — Bind to launch_spec

- Latest `.claude/runs/launch-specs/launch_spec_*.md` exists → append row.
- Else → create new launch_spec with the same 6-column skeleton used by other commands.

Row format:

```
| <slug> | RES | Research | IN_PROGRESS | <upstream slugs or "none"> | <report path> |
```

| Column | RESEARCH value |
|---|---|
| Risk | `RES` literal (risk-orthogonal per `lifecycle.md`) |
| Phase | `Research` (single value; R1/R2/R3 self-tracked) |
| Status | `IN_PROGRESS` (no Propose, no Approval) |

## Step 6 — Report

```
[Report Status]: CREATED
[Slug]: <slug>
[Scope]: quick | deep
[Report Path]: <path>
[Launch Spec]: <path> (row appended, IN_PROGRESS)
[Gate]: skeleton parsed; substantive gate deferred to archive
[Next Action]: Begin R1 — <one specific first step inferred from slug + scope>
```

## Hard constraints

- Allowed edits: ONLY the new report file + target launch_spec.
- MUST NOT edit `src/`, `pom.xml`, `*.sql`, migration files, or any `task_brief.md`.
- MUST NOT create a task_brief alongside — RESEARCH and STANDARD are mutually exclusive per task.
- MUST NOT overwrite existing report at computed path.
- MUST NOT write WAL during scaffold (WAL question fires only at archive).
- Anti-loop: max 2 retries on path/skeleton issues.
