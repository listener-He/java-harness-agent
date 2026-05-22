# Task Brief Schema (Contract Template)

This is the required contract format for Phase 2 (Propose).

Rules:
- During an active workflow, the proposal document MUST be stored under `.claude/runs/task-briefs/` as `<YYYY-MM-DD>_<slug>_task_brief.md`.
- During `Archive`, the Agent MUST move `<YYYY-MM-DD>_<slug>_task_brief.md` into `.claude/wiki/archive/` to keep the wiki stable and reduce merge conflicts.
- Optional curation: humans (or an explicit librarian run) may later link archived task briefs from the wiki. Do NOT edit shared wiki indexes as part of normal execution unless explicitly requested.

---

## Slim Spec (LOW risk only)

When the change is LOW risk, `<YYYY-MM-DD>_<slug>_task_brief.md` MAY be downgraded to a Slim Spec to reduce review fatigue and documentation cost.

Hard rules:
- The document MUST include the marker `spec_mode: SLIM`.
- The document MUST contain all sections below.

```markdown
spec_mode: SLIM

# Change Summary
- What changed: one sentence
- Why: one sentence

# Scope of Change
- File/module list (paths only)

# Risk & Rollback
- Why LOW: one sentence
- Rollback steps: one sentence or a short list

# Verification & Evidence
- Local verification: build/test/manual steps you actually ran
- Evidence: logs/snippets/screenshots/links (if any)
```

## Standard Spec (MEDIUM/HIGH risk) — Dimension-Driven

When the change is MEDIUM or HIGH risk, you MUST use the Standard Spec format. The structure follows a **spec-floor + dimension-gated** model: a fixed safety floor that every change carries, plus dimension-gated sections that only appear when the change actually touches that dimension.

### Frontmatter (required, exact order)

```markdown
spec_mode: STANDARD
risk: MEDIUM   # or HIGH
dimensions: [domain, api, data, tech_arch, patterns]   # subset of the known set; empty list `[]` is legal
```

