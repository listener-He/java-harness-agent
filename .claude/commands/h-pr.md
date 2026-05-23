---
description: Create a pull request from the current task — pre-gate, build PR body from task_brief, gh pr create, write PR number back to launch_spec
argument-hint: [slug] [--base <branch>] [--draft]
---

Close the downstream gap between Archive and merge. Builds a PR whose body is generated from the task_brief (Human Section + AC summary + Plan Deviation Reflection), runs pre-PR gates, and writes the PR URL back into the launch_spec. Requires `gh` CLI.

## Step 1 — Resolve target task_brief

- If `$ARGUMENTS` contains a slug → resolve `.claude/runs/task-briefs/*_<slug>_task_brief.md` (latest matching).
- Else → `python3 .claude/scripts/harness/find_active_task_brief.py`.
- Neither yields a path → STOP: `No active task_brief — pass slug as argument or ensure launch_spec has an IN_PROGRESS row`.

Read the brief in full. Capture: slug, risk, spec_mode, §1 Context (title line), §7 ACs, Plan Deviation Reflection (if present), `ticket_ref` / `ticket_url` from frontmatter (if present from h-from-ticket).

## Step 2 — Parse remaining `$ARGUMENTS`

- `--base <branch>` (optional): target branch for the PR. When absent, apply detection rule below.
- `--draft` (optional): create as a draft PR.

**Base branch detection** (fires only when `--base` was not provided):

```bash
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
RELEASE_BRANCHES=$(git branch -r --list 'origin/release/*' 'origin/release-*' 'origin/hotfix/*' | sed 's|origin/||' | xargs)
```

| Detection result | Action |
|---|---|
| No release/hotfix branches found | Use `$DEFAULT_BRANCH` silently; record in [Report] block |
| At least one release/hotfix branch found | invoke `AskUserQuestion` block below |

**Release branch confirm** AskUserQuestion:

```
Q: Active release/hotfix branches detected. Pick PR base:
- <DEFAULT_BRANCH> (recommended) — feature PR or routine fix
- <first release branch> — hotfix targeting active release line
- <second release branch, if exists> — hotfix targeting that release line
```

Cap at 3 manual options so Claude Code's auto-appended `Other` (free-text branch name) fits within `maxItems: 4`. If more than 2 release branches exist, list the two most recent and rely on `Other` for the rest. Do NOT add a manual option whose label starts with "Other" — it visually collides with the auto-appended `Other` slot.

## Step 3 — Pre-PR gates

Run both gates. Do not skip.

```bash
# Gate 1 — Secrets
python3 .claude/scripts/gates/secrets_linter.py --paths "$(git diff --name-only HEAD)"
```
```bash
# Gate 2 — Scope audit (full diff against Allowed Scope)
python3 .claude/scripts/gates/scope_guard.py --task-brief <brief path>
```

For each gate:
- exit 0 → OK, continue
- exit 1 → WARN — surface to user, ask whether to proceed or fix first. Do not auto-proceed on WARN.
- exit 2 → FAIL — STOP. Do not create the PR until the failure is resolved. Report the exact gate output.

Also check for uncommitted changes:
```bash
git status --porcelain
```
If non-empty → STOP: `Uncommitted changes detected. Commit or stash before creating PR.`

## Step 4 — Build PR title

Format: `<type>(<scope>): <brief title>`

- `<type>`: infer from task_brief §5 Business Logic or labels — `feat` / `fix` / `refactor` / `chore` / `docs`. Default `feat` if uncertain.
- `<scope>`: derive from primary Allowed Scope path (e.g. `order`, `auth`, `payment`).
- `<brief title>`: first non-blank line of §1 Context (the one-sentence task name). Strip trailing period.

Cap at 72 characters. If over limit → truncate title to 68 chars + `...`.

## Step 5 — Build PR body

Compose from task_brief sections in this order:

