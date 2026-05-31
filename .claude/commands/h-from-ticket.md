---
description: Ingest GitHub Issue / Jira / Linear ticket → task_brief + ambiguity check + launch_spec row. TRIGGER: ticket URL pasted. NOT FOR: PRD/EPIC (use /h-decompose).
argument-hint: <source> <ticket-ref> [--slim] [--risk low|medium|high]
---

Translate an external ticket into a workflow-ready task_brief skeleton. Covers the upstream gap between issue trackers and the Explorer phase. Requires `gh` CLI for GitHub sources.

## Step 1 — Parse `$ARGUMENTS`

Extract:
- `<source>` (required): `github | jira | linear | manual`. Reject any other value.
- `<ticket-ref>` (required):
  - `github`: issue number (e.g. `42`) or `<owner>/<repo>#<number>` for cross-repo
  - `jira`: ticket ID (e.g. `PROJ-123`)
  - `linear`: issue ID or URL
  - `manual`: any slug for naming purposes
- `--risk low|medium|high` (optional): explicit override
- `--slim` (optional): **alias for `--risk low`** — ergonomic shorthand, identical effect. Conflicts with `--risk medium|high` (STOP if both passed). `spec_mode` derives from risk: LOW → SLIM, MEDIUM/HIGH → STANDARD.

If `<source>` or `<ticket-ref>` are missing or invalid → STOP and ask user to re-invoke with corrected args.

Check collision: if `.claude/runs/task-briefs/*_<kebab-ticket-ref>_task_brief.md` already exists → STOP and report. Do not overwrite existing work.

## Step 2 — Fetch ticket content

**GitHub:**
```bash
gh issue view <number> --json title,body,labels,milestone,assignees,state \
  [--repo <owner/repo>]
```
Parse JSON output. Extract:
- `title` → candidate task name
- `body` → raw requirement text
- `labels[].name` → risk/type signals (e.g. `bug`, `enhancement`, `priority:high`, `breaking-change`)
- `milestone.title` → release context if present

If `gh issue view` fails (not found, auth error) → report stderr verbatim, STOP.

**Jira / Linear:**
Invoke `AskUserQuestion`:
- "Paste the ticket content (title + description + acceptance criteria if present)"
Write pasted content to `.claude/runs/decompositions/<YYYYMMDD>_<ticket-ref>_raw.md` before continuing.

**Manual:**
Invoke `AskUserQuestion`:
- "Describe the task — include what you want to build, why, and what done looks like."
Write to `.claude/runs/decompositions/<YYYYMMDD>_<ticket-ref>_raw.md`.

## Step 3 — Classify input

Run `input-classifier` skill INLINE on the fetched content. It emits an `[Intake]` block with `Input-Type` and `Route`.

- **PRD / multi-section spec** → report: `This ticket looks like a PRD. Run /h-decompose instead for multi-task breakdown.` STOP.
- **Bug / Signal** → note: `Routing as DEBUG scenario. Run /h-brief <slug> after root-cause analysis.` STOP.
- **Idea / Feedback / Compliance / Security** → continue to Step 4.

## Step 4 — Ambiguity gate

Dispatch `ambiguity-gatekeeper` with the raw ticket content.

- **PASS** → continue to Step 5.
- **FAIL** → relay every `[Must-Ask Questions]` item via `AskUserQuestion`. After user answers, re-enter Step 4 with the enriched content. Do NOT proceed until PASS.

## Step 5 — Infer risk

Priority (first match wins):
1. `--risk` arg → use it directly
2. `--slim` arg → LOW
3. GitHub labels: `breaking-change`, `security`, `migration`, `auth` → HIGH; `enhancement`, `feature` → MEDIUM; `bug`, `chore`, `docs` → LOW
4. Main agent's earlier `[Risk: LOW|MEDIUM|HIGH | Scenario: ...]` line in this conversation
5. Ask user via `AskUserQuestion` with three options (LOW / MEDIUM / HIGH) + descriptions. Do not silently default.

If risk = LOW → `spec_mode: SLIM`. MEDIUM/HIGH → `spec_mode: STANDARD`.

## Step 6 — Derive slug

Convert ticket-ref to kebab-case slug:
- GitHub: `<repo>-issue-<number>` (e.g. `api-issue-42`) or just `issue-<number>` for same-repo
- Jira: lowercase ticket ID with dashes (e.g. `proj-123`)
- Linear/manual: user-supplied ref as-is, normalized to kebab-case

