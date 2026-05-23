---
description: Force Propose-phase design pipeline — dispatch system-architect, write ADRs (HIGH), fill brief §8/§9
argument-hint: [slug]
---

Drive the design work that turns an empty task_brief skeleton (post-`/h-brief`) into a contract that's ready for Review. Bundles: (1) dispatch `system-architect` sub-agent with the correct contract, (2) enforce ADR count per risk tier, (3) update the brief's Technical Architecture / Design Patterns sections, (4) re-validate.

## Step 1 — Resolve target task_brief

- If `$ARGUMENTS` is non-empty: treat as slug → `.claude/runs/task-briefs/*_<slug>_task_brief.md` (latest matching).
- Else: `python3 .claude/scripts/harness/find_active_task_brief.py`.
- Neither yields a path → STOP, report `No active task_brief — run /h-brief <slug> first`.

Read the brief in full. Capture:
- Frontmatter: `spec_mode`, `risk`, `dimensions`
- §1 Context, §5 Business Logic, §6 Non-Functional Constraints, §7 Acceptance Criteria
- Current state of §8 / §9 (placeholders or substantive)

## Step 2 — Validate that design work is warranted

| Brief state | Action |
|---|---|
| `spec_mode: SLIM` (LOW risk) | invoke `AskUserQuestion` "SLIM routing" block below |
| `risk: MEDIUM`, §8 already substantive (no `TODO(h-brief)` markers) | invoke `AskUserQuestion` "already-designed" block below |
| `risk: HIGH`, §8 ADR section finalized (either ≥1 ADR file linked OR explicit `Mechanical implementation — no irreversible architectural decision; no ADR required.` line) | invoke `AskUserQuestion` "already-designed" block below |
| `risk: MEDIUM` or `HIGH`, §8/§9 placeholder or missing (when dimension declared) | Proceed to Step 3. |

**SLIM routing** AskUserQuestion:

```
Q: Brief is spec_mode: SLIM. SLIM does not carry §8/§9 architecture sections. How to proceed?
- Edit SLIM sections directly (recommended) — open the brief, fill the 5 SLIM sections without dispatching architect
- Force re-classification — STOP /h-design; user re-runs the brief-scaffold command with --risk medium|high first
```

**Already-designed** AskUserQuestion:

```
Q: §8/§9 already substantive (last edited <ISO timestamp from git log>). Re-design risks scope creep. How to proceed?
- Keep current design (recommended) — STOP /h-design; resume next phase
- Force re-design — delete §8 (and §9 if present) inline, then proceed to Step 3 dispatch
```

User picks "Force re-design" → main agent deletes the matching section bodies in-place (leave headers), then continues to Step 3. Any other choice → STOP with no state change.

## Step 3 — Build dispatch prompt and invoke `system-architect`

Strictly from `.claude/rules/dispatch-template.md`. The `system-architect` agent explicitly ESCALATEs if the `## Source Documents` section is missing or paraphrased — every line in that section MUST be a `path#L<a>-L<b>` pointer or `VERBATIM:"""..."""` quote.

Fill:

- **Allowed Scope**:
  - The resolved task_brief (the architect will edit §8 / §9 inside it)
  - `.claude/wiki/wiki/architecture/adr/` (HIGH only — ADR file writes go here)
- **Source Documents** (MUST READ):
  - The resolved task_brief with `#L<a>-L<b>` covering §1 Context + §5 Business Logic + §6 Non-Functional + §7 Acceptance Criteria — NOT summarized
  - For each path/prefix in §1 "Scope of Change", add a pointer (line range if known, full file otherwise) so the architect designs against real code, not the brief's restatement
  - Any `[Intake]` block, requirement-engineer return, or PRD reference present earlier in this conversation — copy in as `VERBATIM:"""..."""` if no file exists
- **Acceptance Criteria** (for the architect, distinct from brief AC):
  - AC-1: §8 Technical Architecture filled with substantive Component / Deployment / Third-party / Rationale content (no `TODO` markers) **IF** `tech_arch` in dimensions
  - AC-2: §9 Design Patterns Applied filled **IF** `patterns` in dimensions
  - AC-3 (HIGH only): EITHER ≥1 ADR file written per actual irreversible decision under `.claude/wiki/wiki/architecture/adr/ADR-NNNN-<slug>.md` (following `.claude/wiki/wiki/architecture/adr/template.md` with populated `## Alternatives Considered` Pros/Cons/Why-not and `## Consequences` Positive/Negative), OR §8 carries the explicit line `> Mechanical implementation — no irreversible architectural decision; no ADR required.` Architect MUST consciously decide which applies — silently producing zero ADRs is NOT acceptable.
  - AC-4 (HIGH only): §8 either references the ADRs by file path OR carries the verbatim "mechanical" note
