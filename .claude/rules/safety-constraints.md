# Safety Constraints & Commit Policy

## Hard Constraints

| Constraint | Rule |
|---|---|
| **Anti-loop** | Max 3 retries per script/linter. Max 2 retries for compile fixes. Exceed → STOP, ask human. |
| **Artifact Paths** | Runtime artifacts under `.claude/runs/`. Never in repo root. Archive phase moves task_brief to `wiki/archive/`. |
| **State Files** | Only two: `launch_spec_*.md` (task queue) and `task_brief.md` (per-task contract). No brake_snapshot, no engine_state.json. |

## Commit Policy

**Never commit:**
- `.claude/runs/` (launch-specs, active task_briefs)
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit:** source code, archived task briefs (`.claude/wiki/archive/`), and `.claude/**/wal/` fragments.
