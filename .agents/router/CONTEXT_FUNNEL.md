# Context Funnel (Navigation + Write-back)

This document defines two symmetric rules:
- Forward navigation: how the Agent MUST collect context without blind searching.
- Reverse write-back: how the Agent MUST write stable knowledge back to the wiki during `Archive`.

## Forward Funnel (Navigation Rules)

### Rule 1: Always start at the root (MUST)
Context collection MUST start by reading:
- [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)

### Rule 2: Drill down via indexes (MUST)
1. In `KNOWLEDGE_GRAPH.md`, pick the correct domain index (example: [domain/index.md](../llm_wiki/wiki/domain/index.md)).
2. Read that `index.md`.
3. From the `index.md`, follow the link to the specific document you need and read it.

### Rule 3: Fallback search is last resort (MAY)
Only when the index tree cannot locate the concept, the Agent MAY use keyword search within:
- `llm_wiki/wiki/`

## Reverse Funnel (Write-back Rules)
During `Archive`, the Agent MUST apply the reverse funnel to write stable knowledge back without breaking concurrency safety.

1. Find the mount point by reading [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md).
2. DO NOT edit shared `index.md` directly. Write a WAL fragment into the target domain `wal/` directory (example: `../llm_wiki/wiki/api/wal/YYYYMMDD_feature_x_api_append.md`).
3. Merge and split are done in a low-conflict window (typically by a human). If an index exceeds the hard limit, it MUST be split.

## Hard Constraints
- Links inside `.agents/` MUST use relative paths from the current file.
- If you cannot decide what expertise to apply, consult [trae-skill-index](../skills/trae-skill-index/SKILL.md).
- Every `index.md` MUST provide a 1–2 sentence summary for each linked child document.
