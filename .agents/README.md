# .agents/ — Framework Layer

This directory contains the governance framework for AI-assisted Java development.

## Structure

```
.agents/
├── README.md                  ← This file
├── skills/                    ← Skill library (each skill = one directory + SKILL.md)
├── workflow/
│   ├── LIFECYCLE.md           ← Phase state machine (Explorer → Propose → Review → Implement → QA → Archive)
│   ├── HOOKS.md               ← Hook definitions (pre/guard/shift_left/post/fail/loop)
│   ├── ARCHIVE_WAL.md         ← WAL compaction policy
│   ├── ROLE_MATRIX.md         ← Human-readable role definitions
│   └── role_matrix.json       ← Machine-readable role mount rules
├── router/
│   ├── ROUTER.md              ← Intent Signal Matrix and routing rules
│   └── CONTEXT_FUNNEL.md      ← Context budget and navigation protocol
├── llm_wiki/                  ← Persistent knowledge base (WAL + compacted indexes)
├── events/
│   └── drift_queue/           ← Lightweight change signals written by PATCH tasks
└── scripts/
    ├── gates/                 ← Quality gate scripts (run by hooks)
    ├── wiki/                  ← Wiki maintenance scripts (linter, compactor, auditor)
    ├── local_intel/           ← Pure-local search tools (wiki_search, code_index, failure_memory)
    └── tools/                 ← Utility scripts (archive, import, librarian)
```

## Entry Points

- **Start here**: `../AGENTS.md` — top-level rules and lifecycle overview
- **Find the right skill**: `.agents/skills/skill-index/SKILL.md`
- **Understand routing**: `.agents/router/ROUTER.md`
- **Run quality checks**: `python3 .agents/scripts/wiki/wiki_linter.py`
