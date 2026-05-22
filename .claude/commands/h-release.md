---
description: Drive Scenario RELEASE — load/build release rules, version bump, changelog from WAL, tag, push, verify CI
argument-hint: [version] [--dry-run] [--refresh] [--base <branch>]
---

Execute the full release workflow per `.claude/rules/lifecycle.md` Scenario RELEASE. Wraps `.claude/skills-archive/release/SKILL.md` with project-specific pre-checks (launch_spec gate, WAL changelog) before delegating to the skill's Steps 0–8. Requires `gh` CLI and `mvn`.

## Step 1 — Parse `$ARGUMENTS`

- `[version]` (optional): semver string (e.g. `1.3.0`), or `patch` / `minor` / `major`. If omitted, ask in Step 4.
- `--dry-run` (optional): print all intended actions but do NOT execute git commit, tag, or push.
- `--refresh` (optional): force re-analysis of repo rules even if cached rule file exists (passed through to release skill Step 0).
- `--base <branch>` (optional): branch to release from. Default: `main` (or repo default).

## Step 2 — Read release skill

Read `.claude/skills-archive/release/SKILL.md` in full. This is mandatory per lifecycle.md Scenario RELEASE. The skill's Steps 0–8 are the execution backbone; this command wraps them with project-specific gates.

## Step 3 — Pre-release project gates

Run these before the skill's Step 0. All must pass (exit 0 or 1 WARN) before continuing.

### Gate A — Queue completeness
Read the latest `.claude/runs/launch-specs/launch_spec_*.md`. All rows must be `DONE` or `FAILED` — no `IN_PROGRESS`, `PENDING`, or `WAITING_APPROVAL` rows allowed.

If any non-terminal rows exist → STOP and report:
```
[Pre-Release Gate A FAIL]: launch_spec has unfinished work:
  - <slug> (status=<status>, risk=<risk>)
Resolve or defer these tasks before releasing.
```

If no launch_spec exists → proceed (clean-slate project).

### Gate B — Clean working tree
```bash
git status --porcelain
```
Non-empty → STOP: `Uncommitted changes detected. Commit or stash before releasing.`

### Gate C — On release branch
```bash
git rev-parse --abbrev-ref HEAD
```
Must equal `--base` value (default `main`). If not → STOP: `Not on release branch '<base>'. Switch branches or use --base.`

### Gate D — Secrets scan
```bash
python3 .claude/scripts/gates/secrets_linter.py --paths "$(git diff HEAD~1 HEAD --name-only)"
```
Exit 2 → STOP. Exit 1 (WARN) → surface, continue.

## Step 4 — Execute release skill Steps 0–3 (rules + version)

Follow the release skill's execution flow directly:

**Step 0 (skill):** Load or build release rules artifact under `.claude/runs/task-briefs/`. Pass `--refresh` if provided.

**Step 1 (skill):** Repo analysis — inspect version sources, registry, CI trigger, test gate, changelog convention.

**Step 2 (skill):** Write/update release rule artifact at `.claude/runs/task-briefs/<YYYYMMDD>_release-rules.md`.

**Step 3 (skill):** Determine version.
- If version arg provided → validate semver, use it.
- If `patch`/`minor`/`major` shorthand → compute from current version in pom.xml.
- If absent → show current version + computed variants, ask via `AskUserQuestion`.

## Step 5 — Generate WAL changelog

Before the skill's Step 5 (Release Notes), generate a changelog draft from WAL fragments written since the last git tag.

```bash
# Find last release tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Find WAL fragments written after last tag
if [ -n "$LAST_TAG" ]; then
  LAST_TAG_DATE=$(git log -1 --format="%ai" "$LAST_TAG" | cut -d' ' -f1 | tr -d '-')
  find .claude/wiki/wiki -name "*.md" -newer <(git show "$LAST_TAG":README.md 2>/dev/null || echo /dev/null) \
    -path "*/wal/*" | sort
else
  find .claude/wiki/wiki -name "*.md" -path "*/wal/*" | sort
fi
```

Group found WAL fragments by dimension prefix:
- `*_api_*.md` → **API Changes**
- `*_domain_*.md` → **Domain / Business Logic**
- `*_data_*.md` → **Data / Schema**
- `*_architecture_*.md` → **Architecture**
- `*_rules_*.md` → **Business Rules**

Write draft changelog to `.claude/wiki/archive/<version>_changelog.md`:
```markdown
# Changelog — v<version>
Released: <YYYY-MM-DD>

## API Changes
<summary from api WAL fragments, or "None">

## Domain / Business Logic
<summary from domain WAL fragments, or "None">

## Data / Schema
<summary from data WAL fragments, or "None">

## Architecture
<summary from architecture WAL fragments, or "None">

## Business Rules
<summary from rules WAL fragments, or "None">
```

