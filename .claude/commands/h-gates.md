---
description: Phase-aware gate suite runner — auto-detects active phase/scenario and runs applicable gates
argument-hint: [--phase explore|propose|implement|qa|archive] [--scenario B|C|E] [--all]
---

Run the gates that apply to the current state of work. Hooks already cover edit-time scope/secrets checks; this command does the **full-suite audit** you'd run before a commit, phase transition, or PR. Output is severity-aggregated per `.claude/skills-archive/linter-severity-standard/SKILL.md`.

### Relationship to the PreToolUse hook

`pre_tool_use_hook.py` runs `scope_guard.py` on **every single Edit/Write** with that one file as the only changed file. It's a per-edit tripwire — fast, scoped to one path, fails the Edit before the diff lands.

`/h-gates` runs `scope_guard.py` (and the rest of the suite) on the **full accumulated git diff**. It's a batch audit — catches drift across many edits, finds files that escaped per-edit detection (e.g. created via Bash redirection or a script that bypassed the hook), and aggregates with other gates that have no per-edit equivalent (`task_brief_gate.py`, `migration_gate.py`, etc.).

They are complementary, not redundant: per-edit catches issues at write-time; batch catches "the whole change set still consistent?" before a phase transition. Run `/h-gates` at phase boundaries even when the hook reported zero blocks during Implement.

## Step 1 — Detect context

1. Run `python3 .claude/scripts/harness/find_active_task_brief.py`. Stdout = active task_brief path, or empty.
2. If `$ARGUMENTS` contains `--phase X` or `--scenario Y` → honor the explicit override (skip auto-detection in Step 2).
3. Else auto-detect:
   - **No active brief** → mode = `Vibe / PATCH`. Only universal gates apply.
   - **Brief found** → read frontmatter (`spec_mode`, `risk`, `dimensions`) and parse the latest `launch_spec_*.md` for this brief's Phase column.

## Step 2 — Determine which gates to run

Build the gate list from the detected (or overridden) context:

**Universal (always, if there is any code change)**

| Gate | When skipped |
|---|---|
| `secrets_linter.py --paths <git-diff-changed-files>` | `git diff` is empty |

**Phase-keyed (from lifecycle.md Part 3)**

| Phase | Gate(s) |
|---|---|
| Explore | `failure_memory.py query --intent Change --phase Explorer` (read-only) |
| Propose | `task_brief_gate.py --require <brief>` |
| Implement | `scope_guard.py --task-brief <brief>` (audit full diff); `mvn compile -q` if `.java` **OR** `pom.xml` in diff |
| QA | (no extra full-suite gate; tests + AC mapping are LLM-driven) |
| Archive | universal + scenario gates only |

**Scenario-keyed (additive — run if condition holds OR if `--scenario X` was set explicitly)**

| Trigger | Gate |
|---|---|
| `data` in dimensions OR `--scenario B` OR any `*.sql` in diff under a migration path | `migration_gate.py --sql-dir <inferred dir>` |
| `api` in dimensions OR `--scenario C` | `api_breaking_gate.py --task-brief <brief>` |
| `pom.xml` in diff OR `--scenario E` | `dependency_gate.py --pom <pom path>` |

If `--all` is passed, run every gate above for which the required input can be located. If a required input is missing (e.g. no brief for `task_brief_gate.py`) → skip that gate and note SKIP in the report.

## Step 3 — Run gates and aggregate

For each gate in the assembled list:

1. Print the command line being run (so the user sees it).
2. Execute it.
3. Capture exit code and last line of stderr for the report.

Per `linter-severity-standard`:
- exit 0 → OK
- exit 1 → WARN (surface inline)
- exit 2 → FAIL (do NOT stop further gates — collect all results first)
- any other exit → ERROR (treat as FAIL, mark script-broken)

**Do not short-circuit**: even after a FAIL, continue running remaining gates so the user gets the full picture in one pass.

## Step 4 — Final report

Emit exactly this block:

```
[Gates Status]: OK | WARN | FAIL
[Context]: phase=<detected/forced>, risk=<LOW|MEDIUM|HIGH|n/a>, scenarios=<comma-separated or "none">
[Brief]: <path or "none (Vibe/PATCH)">
[Diff Files]: <N changed | none>

[Gate Results]
| Gate | Severity | One-line reason |
|---|---|---|
| secrets_linter | OK / WARN(...) / FAIL(...) / SKIP(no diff) | ... |
| task_brief_gate | ... | ... |
| scope_guard | ... | ... |
| <each gate run> | ... | ... |

[Next Action]: <start with a command — e.g. "Fix scope_guard FAIL by reverting <path> or updating brief, then re-run /h-gates" or "All OK — proceed to next phase via /h-resume or /h-pr">
```

Overall `[Gates Status]` rules:
- Any FAIL → overall FAIL
- No FAIL, any WARN → overall WARN
- All OK / SKIP → overall OK

## Hard constraints

- **Read-only command** — do NOT edit any file. Gates may write to `.claude/runs/local_intel/failure_memory.json` themselves via the failure-memory record path, but **you** must not directly modify it.
- **No sub-agent dispatch** — this is a pure script orchestrator.
- **No mvn compile** unless explicitly authorized by `--all` or `--phase implement`, because compile can be slow and may surface unrelated errors. Default Implement-phase run includes `mvn compile -q` only if `.java` files **OR `pom.xml`** appear in diff (pom edits can break the build even without `.java` edits — dependency rename, plugin version bump, etc.).
- Anti-loop: each gate runs at most ONCE per invocation. If a gate has flaky failure (timeout, environment issue), report it as ERROR — do not retry.
- **Failure memory recording**: for every FAIL above, after report emission, run:
  ```
  python3 .claude/scripts/local_intel/failure_memory.py record --intent Change --profile <profile> --phase <phase> --gate <script> --pattern "<one-line reason>" --task-id <slug-or-"adhoc">
  ```
  Skip recording for WARN/SKIP/OK.
