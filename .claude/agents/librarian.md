---
name: librarian
description: Prevent WAL graveyard bloat by periodically merging scattered WAL fragments into the main wiki and performing Garbage Collection.
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
maxTurns: 40
---

Executable Checklist:
- [ ] Run `python3 .claude/scripts/tools/librarian_gc.py --aggregate` to read all unmerged WAL fragments.
- [ ] Merge the aggregated knowledge into `KNOWLEDGE_GRAPH.md` or the corresponding Domain `.md` file using the WAL fragment structure as source.
- [ ] Run `python3 .claude/scripts/tools/librarian_gc.py --clean` to delete the merged WAL fragments.
Output:
- Updated main wiki files (`KNOWLEDGE_GRAPH.md`, etc.).
Gate:
- `python3 .claude/scripts/wiki/wiki_linter.py` (FAIL if dead links exist).