- `spec_mode: STANDARD` — selects this template.
- `risk:` — narrowed semantics: drives the **flow** (HIGH triggers Approval Gate, one ADR per actual irreversible decision (or explicit "mechanical" note), adversarial-review Category B). Does NOT decide which sections are required. Both `MEDIUM` and `HIGH` carry the same spec-floor + dimension-gated rules.
- `dimensions:` — YAML inline list. Known starter set (gate FAILs only when a declared dimension's section is missing/empty; unknown names WARN but do not FAIL — the set is open for ADR-driven extension):

  | dimension | gates section | use when the change … |
  |---|---|---|
  | `domain` | §2 Domain Model | introduces or modifies business terms / state machines / aggregates |
  | `api` | §3 API Contract | adds or changes a public HTTP/RPC/SDK contract |
  | `data` | §4 Data Model | alters DB schema, indexes, migrations, table layout |
  | `tech_arch` | §8 Technical Architecture | introduces components, deployment topology, third-party deps |
  | `patterns` | §9 Design Patterns Applied | introduces or codifies an architectural pattern |

### Hard rules

- **`## Allowed Scope`** (machine-readable allowlist) — **always required** for STANDARD spec_mode. SLIM mode is exempt (it uses `# Scope of Change` instead, with no enforcement). Format and parsing rules below.
- **Spec-floor**: §1 Context, §5 Business Logic, §6 Non-Functional Constraints, §7 Acceptance Criteria — **always required**, regardless of `dimensions:`. Header MUST be present and body MUST be substantive (not `None`, `N/A`, `无`, or whitespace). Spec-floor exists so a security-only / observability-only / config-only change cannot legally omit its NFR and AC documentation.
- **Dimension-gated**: §2 / §3 / §4 / §8 / §9 — required if and only if the corresponding dimension is in `dimensions:`. When required, header AND body MUST be present and substantive. When NOT required, the section MAY be entirely omitted (no header). Writing the header with `None` body is tolerated for backward compatibility with legacy briefs.
- **Heuristic backstop**: `task_brief_gate.py` scans Allowed Scope path prefixes; if a typical signature appears (`controller/`, `web/`, `mapper/`, `dao/`, `entity/`, `migration/`, `event/`, `domain/`) but the corresponding dimension is not declared, the gate emits WARN with a hint — never FAIL, since path conventions vary.
- **Unknown dimensions** in `dimensions:` produce WARN, never FAIL. To add a new dimension permanently (e.g. `security`, `observability`, `config`), open an ADR and update this schema + the gate's known set in the same PR.
- **Empty `dimensions: []`** is legal and means: only spec-floor sections (§1/§5/§6/§7) are required. Use for pure internal refactors, bugfixes that don't touch any of the 5 dimensions, or harness/tooling changes that genuinely fit none.

### `## Allowed Scope` format (parsed by `task_brief_gate.py` and `scope_guard.py`)

```markdown
## Allowed Scope

- src/main/java/com/example/order/OrderService.java
- src/main/java/com/example/order/
- .claude/runs/task-briefs/2026-05-22_<slug>_task_brief.md
```

Parsing rules — keep entries simple to avoid surprising the parser:

- One `-` bullet per entry.
- **Bare paths only**: the parser strips surrounding markdown backticks (`` `path` `` is equivalent to `path`) and stops at the first whitespace, so trailing inline annotations like ` (this file)` or ` # note` are dropped. Prefer no annotation at all for unambiguous diffs.
- **Trailing `/` = directory prefix**: `src/foo/` matches any file under that directory.
- **No trailing `/` + contains `/` = file prefix** (gate behavior): `src/foo/Bar.java` is registered as a file path. `scope_guard.py` enforces it as an exact match; `task_brief_gate.py` treats it as a prefix for the AC↔Scope coherence check.
- `- None` (case-insensitive) is treated as "no entry" — useful only to keep the section non-empty for SLIM templates that mistakenly migrate here.

### Section templates

```markdown
spec_mode: STANDARD
risk: MEDIUM   # or HIGH (narrowed semantics — flow only)
dimensions: [<subset of: domain, api, data, tech_arch, patterns>]

## Allowed Scope        ← MACHINE-READABLE ALLOWLIST (always required for STANDARD)
- <bare path or directory prefix, one per bullet — see format rules above>

## 1. Context           ← SPEC-FLOOR (always required, substantive)
- Business goal: one sentence.
- Scope of change: list modules/packages/key classes to be changed (objective checklist for review and QA).
- Dependencies: list the wiki documents you read (MUST include relative links).
  - Example: `depends_on: [../wiki/domain/index.md]`

## 2. Domain Model      ← DIMENSION-GATED (required iff `domain` in dimensions; otherwise omit this whole section)
- New or updated terms.
- State machine changes or enum updates.

## 3. API Contract (Handoff)   ← DIMENSION-GATED (required iff `api` in dimensions)
This section MUST be highly structured when present.
- Endpoint: `POST /api/v1/...`
- Header/Auth: token required? special headers?
- Request:
  - Provide exact field types, required/optional, validation rules.
  - Provide a standard JSON example.
- Response:
  - Provide the full JSON response schema (including error response shape).

## 4. Data Model        ← DIMENSION-GATED (required iff `data` in dimensions)
- Table name, new fields, types, defaults, indexes.

## 5. Business Logic    ← SPEC-FLOOR (always required, substantive)
- Step-by-step behavior.
- Error handling and fallback branches.

## 6. Non-Functional Constraints (Hard Constraints)   ← SPEC-FLOOR (always required, substantive)
- Security & permissions.
- Concurrency & idempotency.
- Forbidden patterns (DO NOT do).
- Rollback steps for partial failures.

## 7. Acceptance Criteria (Testing)    ← SPEC-FLOOR (always required, substantive)
This section MUST use structured language suitable for automated tests.
- Happy path: Given / When / Then.
- Edge cases: invalid params, concurrency, permission denied, etc.
- Unit test requirements: key branches and asserts.

## 8. Technical Architecture    ← DIMENSION-GATED (required iff `tech_arch` in dimensions)
- **Component View**: list the components (services, modules, packages, external systems) that participate; show data/control flow direction between them. Mermaid diagram acceptable but not required.
- **Deployment View**: where each component runs (process, container, pod, node); any new infrastructure needed.
- **Third-party Dependencies**: new libraries or services pulled in, with version and reason. If "None", say so explicitly.
- **Technology Selection Rationale**: for any non-default tech choice (new framework, queue, cache, storage), state why it was picked over the project's existing alternatives. Reference any ADR-NNNN written in `.claude/wiki/wiki/architecture/adr/`.

## 9. Design Patterns Applied    ← DIMENSION-GATED (required iff `patterns` in dimensions)
- **Layering Rules**: where this change sits in the layered architecture (Controller / Service / Repository / Domain); any cross-layer call that violates the default convention must be justified here.
- **Key Patterns**: enumerate the GoF / DDD / integration patterns the design relies on (Strategy, Factory, Repository, Aggregate Root, Anti-Corruption Layer, Saga, Outbox, etc.). For each: one line on which class/component embodies it.
- **Anti-Corruption Layer (ACL)**: when integrating with an external system or a legacy domain, name the adapter/translator that prevents external models from leaking into our domain. If no integration, say "N/A".
- **Forbidden Patterns**: explicitly call out patterns this change does NOT use (e.g. "no shared mutable singleton state", "no synchronous fan-out to >3 downstreams"). These mirror Section 6 but at the pattern level.
```

### Omission vs `None`

| What you wrote | Meaning | Gate behavior |
|---|---|---|
| Section header absent (no `## 2.` line) | "This change doesn't touch the domain" | OK iff `domain` not in `dimensions:`; FAIL otherwise |
| Section header present, body is `None` | "Legacy / placeholder" | OK iff `domain` not in `dimensions:` (tolerated); FAIL otherwise |
| Section header present, body has substantive content | "Documented" | OK |

Prefer outright omission over `None` for new briefs — it makes the intent unambiguous.
