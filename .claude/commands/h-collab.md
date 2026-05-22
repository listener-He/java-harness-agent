---
description: Generate a cross-team collaboration deliverable from task_brief — draft document, create collab state file, mark task pending external review
argument-hint: <slug> [--type api|process|data|integration|custom]
---

Generate a structured collaboration deliverable for external teams (frontend, third-party, QA, ops). This command handles **internal generation and tracking only** — sharing with the external team is manual. After generating, copy the deliverable path from the report and send via your preferred channel.

Run between Propose and Implement when the task requires external alignment before code is written.

## Step 1 — Parse `$ARGUMENTS`

- `<slug>` (required): task slug. Resolves to `.claude/runs/task-briefs/*_<slug>_task_brief.md`.
- `--type api|process|data|integration|custom` (optional): deliverable type. If omitted, inferred in Step 3.

If slug missing → STOP: `Pass the task slug as first argument.`

Check collision: if `.claude/runs/collabs/*_<slug>_collab.md` already exists → read it. If `status: SIGNED_OFF` → STOP: `Collab for <slug> already signed off. Run /h-collab-update <slug> to add follow-up.` If status is anything else → ask via `AskUserQuestion`: "A collab for this slug already exists (status: <status>). Overwrite draft or continue from existing?" Overwrite → proceed. Continue → jump to Step 7 to show current state.

## Step 2 — Read task_brief

Resolve and read the full task_brief for `<slug>`. Capture:
- `risk`, `dimensions`, `spec_mode`
- §1 Context (task name + rationale)
- §5 Business Logic
- §7 Acceptance Criteria
- §8 Technical Architecture (if present)
- §9 Design Patterns (if present)
- Any `ticket_ref` / `ticket_url` from frontmatter (from h-from-ticket)

If task_brief not found → STOP: `No task_brief found for slug <slug>. Run /h-brief <slug> first.`

## Step 3 — Infer or confirm deliverable type

**If `--type` provided** → use it.

