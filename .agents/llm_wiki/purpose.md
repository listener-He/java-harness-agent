# Purpose (Design Philosophy)

This wiki exists to help an AI agent produce correct engineering outcomes with minimal hallucination and maximal traceability.

## Core Principles

1. YAGNI (Do Not Over-Design)
   - If a feature is not required now, do not introduce it "for future use".

2. High Cohesion, Low Coupling (Indexed by domain)
   - API/Data/Domain knowledge MUST be separated by module (example: `trade`, `user`) via per-domain `index.md`.
   - Each `index.md` MUST stay small: navigation + short summaries only. Do not write full field lists in an index.

3. Knowledge Lifecycle Management
   - Specs decay quickly after code lands. Stable knowledge MUST be extracted during `Archive`.
   - After extraction, the original spec MUST move to the archive area.
   - No orphan docs: every active document MUST be reachable from [KNOWLEDGE_GRAPH.md](KNOWLEDGE_GRAPH.md).

4. Agent-Driven Navigation (No forced RAG dumps)
   - The agent MUST start from the root index and drill down. Do not dump large context blobs into the prompt.
