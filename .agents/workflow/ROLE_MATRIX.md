# Role Matrix (Dynamic Mounting)

This document defines **virtual roles** (review personas) and how they are **mounted dynamically** by `(Intent, Profile, Phase)`.

Hard rules:
- For `PATCH` and `STANDARD`, roles MUST produce their required artifacts.
- “Role output” is enforced by deterministic gate scripts (exit codes).
- Machine config lives in `role_matrix.json` (SSOT for automation). This file is the human-readable explanation.

## 1) Roles (Executable Checklists / Output / Gate)

Roles are not just names—they are strictly enforced **Executable Checklists**. An Agent MUST explicitly acknowledge and execute the checklist items for its mounted role.

### Ambiguity Gatekeeper
Purpose:
- Prevent starting work on vague input and stop runaway exploration early.
Output:
- `focus_card.md` (goal / non-goals / allowed scope / stop rules) OR an escalation card.
Gate:
- `ambiguity_gate.py` + `focus_card_gate.py` (FAIL blocks progress).

### Domain Analyst
Purpose:
- Capture business domain vocabulary, invariants, and boundaries.
Output:
- Domain WAL fragment.
Gate:
- `writeback_gate.py` (Domain WAL required).

### Interface Steward
Purpose:
- Capture API contract facts (endpoints/auth/error semantics) and link to spec.
Output:
- API WAL fragment.
Gate:
- `writeback_gate.py` (API WAL required).

### Rules Lawyer
Purpose:
- Capture rules domain (permission/data scope/cache/exception).
Output:
- Rules WAL fragment.
Gate:
- `writeback_gate.py` (Rules WAL required).

### Security Sentinel
Purpose:
- Prevent secret leakage and obvious authZ bypass risks.
Output:
- Delivery capsule “Security notes” (or explicit “N/A”).
Gate:
- `secrets_linter.py` (default FAIL on high-confidence hits).

### Documentation Curator
Purpose:
- Ensure end-of-work has a complete, handoff-ready capsule + WAL references.
Output:
- Delivery capsule.
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

## 2) Mounting Rules (By Intent/Profile/Phase)

### Change / PATCH
- Explorer: `@Ambiguity Gatekeeper` + `@Focus Guard`
- Implement: `@Focus Guard` + `@Security Sentinel`
- QA: `@Documentation Curator`
- Archive: `@Domain Analyst` + `@Interface Steward` + `@Rules Lawyer` + `@Documentation Curator` + `@Skill Graph Curator`

### Change / STANDARD
- Explorer: `@Ambiguity Gatekeeper` + `@Focus Guard`
- Propose/Review: `@Domain Analyst` + `@Interface Steward` + `@Rules Lawyer`
- Implement: `@Focus Guard` + `@Security Sentinel`
- QA: `@Documentation Curator`
- Archive: `@Domain Analyst` + `@Interface Steward` + `@Rules Lawyer` + `@Documentation Curator` + `@Skill Graph Curator`

## 3) LLM Cognitive Execution Protocol (MUST)

When transitioning to a new phase, the Agent MUST check the **Mounted Roles** listed in `LIFECYCLE.md` and explicitly embody them inside the `<Cognitive_Brake>` block.

**If the Role Matrix is ignored or unused:**
- The LLM defaults to a generic "Coder" persona, which fails to produce required WAL fragments (Domain/API/Rules) or violates scope (Focus Guard).
- This will cause the deterministic Python gates (e.g., `writeback_gate.py`, `scope_guard.py`) to **FAIL**, blocking the workflow.

**How the LLM MUST handle multiple roles:**
In the `<Cognitive_Brake>`, explicitly state the active roles and their required artifacts.
*Example (Phase 4: Implement):*
```xml
- Role Assumption: As @Focus Guard, I will only modify `UserService.java`. As @Security Sentinel, I will not log user passwords in the new error handler.
```
*Example (Phase 6: Archive):*
```xml
- Role Assumption: As @Domain Analyst, I must write the DB schema WAL. As @Interface Steward, I must write the API WAL. As @Documentation Curator, I must finalize the Delivery Capsule.
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