```markdown
## Summary
<§1 Context — 2-3 sentences from the Human Section rationale>

## Acceptance Criteria
<§7 ACs as a checkbox list — one line per AC, trimmed to the "then" clause for readability>
- [ ] AC-1: <observable outcome>
- [ ] AC-2: <observable outcome>
...

## Plan Deviations
<## Plan Deviation Reflection content, or "None — implemented as specified.">

## Links
<If ticket_ref present from h-from-ticket frontmatter:>
- Closes <ticket_url> (<ticket_ref>)
<If no ticket, omit this section entirely>

---
*Generated from task_brief: `<relative brief path>`*
```

Do NOT include Machine Section content (Allowed Scope, Hard Constraints) — those are AI-internal. The PR body is for human reviewers.

## Step 6 — Confirm with user

Show the composed title and body inline. Ask via `AskUserQuestion`:
- "Does this PR description look correct?"
  - Yes, create PR
  - Edit title/body first (I'll describe changes)
  - Cancel

If user selects "Edit" → ask for the changes via a follow-up question, apply them, show the revised version, and ask for confirmation again. Maximum 2 edit rounds before stopping and asking user to edit the brief directly.

## Step 7 — Create PR

```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --base <base-branch> \
  [--draft]
```

Capture the PR URL from stdout (format: `https://github.com/<owner>/<repo>/pull/<number>`). Extract PR number from URL.

If `gh pr create` exits non-zero → report stderr verbatim, STOP. Do not proceed to Step 8.

## Step 8 — Write PR back to task_brief and launch_spec

**task_brief** — append a new section at the end of the file:
```markdown
## PR
- URL: <PR URL>
- Number: #<number>
- Base: <base-branch>
- Created: <YYYY-MM-DD>
- Status: open
```

**launch_spec** — in the latest `.claude/runs/launch-specs/launch_spec_*.md`, find this task's row and:
- Status stays `IN_PROGRESS` — do NOT transition to `WAITING_APPROVAL` (that status is reserved for the HIGH-risk Approval Gate between Review and Implement, per lifecycle.md). The PR-open state is tracked via the Artifact marker, not the status column — same pattern as the COLLAB marker.
- Append PR number to the `Artifact` column: `<brief path> | PR #<number>`
- `/h-archive` will flip `IN_PROGRESS` → `DONE` after merge. Until then, the PR marker is informational only.

## Step 9 — Report

Output exactly this block:

```
[PR Status]: CREATED | FAILED
[Task]: <slug>
[PR]: <PR URL>
[PR Number]: #<number>
[Base Branch]: <branch>
[Draft]: yes | no
[Gates]: secrets=<OK|WARN|FAIL>, scope=<OK|WARN|FAIL>
[launch_spec Status]: IN_PROGRESS (PR marker appended to Artifact column)
[Next Action]: <one sentence — e.g. "PR open for review. After merge, run /h-archive to flip IN_PROGRESS → DONE and complete the workflow loop.">
```

## Hard constraints

- **Allowed edits**: the resolved task_brief (append `## PR` section only), the target `launch_spec_*.md` row. NO source-code edits. NO wiki edits.
- **Do NOT create PR if any gate exits 2 (FAIL)** — the gates are there to prevent broken code from reaching review.
- **Do NOT proceed past Step 7 if `gh pr create` fails** — a failed PR creation must not write a `| PR #<n>` Artifact marker. Leave the row untouched until the PR is actually created.
- **Draft flag is sticky** — if `--draft` is set, create as draft. Do not auto-promote.
- **Ticket closure** (`Closes #<number>`) is only added when `ticket_url` is present in the brief frontmatter from h-from-ticket. Do not guess ticket numbers.
- Anti-loop: max 2 user edit rounds in Step 6, then STOP.
- This command does NOT run tests — tests belong in Phase 5 (QA). Run `/h-gates --phase qa` before this command if QA hasn't been completed.
