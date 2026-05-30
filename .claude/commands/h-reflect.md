---
description: Session reflection — multi-select lessons (incident/wiki/failure/success/memory) → reset counters. TRIGGER: [reflect-hint] / '复盘'. NOT FOR: archive (use /h-archive).
argument-hint: (none)
---

Non-archival reflection. Unlike `/h-archive` (which closes a STANDARD/RESEARCH task), `/h-reflect` runs at any time — typically when the Stop hook emits `[reflect-hint]` showing accumulated work without a recent capture. Goal: surface candidates the user can multi-select to persist, then reset session counters.

Sequential; user-driven decisions; non-blocking on Skip.

## Step 1 — Collect evidence (main agent inline; no sub-agent)

Gather **without prompting the user** — Step 2 will use this to populate option text:

1. **Diff scope**: `git diff <base>..HEAD --stat` where `<base>` is `git log -1 --format=%H -- .claude/wiki/archive 2>/dev/null` (last archive). If empty (no archive ever), use `git log -1 --format=%H HEAD~5` or `HEAD~10`.
2. **Failure summary**: `python3 .claude/scripts/local_intel/failure_memory.py summary --days 1 --min-count 1 --top 5 --include-incidents`
3. **Session counters + bootstrap sanity check** (F7):
   ```bash
   python3 .claude/scripts/local_intel/session_stats.py read --json
   git diff HEAD --shortstat   # "N files changed, M insertions(+), K deletions(-)"
   ```
   Parse `N` from `--shortstat`. If `session_stats.edits < N / 5` AND `N > 3`, the counter is bootstrap-underreporting (created mid-session OR reset right before substantive work). Emit:
   ```
   [reflect-bootstrap-warn] session_stats edits=<S> but git diff shows <N> changed files — counter underreports; using diff stat as primary signal for Step 2.
   ```
   Subsequent steps MUST then use `N` (files-changed from git) and `git diff --stat` line counts when populating Step 2 option WHY text — not the session_stats numbers.
4. **Active queue**: read latest `.claude/runs/launch-specs/launch_spec_*.md` — note any `IN_PROGRESS` rows.
5. **Incident-shape scan** on the diff content: look for **stack trace / NullPointer / OOMException / panic / "race condition" / "data inconsistency" / "deadlock"** + HTTP status `500\b`/`503\b` (use word boundary — bare `500` matches code constants like `MAX_RECORDS = 500` and false-fires). If any signature present, flag for Step 2 incident option.

Do NOT summarize this to the user. It feeds Step 2.

## Step 2 — Surface candidates via AskUserQuestion (filter + cap to 4)

### 2a — Classify the 5 capture types by signal strength

From Step 1 evidence, mark each capture type as **strong** or **weak**:

| Type | Strong if … |
|---|---|
| `incident` | Step 1.5 found ≥1 incident signature (word-bounded `500`/`503`/stack-trace/NPE/OOM/panic/race/inconsistency/deadlock) |
| `wiki-patch` | Step 1.1 diff touches ≥ 5 distinct files OR diff introduces concepts (new class / new module / new domain term) not yet referenced in any `wiki/<domain>/index.md` |
| `failure-pattern` | Step 1.2 summary shows ≥ 2 recurring patterns today |
| `success` | Step 1.4 launch_spec has ≥ 2 rows flipped IN_PROGRESS→DONE in the last session OR git log shows ≥ 1 task_brief archived |
| `auto-memory` | User explicitly corrected or validated a non-obvious approach earlier this session (the agent must judge from session memory) |

### 2b — Present to user

`AskUserQuestion` is capped at **4 options per question** (F6 — see Hard constraints). Apply:

| Strong-signal count | Action |
|---|---|
| 0 | **Auto-Skip** — jump straight to Step 4 without asking. Tell the user `[reflect] no signals — auto-skipped`. |
| 1–3 | One `AskUserQuestion` with strong signals + Skip (2–4 options). |
| 4–5 | One `AskUserQuestion` with top-3 strong by priority `incident > wiki > failure > success > memory` + Skip (4 options). Note dropped type(s) in plain text: `Also detected but not shown (re-invoke /h-reflect after this pass to capture): <list>`. |

Each option description MUST embed a one-line WHY from Step 1 evidence. Example:

```
Q: Which lessons to capture from this session? (Multi-select)
- [ ] Patch wiki         — <WHY: e.g. "14 files changed; introduces 'origin trust tier' concept absent from wiki/architecture/">
- [ ] Add success record — <WHY: e.g. "12 tasks completed clean, 0 retries">
- [ ] Add auto-memory    — <WHY: e.g. "user repeatedly validated 'small batches over big bangs'">
- [ ] Skip — no captures
```

Zero selections OR `Skip` → jump straight to Step 4.

## Step 3 — Dispatch by selection

For EACH selected option (independent; one failure does not abort the others):

### 3a — Write incident

Prompt inline (plain text, NOT AskUserQuestion — schema overkill for slug/source):
- `Slug for the incident? (kebab-case, e.g. user-login-500-spike)`
- `Source? (sentry|jira|log|manual)`
- `Paste or describe the raw fact (or path to a file)`

Then:
```bash
python3 .claude/scripts/local_intel/ingest_incident.py --source <src> --slug <slug>
# (script reads raw from stdin or --from-file; saves <date>_<slug>.raw.txt; prints extraction prompt)
```

Main agent then drafts `.claude/wiki/incidents/<YYYY-MM-DD>_<slug>.md` per `.claude/wiki/incidents/TEMPLATE.md`. Surface the file path and the `## 提醒未来 LLM` line back to user.

### 3b — Patch wiki

