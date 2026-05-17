# Purpose (Design Philosophy)

This wiki exists to help an AI agent produce correct engineering outcomes with minimal hallucination and maximal traceability.

## Methodological Foundations

This framework composes four software development methodologies into one lifecycle:

### PDD (Plan-Driven Development)
**What**: Plan first, then execute. The plan is a first-class artifact — not an afterthought or a loose backlog. Every task carries explicit dependency declarations, parallelism constraints, and success metrics before any code is written.
**Core artifacts**: `launch_spec.md` (task queue with dependency graph) + `task_brief.md` (per-task contract with dependency declarations).
**Where in lifecycle**:
- **Phase 2 (Propose)**: Task dependencies and parallelism constraints declared. Dependency graph drawn when ≥3 tasks exist.
- **Phase 3 (Review)**: Plan Review Checklist verifies completeness, consistency, feasibility, risk coverage, and dependency soundness.
- **Phase 6 (Archive)**: Plan Deviation Reflection compares planned vs. actual — scope drift, dependency accuracy, plan invalidations, and AC coverage.
**Relationship to SDD/SPEC**: SDD/SPEC is PDD's contract-encoding mechanism. PDD says "plan it first"; SDD/SPEC says "encode the plan as a machine-readable contract."

### BDD (Behavior-Driven Development)
**What**: Define expected behavior before writing any code, using a shared language that both business and engineering can read.
**Core format**: `Given [precondition], when [action], then [observable, measurable result]`.
**Where in lifecycle**:
- **Phase 1 (Explorer)**: Every requirement is translated into Given/When/Then ACs. Vague language ("handle correctly") is blocked.
- **Phase 5 (QA)**: Every Given/When/Then AC is mapped to a test method → expected → actual result in the Evidence Mapping Table. Every behavior declared in Phase 1 is verified.

### SDD / SPEC (Specification-Driven Development)
**What**: A contract-first approach where a specification document governs all downstream work. No code is written until the spec is complete and, for HIGH risk, approved.
**Core artifact**: `task_brief.md` — the universal contract with two sections:
- **Machine Section** (English): Allowed Scope, Acceptance Criteria, Hard Constraints — consumed by AI agents.
- **Human Section** (Chinese): Business rationale, design trade-offs, decision questions — consumed by humans.
**Where in lifecycle**:
- **Phase 2 (Propose)**: Spec written with design alternatives, constraint list, and file-level scope.
- **Phase 3 (Review)**: Spec scrutinized via adversarial review; HIGH risk requires explicit human Approval Gate.
- **Phase 4 (Implement)**: Agent reads only the Machine Section; must not deviate from Allowed Scope.
- **Phase 6 (Archive)**: Stable knowledge extracted from the spec into WAL fragments.

### TDD (Test-Driven Development)
**What**: Write a failing test first, then write the minimum code to make it pass, then refactor. The test is derived from the spec (BDD ACs), not invented by the implementer.
**Core cycle**: RED (failing test) → GREEN (minimum implementation) → REFACTOR (clean up within passing tests).
**Where in lifecycle**:
- **Phase 4 (Implement)**: Tests are written from the ACs in `task_brief.md` Machine Section. Agent must see test failure before writing implementation code.
- Phase 5 (QA) runs the full suite and validates all ACs pass.

### How They Compose

```
PDD (Propose)   →  SDD/SPEC (Propose → Review)  →  TDD (Implement)  →  BDD (QA)
  依赖+并行规划        task_brief 契约             Red→Green→Refactor   行为验证
        ↑                                              |
        └── BDD (Explorer: 写可执行规格) ────────────────┘
```

PDD establishes *what* to plan and *how* dependencies interlock. SDD/SPEC encodes the plan into a *contract*. BDD defines *what* behavior the contract must satisfy via executable specs. TDD enforces *how* implementation satisfies the contract. BDD at QA *proves* the contract was fulfilled. No methodology works in isolation — the lifecycle is the composition.

---

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