- **Hard Constraints**:
  - MEDIUM: produce exactly 1 option with explicit rationale + constraint list
  - HIGH: produce 2–3 alternatives, then state which is chosen and why
  - Do NOT edit source code under `src/` — architect is design-only
  - Do NOT touch ADR template, README, or index.md
- **Memory Snapshot**: copy relevant `type=user` / `type=feedback` entries (especially anything about API design preferences, persistence patterns, or stack choices).

Dispatch the agent. Wait for return.

## Step 4 — Validate sub-agent return

```
python3 .claude/scripts/gates/subagent_return_gate.py --return-file <tmp> --task-kind extract
```

(Use `--task-kind extract` because architect's output pattern — files-changed + ACs-mapped — matches the extract template most closely; the gate validates structure, not semantic category.)

- exit 0 → continue
- exit 1 (WARN) → surface, continue
- exit 2 (FAIL) → re-dispatch ONCE with corrected template; second FAIL → STOP

## Step 5 — Post-conditions check

Independently verify the architect's claimed work, do not trust `[Status]: PASS` alone:

1. **ADR coverage** (HIGH only): EITHER `ls .claude/wiki/wiki/architecture/adr/ADR-*-<slug>*.md | wc -l` ≥ 1 with each ADR linked from §8, OR §8 contains the verbatim line `Mechanical implementation — no irreversible architectural decision; no ADR required.` Neither present → reject the architect's return, ask for revision; second insufficient run → STOP.
2. **ADR structure** (HIGH only, when ADRs exist): each ADR file contains substantive `## Alternatives Considered` with ≥2 alternatives and `## Consequences` Positive + Negative sections. Missing → reject.
3. **§8 substantive** (if `tech_arch` in dimensions): no `TODO(h-brief)` or `TODO(h-design)` markers remain; Component / Deployment / Third-party / Rationale all populated.
4. **§9 substantive** (if `patterns` in dimensions): same check.
5. **§8 ADR links** (HIGH only): §8 body contains the actual ADR file paths.

Any check fails → ONE revision allowed; second failure → STOP and ask user.

## Step 6 — Re-validate brief structure

```
python3 .claude/scripts/gates/task_brief_gate.py --require <brief path>
```

- OK → proceed
- WARN → surface, proceed
- FAIL → STOP (the architect introduced a structural regression — surface the gate output for user to inspect)

## Step 7 — Report

Output exactly this block:

```
[Design Status]: COMPLETE | PARTIAL | FAILED
[Brief]: <path>
[Risk]: MEDIUM | HIGH
[Dimensions Touched]: <comma-separated of: tech_arch, patterns, ... or "none">
[Design Options Produced]: <N>
[ADRs Written]: <list of ADR-NNNN file paths, or "n/a (MEDIUM)">
[§8 Status]: SUBSTANTIVE | PLACEHOLDER | NOT-REQUIRED (tech_arch not declared)
[§9 Status]: SUBSTANTIVE | PLACEHOLDER | NOT-REQUIRED (patterns not declared)
[task_brief_gate]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Next Action]: <one specific sentence — e.g. "ready for Review phase: dispatch code-reviewer and adversarial-review Category B (HIGH)">
```

## Hard constraints

- **Allowed edits**: the resolved task_brief, ADR files under `.claude/wiki/wiki/architecture/adr/` (HIGH only). NOTHING ELSE — explicitly NO source code, NO wiki indexes, NO ADR template / README.
- **No re-design**: refuse to run if §8/§9 are already substantive (Step 2 table). The deliberate way to revise is to delete the section first, then re-invoke.
- **HIGH risk + no ADRs AND no explicit "mechanical" §8 note is a hard fail** — the discipline is to *consciously decide* whether an irreversible decision exists, not to skip the question. Silently producing zero ADRs without the mechanical note = reject.
- **Dispatch-template is non-negotiable**: system-architect agent ESCALATEs on missing `## Source Documents`. Build the prompt correctly the first time — do not paraphrase brief content into the prompt.
- Anti-loop: max 1 revision per gate (Step 4, Step 5, Step 6). Second failure of the same gate → STOP.
- This command does NOT invoke `adversarial-review` Category B — that belongs to Phase 3 (Review), not Propose. Keep phase boundaries clean.
