---
title: insights.jsonl Insight Layer schema
category: architecture
status: active
---

# insights.jsonl — Pattern-Recognition Output Stream

## Purpose

L2 (Insight) layer of the Sensor / Insight / Policy / Enforce architecture. The Insight Detector reads from `events.jsonl` + `failure_memory.json` + `usage_tracker` + `incidents/` and emits structured insights for agents and humans to review.

```
Sensor   (events.jsonl + failure_memory + ...)
   ↓
Insight  (detector → insights.jsonl)         ← this layer
   ↓
Policy   (/h-context-check surfaces top insights; /h-evolve turns one into a rule change proposal;
          /h-publish-insight elevates one to a git-tracked team knowledge doc)
   ↓
Enforce  (human-approved rule changes land via git commit)
```

**Discipline**: the Insight Detector observes only. Rule changes always go through `/h-evolve` (human-approved Edit) or `/h-publish-insight` (human-approved Write). The detector itself never modifies `CLAUDE.md`, hooks, or any configuration.

## File Location

```
.claude/runs/local_intel/insights.jsonl
```

- gitignored (lives under `.claude/runs/`)
- append-only JSONL
- rotates to `insights.jsonl.YYYY-MM-DD` when the file exceeds 5 MB

## Common Fields (every insight)

| Field | Type | Notes |
|---|---|---|
| `id` | string | short hash (first 10 chars of SHA-256 over `kind::summary`) — same kind + summary always yields the same id (idempotent re-emit) |
| `ts` | string | ISO 8601 + tz |
| `kind` | string | one of 5 kinds, see below |
| `confidence` | string | `high` / `medium` / `low` |
| `summary` | string | one-line human-readable description (≤ 120 chars) |
| `suggested_action` | string | one-line recommended action (≤ 200 chars), verb-led |
| `evidence` | list | pointers to source data: file:line / event ts / failure_memory keys |
| `status` | string | `new` / `acknowledged` / `acted_on` / `published` / `dismissed` (default `new`) |

Optional: `detector` (which detector produced it), `tags` (free-form topic tags).

## Insight Kinds

### `recurring_failure_cluster`
| Field | Required | Notes |
|---|---|---|
| `gate` | ✓ | failing gate name (e.g. `scope_guard`) |
| `pattern` | ✓ | pattern text recorded by failure_memory |
| `count` | ✓ | recurrence count (≥ 3 to surface) |
| `days_span` | ✓ | days between first and most recent occurrence |

Confidence: `count ≥ 10` → high; `≥ 5` → medium; `≥ 3` → low.

### `co_edit_cluster`
| Field | Required | Notes |
|---|---|---|
| `files` | ✓ | files co-edited within proximity windows (2-5 typical) |
| `total_pair_count` | ✓ | sum of pair co-occurrences across the cluster (post union-find dedup) |
| `member_count` | ✓ | size of the cluster |
| `window_days` | ✓ | scan window |
| `min_age_hours` | ✓ | minimum age filter (default 24) — excludes active-session noise |

Confidence: `count ≥ 10` → high; `≥ 5` → medium; `≥ 3` → low.

### `decayed_knowledge`
| Field | Required | Notes |
|---|---|---|
| `file_path` | ✓ | candidate stale file |
| `last_read_days` | ✓ | days since last read (from `usage_tracker`) |
| `file_age_days` | ✓ | days since file mtime |
| `reason` | ✓ | e.g. "unread ≥ 90d" / "referenced file no longer exists" |

Confidence: `last_read ≥ 180d` → high; `≥ 90d` → medium; `≥ 60d` → low.

### `override_drift`
| Field | Required | Notes |
|---|---|---|
| `env_var` | ✓ | which bypass env var (e.g. `CLAUDE_SCOPE_GUARD_BYPASS`) |
| `count_30d` | ✓ | usage count in last 30 days |
| `top_contexts` | — | top 3 most common file_paths during bypass |

