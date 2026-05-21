# Dispatch Prompt Template

Canonical skeleton for every sub-agent dispatch. The main agent fills `<…>` placeholders — do NOT write dispatch prompts from scratch. The receiving sub-agent validates the structure before working; missing sections → `[Status]: ESCALATE`.

Why this exists: sub-agents do NOT inherit `CLAUDE.md`, project rules, memory, or anti-loop limits. The dispatch prompt is the *only* contract they see. Free-form prompts lead to forgotten constraints and unparseable returns.

**Design principle (anti-bloat):** the dispatch prompt does NOT duplicate the task_brief. Allowed Scope, ACs, and Hard Constraints live in the brief — the dispatch points to it and the sub-agent reads it. This keeps prompts ~40 lines instead of ~100, and avoids the classic copy-paste drift between brief and prompt.

---

## Template (copy verbatim, fill the `<…>` placeholders)

```
# Dispatch: <role-name>

## Inputs
- **Task brief:** `<.claude/runs/task-briefs/…_task_brief.md>#L<machine-section-range>` — your contract. Allowed Scope, ACs (with AC-ids), and Hard Constraints all live in the Machine Section. **Read it FIRST.**
- Files to inspect/modify: <comma-separated paths, or "see Allowed Scope in task_brief">
- Commit range / line numbers (if applicable): <…>
- Other inputs: <…>

(For review-only dispatches with no task_brief — e.g. PR review on a commit range — replace the Task brief line with the commit range; Source Documents below carries the contract.)

## Source Documents (MUST READ before producing output)
Pointers, never summaries — paraphrasing here triggers Gresham's law for context (劣质上下文驱逐优质上下文). Each line MUST be ONE of:
- `<relative/path>[#L<a>-L<b>] — <one-line WHY>`
- `VERBATIM: """<逐字 quote — only when no source file exists, e.g. small Idea input; do NOT paraphrase>"""`

Required first entry: the task_brief Machine Section (or, for review-only, the diff endpoints).

Hard rule: if this section is missing, empty, or any line lacks both a `#L...` pointer AND a `VERBATIM:` prefix, return `[Status]: ESCALATE` with `[Reason]: Source Documents missing or summarized`.

## Memory Snapshot (auto-memory NOT inherited — main agent fills only entries relevant to THIS task)
- type=user: <or "none">
- type=feedback: <or "none">
- type=project: <or "none">

Default is "none". The main agent fills an entry only when an `auto-memory` record demonstrably affects how this specific task should be done. Pasting unrelated memory is noise — leave it out.

## Hard Limits (apply to YOU, the sub-agent — your context does NOT inherit them)
- MAX 3 retries per gate/linter run. MAX 2 retries for **in-scope** compile errors only — out-of-scope compile errors are pre-existing upstream issues; report `[Status]: PARTIAL` with `[Issues Found]: pre-existing compile error in <file:line>`, do NOT count toward retries, do NOT fix.
- After 2 same-root-cause failures → STOP, return `[Status]: ESCALATE`.
- Files outside Allowed Scope (see task_brief) → return `[Status]: BOUNDARY_EXCEPTION` with file + reason; wait for main agent. Do NOT edit.
- DO NOT skip mandatory `## Source Documents` reads. List every file you Read in `[Source Documents Read]`. Skipped read = `[Status]: ESCALATE`.
- DO NOT bypass safety checks (`--no-verify`, `--no-gpg-sign`). DO NOT invoke other sub-agents. DO NOT summarize when passing context downstream — use pointers + verbatim quotes.

## Expected Output (structured — parseable by main agent; return ONLY this block, no preamble)

[Status]: PASS | PARTIAL | FAIL | ESCALATE | BOUNDARY_EXCEPTION
[Files Changed]: <relative paths with +N/-M, or "none">
[Commands Run]: <each command + exit code, or "none">
[ACs Mapped]: <AC-id → test method or evidence → PASS/FAIL/SKIP>
[Source Documents Read]: <comma-separated paths you actually Read from the '## Source Documents' section, or "none">
[Issues Found]: <numbered list, or "none">
[Next Step]: <one sentence — what main agent should do next>

