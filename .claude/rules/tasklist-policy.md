# TaskList Usage Policy

Single source of truth for **when to open Claude Code's built-in TaskList**, what granularity to use, and when to skip it entirely. Resolves overlap with the project's existing state machines: `launch_spec_*.md` (task-level status) and `task_brief.md` (phase-level state).

Background: TaskList is the agent's progress-tracking tool surfaced in Claude Code's UI. Used reflexively, it duplicates `launch_spec` and `task_brief` — costing ~2-3k tokens per STANDARD task with no behavior change. Used selectively, it covers two gaps the file-based state machines can't: **sub-task DAG visualization (EPIC)** and **AC-level granularity inside large Implement phases**.

**Reading rule:** consult this file before calling `TaskCreate`. If your trigger isn't in §1, skip TaskList — `launch_spec` already covers task-level state.

---

## §1 — When to OPEN TaskList (whitelist)

TaskList is opened ONLY when one of these triggers fires. Whitelist, not fallback.

| Trigger | Granularity | Reason it can't be replaced by file-based state |
|---|---|---|
| **Scenario EPIC** with ≥2 INVEST sub-tasks | One item per sub-task | `launch_spec` is a flat list; only TaskList visualizes parallel sub-task progress |
| **Implement phase** with **AC count ≥ 4** | One item per AC | AC granularity is below `launch_spec`; user needs "3/7 passing" feedback |
| **Approval Gate triggers** (HIGH risk only) | One "WAITING_APPROVAL" item until resolved | UI persistence prevents the user missing the approval request |
| **Scenario A (Emergency Hotfix)** | 1-2 items: `Emergency Justification written` + `secrets_linter clean` | Audit anchors — required artifacts must be visible in transcript |

That's the full list. Nothing else opens TaskList.

---

## §2 — When NOT to open TaskList (blacklist)

| Anti-trigger | Why no |
|---|---|
| STANDARD-MEDIUM full 6-phase tracking | `launch_spec` status + `task_brief` Phase already cover this — duplicate state machine |
| PATCH profile (Vibe / Patch modes) | Task is short; opening TaskList is decoration |
| LEARN profile | No work product; nothing to mark done |
| Single tool call (one Bash, one Edit) | TaskList unit is a user-observable interval, not a tool call |
| Sub-agent dispatch | The dispatch IS the atomic unit; don't wrap it |
| Hook execution / gate scripts | Automated, sub-second, no decision point |
| Memory writes / WAL fragment writes | Mechanical post-decision actions |
| Compile / test retries | Already bounded by anti-loop rules in CLAUDE.md |

**Hard rule:** if the work is shorter than ~5 minutes wall-clock OR has no human-visible intermediate state, do NOT open TaskList.

---

## §3 — Granularity rules

When TaskList is opened (per §1), follow these rules.

| Rule | Statement |
|---|---|
| **G1** | Never create a TaskList item below the granularity of a tool call. "Run `mvn compile`" is not a task. |
| **G2** | Never create a TaskList item that duplicates a `launch_spec` row. The launch_spec row IS the task. |
| **G3** | Every item must have a binary done condition. "Make progress on X" is forbidden; "AC-3 test passes" is required. |
| **G4** | Maximum 12 items concurrent. Beyond that, the user can't scan the list — decompose differently or move some to `launch_spec`. |
| **G5** | Mark `in_progress` BEFORE starting the work, `completed` IMMEDIATELY after. Batched updates defeat the visibility purpose. |
| **G6** | Never rewrite a completed item's title to reflect a later change. Cancel and create a new one. |
| **G7** | If a TaskList item's scope expands mid-task, split it — don't grow the existing one silently. |

---

## §4 — Composition with file-based state machines

TaskList does NOT replace any of these. It supplements when (and only when) §1 applies.