If no WAL fragments found since last tag → write a single-line changelog: `No structured WAL fragments found. Update manually if needed.`

Present the draft changelog to the user via `AskUserQuestion`:
- "Does this changelog look accurate for v<version>?"
  - Yes, use it
  - Edit it (I'll describe changes)
  - Skip — I'll write release notes manually

If user selects "Edit" → apply changes, re-present. Maximum 2 rounds.

## Step 6 — Execute release skill Steps 4–6 (checklist + notes + execute)

**Step 4 (skill):** Present pre-release checklist. Ask user to confirm before executing.

**Step 5 (skill):** Release notes — use the WAL changelog from Step 5 of this command as the draft. Follow the skill's release notes guidance for final polish.

**Step 6 (skill):** Execute release (unless `--dry-run`):

1. Version bump in `pom.xml`:
   ```bash
   mvn versions:set -DnewVersion=<version> -DgenerateBackupPoms=false -q
   ```
2. Run tests:
   ```bash
   mvn test -q
   ```
   If tests fail → STOP. Do not proceed to commit. Report failure output.

3. Commit (unless `--dry-run`):
   ```bash
   git add pom.xml .claude/wiki/archive/<version>_changelog.md
   git commit -m "chore(release): bump version to v<version>"
   ```

4. Tag (unless `--dry-run`):
   ```bash
   git tag -a v<version> -m "Release v<version>"
   ```

5. Push (unless `--dry-run`):
   ```bash
   git push origin <base-branch>
   git push origin v<version>
   ```

**`--dry-run` mode:** Print each of the above commands with a `[DRY RUN]` prefix. Do NOT execute them. Report what would happen.

## Step 7 — Post-release verification (skill Steps 7–8)

**Step 7 (skill):** First-time setup suggestions if gaps found during analysis.

**Step 8 (skill):** Verify after push:
```bash
# Check CI triggered
gh run list --limit 3 [--repo <repo>]

# Confirm tag exists on remote
gh release view v<version> 2>/dev/null || echo "GitHub Release not yet created (CI may create it)"
```

Wait up to 30 seconds for the release CI run to appear. If not visible → note that CI may take longer; user can check manually.

## Step 8 — Update launch_spec and archive rule artifact

In the latest launch_spec, add a new row for the release:
```
| release-v<version> | LOW | Archive | DONE | none | .claude/wiki/archive/<version>_changelog.md |
```

Move the release rule artifact from `.claude/runs/task-briefs/` to `.claude/wiki/archive/` if the skill created it:
```bash
python3 .claude/scripts/tools/archive_session_artifacts.py --slug release-rules
```

## Step 9 — Report

Output exactly this block:

```
[Release Status]: COMPLETE | DRY-RUN | FAILED
[Version]: v<version>
[Tag]: v<version>
[Branch]: <base-branch>
[Changelog]: .claude/wiki/archive/<version>_changelog.md
[WAL Fragments Included]: <N (from <LAST_TAG> to HEAD)>
[Pre-Release Gates]: queue=<OK|FAIL>, clean=<OK|FAIL>, branch=<OK|FAIL>, secrets=<OK|WARN|FAIL>
[mvn test]: PASS | FAIL | SKIPPED (dry-run)
[git push]: DONE | SKIPPED (dry-run) | FAILED
[CI Run]: <run URL or "pending">
[GitHub Release]: <URL or "pending CI">
[Next Action]: <one sentence — e.g. "Monitor CI at <url>; GitHub Release will be created automatically on tag push." or "Fix test failures before releasing.">
```

## Hard constraints

- **`--dry-run` is non-destructive**: in dry-run mode, zero git operations are executed — no commit, no tag, no push.
- **Tests MUST pass before commit**: skipping the test run requires `--dry-run`. If tests fail, do NOT proceed. Report the failure.
- **Gate A (queue completeness) is non-negotiable**: releasing with open tasks in the queue contaminates the changelog and creates ambiguity about what's in the release.
- **No source-code edits**: only `pom.xml` (version bump), `CHANGELOG.md` (if repo uses it), and `.claude/wiki/archive/<version>_changelog.md`.
- Anti-loop: max 2 retries on `mvn test` (flaky infra); third failure → STOP and ask user.
- This command does NOT force-push. If `git push` fails due to conflict → STOP and report. Resolve the conflict manually.
