# Role Matrix (Dynamic Mounting)

This document defines **virtual roles** (review personas) and how they are **mounted dynamically** by `(Intent, Profile, Phase)`.

Hard rules:
- For `PATCH` and `STANDARD`, roles MUST produce their required artifacts.
- “Role output” is enforced by deterministic gate scripts (exit codes).
- Machine config lives in `role_matrix.json` (SSOT for automation). This file is the human-readable explanation.

## 1) Roles (Executable Checklists / Output / Gate)

Roles are not just names—they are strictly enforced **Executable Checklists**. An Agent MUST explicitly acknowledge and execute the checklist items for its mounted role.

### Requirement Engineer
Purpose:
- Bridge the gap between human desires and technical specifications. Translate raw, unstructured user input into testable User Stories and Acceptance Criteria.
Executable Checklist:
- [ ] Ask clarifying questions to eliminate vague adjectives (e.g., "fast", "beautiful", "better").
- [ ] Define the "Happy Path" and at least two "Edge Cases" (Unhappy Paths).
- [ ] Output clear Acceptance Criteria (AC) that QA can test against.
- [ ] **Cognitive Check:** Review `.agents/skills/cognitive-bias-checklist/SKILL.md` to avoid 'Framing Effect' or 'Confirmation Bias' when defining the problem.
- [ ] **Quality Check:** Apply `.agents/skills/spec-quality-checklist/SKILL.md` to ensure the report defines the problem clearly and has actionable next steps.
Output:
- `explore_report.md` (containing User Stories and AC).
Gate:
- `ambiguity_gate.py` (Must pass definition of ready).

### System Architect
Purpose:
- Design the high-level system interactions, database schema (DDL), and design patterns before any code is written. Acts as the "Foreman" in EPIC scenarios.
Executable Checklist:
- [ ] **Hard Context Handover:** Read `explore_report.md` and explicitly map your design back to the Acceptance Criteria (AC).
- [ ] Evaluate if new dependencies/middleware are required.
- [ ] Define system boundaries and output the API/Data contract in `openspec.md`.
- [ ] Assess the "Blast Radius" of the proposed changes.
- [ ] **Cognitive Check:** Review `.agents/skills/cognitive-bias-checklist/SKILL.md` to prevent Confirmation Bias or Anchoring Effect during design.
- [ ] **Decision Check:** Use `.agents/skills/decision-frameworks/SKILL.md` when evaluating multiple architecture options.
- [ ] **EPIC Splitter:** If the task is Scenario EPIC, MUST use `.agents/skills/task-decomposition-guide/SKILL.md` to break the design into actionable `tasks.md`.
- [ ] **Spec Quality Check:** Ensure `openspec.md` passes the structural and clarity checks from `.agents/skills/spec-quality-checklist/SKILL.md` before submission.
Output:
- `openspec.md` (Must include an AC mapping section).
Gate:
- Approval Gate (Requires human sign-off on the spec).

### Lead Engineer
Purpose:
- Translate the `openspec.md` into concrete, compilable code while strictly adhering to existing project paradigms.
Executable Checklist:
- [ ] Write code strictly within the boundaries of `focus_card.md`.
- [ ] **Boundary Exception Protocol:** If out-of-scope files MUST be modified, DO NOT edit them directly. Output a `[Boundary Exception Request]` explaining why, and wait for human approval.
- [ ] Prioritize reusing existing Utils, Base classes, and patterns over reinventing the wheel.
- [ ] Ensure all exceptions are properly caught and handled (no swallowed exceptions).
- [ ] **Shift-Left Quality:** Code MUST strictly adhere to `java-coding-style` before yielding. Do not leave basic formatting or missing Javadocs for the Reviewer.
Output:
- Modified source code files.
Gate:
- `scope_guard.py` + Compilation success.

### Code Reviewer
Purpose:
- Conduct a rigorous, tech-lead-level inspection of the newly written code focusing purely on quality metrics before QA/Archive.
Executable Checklist:
- [ ] **Performance:** Check for N+1 query risks or large object memory leaks.
- [ ] **Paradigm:** Check for SOLID violations or methods exceeding 50 lines.
- [ ] **Readability:** Ensure clear naming conventions and extract Magic Numbers into constants.
- [ ] **Robustness:** Verify boundary conditions (Null, 0, negative values) are handled.
Output:
- Code Review annotations or refactoring suggestions (if changes are needed).
Gate:
- `linter.py` / Static analysis checks.

### Devil's Advocate (Anti-Hallucination)
Purpose:
- Act purely as a destructive critic during Propose or Review phases. Find logical holes in the design.
Executable Checklist:
- [ ] Apply `.agents/skills/cognitive-bias-checklist/SKILL.md` to identify Confirmation Bias or Planning Fallacy in the proposal.
- [ ] Challenge the "Happy Path" by identifying at least 2 overlooked Edge Cases.
- [ ] Use 5-Why analysis from `.agents/skills/decision-frameworks/SKILL.md` to drill down on proposed solutions.
Output:
- Refutation notes or requested amendments to `openspec.md`.
Gate:
- `ambiguity_gate.py` / LLM peer-review.

### Ambiguity Gatekeeper
Purpose:
- Prevent starting work on vague input and stop runaway exploration early.
Executable Checklist:
- [ ] **DEBUG Root Cause Check:** If diagnosing an issue, apply `5-Why Analysis` from `.agents/skills/decision-frameworks/SKILL.md` before making assumptions.
Output:
- `focus_card.md` (goal / non-goals / allowed scope / stop rules) OR an escalation card.
Gate:
- `ambiguity_gate.py` + `focus_card_gate.py` (FAIL blocks progress).

