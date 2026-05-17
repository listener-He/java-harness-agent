# Safety Constraints & Commit Policy

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Context Bloat Prevention** | When dispatching tasks to sub-agents, format prompts using the contract in [.claude/wiki/schema/subagent_contract_schema.md](.claude/wiki/schema/subagent_contract_schema.md). If the sub-agent has native agent tooling, use that instead. |
| **Budget exhausted** | STOP and ask human. Do not guess paths or continue reading. Soft budgets: Wiki ≤ 5, Code ≤ 12, Web ≤ 4. |
| **Approval Gate** | For HIGH risk changes only: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval. MEDIUM: show spec summary as FYI, proceed without waiting. |
| **Anti-loop** | Max 3 retries for scripts/linters. Max 2 retries for compilation fixes. On exceed: STOP and ask human. |
| **Scope Guard** | Do not modify files outside `## Allowed Scope` of `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` without explicit human permission. If no task_brief exists (PATCH/TRIVIAL), scope = the single file being changed. |
| **Artifact Paths** | Runtime artifacts live under `.claude/runs/`. Never generate artifacts in the repo root. TRIVIAL/LOW: no task_brief file needed. Archive phase moves task_brief to `wiki/archive/`. |
| **State Files** | Only two state files: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract). No other runtime state files (no brake_snapshot, no engine_state.json). |

---

## Commit Policy

**Never commit runtime state or caches:**

- `.claude/runs/launch-specs/`
- `.claude/runs/` (includes active `task_brief.md` and `launch_spec_*.md`)
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, archived task briefs (`.claude/wiki/archive/*_task_brief.md`), and `.claude/**/wal/` fragments.