| State machine | Owns | TaskList must NOT |
|---|---|---|
| `launch_spec_*.md` | Task-level status (PENDING / IN_PROGRESS / WAITING_APPROVAL / DONE / FAILED) | Duplicate task-level rows |
| `task_brief.md` Phase field | Current lifecycle phase (Explorer / Propose / Review / Implement / QA / Archive) | Mirror phases for STANDARD-MEDIUM |
| `failure_memory.json` | Gate failure recurrence across days | Track retry attempts |
| Hooks (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`) | Scope guard, secrets lint, ambiguity gate, triage probe | Represent hook outcomes |

**Conflict resolution:** the file-based state machine always wins. If TaskList shows DONE but `launch_spec` shows IN_PROGRESS, trust `launch_spec` and correct TaskList — never the reverse. Same rule for `task_brief.md` phase mismatches.

---

## §5 — Budget guardrails

To catch policy misapplication before it costs tokens:

| Check | Threshold | Action if exceeded |
|---|---|---|
| Concurrent item count | > 12 | Decompose differently; some belong in `launch_spec`, not TaskList |
| Items created for non-EPIC task | > 8 | Audit against §1 — likely §2 violation; close items not justified |
| TaskUpdate calls per item | > 3 | Item granularity is wrong; either too coarse (multiple done-states) or rewriting titles (violates G6) |
| Item with zero progress for > 1 phase | — | Either blocked (escalate via `[Issues Found]`) or stale (cancel) |

These are tripwires, not laws — exceed them only with an explicit reason recorded in `task_brief` Plan Deviation Reflection.

---

## §6 — Decision flow (when in doubt)

```
1. Is the trigger in §1?              NO → do not open TaskList.
2. Does §4 already track this state?  YES → do not duplicate; reuse the file.
3. Would a human reviewer ever ask
   "where are we now?" before the
   next visible output?               NO → do not open TaskList.
4. All three pass                     → open TaskList, follow §3 granularity.
```

Default to NOT opening. Cost of an unnecessary TaskList is silent token burn; cost of a missing TaskList is one extra "what's your status?" question from the user — cheap to recover.

---

## §7 — Examples

### Example 1 — STANDARD-MEDIUM, single domain, 2 ACs
**Decision:** no TaskList.
**Rationale:** §1 has no matching trigger; `launch_spec` row + `task_brief` Phase field cover all visible state.

### Example 2 — STANDARD-HIGH, Implement phase has 6 ACs
**Decision:** open TaskList with 6 items, one per AC. Mark `in_progress` as RED test is written; `completed` as GREEN passes.
**Rationale:** §1 row 2 (AC ≥ 4).

### Example 3 — EPIC: PRD decomposed into 5 INVEST sub-tasks
**Decision:** open TaskList with 5 sub-task items at the start. Each sub-task internally may or may not open its own TaskList per §1.
**Rationale:** §1 row 1. `launch_spec` cannot visualize the DAG; TaskList is the only mechanism.

### Example 4 — HIGH risk task waiting on Approval Gate
**Decision:** open ONE item "Approval Gate: <task slug>" in `in_progress` state. Mark `completed` on user approval; cancel on rejection.
**Rationale:** §1 row 3. The launch_spec status WAITING_APPROVAL exists but is in a file the user must open — TaskList is persistent in the UI.

### Example 5 — PATCH: fix a typo in error message
**Decision:** no TaskList.
**Rationale:** §2 row 2 (PATCH). Single Edit + verify; <5 min.

---

## §8 — Maintenance

Update this file when:
- A new scenario in [lifecycle.md](lifecycle.md) introduces a sub-task DAG or human-wait state not covered by §1.
- A whitelisted trigger proves to be compliance theater in practice — close it from §1, add to §2 with the observation.
- A new file-based state machine is added that would conflict with TaskList semantics — extend §4.

When this file and a skill's individual TaskList recommendation disagree, **this file wins** — same conflict-resolution rule as [skill-precedence.md](skill-precedence.md).

When adopting this policy, add the row to `CLAUDE.md` Single Sources of Truth:

```
| TaskList usage (when to open / granularity) | [.claude/rules/tasklist-policy.md](.claude/rules/tasklist-policy.md) |
```
