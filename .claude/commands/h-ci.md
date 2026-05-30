---
description: TRIGGER on red CI run (GitHub Actions failure) OR user says 'CI 挂了' / 'pipeline failed' with run-id. NOT FOR: local test failures (use /h-fix-bug); known incident (use /h-incident). Returns: classified routing + failure_memory record + optional debug task or incident.
argument-hint: [--run-id <id>] [--repo <owner/repo>] [--from-file <path>]
---

Close the CI/CD feedback loop. Pulls failed CI run logs (via `gh`), classifies the failure type, routes it into the correct workflow channel (debug task, incident, or warn), and records it in failure_memory so future `[triage]` blocks surface the pattern. Requires `gh` CLI.

## Step 1 — Parse `$ARGUMENTS`

- `--run-id <id>` (optional): specific GitHub Actions run ID to ingest.
- `--repo <owner/repo>` (optional): target repo. Default: current repo via `git remote get-url origin`.
- `--from-file <path>` (optional): path to a local file containing raw CI log output. Mutually exclusive with `--run-id`.

Mutual exclusion: `--run-id` and `--from-file` cannot both be set. If both provided → STOP and ask user to pick one.

## Step 2 — Obtain CI failure data

**If `--from-file` provided:**
Read the file directly. Skip to Step 3.

**If `--run-id` provided:**
```bash
gh run view <run-id> --log-failed [--repo <repo>]
```
Capture stdout as raw log. If exit non-zero → report stderr, STOP.

