---
description: Distill knowledge from current workspace code into the wiki, reconciling stale claims under a user-bounded scope
argument-hint: <scope-spec> [--dry-run] [--max-add N] [--allow-direct-replace]
---

User-driven, **code → wiki** knowledge reconciler. Complements [knowledge-extractor](../agents/knowledge-extractor.md) (Archive-time WAL) and the [librarian](../agents/librarian.md) Distill flow (wiki → wiki redundancy scan) by reading the **current workspace code** and reconciling existing wiki claims against it.

This command **does not generate** new prose from scratch — it acts as a **reconciler**. Any phase where you feel you are "generating" rather than "diffing", STOP and re-read [§ Anti-patterns](#anti-patterns).

## Goals

1. Let the wiki actively distill from code reality, not only passively accumulate WAL on Archive
2. Actively correct stale wiki claims (not just additively append)
3. Keep scope user-bounded — no full-repo unsupervised scans
4. Every wiki mutation traceable to a current code `file:line` or commit

## Methodology

| # | Principle | Meaning |
|---|---|---|
| M1 | **Evidence-grounded** | Every wiki claim entering the plan MUST cite a current `file:line`. Reuse [documentation-curator](../agents/documentation-curator.md) for writing. |
| M2 | **Diff-based, not regenerative** | Compute the delta (existing wiki claim ↔ current code fact); never rewrite wholesale |
| M3 | **Bounded by user scope** | `ScopeFrame` is locked in Phase 1; all subsequent reads/writes MUST stay inside it |
| M4 | **Classify before plan** | Every claim gets a stale-label (see [Stale Decision Matrix](#stale-decision-matrix)) before any action is proposed |
| M5 | **Human-approved write-back** | Phase 5 emits a plan; nothing is written until user `[x]` confirms |

---

## Step 1 — Parse `$ARGUMENTS`

Extract:
- `<scope-spec>` (required) — at least one of:
  - `domain:<name>` → adds `<name>` to `ScopeFrame.domains`
  - `path:<glob>` → adds glob to `ScopeFrame.files`
  - `topic:"<keywords>"` → adds keywords to `ScopeFrame.topics`
  - Combine freely: `domain:order topic:"cancellation flow"`
- `--dry-run` — run through Phase 5 (plan), STOP before any write
- `--max-add N` — cap ADD actions per run (default 20). Protects against accidental dump
- `--allow-direct-replace` — default **disabled**. When enabled, ORPHANED claims may be removed/replaced inline in `index.md` (form B). Everything else still goes through WAL (form A)

If `ScopeFrame` ends up empty after parsing → STOP with message "scope-spec missing — provide domain: / path: / topic:".

Generate a `run_id` of form `distill-<YYYY-MM-DD>-<HHMM>-<scope-tag>` (e.g. `distill-2026-05-26-1430-order`). Every WAL fragment and audit record this run writes will carry this id in its frontmatter.

---

## Phase 1 — Scope Resolve

Lock the `ScopeFrame`:

```yaml
ScopeFrame:
  domains: [<wiki/<domain>/ targets>]
  files:   [<resolved globs, no <a href="../wal/">wal/</a> prefix>]
  topics:  [<keywords for Phase 3 BM25>]
  run_id:  distill-...
```

**Exit gate**: at least one of `domains`/`files`/`topics` non-empty. Otherwise STOP.

---

## Phase 2 — Code Fact Extraction

Extract **structured** code facts within `ScopeFrame.files`. **Free-text summaries are forbidden** — every fact MUST be one of the kinds below with a `citation`:

| kind | extraction tool |
|---|---|
| `java_method` (public signatures) | [code_index.py](../scripts/local_intel/code_index.py) |
| `endpoint` (`@RestController` / `@*Mapping`) | grep + Read |
| `data_model` (POJO / `@Table` / mapper `<resultMap>`) | grep + Read |
| `business_rule` (`@PreAuthorize` / `if ... throw ...DomainException` / `@Valid`) | grep + Read |
| `config_key` (`application*.yml`, `@Value`, `@ConfigurationProperties`) | grep + Read |
| `example` (extracted from `*Test.java` usage) | Read |

Each fact MUST have `citation: <relative-path>:<line-number>`. **Facts without citation are dropped** (per M1).

**Exit gate**: if `CodeFactSet` is empty → STOP, message "scope too narrow or wrong; no facts extracted".

---

## Phase 3 — Wiki Inventory

Collect existing wiki content inside `ScopeFrame.domains`:

1. Dispatch [local-code-intelligence](../skills/local-code-intelligence/SKILL.md) BM25 search using `ScopeFrame.topics`
2. Read `wiki/<domain>/index.md` **plus all unmerged `wiki/<domain>/wal/*.md` fragments** for each domain in scope (do not skip WAL — recent additions live there)
3. Parse each `.md` into a list of claims. A claim is one bullet/paragraph with potentially a citation. Parse rule:
   - Lines containing `<path>:<line>` or backticked `<symbol>` → extract as `citation`
   - Lines without an extractable citation → set `unanchored: true`

Output `WikiClaimSet` of the form:
```yaml
- text: "OrderService.cancel publishes OrderCancelledEvent"
  source_file: .claude/wiki/wiki/domain/index.md
  source_line: 87
  citation: src/main/java/com/example/order/OrderService.java:142
  unanchored: false
```

---

## Phase 4 — Three-way Diff & Classify

For each `WikiClaim`, apply the [Stale Decision Matrix](#stale-decision-matrix) to assign exactly one label. For each `CodeFact` with no matching claim, label `MISSING_FROM_WIKI`.

Output `DiffReport`:
```yaml
confirmed: <int>
stale: <int>          # STALE + STALE_REF + DRIFT (the actively-correctable set)
orphaned: <int>
redundant: <int>
unanchored_suspect: <int>   # UNANCHORED_STALE candidates — never auto-changed
missing_from_wiki: <int>
```

**Exit gates** (sanity protection):
- `(stale + orphaned) > 0.5 × total_claims` → STOP, message "high stale rate — likely scope misjudgment; reconfirm scope-spec"
- `confirmed == 0 AND total_claims > 5` → STOP, message "no claims confirmed — citation parser may have broken; inspect inventory output"

---

## Phase 5 — Plan & Approve

Translate `DiffReport` into `DistillPlan`. Each plan item MUST include:
- target file + line (for UPDATE/DELETE) or target WAL path (for ADD/MERGE)
- before snippet (current wiki text, when applicable)
- after snippet (proposed text — for ADD/UPDATE)
- citation (the `CodeFact` justifying the action)
- form (A = correction WAL / B = direct replace)

`--max-add N` caps the ADD count.

**Single `AskUserQuestion`** (multi-select, defaults all-checked):
- KEEP confirmed (<count>) — auto, no item shown
- UPDATE stale (<count>)
- DELETE orphaned (<count>) — only enabled with `--allow-direct-replace`
- ADD missing (<count>)
- MERGE redundant (<count>)
- SUSPECT review (<count>) — informational only; never auto-applied

User unchecks → corresponding items skipped. Full reject → STOP, plan discarded.

`--dry-run` STOPs here after rendering the plan (no write).

---

## Phase 6 — Execute & Lint

Apply approved actions per form (see [Replacement Protocol](#replacement-protocol)):

| Action | Form | Target |
|---|---|---|
| ADD | A | `wiki/<domain>/wal/<YYYYMMDD>_<slug>_<category>.md` per [wal-documentation-rules](../skills/wal-documentation-rules/SKILL.md) |
| UPDATE | A (default) | `wiki/<domain>/wal/<YYYYMMDD>_<slug>_correction.md` |
| DELETE | B (forced) | inline `index.md` edit + `wiki/<domain>/wal/<YYYYMMDD>_<slug>_deletion_audit.md` |
| UPDATE on ORPHANED with `--allow-direct-replace` | B | inline `index.md` edit + `wiki/<domain>/wal/<YYYYMMDD>_<slug>_replacement_audit.md` |
| MERGE | A | `wiki/<domain>/wal/<YYYYMMDD>_<slug>_merge_note.md` |

All WAL fragments written this run MUST carry frontmatter:
```yaml
source: h-distill-from-code
run_id: <run_id from Step 1>
scope: { domains: [...], files: [...], topics: [...] }
```

For prose generation inside ADD/UPDATE bodies, dispatch [documentation-curator](../agents/documentation-curator.md) — never write narrative wiki prose inline without that agent's evidence-grounded discipline.

**Lint gate**: run `python3 .claude/scripts/wiki/wiki_linter.py`. FAIL → `git restore .claude/wiki/` (rollback this run's writes) + regenerate plan (max 2 retries; 3rd FAIL → STOP per CLAUDE.md anti-loop).

**Final report** (printed to user):
```
[Run]: <run_id>
[Scope]: domains=[...], files=[...], topics=[...]
[Diff]: confirmed=N stale=N orphaned=N redundant=N missing=N suspect=N
[Applied]: add=N update=N delete=N merge=N (skipped=N)
[Wiki Lint]: PASS
[Audit]: see <wal fragment list>
[Next]: optional — run /librarian Compact to merge corrections into index.md
```

---

<a id="stale-decision-matrix"></a>
## Stale Decision Matrix

The reconciler's heart. Every `WikiClaim` is assigned exactly one label.

| Wiki claim form | Current code state | Label | Default action |
|---|---|---|---|
| Has `file:line` citation + content describes it | file exists, content matches | **CONFIRMED** | none |
| Has `file:line` citation + content describes it | file exists, content has changed | **STALE** | UPDATE (form A) |
| Has `file:line` citation + content describes it | file does not exist | **ORPHANED** | DELETE (form B, requires `--allow-direct-replace`) |
| References a symbol (class / method name) | symbol has been renamed | **STALE_REF** | UPDATE (form A) |
| References a symbol | symbol has been deleted | **ORPHANED** | DELETE (form B, requires `--allow-direct-replace`) |
| No citation; describes a rule/invariant | code still has matching implementation | **UNANCHORED_CONFIRMED** | none (low-confidence; optional citation enrichment) |
| No citation; describes a rule/invariant | no matching implementation in code | **UNANCHORED_STALE** | **SUSPECT only — NEVER auto-changed** |
| Describes a contract (API / field) | same name in code but shape differs | **DRIFT** | UPDATE (form A, code-side wins) |

**Hard rule for unanchored claims**: when there is no `file:line` to verify against, the reconciler **does not modify**. It flags as SUSPECT in Phase 5 and lets the human decide. This is the last firewall against hallucinated "corrections" of content the LLM cannot actually verify.

`REDUNDANT` (duplicate coverage across multiple wiki entries) is detected separately during Phase 4 as a wiki-internal check and yields a MERGE action.

---

<a id="replacement-protocol"></a>
## Replacement Protocol — Two Forms

Direct editing of `index.md` is forbidden in normal operation (per [wal-documentation-rules](../skills/wal-documentation-rules/SKILL.md)). Two legal forms:

### Form A — Correction WAL (default, soft correction)

- Write `wiki/<domain>/wal/<YYYYMMDD>_<slug>_correction.md`
- Body lists: old claim location (`index.md:<line>`) + STALE label + new fact + citation
- [librarian](../agents/librarian.md) Compact run later merges the correction into `index.md`; the old claim is replaced at merge time
- ✅ Honors the WAL contract; nothing about indexing breaks
- ❌ Until librarian Compact runs, old and new claims coexist (accepted trade-off)

### Form B — Direct Replace + Audit (hard correction)

- Directly `Edit` `index.md` to remove/replace the entry
- Simultaneously write `wiki/<domain>/wal/<YYYYMMDD>_<slug>_replacement_audit.md` or `_deletion_audit.md` with: `before` / `after` / `reason` / `run_id`
- Triggered ONLY when:
  - claim is `ORPHANED` (citation target no longer exists; leaving it actively misleads), AND
  - user passed `--allow-direct-replace`
- Default off because form B can overwrite hand-edited content the reconciler cannot fully appreciate

---

<a id="anti-patterns"></a>
## Anti-patterns

Forbidden behaviors — every one of these has bitten a doc-pipeline before. If a phase is about to do one, STOP and ask the user.

- **AP1 Hallucinated facts** — writing a method/path/symbol that does not exist in current code. The biggest risk. Mitigation: every plan item MUST cite a `CodeFact` from Phase 2; no citation = no plan item.
- **AP2 Regenerative distillation** — `rm` the wiki and rebuild from scratch. Destroys hand-edits + invariants. The reconciler is a diff tool, not a generator.
- **AP3 Scope drift** — Reading or writing files outside the locked `ScopeFrame`. Use [scope_guard.py](../scripts/gates/scope_guard.py) discipline mentally even though this command runs outside the task_brief scope-guard hook.
- **AP4 Duplicate insertion** — ADD without checking if the same claim already exists (Phase 3 inventory). Drives wiki bloat against the [policy.md](../rules/policy.md#part-2--write-back-policy-wal--anti-bloat) cap.
- **AP5 Editing `index.md` directly** — violates [wal-documentation-rules](../skills/wal-documentation-rules/SKILL.md). Form B is the only carve-out and it carries an audit record.
- **AP6 Summary-style writes** — copying code content into wiki prose. Wiki should be **pointer-style** (`file:line` link), not a copy. Copies drift; pointers don't.
- **AP7 Sub-agent summary as fact** — when [local-code-intelligence](../skills/local-code-intelligence/SKILL.md) or a sub-agent returns a summary, treat it as a lead, not as truth. Re-Read the source file before writing to wiki.
- **AP8 Auto-delete wiki entries** — DELETE always requires Phase 5 human approval. No exception.
- **AP9 Silent stale overwrite** — Form B without writing the audit record. Every form-B mutation MUST leave a `_audit.md` trail with `before` / `after` / `reason` / `run_id`.
- **AP10 Running inside `task_brief` Archive flow** — Archive's WAL is [knowledge-extractor](../agents/knowledge-extractor.md)'s job (driven by `h-archive` user multi-select). Running this command inside Archive doubles WAL writes and confuses provenance.

---

## Anti-hallucination Guardrails

Four constraints layered on top of the methodology:

1. Every plan item MUST cite a `CodeFact` with `file:line`; items without citation are dropped, not "best-effort guessed"
2. Plan items shown to user MUST include `diff`-style `before` / `after` so the user can scan and reject in one pass
3. "I infer / I suspect" content goes to a `[Open Questions]` block in the plan, NOT to a `DistillPlan` item
4. Any write to wiki MUST pass `wiki_linter.py` (dead-link + line-cap); failure rolls back via `git restore`

---

## Integration Boundaries

| Component | Relationship |
|---|---|
| [local-code-intelligence](../skills/local-code-intelligence/SKILL.md) | **Used** in Phase 3 for BM25 retrieval |
| [code_index.py](../scripts/local_intel/code_index.py) | **Used** in Phase 2 for Java symbols |
| [documentation-curator](../agents/documentation-curator.md) | **Dispatched** in Phase 6 for ADD/UPDATE prose generation |
| [wal-documentation-rules](../skills/wal-documentation-rules/SKILL.md) | **Followed** when writing any WAL fragment |
| [wiki_linter.py](../scripts/wiki/wiki_linter.py) | **Gate** at end of Phase 6 |
| [knowledge-extractor](../agents/knowledge-extractor.md) | **NOT invoked** — that agent is Archive-driven; this command is independent of any task |
| [librarian](../agents/librarian.md) Compact | **NOT invoked** here; user runs it later to merge correction WAL into `index.md` |
| [librarian](../agents/librarian.md) Distill | **Complementary not overlapping** — Distill scans wiki→wiki for redundancy; this command scans code→wiki for stale. Suggested order: `/h-distill-from-code` first, then librarian Distill. |
| [knowledge-architect](../agents/knowledge-architect.md) | **NOT invoked**; if `wiki_linter` reports cap exceeded, surface a hint suggesting the user run knowledge-architect separately |

---

## Anti-loop / Failure Handling

| Trigger | Action |
|---|---|
| Phase 2 `CodeFactSet` empty | STOP — scope too narrow |
| Phase 4 `(stale + orphaned) > 0.5 × total` | STOP — likely scope misjudgment, reconfirm |
| Phase 4 `confirmed == 0 AND total > 5` | STOP — citation parser likely broken |
| Phase 6 `wiki_linter` FAIL | `git restore .claude/wiki/` + regenerate plan, max 2 retries; 3rd FAIL → STOP per CLAUDE.md anti-loop |
| Any phase Reads > 50 files | WARN to user — scope may be too wide |

---

## TaskList

This command does NOT open TaskList. The 6 phases run sequentially in one invocation and are below the threshold in [tasklist-policy.md §1](../rules/tasklist-policy.md). The plan in Phase 5 is the user-facing progress artifact.

---

## Hard Constraints

- **Allowed writes**: `.claude/wiki/<domain>/wal/**` always; `.claude/wiki/<domain>/index.md` only under Form B with `--allow-direct-replace`. Nothing else.
- **No source-code edits** under `src/**`. This is a knowledge-base command, not a code command.
- **No silent defaults** — `<scope-spec>` is required; `--allow-direct-replace` must be explicit.
- **Refuse to write** any wiki content not traceable to a `CodeFact.citation`.
- **Refuse to run** inside an active task_brief flow (detected by `.claude/runs/launch-specs/launch_spec_*.md` having an `IN_PROGRESS` row whose Phase is `Implement`). Per AP10.
