# Dispatch Prompt Template

Canonical skeleton for every sub-agent prompt. The main agent fills in placeholders — it MUST NOT write dispatch prompts from scratch. The receiving sub-agent MUST validate this structure before doing any work; missing sections → return `[Status]: ESCALATE` with the missing section name.

Why this exists: sub-agents do NOT inherit `CLAUDE.md`, project rules, memory, or anti-loop limits. The dispatch prompt is the *only* contract they see. Free-form prompts lead to forgotten constraints and unparseable returns.

---

## Template (copy verbatim, fill the `<…>` placeholders)

```
# Dispatch: <role-name>

## Task Contract
**Allowed Scope** (verbatim from task_brief — file paths/prefixes, one per line):
- <path-or-prefix-1>
- <path-or-prefix-2>

**Acceptance Criteria** (Given/When/Then, copied from task_brief; assign each an AC-id):
- AC-1: Given <…>, when <…>, then <…>.
- AC-2: Given <…>, when <…>, then <…>.

**Hard Constraints** (invariants the sub-agent MUST NOT violate):
- <constraint-1>
- <constraint-2>

## Inputs
- Task brief: <.claude/runs/task-briefs/…_task_brief.md>
- Files to inspect/modify: <comma-separated paths or "see Allowed Scope">
- Commit range / line numbers (if applicable): <…>
- Other inputs: <…>

## Memory Snapshot (sub-agent does NOT inherit auto-memory — main agent copies relevant entries here)
- type=user: <key user identity / role / preferences that affect this task, or "none">
- type=feedback: <feedback rules the sub-agent must honor, e.g. "no single-file directory creation", or "none">
- type=project: <ongoing-work facts relevant to this task, or "none">

If a section has no relevant entries, write "none" — do not delete the section.

## Hard Limits (apply to YOU, the sub-agent — your context does NOT inherit them)
- MAX 3 retries per gate/linter run.
- MAX 2 retries for compile failures.
- After 2 same-root-cause failures: STOP, return `[Status]: ESCALATE`.
- DO NOT modify files outside Allowed Scope. If required, return `[Status]: BOUNDARY_EXCEPTION` with the file and reason — wait for main agent, do not edit.
- DO NOT bypass safety checks (`--no-verify`, `--no-gpg-sign`, etc.).
- DO NOT invoke other sub-agents. Return to the main agent for orchestration.

## Expected Output (structured — parseable by main agent)
Return ONLY this block, no preamble:

[Status]: PASS | PARTIAL | FAIL | ESCALATE | BOUNDARY_EXCEPTION
[Files Changed]: <list of relative paths with +N/-M line counts, or "none">
[Commands Run]: <each command + exit code, or "none">
[ACs Mapped]: <AC-id → test method or evidence → PASS/FAIL/SKIP>
[Issues Found]: <numbered list, or "none">
[Next Step]: <one sentence — what main agent should do next>

(If [Status] is ESCALATE or BOUNDARY_EXCEPTION, also include a [Reason]: line explaining why.)

## Template Source
This prompt was built from: .claude/rules/dispatch-template.md
```

---

## Validation rules (for the receiving sub-agent)

Before doing anything, check the incoming prompt has these sections (header lines):
- `## Task Contract` with all three subsections: Allowed Scope, Acceptance Criteria, Hard Constraints
- `## Inputs`
- `## Memory Snapshot`
- `## Hard Limits`
- `## Expected Output`

If any are missing OR if Allowed Scope is empty:
```
[Status]: ESCALATE
[Reason]: Dispatch prompt missing required section(s): <list>
[Next Step]: Main agent must re-dispatch using .claude/rules/dispatch-template.md
```

Do not attempt to fill in missing sections from inference. The contract must be explicit.

---

## Return validation (for the main agent — RUN AFTER RECEIVING)

After the sub-agent returns, the main agent MUST validate the return block before acting on it. Save the return text to a file (or pipe it), then run:

```bash
python3 .claude/scripts/gates/subagent_return_gate.py \
    --return-file <path> \
    --task-kind implement|review|extract|audit
```

Exit codes (per linter-severity-standard):
- **0 OK** — proceed
- **1 WARN** — return is structurally valid but has consistency warnings (e.g., `[Status]=PASS` with no files changed). Surface the WARN to the user; do not silently accept.
- **2 FAIL** — return is structurally broken or contains direct contradiction (`[Status]=PASS` with an AC row reporting FAIL). Re-dispatch the sub-agent with the original template; do not accept the result.

This gate catches a real failure mode: sub-agent claims `[Status]: PASS` while internal evidence ([Files Changed], [Commands Run], [ACs Mapped]) is empty or contradicts the claim. The validator runs in < 1s and burns ~50 tokens of context — well worth catching one bad return.

---

## When the template is NOT required

For LEARN/MAINTENANCE-only sub-agent dispatches (e.g., librarian, knowledge-architect doing read-only wiki ops), the `Hard Constraints` and `ACs Mapped` may be empty (`none`) — but the headers must still be present. This keeps the parsing contract uniform.

---

## Examples

### Example 1 — Dispatching lead-engineer

```
# Dispatch: lead-engineer

## Task Contract
**Allowed Scope**:
- src/main/java/com/example/order/
- src/test/java/com/example/order/

**Acceptance Criteria**:
- AC-1: Given an order with status=PENDING, when cancel() is called, then status becomes CANCELLED and event is published.
- AC-2: Given an order with status=SHIPPED, when cancel() is called, then BusinessException with code ORDER_NOT_CANCELLABLE is thrown.

**Hard Constraints**:
- No JPA cascade changes
- No new external dependencies
- Order entity table must not be altered (DDL frozen)

## Inputs
- Task brief: .claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md
- Files to inspect/modify: see Allowed Scope
- Other inputs: existing OrderService at src/main/java/com/example/order/OrderService.java

## Hard Limits
[…verbatim from template…]

## Expected Output
[…verbatim from template…]

## Template Source
This prompt was built from: .claude/rules/dispatch-template.md
```

### Example 2 — Dispatching code-reviewer

```
# Dispatch: code-reviewer

## Task Contract
**Allowed Scope**:
- (review-only — no edits)

**Acceptance Criteria**:
- AC-1: Given the diff in commit range abc123..def456, when reviewed, then no FAIL-severity findings remain.

**Hard Constraints**:
- Review must check java-architecture-standards Layer 1 violations
- Review must check security-review-checklist
- DO NOT modify code; report-only

## Inputs
- Task brief: .claude/runs/task-briefs/2026-05-19_order_cancel_task_brief.md
- Commit range: abc123..def456
- Files changed: src/main/java/com/example/order/OrderService.java (+45/-12), src/test/java/com/example/order/OrderServiceTest.java (+89/-0)

## Hard Limits
[…verbatim from template…]

## Expected Output
[…verbatim from template…]
```