**If neither provided — auto-detect:**
```bash
gh run list --limit 10 --status failure --json databaseId,name,conclusion,headBranch,createdAt \
  [--repo <repo>]
```
Present the list to user via `AskUserQuestion`:
- "Which failed CI run do you want to ingest?"
  - One option per run: `#<id> — <name> on <branch> at <createdAt>` (cap at 4 per Claude Code's `maxItems: 4`; if more failures exist, list the 4 most recent)
  - Do NOT add a manual "None of these" option — it duplicates Claude Code's auto-appended `Other` free-text and steals a slot. Users who want to provide a file path or out-of-list run id type it into `Other`.

After user selects a listed id → `gh run view <selected-id> --log-failed [--repo <repo>]`. If user typed a file path via `Other` → read that file directly.

If `gh run list` returns empty (no failures) → STOP: `No failed CI runs found in the last 10 runs.`

## Step 3 — Classify failure type

Scan the raw log for these patterns (first match wins):

| Pattern | Type | Severity |
|---|---|---|
| `[ERROR] COMPILATION ERROR` / `BUILD FAILURE` / `error: cannot find symbol` | `compile` | P2 |
| `Tests run: N, Failures: M` / `FAILED` in test output / `AssertionError` | `test` | P2 |
| `secret` / `credential` / `token` found in secrets scan output / `secrets_linter` exit 2 | `security` | P1 |
| `coverage` / `JaCoCo` / `below minimum` | `coverage` | P3 |
| `OutOfMemoryError` / `heap space` / `GC overhead` | `oom` | P2 |
| `dependency` / `Could not resolve` / `artifact not found` | `dependency` | P2 |
| Timeout / `Process killed` / `Killed` | `timeout` | P2 |
| None of the above | `unknown` | P2 |

If multiple patterns match, list all but use the first for primary routing.

Extract:
- **Failing component**: class name, module, test class, or job step name nearest to the failure marker
- **Error message**: first 3 lines of the error block (not the full stack trace)
- **Branch**: from run metadata or log header

## Step 4 — Record in failure_memory

Always run this before routing, regardless of type:

```bash
python3 .claude/scripts/local_intel/failure_memory.py record \
  --intent Change \
  --profile STANDARD \
  --phase QA \
  --gate ci-<type> \
  --pattern "<failing component>: <one-line error summary>" \
  --task-id "ci-<run-id-or-filename>"
```

## Step 5 — Route by failure type

### type = `security` (P1)
Open `.claude/commands/h-incident.md` and execute its Steps 3–8 in this conversation (slash commands are LLM prompt templates, not callable functions — "execute inline" means follow the Steps yourself; do NOT dispatch a sub-agent, do NOT try to invoke `/h-incident` as if it were a tool). Use these inputs:

- `source`: `log`
- `slug`: `ci-secret-<YYYYMMDD>`
- raw file: write the relevant log lines to `.claude/runs/decompositions/<YYYYMMDD>_ci-secret_raw.md` first, then pass that path to h-incident Step 4's `--from-file`

Steps 1–2 (arg parsing + raw-fact acquisition) are already satisfied by the inputs above, so jump straight to h-incident Step 3 (path collision check) and continue through Step 8 (final report).

STOP after the incident is recorded. Do not proceed to standard task creation.

### type = `compile`
Surface immediately:
```
[CI Failure]: compile error in <component>
[Error]: <3-line excerpt>
[Suggested Action]: Fix the compile error locally, then push again.
```
Offer to create a fix task: ask via `AskUserQuestion`:
- "Create a PATCH fix task for this compile error?"
  - Yes → create launch_spec row: `| ci-compile-fix-<date> | LOW | Implement | PENDING | none | (no brief, inline PATCH) |`
  - No → skip

### type = `test`
Ask via `AskUserQuestion`:
- "This CI test failure — is it a known flake or a real regression?"
  - Real regression → create a DEBUG task in launch_spec:
    ```
    | ci-test-debug-<date> | MEDIUM | Explore | PENDING | none | (no brief yet) |
    ```
    Add note: `Scenario DEBUG — root cause unknown. Run /h-brief after root-cause analysis.`
  - Known flake → record in failure_memory with pattern `flake: <test class>` and STOP.

### type = `oom`
OOM is almost never a flake — the test-route flake/regression question is the wrong frame. Ask via `AskUserQuestion`:

- "OOM in CI — what's the most likely cause?"
  - Heap config too small for new workload — adjust CI heap setting; no fix task needed
  - Test isolation / memory leak in new code — create DEBUG task to find the leak
  - Unknown — create DEBUG task at HIGH risk for investigation

Branch on selection:
- **Heap config** → already recorded in failure_memory at Step 4. Surface inline: `[CI OOM — heap config]: adjust -Xmx / -XX:MaxRAMPercentage in CI workflow (likely .github/workflows/*.yml or pom surefire config). No fix task created.` STOP.
- **Test leak** → create launch_spec row: `| ci-oom-leak-<date> | MEDIUM | Explore | PENDING | none | (no brief yet) |` with note `Scenario DEBUG — test isolation/leak suspected. Run /h-brief after root-cause analysis.`
- **Unknown** → create launch_spec row: `| ci-oom-debug-<date> | HIGH | Explore | PENDING | none | (no brief yet) |` with note `Scenario DEBUG — OOM root cause unknown. Heap config and isolation both candidates; investigate before fixing.`

### type = `coverage`
Warn only — no task created:
```
[CI Coverage Warning]: coverage dropped below threshold in <component>
[Suggested Action]: Add tests before next PR. No task created (coverage gaps are tracked per-task in /h-archive WAL election).
```

### type = `dependency`
```
[CI Dependency Failure]: <component> — <error excerpt>
[Suggested Action]: Run /h-gates --scenario E to check pom.xml changes, then fix the dependency.
```
No task created. Route user to `h-gates`.

### type = `timeout` / `unknown`
```
[CI Failure]: <type> in <component>
[Error excerpt]: <3 lines>
[Suggested Action]: Investigate manually. Run /h-incident if this is production-impacting.
```

## Step 6 — Report

Output exactly this block:

```
[CI Status]: ROUTED | WARN | FAILED
[Run ID]: <id or "from-file">
[Branch]: <branch>
[Failure Type]: <type>
[Severity]: P1 | P2 | P3
[Failing Component]: <component>
[failure_memory]: recorded
[Routing]:
  - <action taken, e.g. "DEBUG task created: ci-test-debug-<date>" or "incident recorded" or "warn only">
[Next Action]: <start with a command — e.g. "Run /h-resume to pick up the created DEBUG task" or "Run /h-incident to escalate" or "No follow-up — coverage warning only">

## Hard constraints

- **Allowed edits**: `launch_spec_*.md` (new row only for task creation), `failure_memory.json` (via the script — not directly), new incident `.md` under `.claude/wiki/incidents/` (security type only). NO source-code edits. NO task_brief writes (task creation here is always PENDING with no brief — brief is written at the task's own Propose phase).
- **Do NOT auto-fix CI failures** — this command classifies and routes, it does not write code.
- **Do NOT create a task for coverage drops** — warn only.
- **Security failures are ALWAYS P1 incidents** — never downgrade to a task/warn.
- Anti-loop: if `gh run view` fails twice (e.g. auth error) → STOP and ask user to paste log output manually.
