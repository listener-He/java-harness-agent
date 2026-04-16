# Intent Gateway Router

This document is the routing contract. It selects an execution profile, then optionally launches a lifecycle queue.

For lifecycle rules, see [LIFECYCLE.md](../workflow/LIFECYCLE.md).

## Guiding Principle
Do not create more intent codes to represent every micro-scenario.

Instead:
- Keep a small set of top-level intents.
- Use profiles + parameters to express the differences in execution.

## 0) Shortcuts (Explicit Routing)
If the user provides an explicit shortcut, it MUST override automatic routing.

Supported shortcuts:
- `@read` / `@learn`: force Profile `LEARN` (read-only)
- `@patch` / `@quickfix`: force Profile `PATCH` (small change / bugfix)
- `@standard`: force Profile `STANDARD` (full lifecycle)

### Shortcut DSL (Composable)
Shortcuts can be composed with flags to express common workflows as a small DSL.

Syntax:
```text
@<profile> <flags...> -- <natural language request or question>
```

Profiles:
- `@learn`: read-only explanation (no launch, no write-back)
- `@patch`: small change / bugfix (minimal artifacts, hooks still apply)
- `@standard`: full delivery lifecycle

Flags (order-independent):
- Scope / read:
    - `--scope <path|glob|symbol>`: explicit scope (file/dir/symbol)
    - `--direct`: force direct reads (do not start with Knowledge Graph drill-down)
    - `--funnel`: force the funnel even if scope is explicit
    - `--depth shallow|normal|deep`: explanation depth (LEARN only)
- Risk / artifacts:
    - `--risk low|medium|high`: explicit risk override
    - `--slim`: force Slim Spec (PATCH only, or STANDARD with `--risk low`)
    - `--changelog`: use Change Log only (PATCH only)
    - `--evidence required|optional|none`: evidence requirement (default: PATCH=required)
- Launch / write-back:
    - `--launch`: force lifecycle launch (STANDARD only)
    - `--no-launch`: force no launch
    - `--writeback`: allow wiki/WAL write-back (not allowed for LEARN)
    - `--no-writeback`: forbid write-back (default)
- Verification:
    - `--test "<cmd>"`: required verification command + evidence
    - `--no-test`: skip tests (LEARN only; PATCH requires an explicit justification)
- DocQA actionize:
    - `--actionize`: convert DocQA into an executable STANDARD queue (requires confirmation)
    - `--yes`: auto-confirm `--actionize` / `--launch` (team use with caution)

Conflict rules (MUST enforce):
- `@learn` MUST NOT be combined with `--launch` or `--writeback`.
- `--launch` MUST be used with `@standard` only.
- `--slim` requires `--risk low` (or implied low risk in PATCH).
- `--actionize` MUST ask for confirmation unless `--yes` is present.

Examples:
```text
@learn --scope src/foo/bar.ts --direct --depth deep -- explain this file
@patch --risk low --slim --test "mvn test -Dtest=OrderServiceTest" -- fix NPE in createOrder
@standard --risk high --launch -- implement tenant permission checks for order list API
@learn --funnel -- what is the API design standard? --actionize
```

## 1) Profiles (Execution Modes)

### Profile: LEARN (Read-only)
Use when the goal is to understand code or explain behavior.
- No launch spec.
- No wiki write-back.
- No lifecycle phases.
- Direct read is allowed and preferred when scope is explicit.

### Profile: PATCH (Small change / bugfix)
Use when the change is small and risk is LOW.
- Minimal artifacts: Slim Spec or Change Log + objective verification evidence.
- No full `Propose -> Review -> Approval` chain by default.
- Hooks still apply (guard/fail/max retries).
- Archive write-back is optional and only when stable knowledge changed.

### Profile: STANDARD (Full delivery)
Use for MEDIUM/HIGH risk changes and any change with wide blast radius.
- Uses the full lifecycle (Explorer -> Propose -> Review -> Approval Gate -> Implement -> QA -> Archive).
- Requires `openspec.md` (full schema for MEDIUM/HIGH).

## 2) Top-level intents (keep this list small)

| Intent | When to use | Default Profile | Launch spec | Write-back |
|---|---|---|---|---|
| `Learn` | “Explain/read/understand this code” with explicit scope | LEARN | No | No |
| `Change` | “Modify code” (feature, refactor, bugfix) | PATCH or STANDARD | Yes (STANDARD only) | Optional (Archive) |
| `DocQA` | “What is the rule/process/template?” | LEARN | No | No (unless actionized) |
| `Audit` | “Assess the codebase” (read-only review/risk scan) | LEARN | No | No |

## 3) Routing rules (Automatic)

### Rule 1: If scope is explicit and the user wants to learn, do Direct Read (MUST)
If the user provides an explicit scope (file path, directory, class/method name, or pasted snippet) and the goal is learning/explanation:
- Select `Learn` + Profile `LEARN`.
- DO NOT start with Knowledge Graph drill-down.
- Use the funnel only if you need background context after the first read.

### Rule 2: Otherwise, use the Context Funnel (MUST)
DO NOT start with full-text search.

The Agent MUST:
1. Read the root: [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)
2. Drill down via: [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)
3. If you cannot pick a specialist skill, consult: [trae-skill-index](../skills/trae-skill-index/SKILL.md)

### Rule 3: Change intent selects profile by risk
- LOW -> Profile `PATCH` (Slim Spec allowed)
- MEDIUM/HIGH -> Profile `STANDARD` (full schema + Approval Gate)

### Rule 4: Actionize DocQA into STANDARD is an explicit opt-in
DocQA is read-only by default.
The Agent MUST NOT launch a lifecycle queue unless:
- the user explicitly requests actionize (via `--actionize` or an equivalent natural language request), and
- the user confirms (or uses `--yes`).

## 4) Internal lifecycle queue codes (used only when launching STANDARD)
When Profile is `STANDARD`, the `Change` intent is expanded into a lifecycle queue using these internal codes:

| Code | Phase | Notes |
|---|---|---|
| `Explore.Req` | Explorer | Clarify requirements + scope anchors |
| `Propose.API` | Propose -> Review | API contract and design |
| `Propose.Data` | Propose -> Review | Database schema changes |
| `Implement.Code` | Implement -> QA | Code changes |
| `QA.Test` | QA | Tests + evidence |

## 5) Launch Spec (STANDARD only)
When launching a lifecycle queue:
1. Persist to `router/runs/launch_spec_{timestamp}.md`
2. Drive transitions by updating only `Status/Phase/Failed_Reason`
3. Optional helper: `python ../scripts/harness/engine.py init "..."` can create and maintain the file

After each `Archive` phase, the Agent MUST re-read the launch spec to decide whether to continue with the next intent.

### Launch Spec Template
Status enum: `PENDING`, `IN_PROGRESS`, `DONE`, `WAITING_APPROVAL`, `FAILED`

```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## State Machine
| Intent | Status | Phase | Artifact/Log | Failed_Reason |
|---|---|---|---|---|
| Explore.Req | IN_PROGRESS | 1_Explorer | `explore_report.md` | - |
| Propose.API | PENDING | - | - | - |
| Implement.Code | PENDING | - | - | - |

## Resume
- If the session is interrupted, the first action is to read this file and restore from `Status/Phase`.
- If any row is `WAITING_APPROVAL`, stop and wait for human approval; then switch back to `IN_PROGRESS` and continue.
- If any row is `FAILED`, stop and report `Failed_Reason`.
```
