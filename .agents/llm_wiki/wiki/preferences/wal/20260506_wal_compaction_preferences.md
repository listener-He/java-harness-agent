# WAL Compaction — preferences — 2026-05-06

## 20260423_runtime_artifacts_paths

**What changed:**
Standardize runtime artifact locations: `<YYYY-MM-DD>_<slug>_openspec.md` and `<YYYY-MM-DD>_<slug>_focus_card.md` are generated only under `.agents/workflow/runs/`. During `Archive`, move session spec to `.agents/llm_wiki/archive/<YYYY-MM-DD>_<slug>_openspec.md` and write WAL fragments before final response.

**Why:**
Prevent root directory clutter and accidental commits of runtime artifacts. Ensure consistent "single source of truth" paths across workflow docs and gate scripts.

**Touch points:**
`AGENTS.md`, `.agents/workflow/LIFECYCLE.md`, `.agents/router/ROUTER.md`, `.agents/workflow/HOOKS.md` — align references to `.agents/workflow/runs/` paths.
