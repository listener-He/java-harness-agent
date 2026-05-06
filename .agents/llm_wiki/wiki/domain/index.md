# Domain Index (Vocabulary & State)

This index defines the project's vocabulary. The Agent MUST use these terms during `Explorer` and `Propose` to avoid domain drift.

## Core Concepts & State Machines

| Concept | Definition | Related Concepts | Details |
|---|---|---|---|
| (Example) Opportunity | A sales opportunity representing a potential deal | Lead, Account, Deal | `[opportunity_states.md]` |

---

## Archive Extraction SOP
If an `<YYYY-MM-DD>_<slug>_openspec.md` introduces new terms, roles, enum values, or state transitions, the Agent MUST extract them here during `Archive`.

### Append Template
```markdown
| {term} | {1–2 sentence definition and boundary} | {Related Concepts / Synonyms} | `[{details_doc}]` |
```

Anti-bloat rule: if the vocabulary exceeds 30 concepts, you MUST split into per-line dictionaries (example: `dictionary_xxx.md`) and keep this file as a router.


---

## WAL Compaction - domain - 2026-05-06 15:26:56


### 20260506_trae_skills_import_domain_append.md

# Domain WAL Append - 2026-05-06 - trae_skills_import

Source spec:
- `.agents/workflow/runs/2026-05-06_trae_skills_import_openspec.md`

## Domain
- Term: `skill`
  - Definition: A reusable workflow capability stored at `.agents/skills/<skill-name>/SKILL.md`, discoverable via the central index.
- Term: `skill index`
  - Definition: The central registry `.agents/skills/trae-skill-index/SKILL.md`, required to reference every installed skill.
- Term: `conflict stash`
  - Definition: When importing a skill that already exists and differs, save upstream `SKILL.md` under `.agents/workflow/runs/<slug>_conflicts/` for manual merge.


### 20260506_trae_skills_import_rules_append.md

# Rules WAL Append - 2026-05-06 - trae_skills_import

Source spec:
- `.agents/workflow/runs/2026-05-06_trae_skills_import_openspec.md`

## Rules
- MUST compare incoming skill content with existing `.agents/skills/<skill>/SKILL.md` before overwriting.
- MUST avoid duplicate skills with the same purpose; when conflict exists, stash upstream content and merge explicitly.
- MUST update `.agents/skills/trae-skill-index/SKILL.md` to reference every installed skill (required for `skill_index_linter.py`).
- MUST keep skill imports within `.agents/**` scope.


---

## WAL Compaction - domain - 2026-05-06 15:52:44


### 20260506_skills_align_domain_append.md

# Domain WAL Append - 2026-05-06 - skills_align

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_align_openspec.md`

## Domain
- Term: `repo-aligned skill`
  - Definition: A skill whose instructions and artifacts strictly follow this repo’s `AGENTS.md` workflow gates and `.agents/**` conventions.
- Term: `canonical + wrapper`
  - Definition: Consolidation pattern where one skill holds the full protocol (canonical) and any overlapping skill becomes a thin entrypoint pointing to it (wrapper).


### 20260506_skills_align_rules_append.md

# Rules WAL Append - 2026-05-06 - skills_align

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_align_openspec.md`

## Rules
- Skills MUST NOT reference `.trae/` paths or depend on external state directories.
- Skills MUST NOT reference non-existent local files or non-existent skills as required prerequisites.
- Skills that describe automation/loops MUST be bounded and MUST respect Approval Gate and anti-loop limits.
- Plans/evals/releases produced by skills MUST be stored as runtime artifacts under `.agents/workflow/runs/`.


---

## WAL Compaction - domain - 2026-05-06 16:09:12


### 20260506_skills_consolidate_domain_append.md

# Domain WAL Append - 2026-05-06 - skills_consolidate

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate_openspec.md`

## Domain
- Term: `skill consolidation`
  - Definition: Merge overlapping skill protocols into canonical skills, then delete the superseded skills and update the central index.


### 20260506_skills_consolidate_rules_append.md

# Rules WAL Append - 2026-05-06 - skills_consolidate

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate_openspec.md`

## Rules
- Prefer consolidation over proliferation: when two skills overlap, keep one canonical skill and delete the superseded one after content merge.
- Debugging guidance is canonicalized under `systematic-debugging` (triage + root-cause + bug-fix).
- Plan creation and inline execution guidance is canonicalized under `writing-plans`.


---

## WAL Compaction - domain - 2026-05-06 16:26:06


### 20260506_skills_consolidate2_domain_append.md

# Domain WAL Append - 2026-05-06 - skills_consolidate2

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate2_openspec.md`

## Domain
- Term: `review workflow (canonical)`
  - Definition: Requesting review and receiving feedback guidance is canonicalized into `code-review-checklist` to reduce skill sprawl.


### 20260506_skills_consolidate2_rules_append.md

# Rules WAL Append - 2026-05-06 - skills_consolidate2

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_consolidate2_openspec.md`

## Rules
- Prefer a single canonical for code review workflow: `code-review-checklist` includes request/reception guidance.
- When consolidating skills, update central index and remove superseded skill directories.


---

## WAL Compaction - domain - 2026-05-06 16:36:38


### 20260506_skills_enable_set_domain_append.md

# Domain WAL Append - 2026-05-06 - skills_enable_set

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_enable_set_openspec.md`

## Domain
- Term: `default enabled set`
  - Definition: A small set of skills preferred for auto-trigger and daily workflow; all other skills are opt-in unless required by mounted roles.
- Term: `role-required skill`
  - Definition: A skill that is invoked because a mounted role checklist requires it, even if not in the default enabled set.


### 20260506_skills_enable_set_rules_append.md

# Rules WAL Append - 2026-05-06 - skills_enable_set

Source spec:
- `.agents/workflow/runs/2026-05-06_skills_enable_set_openspec.md`

## Rules
- The central skill index MUST define a small Default Enabled Set to reduce skill sprawl.
- Skills outside Default Enabled are opt-in unless mounted role checklists require them.
- The index MUST include a lifecycle phase map aligned with mounted roles (Explorer/Propose/Implement/QA/Archive).