Confidence: `count ≥ 10` → high; `≥ 5` → medium; `≥ 3` → low.

### `user_correction`
| Field | Required | Notes |
|---|---|---|
| `correction_phrase` | ✓ | exact phrase that fired (e.g. `wrong`, `不对`) |
| `count` | ✓ | recurrence in 30d |
| `recent_excerpts` | — | up to 3 recent `prompt_excerpt` samples |
| `bound_to_prior_action` | — | count of those bound to `prior_actions_5min > 0` |

Confidence: `count ≥ 10` → high; `≥ 5` → medium; `≥ 3` → low.

The detector defaults to `require_prior_action=True` — corrections fired with no recent agent activity are filtered out as session-opening false fires.

## Status State Machine

```
new ──────────────► acknowledged   (agent saw it during /h-context-check)
 │                       │
 │                       ▼
 │                  acted_on        (/h-evolve applied a rule change)
 │
 ├──────────────► published          (/h-publish-insight wrote a team-visible doc)
 │
 └──────────────► dismissed          (human/agent explicitly rejected it)
```

Only forward transitions are valid: `new → {acknowledged, acted_on, published, dismissed}`; `acknowledged → {acted_on, published, dismissed}`. `acted_on` and `published` are both terminal but represent different actions (rule change vs team-doc share); the same insight typically picks one path. Status changes are recorded by appending a `{id, ts, kind: "status_change", status: <new>}` row — the original insight row is never mutated (append-only audit trail).

**`published` semantics**: triggered by `/h-publish-insight`, which writes the insight as a git-tracked `.claude/wiki/insights/<date>_<id>_<slug>.md` doc. This is the bridge between single-machine local Insight Layer and team-shared knowledge. **It must be a deliberate user action** — no hook, detector, or other command auto-fires `/h-publish-insight`, because publishing is the moment a user decides "the team should know this".

## /h-evolve Proposal Format

`/h-evolve --insight-id <id>` produces (without modifying any file):

```
[evolve-proposal] insight=<id>

Summary:          <insight summary>
Suggested action: <insight suggested_action>

Proposed change:
  File:   <path>
  Locate: <line range or grep pattern>
  Replace/Add:
    <new content>

Rationale:
  Evidence:
    - <bullet list from insight.evidence>
  Risk if applied:     <one line>
  Risk if NOT applied: <one line>

To apply:   confirm and the agent will Edit; status updates to acted_on on success.
To dismiss: status updates to dismissed.
```

## /h-publish-insight Output Path

`/h-publish-insight --insight-id <id>` writes:

```
.claude/wiki/insights/<YYYY-MM-DD>_<short-id>_<slug>.md
```

with the agent-drafted markdown described in `.claude/commands/h-publish-insight.md` Step 4.

## insights.jsonl vs events.jsonl

- **events.jsonl** holds raw observations (one line = one event, no judgment)
- **insights.jsonl** holds second-order inferences (one entry = aggregated judgment from multiple events / failures)

Insight `evidence` references events with `{kind: "event", ts: "...", file_path: "..."}` and failures with `{kind: "failure", pattern: "...", gate: "..."}`.

## When Detectors Run

| Trigger | Effect |
|---|---|
| `/h-context-check` | invokes `insight_detector --write` to refresh active insights, then queries top high+medium for display |
| `/h-evolve` | explicit invocation; no auto-fire |
| Periodic / cron | not implemented in this baseline; add via `--auto-run` if needed |

## Anti-Patterns

- **Do NOT** let any insight_detector modify a configuration file, hook, or `CLAUDE.md` directly — all rule changes go through `/h-evolve` + human approval
- **Do NOT** block tool calls based on an insight — that is the Enforce layer's job (PreToolUse secrets pre-check + `/h-gates --phase ...`)
- **Do NOT** write hand-crafted rows into `insights.jsonl` — keep human-authored data and auto-detector output separate (use `.claude/wiki/insights/` for human-authored team docs)