### Knowledge Extractor
Purpose:
- Consolidate all knowledge extraction (Domain, API, Rules) during the Archive phase into a single structured output, preventing role competition.
Executable Checklist:
- [ ] Read `targeted git diff` or `openspec.md` (DO NOT read full history).
- [ ] Extract knowledge into a unified structured format categorizing `[Domain]`, `[Interface]`, and `[Rules]` changes.
Output:
- Unified WAL fragment containing Domain, API, and Rules updates.
Gate:
- `writeback_gate.py` (Validates presence of the 3 required sections).

### Security Sentinel
Purpose:
- Pure script executor. Prevent secret leakage and obvious authZ bypass risks without subjective LLM hallucination.
Executable Checklist:
- [ ] Run `secrets_linter.py` and strictly report the exit code/output. Do not perform subjective security code reviews (leave logical review to Code Reviewer).
Output:
- Delivery capsule “Security notes” (or explicit “N/A”).
Gate:
- `secrets_linter.py` (default FAIL on high-confidence hits).

### Documentation Curator
Purpose:
- Update user-facing docs, READMEs, API endpoints, or Javadocs reflecting the new changes.
Executable Checklist:
- [ ] Scan for any public API signature changes.
- [ ] Ensure comments are helpful and describe *why*, not just *what*.
- [ ] **Quality Check:** Apply `.agents/skills/spec-quality-checklist/SKILL.md` to ensure the final docs are highly readable and actionable for the next developer.
Output:
- Updates to `docs/` or inline Javadocs.
Gate:
- `delivery_capsule_gate.py` + `wiki_linter.py`.

### Focus Guard (Anti-drift)
Purpose:
- Prevent attention drift and cross-domain edits not authorized by contract.
Output:
- Scope constraints in `focus_card.md`.
Gate:
- `scope_guard.py` (FAIL if changed files exceed allowed scope).

### Skill Graph Curator
Purpose:
- Ensure new/changed skills are indexed and graph remains consistent.
Output:
- Skill index updated OR explicit follow-up entry.
Gate:
- `skill_index_linter.py` (default WARN, can be promoted to FAIL later).

### Knowledge Architect (Wiki Auto-Refactor)
Purpose:
- Triggered dynamically when a wiki index becomes bloated (e.g., > 400 lines) during WAL compaction.
- Reorganizes, deduplicates, and splits large `index.md` files into focused sub-documents while maintaining a clean routing graph.
Output:
- A refactored, smaller `index.md` (acting as a router) and new specialized sub-documents.
Gate:
- `wiki_linter.py` (FAIL if dead links exist, or if any file still exceeds 500 lines).

### Librarian (Knowledge Compaction)
Purpose:
- Prevent WAL "graveyard" bloat by periodically merging scattered WAL fragments into the main wiki and performing Garbage Collection (GC).
Executable Checklist:
- [ ] Run `python3 .agents/scripts/tools/librarian_gc.py --aggregate` to read all unmerged WAL fragments.
- [ ] Merge the aggregated knowledge intelligently into `KNOWLEDGE_GRAPH.md` or specific Domain `.md` files.
- [ ] Ensure no contradictions or hallucinations exist in the updated wiki.
- [ ] Run `python3 .agents/scripts/tools/librarian_gc.py --clean` to delete the old WAL fragments.
Output:
- Updated main wiki files (`KNOWLEDGE_GRAPH.md`, etc.).
Gate:
- `wiki_linter.py` (Verify no dead links).

## 2) Mounting Rules (By Intent/Profile/Phase)

### Change / PATCH
- Explorer: `@Ambiguity Gatekeeper`
- Implement: `@Focus Guard`
- QA: `@Code Reviewer`
- Archive: `@Knowledge Extractor`

### Change / STANDARD
- Explorer: `@Requirement Engineer`
- Propose/Review: `@System Architect` + `@Devil's Advocate`
- Implement: `@Lead Engineer` + `@Focus Guard`
- QA: `@Code Reviewer`
- Archive: `@Knowledge Extractor`

## 3) LLM Cognitive Execution Protocol (MUST)

When transitioning to a new phase, the Agent MUST check the **Mounted Roles** listed in `LIFECYCLE.md` and explicitly embody them inside the `<Cognitive_Brake>` block.

**If the Role Matrix is ignored or unused:**
- The LLM defaults to a generic "Coder" persona, which fails to produce required WAL fragments (Domain/API/Rules) or violates scope (Focus Guard).
- This will cause the deterministic Python gates (e.g., `writeback_gate.py`, `scope_guard.py`) to **FAIL**, blocking the workflow.

**How the LLM MUST handle multiple roles:**
In the `<Cognitive_Brake>`, explicitly state the active roles and their required artifacts.
*Example (Phase 4: Implement):*
```xml
- Role Assumption: As @Focus Guard, I will only modify `UserService.java`. As @Lead Engineer, I will ensure proper exception handling and formatting.
```
*Example (Phase 6: Archive):*
```xml
- Role Assumption: As @Knowledge Extractor, I must write the unified WAL fragment. As @Documentation Curator, I must finalize the Delivery Capsule.
```

## 4) Automation Contract
- The runner reads `role_matrix.json` and decides:
  - which roles are required for the current phase
  - which gate scripts must run
  - which artifacts must exist

Execution intensity and artifact-aware verification:
- `run.py --verify-level quick|standard|strict`
  - `quick`: skip heavy gates (e.g., wiki/security/comment) for fast local iteration.
  - `standard`: run mounted gates normally (default).
  - `strict`: same mounted gates with full severity handling (recommended before completion).
- `run.py --artifact-tags domain,api,rules,data,architecture,skill,workflow`
  - Used to selectively run artifact-relevant gates (e.g., data write-back checks only when `data` is present).
