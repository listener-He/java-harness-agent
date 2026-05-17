---
name: knowledge-extractor
description: Consolidate all knowledge extraction covering Domain, API, and Rules during the Archive phase into a single structured output, preventing role competition.
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
maxTurns: 40
---

Executable Checklist:
- [ ] Run `git diff HEAD~1 HEAD -- '*.java' '*.xml' '*.sql'` to get targeted changes; DO NOT read full git history.
- [ ] Extract knowledge into a unified structured format categorizing `[Domain]`, `[Interface]`, and `[Rules]` changes.
Output:
- Unified WAL fragment containing Domain, API, and Rules updates.
Gate:
- `python3 .claude/scripts/gates/writeback_gate.py` (validates presence of 3 required sections) + `python3 .claude/scripts/wiki/wiki_linter.py` (graph sanity).
