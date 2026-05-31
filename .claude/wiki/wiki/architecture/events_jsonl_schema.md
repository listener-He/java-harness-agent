---
title: events.jsonl event stream schema
category: architecture
status: active
---

# events.jsonl — Unified Event Stream Schema

## Purpose

L1 (Sensor) layer output of the Sensor / Insight / Policy / Enforce architecture. All Claude Code hooks emit events to this file; the agent queries it on demand via `events_query.py` instead of receiving pushed inline context blocks per prompt.

## File Location

```
.claude/runs/local_intel/events.jsonl
```

- gitignored (lives under `.claude/runs/`)
- append-only JSONL (one event per line, UTF-8 no BOM)
- rotates to `events.jsonl.YYYY-MM-DD` when the file exceeds 10 MB

## Common Fields (every event)

| Field | Type | Notes |
|---|---|---|
| `ts` | string | ISO 8601 with timezone, e.g. `2026-05-31T14:23:01+0800` |
| `kind` | string | event type — see below |

Extra fields are free-form per `kind`; the writer does not validate them and queries project as needed.

## Event Kinds

### `prompt` — user submitted a prompt
| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string | ✓ | original prompt text, truncated to 2000 chars |
| `session_id` | string | — | Claude Code session id, if present in payload |

### `edit_pre` — Edit/Write about to fire
| Field | Type | Required | Notes |
|---|---|---|---|
| `file_path` | string | ✓ | target file (absolute or repo-relative) |
| `tool` | string | — | `Edit` or `Write` if inferable |
| `secrets_check` | string | — | `PASS`/`WARN`/`FAIL`/`SKIP` from secrets pre-check |
| `blocked` | bool | — | true iff secrets FAIL caused PreToolUse block |

### `edit_post` — Edit/Write completed
| Field | Type | Required | Notes |
|---|---|---|---|
| `file_path` | string | ✓ | the file just written |
| `tool` | string | — | `Edit` or `Write` |
| `success` | bool | — | default true |

### `read` — Read tool completed
| Field | Type | Required | Notes |
|---|---|---|---|
| `file_path` | string | ✓ | the file read |
| `tracked` | bool | — | true iff path is under `.claude/wiki/**` or `.claude/skills/**` (usage_tracker bumped) |

### `subagent_return` — sub-agent finished a turn
| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string | ✓ | sub-agent's final assistant message, truncated to 4000 chars |
| `transcript_path` | string | — | original JSONL transcript path, if available |

### `turn_end` — main agent finished a turn
| Field | Type | Required | Notes |
|---|---|---|---|
| `branch` | string | — | current git branch |
| `head` | string | — | current short HEAD commit |
| `dirty_files` | int | — | `git diff --name-only` line count |

### `notification` — Claude Code UI notification fired
| Field | Type | Required | Notes |
|---|---|---|---|
| `message` | string | ✓ | from payload.notification / .message / .title |
| `notif_type` | string | — | payload's `type` field (e.g. `permission` / `idle`) |
| `session_id` | string | — | Claude Code session id |

### `compact` — Claude Code about to compress context
| Field | Type | Required | Notes |
|---|---|---|---|
| `branch` | string | — | current branch |
| `head` | string | — | current short HEAD |
| `active_task_brief` | string | — | active task_brief path |
| `in_progress_slugs` | list[string] | — | launch_spec slugs with status `IN_PROGRESS` |

### `env_bypass` — user/agent invoked an env var to bypass a hook
| Field | Type | Required | Notes |
|---|---|---|---|
| `env_var` | string | ✓ | e.g. `CLAUDE_SECRETS_BYPASS`, `CLAUDE_SCOPE_GUARD_BYPASS` |
| `hook` | string | ✓ | affected hook (e.g. `pre_tool_use_hook`) |
| `file_path` | string | — | target file at the time of bypass |

Emitted by `pre_tool_use_hook` when an env bypass is detected. Consumed by the `override_drift` insight detector to surface "gate is bypassed too often" patterns.

### `user_correction` — prompt opens with a correction phrase
| Field | Type | Required | Notes |
|---|---|---|---|
| `correction_phrase` | string | ✓ | exact matched phrase (e.g. `wrong`, `actually`, `不对`) |
| `prompt_excerpt` | string | ✓ | first 100 chars of the prompt |
| `session_id` | string | — | shared with the same-turn `prompt` event |
| `prior_actions_5min` | int | — | count of `edit_post` + `subagent_return` events in the prior 5 minutes |

Emitted by `user_prompt_submit_hook` when the prompt's first 50 characters start with a known correction/frustration phrase. Consumed by the `user_correction` insight detector; the `prior_actions_5min` field filters out spurious correction-style openings when the agent had not actually acted yet.

## Naming Conventions

- Snake case for field names (`file_path`, `dirty_files`, `session_id`)
- Paths written as received from the payload (no abspath normalization)
- `ts` is the only timestamp field; ISO 8601 with local timezone
- Long strings truncated to the cap noted per kind

## Writer API (`event_writer.py`)

```python
from event_writer import append

append("edit_post", file_path="src/foo/Bar.java", tool="Edit", success=True)
# Appends one line to events.jsonl:
#   {"ts": "2026-05-31T14:23:01+0800", "kind": "edit_post",
#    "file_path": "src/foo/Bar.java", "tool": "Edit", "success": true}
```

- `kind` is the only required positional argument
- Other fields are free-form kwargs
- All I/O errors are silenced (hook safety)
- No return value

## Query CLI (`events_query.py`)

| Command | Purpose |
|---|---|
| `events_query.py --kind edit_post --since 30m` | Recent edits in the last 30 minutes |
| `events_query.py --file src/Foo.java --last 50` | Last 50 events touching a path |
| `events_query.py --kind subagent_return --last 5` | Most recent sub-agent returns |
| `events_query.py --aggregate-by-kind --since 7d` | Count events grouped by kind |
| `events_query.py --kind edit_post --since 1h --json` | JSON output (machine-readable) |

Default output is human-readable text (one event per line). `--json` switches to a JSON array.

## Rotation Rules

| Trigger | Action |
|---|---|
| `events.jsonl` size > 10 MB (checked pre-write) | rename to `events.jsonl.YYYY-MM-DD`; new empty file takes over |
| A `events.jsonl.YYYY-MM-DD` already exists | append numeric suffix: `.YYYY-MM-DD.1`, `.YYYY-MM-DD.2` |

Old rotated files are not garbage-collected automatically — handle via cron or manual cleanup if you keep this around for long.

## What NOT to Log

- Secrets bypass IS logged via `env_bypass`, but never log the bypassed content itself.
- The writer does NOT scan content for secrets. Sanitization is the caller's responsibility (e.g., `user_prompt_submit_hook` truncates to 2000 chars but does not strip credentials — if a user pastes a token, it lands here).

## Relationship to Other Sidecars

| Sidecar | Status |
|---|---|
| `failure_memory.json` | retained — gate failure ledger; events_query can join via tooling, not built-in |
| `notifications.jsonl` | retained — Claude Code notification dedicated sink; this file also receives a parallel `notification` event |
| `last_compact_snapshot.json` + `compact_snapshots/` | retained — PreCompact-specific snapshot of recoverable state |
| `.usage/` | retained — `usage_tracker.py` per-file read counters |

events.jsonl is the unified context stream; the others are domain-specific sinks the agent can also query directly.