Dispatch `knowledge-extractor` per `.claude/rules/dispatch-template.md`. Required content unique to /h-reflect:

- `## Inputs`: include `[Chosen Dimensions]: <comma-list>` derived from Step 1 diff signals — same heuristic as `/h-archive` Step 3a (sql→data, controller→api, enum→domain, etc.)
- `## Source Documents`: pointer to the diff range; pointer to any wiki indexes already opened in this session
- **Add this exact instruction block under `## Source Documents`** (Hermes "four-level priority", written as inline guidance to override extractor's default new-fragment bias):

  ```
  PRIORITY ORDER (apply top-down; do NOT new-create until 1-3 exhausted):
  1. Patch wiki files this session already opened (check session_stats.files for hints on which domains)
  2. Append to existing umbrella index.md entries when a concept matches
  3. Create reference/ or template/ files for session-specific details
  4. Last resort: new wal/ fragment (the current default)
  ```

Per T2 contract: extractor writes `origin: agent-extracted` frontmatter automatically.

Run `subagent_return_gate.py --return-stdin --task-kind extract` after return.

### 3c — Add failure pattern

Prompt inline:
- `Failure phase? (Explorer|Propose|Review|Implement|QA|Archive)`
- `Pattern? (if mentioning broken state, lead with 'fix: <command>' or 'workaround: <approach>' per Anti-Petrification lint)`

Then:
```bash
python3 .claude/scripts/local_intel/failure_memory.py record \
  --intent Change --profile <from-context> --phase <answered> \
  --gate "<answered or 'n/a'>" --pattern "<answered>" \
  --task-id "reflect-<YYYY-MM-DD>"
```

Exit 2 (REFUSED by lint) → surface the stderr message verbatim to user; re-prompt for a fixed version (MAX 2 retries; 3rd → `[Issues Found]` and continue).

### 3d — Add success record

Prompt inline:
- `Success phase? (default: the most recent non-Archive phase this session — infer from launch_spec or diff)`
- `Short note — what approach worked? (≤200 chars)`

Then:
```bash
python3 .claude/scripts/local_intel/failure_memory.py record-success \
  --intent Change --profile <from-context> --phase <answered> \
  --note "<answered>"
```

### 3e — Add auto-memory

Engage the auto-memory protocol from your system prompt (the `# auto memory` block under `/Users/<user>/.claude/projects/<project-hash>/memory/`).

- Default classification: **feedback** type (the most common /h-reflect output — user gave a correction or validated a non-obvious choice this session)
- Reason cite: name the specific moment in this session that triggered the memory (e.g. "user said 'don't use mocks for migration tests' at 23:14")
- Use existing `auto-memory` schema; do NOT introduce new types or fields
- After writing the file + appending to `MEMORY.md` index, surface the new memory's `name:` slug back to user

## Step 4 — Reset session counters

```bash
python3 .claude/scripts/local_intel/session_stats.py reset
```

This MUST run even on Skip path — the purpose of the reset is "user has explicitly closed the reflection window" regardless of what (if anything) was captured.

## Step 5 — Final report

Output exactly this block, nothing else:

```
[Reflect Status]: COMPLETE | PARTIAL | SKIPPED
[Captured]: <comma-sep selections actually persisted, or "none — Skip elected">
[Incidents]: <new incident path, or "n/a">
[WAL Fragments]: <comma-sep paths from extractor, or "n/a">
[Failure Patterns]: <count recorded, or "n/a">
[Success Records]: <count recorded, or "n/a">
[Auto-Memory]: <new memory slug, or "n/a">
[Session Reset]: yes
[Next]: <one sentence — typically "continue current task" or "run /h-status to see queue">
```

## Hard constraints

| Rule | Value |
|---|---|
| Allowed edit set | `.claude/wiki/incidents/<date>_<slug>.md`, `.claude/wiki/incidents/<date>_<slug>.raw.txt`, WAL fragments via knowledge-extractor sub-agent, auto-memory files under `~/.claude/projects/<hash>/memory/`, `.claude/runs/local_intel/session_stats.json` (via script) |
| Source-code edits | FORBIDDEN |
| Anti-loop | Max 2 retries per Step 3 sub-step; on second failure record `[Issues Found]` and continue to next selection — never abort the whole flow |
| Skip path | Step 2 zero-selection or Skip → bypass Step 3 entirely; Steps 4-5 still run |
| Idempotency | Re-running `/h-reflect` after a partial run is safe; `session_stats.reset` is idempotent; sub-agent dispatches use their own idempotency rules |
| Hermes priority alignment | Step 3b MUST embed the 4-level priority verbatim in the dispatch prompt — without it `knowledge-extractor` defaults to step 4 (new fragment) every time, defeating the patch-existing-first goal |
| Auto-memory neutrality | Step 3e MUST NOT prescribe memory content; it only points at the existing protocol. Per `CLAUDE.md` user constraint: 记忆模块不要具体思想，做引导 |
| AskUserQuestion cap (F6) | Tool schema enforces 2–4 options per question. Step 2b uses filter+priority-cap; weaker signals are deferred to a re-invocation (announced inline). Do NOT split one logical question into two AskUserQuestion calls just to fit all 5 capture types — that doubles user friction with no payoff. |
| Bootstrap gap (F7) | `session_stats.py` was created mid-T1; the first session post-install may show `edits ≈ 0` even with substantive work because the bumping hook wasn't live for early edits. Step 1.3 sanity check substitutes `git diff --shortstat` numbers when the counter underreports. Do NOT "fix" this by seeding the counter from git — the counter's invariant is "edits since last reset", and git diff has its own (correct) semantics; both signals coexist. |