## Step 7 — Bootstrap task_brief

Write `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` following `.claude/wiki/schema/task_brief_schema.md`.

**Ticket → brief field mapping:**
| Ticket field | Brief field |
|---|---|
| `title` | §1 Context (first line), Human Section task name |
| `body` / pasted description | §5 Business Logic (adapted, not copied verbatim) |
| `labels` / priority | `risk:` frontmatter |
| `milestone` | Human Section: target release context |
| Acceptance criteria lines (if present in body) | §7 AC — convert to Given/When/Then format |

For §7 ACs, apply detection rules in order (first match wins):

1. **Explicit "Acceptance Criteria" / "Definition of Done" / "验收标准" section** → convert each bullet to Given/When/Then.
2. **GitHub Issue task list** — lines matching `^[-*] \[ \]` (unchecked checkboxes, any nesting): each becomes a candidate AC. Rewrite each as Given/When/Then. Skip `^[-*] \[x\]` (already-done sub-tasks, not pending ACs). Example:
   - `- [ ] User can log in with email + password` →
     `Given a registered user with valid credentials, when they submit the login form, then they are authenticated and redirected to /home.`
   - When 4+ checkboxes are found AND none are clearly user-observable behavior (e.g. "Add unit tests", "Update README" — implementation tasks not ACs), fall through to rule 3 instead of fabricating Given/When/Then from chores.
3. **Neither pattern present** — write the placeholder:
   ```
   <!-- TODO(h-from-ticket): AC not found in ticket — define before Review phase. Source: <ticket-ref> -->
   ```

For SLIM spec: fill the 5 SLIM sections (Change Summary / Scope of Change / Risk & Rollback / Verification & Evidence).

Spec-floor sections (§1, §5, §6, §7) must be substantive or have named placeholders — no `N/A` or empty sections.

## Step 8 — Validate structure

```bash
python3 .claude/scripts/gates/task_brief_gate.py --require <brief path>
```
- exit 0 → continue
- exit 1 (WARN) → surface, continue
- exit 2 (FAIL) → revise once, re-run. Second FAIL → STOP and ask user.

## Step 9 — Bind to launch_spec

Locate or create `.claude/runs/launch-specs/launch_spec_<YYYY-MM-DD>.md` (same logic as `/h-brief` Step 6).

Append row:
```
| <slug> | <LOW|MEDIUM|HIGH> | Explore | PENDING | none | <brief path> |
```

Note: status starts as `PENDING`, phase is `Explore` (not `Propose`) because ticket-sourced briefs typically need Explorer work before Propose.

Also append to the brief's frontmatter:
```yaml
ticket_source: <source>
ticket_ref: <original ticket-ref>
ticket_url: <full URL if GitHub, else "manual">
```

## Step 10 — Report

Output exactly this block:

```
[Ticket Status]: IMPORTED | INCOMPLETE | FAILED
[Source]: github | jira | linear | manual
[Ticket Ref]: <original ref>
[Slug]: <derived slug>
[Risk]: LOW | MEDIUM | HIGH
[spec_mode]: SLIM | STANDARD
[Brief Path]: <path>
[Launch Spec]: <path> (row appended)
[AC Status]: EXTRACTED(<N> ACs) | PLACEHOLDER (missing from ticket)
[Ambiguity Gate]: PASS | PASS-after-<N>-questions
[task_brief_gate]: OK | WARN(<one-line>) | FAIL(<one-line>)
[Next Action]: Run Explorer phase inline (`local-code-intelligence` + `input-classifier`), then /h-design <slug> if MEDIUM/HIGH with architectural dimension, OR begin Implement directly if LOW. If §7 ACs are placeholders: fill them via conversation BEFORE moving past Explorer.
```

## Hard constraints

- **Allowed edits**: new task_brief, `.claude/runs/decompositions/<raw input file>`, target `launch_spec_*.md`. Nothing else.
- **No source-code edits**.
- **No silent risk defaulting** — risk MUST come from arg, labels, the main agent's `[Risk: ...]` line, or explicit user answer.
- **Refuse to overwrite** existing task_brief at the computed path.
- **PRD and Bug tickets are NOT handled here** — redirect to `/h-decompose` and DEBUG scenario respectively.
- Anti-loop: max 2 ambiguity-gate iterations (two rounds of Must-Ask questions). Third unresolved → STOP and report.
