---
name: knowledge-architect
description: Reorganize, deduplicate, and split large wiki index files into focused sub-documents when a wiki index becomes bloated during WAL compaction.
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
maxTurns: 40
---

Executable Checklist:
- [ ] Check if the target wiki index file exceeds 500 lines; if not, abort and report no action needed.
- [ ] Deduplicate repeated entries and split the bloated `index.md` into focused sub-documents.
- [ ] Rewrite `index.md` as a lean routing graph that links to the new sub-documents without duplicating their content.
- [ ] Run `python3 .claude/scripts/wiki/wiki_linter.py` and FAIL if dead links exist or any file still exceeds 500 lines.
Output:
- A refactored, smaller `index.md` (acting as a router) and new specialized sub-documents.
Gate:
- `python3 .claude/scripts/wiki/wiki_linter.py` (FAIL if dead links exist, or if any file still exceeds 500 lines).
