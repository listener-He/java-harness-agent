# Purpose (Design Philosophy)

This wiki exists to help an AI agent produce correct engineering outcomes with minimal hallucination and maximal traceability.

## Core Principles

1. YAGNI (Do Not Over-Design)
   - If a feature is not required now, do not introduce it "for future use".

2. High Cohesion, Low Coupling (Indexed by domain)
   - API/Data/Domain knowledge MUST be separated by module via per-domain `index.md`.
   - Example directory structure:
     ```text
     wiki/api/
     ├── index.md        # Master router
     ├── trade_api.md    # Trade module APIs
     └── user_api.md     # User module APIs
     ```
   - Each `index.md` MUST stay small: navigation + short summaries only. Do not write full field lists in an index.

3. Knowledge Lifecycle Management
   - Specs decay quickly after code lands. Stable knowledge MUST be extracted during `Archive`.
   - After extraction, the original spec MUST move to the archive area.
   - **Write-back Protocol**: When creating or updating any knowledge document, the agent MUST update `KNOWLEDGE_GRAPH.md` or the relevant domain `index.md` first to ensure no orphan docs are created. Every active document MUST be reachable from [KNOWLEDGE_GRAPH.md](KNOWLEDGE_GRAPH.md).

4. Agent-Driven Navigation (No forced RAG dumps)
   - The agent MUST start from the root index and drill down. Read maximum 1-2 index files per step, analyze, and then decide the next exact file to read. Do not dump large context blobs into the prompt.