(If [Status] is ESCALATE or BOUNDARY_EXCEPTION, also include a `[Reason]:` line.)

The `[Source Documents Read]` field MUST list every file you opened with `Read` from `## Source Documents`. `subagent_return_gate.py` cross-checks this — leaving it "none" while the dispatch had pointers triggers a WARN.

## Template Source
.claude/rules/dispatch-template.md
```

---

## Validation rules (for the receiving sub-agent)

Before doing anything, check the incoming prompt has these section headers:
- `## Inputs` with a Task brief path (or a commit range / explicit description for review-only dispatch)
- `## Source Documents (MUST READ before producing output)` with at least one valid pointer or VERBATIM line
- `## Memory Snapshot`
- `## Hard Limits`
- `## Expected Output`

If any are missing OR the Task brief path is unset AND no review-only context is given:
```
[Status]: ESCALATE
[Reason]: Dispatch prompt missing required section(s): <list>
[Next Step]: Main agent must re-dispatch using .claude/rules/dispatch-template.md
```

Do not infer Allowed Scope / ACs / Hard Constraints from the prompt — read them from the task_brief Machine Section listed in `## Inputs`. The contract is in the brief, not the prompt.

---

## Return validation (for the main agent — RUN AFTER RECEIVING)

```bash
python3 .claude/scripts/gates/subagent_return_gate.py \
    --return-file <path> \
    --task-kind implement|review|extract|audit
```

Exit codes (per linter-severity-standard):
- **0 OK** — proceed
- **1 WARN** — structurally valid but with consistency warnings (e.g., `[Status]=PASS` with no files changed). Surface to user; don't silently accept.
- **2 FAIL** — structurally broken or contradictory (`[Status]=PASS` with an AC reporting FAIL). Re-dispatch; don't accept.

This catches a real failure mode: sub-agent claims `[Status]: PASS` while internal evidence ([Files Changed], [Commands Run], [ACs Mapped]) is empty or contradicts the claim.

---

## When the structure is relaxed

For LEARN/MAINTENANCE-only sub-agent dispatches (librarian, knowledge-architect doing read-only wiki ops):
- `## Inputs` Task brief line may be replaced with a description of the read-only scope (e.g., "wiki index `.claude/wiki/wiki/domain/index.md` plus its WAL fragments").
- `[ACs Mapped]` in return may be "none".
- All section headers MUST still be present — keeps the parsing contract uniform.

---

## Examples

### Example 1 — Dispatching lead-engineer

```
# Dispatch: lead-engineer

## Inputs
- **Task brief:** `.claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md#L40-L120` — your contract (Allowed Scope, ACs, Hard Constraints all in the Machine Section). Read first.
- Files to inspect/modify: see Allowed Scope in task_brief

## Source Documents (MUST READ before producing output)
- `.claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md#L40-L120` — Machine Section; the contract
- `src/main/java/com/example/order/OrderService.java#L80-L140` — current `cancel()` logic; do NOT break
- `src/main/java/com/example/order/OrderEvents.java` — event publisher you must reuse (no new bus)

## Memory Snapshot
- type=user: none
- type=feedback: none
- type=project: none

## Hard Limits
[…verbatim from template…]

## Expected Output
[…verbatim from template…]

## Template Source
.claude/rules/dispatch-template.md
```

### Example 2 — Dispatching code-reviewer (review-only)

```
# Dispatch: code-reviewer

## Inputs
- **Task brief:** `.claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md#L40-L120` — the contract you check the diff against (review-only; you do NOT modify)
- Commit range: `abc123..def456`
- Files changed: `src/main/java/com/example/order/OrderService.java` (+45/-12), `src/test/java/com/example/order/OrderServiceTest.java` (+89/-0)

## Source Documents (MUST READ before producing output)
- `.claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md#L40-L120` — contract; check diff against this
- `src/main/java/com/example/order/OrderService.java` — full post-change state
- `src/test/java/com/example/order/OrderServiceTest.java` — asserted behavior

## Memory Snapshot
- type=user: none
- type=feedback: none
- type=project: none

## Hard Limits
[…verbatim from template…]

## Expected Output
[…verbatim from template…]
```
