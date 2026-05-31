---
description: Manually convert a local insight into a git-tracked team knowledge doc under .claude/wiki/insights/. Bridges single-machine expert system → team-shared learning. TRIGGER: user explicit invoke ONLY (never auto-fired). NOT FOR: rule changes (use /h-evolve), routine viewing (use /h-context-check).
argument-hint: <--insight-id <id>> [--slug <kebab>] [--dry-run]
---

The single bridge from local Insight Layer (gitignored `.claude/runs/local_intel/insights.jsonl`) to committed team knowledge. **By design, never auto-fires** — publishing is a deliberate human "I think the team should know this" act.

Solves the multi-developer pain identified in T9: insights you generate stay on your laptop; teammates re-trip the same patterns. This command lets you elevate a specific insight into a `.claude/wiki/insights/<date>_<id>_<slug>.md` doc that ships in git.

## Step 1 — Parse args

| Arg | Effect |
|---|---|
| `--insight-id <id>` | **Required.** Insight to publish. Get id via `python3 .claude/scripts/local_intel/insight_writer.py query` or `/h-context-check`. |
| `--slug <kebab-case>` | Optional override of auto-derived filename slug (max 40 chars, `[a-z0-9-]+` only). |
| `--dry-run` | Render the proposed doc to stdout WITHOUT writing or status change. Use to preview wording before commit. |

If `--insight-id` missing → STOP with `[Publish Status]: MISSING_ARG`.

## Step 2 — Load insight + verify publishable

Run:
```bash
python3 .claude/scripts/local_intel/insight_writer.py query --top 50 --min-confidence low --json
```

Find the insight where `id == <insight-id>`.

| Situation | Action |
|---|---|
| Insight not found in active set | Check terminal-status (acted_on/published/dismissed) — re-query with `cat .claude/runs/local_intel/insights.jsonl | grep <id>`; if already `published` → report path, `[Publish Status]: ALREADY_PUBLISHED`; if `dismissed` → STOP, `DISMISSED_REFUSED`; if `acted_on` → ask user if publishing-on-top-of-acted-on is intentional (might be) |
| Insight confidence is `low` | Warn user via `AskUserQuestion`: "Confidence is low — publishing may surface noise. Continue?" |
| Found, status new/acknowledged | Proceed to Step 3 |

## Step 3 — Derive target path

Filename pattern: `<YYYY-MM-DD>_<short-id>_<slug>.md` under `.claude/wiki/insights/`.

Slug derivation (only if `--slug` not given):
- Take insight.summary, lowercase
- Replace non-alphanumeric with `-`, collapse repeats
- Truncate to 40 chars
- Strip leading/trailing `-`

Examples:
- summary "scope_guard FAIL ×7 on .yml" → slug `scope-guard-fail-on-yml`
- summary "AuthService + AuthRepository co-edited" → slug `authservice-authrepository-co-edited`

If file already exists at the target path → STOP, `[Publish Status]: PATH_CONFLICT`, ask user to provide `--slug` override.

## Step 4 — Render markdown content

Agent drafts the full document using insight evidence + its own codebase knowledge. Template:

```markdown
---
insight_id: <id>
kind: <kind>
confidence: <confidence>
detector: <detector>
published_date: <YYYY-MM-DD>
source_summary: <verbatim insight.summary>
---

# <Human-readable title — agent crafts from summary>

## What we observed

<1-2 paragraphs explaining the insight summary in team-readable language>

## Evidence

<bullet-render of insight.evidence:
 - recurring_failure_cluster → "Gate X failed N times in 30d on pattern Y"
 - co_edit_cluster → "Files {A, B, C} edited together N times"
 - decayed_knowledge → "File X unread Nd, age Md"
 - override_drift → "Env var X used N times in 30d, top files: ..."
 - user_correction → "Phrase 'X' fired N times after agent actions"
>

## What we did about it

<agent fills based on context: e.g. "Updated scope_guard implicit allowlist to cover *.yml fixtures"
 OR "Wiki only — no rule change yet; team should consider before extending the pattern"
 OR "TBD — published for team awareness, action pending discussion">

## What you should know

<agent crafts 1-2 sentences of takeaway useful to a teammate seeing this for the first time;
 frame as actionable: "When editing X, also check Y" / "Avoid Z because W">

## Original insight metadata

- ID: <id>
- Detector: <detector>
- Window: <window_days>d
- Generated: <ts>
- Promoted from local `.claude/runs/local_intel/insights.jsonl` by `/h-publish-insight` on <YYYY-MM-DD>
```

Then `AskUserQuestion`: "Preview the above content. Publish to `<target_path>`? (Yes / Show full draft again / Cancel)"

| User | Action |
|---|---|
| Yes | Step 5 |
| Show again | Re-render Step 4, re-ask |
| Cancel | STOP, `[Publish Status]: CANCELLED` |

If `--dry-run`: skip Step 4's AskUserQuestion entirely; just print the rendered doc to stdout + `[Publish Status]: DRY_RUN`. No Step 5.

## Step 5 — Write file + mark status

1. Use `Write` tool to create the file at `<target_path>` with the rendered markdown.
2. Mark insight `published`:
   ```bash
   python3 .claude/scripts/local_intel/insight_writer.py mark-status --id <id> --status published
   ```
3. Suggest `git add <target_path>` to user (do NOT auto-stage — let user control commit timing).

## Step 6 — Final report

Emit:

```
[Publish Status]: PUBLISHED | DRY_RUN | CANCELLED | ALREADY_PUBLISHED | DISMISSED_REFUSED | PATH_CONFLICT | MISSING_ARG
[Insight ID]: <id> | n/a
[Published Path]: <relative path> | n/a
[New Insight Status]: published | <unchanged>
[Next Action]: <one-line>
  Typical: "git add <path> && git commit -m 'docs(insights): publish <slug>'"
  Or:      "Show another insight to publish: python3 .claude/scripts/local_intel/insight_writer.py query"
```

## Hard constraints

| Constraint | Rule |
|---|---|
| **Allowed edit set** | Step 5 writes EXACTLY ONE file: `.claude/wiki/insights/<filename>.md`. Plus one append to `insights.jsonl` via `mark-status`. Nothing else. |
| **Source-code edits FORBIDDEN** | Never edit `src/**`. The published doc is wiki-only knowledge; rule changes belong to `/h-evolve` and are a separate decision. |
| **Anti-loop** | One insight per invocation. Re-running on same `--insight-id` after publish → `[Publish Status]: ALREADY_PUBLISHED` (idempotent skip). |
| **Skip-path semantics** | Missing arg / not-found / dismissed → return with explicit `[Publish Status]` block + exit; do not silent-fail. |
| **Idempotency** | `--dry-run` is fully idempotent (zero side effects). Non-dry-run with same id after published → idempotent skip. |
| **No auto-fire** | This command is NEVER invoked by hook, detector, or other command. ONLY user types `/h-publish-insight ...` explicitly. If you find yourself wanting to auto-fire this, redesign — publish is a deliberate "share this with the team" act. |
| **Sub-agent dispatch** | None. Pure orchestrator. |
| **No auto git add/commit** | Step 5 suggests the command but never runs it — user owns commit timing + message. |

## Out of scope

- Marking insight published WITHOUT writing a doc → use `insight_writer.py mark-status --id <id> --status published` directly (you're declaring "I judged this team-worth but won't write a doc")
- Editing an already-published doc → direct edit of the .md file
- Bulk publish → invoke multiple times; anti-loop is by design
- Auto-fire on high-confidence insights → **never**; publishing is intentional