**If not provided** → infer from task_brief:
- `dimensions` contains `api` OR §8 has endpoint definitions → `api`
- §5 Business Logic describes multi-party flow (keywords: 流程, 串联, 触发, 状态机, upstream, downstream) → `process`
- §5 or §8 mentions field mapping, schema alignment, data dictionary → `data`
- §1 mentions third-party / 第三方 / external system → `integration`
- None of the above → ask via `AskUserQuestion`:
  - "What kind of collaboration deliverable do you need?"
  - `api` — Interface contract (endpoints, request/response, error codes)
  - `process` — Business process alignment (flow steps, decision points, party responsibilities)
  - `data` — Data / field mapping confirmation (schemas, enums, field names)
  - `integration` — Third-party integration spec (what each side provides/expects)
  - `custom` — Freeform (I'll describe the content)

## Step 4 — Gather content gaps

For each type, check if the task_brief has sufficient content. If gaps exist, ask targeted questions via `AskUserQuestion` before generating.

**`api` type** — gaps: no §8 endpoint definitions
- Ask: "List the endpoints involved (method + path + one-line purpose). E.g. `POST /api/orders — create order`"

**`process` type** — task_brief rarely has process flow detail
- Ask: "Describe the business flow as numbered steps. For each step, who triggers it and what does the other party receive?"

**`data` type** — gaps: no field mapping in brief
- Ask: "List the fields to align: field name / type / source system / target system / notes."

**`integration` type** — gaps: no third-party contract in brief
- Ask two questions:
  1. "What does our system provide to the third party? (endpoints, callbacks, data format)"
  2. "What do we expect from the third party? (webhooks, response format, auth method)"

**`custom` type** — always ask:
- "Describe the content this deliverable should cover."

Save gathered answers to use in Step 5. These become part of the collab state so future sessions can reconstruct without re-asking.

## Step 5 — Generate deliverable draft

Write `.claude/runs/collabs/<YYYYMMDD>_<slug>_deliverable.md` using the type-appropriate template:

---
**`api` template:**
```markdown
# API Contract — <task name>
Generated: <YYYY-MM-DD> | Task: <slug> | Status: DRAFT

## Overview
<§1 Context rationale — 2 sentences>

## Endpoints

### <METHOD> <path>
**Purpose:** <one line>
**Request:**
| Field | Type | Required | Description |
|---|---|---|---|
| ... | ... | ... | ... |

**Response 200:**
| Field | Type | Description |
|---|---|---|
| ... | ... | ... |

**Error Codes:**
| Code | Condition |
|---|---|
| 400 | ... |

## Breaking Changes
<list any changes vs previous version, or "None — new interface">

## Open Questions
<leave blank — filled by /h-collab-update>
```

---
**`process` template:**
```markdown
# Business Process Alignment — <task name>
Generated: <YYYY-MM-DD> | Task: <slug> | Status: DRAFT

## Flow Overview
<2-sentence summary of what this process achieves>

## Step-by-Step

| Step | Trigger | Our Side | External Side | Output |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

## Decision Points
<conditions where the flow branches>

## Error / Exception Handling
<what happens when a step fails — who retries, who notifies>

## Open Questions
<leave blank>
```

---
**`data` template:**
```markdown
# Data Alignment — <task name>
Generated: <YYYY-MM-DD> | Task: <slug> | Status: DRAFT

## Field Mapping

| Our Field | Type | Their Field | Type | Notes |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Enum Values
<list any enum fields with agreed values>

## Validation Rules
<constraints both sides must enforce>

## Open Questions
<leave blank>
```

---
**`integration` template:**
```markdown
# Integration Spec — <task name>
Generated: <YYYY-MM-DD> | Task: <slug> | Status: DRAFT

## What We Provide
<endpoints / callbacks / data format we expose>

## What We Expect
<webhooks / responses / auth / SLA we require from them>

## Authentication
<method, token lifetime, refresh mechanism>

## Error Handling
<retry policy, timeout, fallback behavior>

## Open Questions
<leave blank>
```

---
**`custom` template:**
```markdown
# Collaboration Document — <task name>
Generated: <YYYY-MM-DD> | Task: <slug> | Status: DRAFT

<content from user's description in Step 4>

## Open Questions
<leave blank>
```

## Step 6 — Create collab state file

Write `.claude/runs/collabs/<YYYYMMDD>_<slug>_collab.md`:

```yaml
---
slug: <slug>
type: api|process|data|integration|custom
status: PENDING_REVIEW
task_brief: .claude/runs/task-briefs/<date>_<slug>_task_brief.md
deliverable: .claude/runs/collabs/<YYYYMMDD>_<slug>_deliverable.md
created: <YYYY-MM-DD>
reviewers: ""
open_questions: []
feedback_log: []
signed_off_by: ""
signed_off_date: ""
---
```

Then update the launch_spec row for `<slug>`: append `| COLLAB:<YYYYMMDD>-<slug>` to the Artifact column. Status remains `IN_PROGRESS`.

## Step 7 — Report

Output exactly this block:

```
[Collab Status]: CREATED | EXISTING
[Slug]: <slug>
[Type]: api | process | data | integration | custom
[Deliverable]: .claude/runs/collabs/<YYYYMMDD>_<slug>_deliverable.md
[Collab State]: .claude/runs/collabs/<YYYYMMDD>_<slug>_collab.md
[launch_spec]: COLLAB marker appended to Artifact column

[Next Steps — Manual]
1. Open the deliverable and review the draft for accuracy.
2. Share it with the external team via your preferred channel (copy path above).
3. When they respond, run: /h-collab-update <slug>

[Implement is NOT blocked] — you may proceed to Implement while awaiting review.
Implement SHOULD be blocked only if the deliverable contains unresolved design decisions
that affect code structure. In that case, note it explicitly and wait for /h-collab-update --signoff.
```

## Hard constraints

- **Allowed edits**: new deliverable file, new collab state file, target `launch_spec_*.md` Artifact column only. No source-code edits. No task_brief edits.
- **External communication is manual** — this command generates a file. It does NOT send emails, Lark messages, or GitHub comments. That is by design (Option A scope).
- **Implement is not automatically blocked** — the COLLAB marker is informational. Whether to wait for signoff before coding is a human judgment call, stated clearly in the report.
- **Do NOT generate empty deliverables** — if Step 4 gaps cannot be filled (user skips all questions), STOP: `Insufficient content to generate a useful deliverable. Provide details for at least the core section.`
- Anti-loop: max 2 rounds of gap-filling questions (Step 4). If still insufficient after 2 rounds → STOP.
