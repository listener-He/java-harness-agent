# Context Funnel (Navigation + Write-back)

Two symmetric protocols:
- **Forward (navigation)**: how the Agent collects context without blind searching.
- **Reverse (write-back)**: how the Agent writes stable knowledge back to the wiki during `Archive`.

---

## Forward Funnel — Navigation Rules

### Rule 0: Direct Read when scope is explicit (MUST)
When the user provides an explicit scope (file path, directory, class/method, or pasted snippet) and the goal is learning:
- Read the target directly first.
- Use the wiki funnel only if background context is still needed after the direct read.
- Do NOT start with a Knowledge Graph drill-down for this scenario.

### Rule 0.5: Local Search Pre-flight (SHOULD, before manual drill-down)
When scope is NOT explicit, run local search tools BEFORE opening wiki or code files.
These tools are pure local — zero network calls, zero token cost.

**Wiki semantic search (BM25):**
```bash
python3 .agents/scripts/local_intel/wiki_search.py --query "<intent keywords>" --top 3
```
- Returns ranked wiki document paths with excerpts.
- Use the top result as the starting point instead of `KNOWLEDGE_GRAPH.md → index.md` drill-down.
- Still counts toward wiki budget when you actually READ the returned file.
- Skip if the query is too vague (< 3 content words); fall back to Rule 1.

**Code impact query (before writing Focus Card):**
```bash
python3 .agents/scripts/local_intel/code_index.py --impact-of <target_file>
python3 .agents/scripts/local_intel/code_index.py --who-calls <MethodName>
python3 .agents/scripts/local_intel/code_index.py --what-touches-table <table_name>
```
- Use to enumerate callers/importers of the changed file BEFORE writing the Allowed Scope list.
- Does NOT consume code budget (it reads the index file, not source files directly).
- Requires `code_index.py --build` to have been run. If index absent: skip and fall back to grep.

**Failure memory query (at session start for Change intent):**
```bash
python3 .agents/scripts/local_intel/failure_memory.py query --intent Change --phase <phase>
```
- Returns top-5 similar past failures to warn the agent before it repeats them.
- Output is advisory only — does NOT block execution.

### Rule 0.1: Budget Preflight (MUST)
Before any heavy navigation, internally assess the goal and enforce hard resource budgets.
No need to output a verbose preflight block to chat unless specifically requested.

**Hard Limits:**
- Wiki budget: 3 distinct wiki documents
- Code budget: 8 distinct workspace files
- Web Search budget: 2 distinct external searches (`web_search` / `fetch_url`)
- Same-file pagination reads (different line ranges) do NOT consume additional budget.

**Stop condition:** If any budget is hit and no auto-extension trigger applies, escalate via Rule 5. See Rule 4.5 for Tier 1 auto-extension logic and Rule 4.6 for Tier 2.

### Rule 1: Start at the root (MUST)
Context collection MUST begin by reading:
- [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)

### Rule 2: Drill down via indexes (MUST)
1. In `KNOWLEDGE_GRAPH.md`, identify the correct domain index (e.g., [domain/index.md](../llm_wiki/wiki/domain/index.md)).
2. Read that `index.md`.
3. Follow the link to the specific document you need.

### Rule 3: Fallback search is last resort (MAY)
Only when the index tree cannot locate the concept, search within `llm_wiki/wiki/`.

### Rule 4: Budgeted Navigation Detail

#### 4.1 Counting Rules
- Wiki budget: one unit per distinct wiki markdown file read.
- Code budget: one unit per distinct workspace file read.
- Pagination of the same file does NOT count.

#### 4.2 Example-First (Code Read Default)
For `Change` intent, attempt to locate a correct in-repo example before broad reading.
- First 2 code reads SHOULD capture one end-to-end example (typically `Controller + Service` or `Entity + Mapper/XML`).
- Only if the example is missing, conflicting, or insufficient: enter escalation within the remaining budget.

#### 4.3 Saturation Gate — Stop Reading When Any Is Met
- **Template acquired**: any 2 of (route shape, DTO validation style, service entry pattern, mapper/SQL pattern, table field pattern)
- **Integration point acquired**: a concrete usage example of the dependency (e.g., a `Provide/Template` call shape)
- **Executable chain acquired**: a known-good call chain exists; remaining work is a mechanical extension

#### 4.4 Stop-Wiki and Stop-Code (Hard Stop Signals)

These rules fire BEFORE auto-extension evaluation. If a hard stop fires, do not auto-extend — escalate immediately.

**Wiki "no-gain" definition**: a wiki read did NOT add constraints that affect DB / API / permissions / flow and did NOT reduce rework risk.
- If 3 consecutive wiki reads are "no-gain": hard stop — escalate.
- **Wiki-Rot Fallback**: if the wiki appears outdated, contradictory, or lacks implementation details — STOP reading the wiki and shift to workspace code. Code is the ultimate source of truth. This may trigger a Wiki-Rot Bypass auto-extension (see 4.5).

**Code scope shrink rule:**
- After each code read, update the target file/class/method list — it MUST be smaller or more precise than before.
- If scope does not shrink for 2 consecutive reads: hard stop — escalate.

#### 4.5 Auto-Extension Triggers — Tier 1 (Silent, No Block Required)

When the Agent is making measurable progress, budgets auto-extend without requiring a formal `<Confidence_Assessment>` block. The Agent evaluates these triggers after each budget-consuming read and silently increments the effective limit when one fires.

| Trigger | Condition | Grant |
|---|---|---|
| **Progress Signal** | Agent has confirmed ≥ 3 distinct facts (with file/line evidence) AND is tracking a specific call chain, symbol trail, or domain concept. Fires once per budget category per session. | Wiki +1 / Code +2 / Web +1 |
| **Saturation Near-Miss** | Agent has met 2 of the 3 saturation gates from Rule 4.3 (template / integration point / executable chain) and the 3rd gate has a concrete next target. Fires once per session. | Code +2 |
| **Wiki-Rot Bypass** | Wiki is confirmed outdated or contradictory by workspace code evidence (not by assumption). Agent has already shifted to code as source of truth (Rule 4.4). Fires once per session. | Code +3 / Web +1 |
| **External Dependency** | The code under investigation calls an external library, framework, or API whose contract/behavior is not documented in-repo and not inferrable from the current code budget. Fires once per session. | Web +2 |

**Constraint:** Each trigger fires at most once per session. Auto-extensions are cumulative with Tier 2 extensions but MUST NOT exceed the Hard Ceilings:

| Budget | Base | Max Auto | Max Tier 2 | Hard Ceiling |
|---|---|---|---|---|
| Wiki | 3 | +3 | +2 | 8 |
| Code | 8 | +7 | +5 | 20 |
| Web Search | 2 | +2 | +2 | 6 |

#### 4.6 Confidence_Assessment — Tier 2 (Explicit Block)

When auto-extension triggers are exhausted or do not apply, and the Agent is close to a breakthrough, it MAY output a `<Confidence_Assessment>` block to request additional budget.

**Format:**
```xml
<Confidence_Assessment>
- Consumed: wiki X/3, code Y/8, web Z/2
- Auto-extensions used: [list which Tier 1 triggers have fired, or "none"]
- Missing concept: [specific concept / symbol / file — not a vague category]
- Next target: [exact file path, symbol name, or search query]
- Why blocking: [one sentence]
</Confidence_Assessment>
```

**Grant per block:** +2 wiki / +3 code / +2 web search (each can be requested independently — only include the budget(s) you need).
**Constraint:** Tier 2 can fire at most once per budget category per session. Hard Ceilings still apply.

#### 4.7 Web Search Budget — Rules

Web Search (`web_search`, `fetch_url`) is a distinct budget category for external information not available in-repo.

**Counting Rules:**
- One unit per distinct `web_search` or `fetch_url` call, regardless of result count.
- Follow-up searches on the same domain/topic within the same investigation thread count as new units.

**When to use Web Search:**
- External dependency contract/behavior not documented in-repo (may auto-trigger External Dependency grant).
- Upstream library changelog / migration guide for dependency upgrade (Scenario E).
- Reference implementation or algorithm documentation for performance tuning (Scenario D).
- Security vulnerability database lookup when `secrets_linter.py` flags a dependency.

**When NOT to use Web Search:**
- Information likely available in the workspace wiki or code.
- General "research" without a specific, named target.
- As a substitute for reading in-repo documentation.

**Hard Ceiling:** 6 total (base 2 + Tier 1 max 2 + Tier 2 max 2). Hit ceiling → escalate.

### Rule 5: Escalation Protocol (MUST)
If budgets are exhausted OR stop rules trigger without meeting success criteria, request human help — do NOT continue reading.

#### 5.1 Escalation Card Format (Required)
```
- Consumed: wiki X/(3+A), code Y/(8+B), web Z/(2+C)  [A,B,C = auto-extensions granted]
- Auto-extensions used: [list triggers fired, or "none"]
- Confirmed facts: (≤ 5 bullets)
- Missing info: (≤ 2 bullets — must be specific)
- Why blocking: (one sentence)
- Proposed next targets: (≤ 5 file paths, keywords, or search queries)
- Request (small step): wiki +1 / code +2 / web +1
- Fallback if still missing: pick one of:
    - Ask 1 critical question
    - Request a concrete anchor (class / table / entrypoint) from human
    - Deliver a minimal viable plan with explicit risks stated
```

#### 5.2 Lifecycle Persistence on Escalation
Set the intent row in `launch_spec_*.md` to `WAITING_APPROVAL`. The `Artifact` column must already contain the `task_brief.md` path — if not, write it now before setting the status.

---

## Reverse Funnel — Write-back Rules

Write-back eligibility is defined in [ROUTER.md](ROUTER.md) (by profile and flags).

**Profile split:**
- **PATCH**: No WAL write-back. Move openspec to `archive/` and write drift_queue entry only. Wiki refresh is deferred to milestone or `@wiki-update`.
- **STANDARD**: Full WAL write-back as described below.

**Protocol (STANDARD only):**
1. Read [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md) to find the correct mount point.
2. Do NOT edit shared `index.md` files directly.
3. Write a WAL fragment into the target domain `wal/` directory.
   - Example (API): `../llm_wiki/wiki/api/wal/YYYYMMDD_feature_x_api_append.md`
   - Example (Data/DB): `../llm_wiki/wiki/data/wal/YYYYMMDD_feature_x_db_schema.md` (DO NOT write `.sql` files into the project root `sql/` directory).
4. Merge and splitting are performed in a low-conflict window (typically by a human or by the compactor script when explicitly triggered).
5. If an index exceeds the hard size limit: it MUST be split (see `ARCHIVE_WAL.md`).

**Few-Shot Example (DB Change Archive):**
When generating a new table or altering a schema, the Agent MUST NOT drop a raw `.sql` file in the project root.
*Correct behavior:* Create a Markdown file `.agents/llm_wiki/wiki/data/wal/20260419_add_tenant_asset_table.md` containing the DDL code blocks and ER mapping notes.

---

## Hard Constraints

- Links inside `.agents/` MUST use relative paths from the current file.
- If expertise is unclear: consult [skill-index](../skills/skill-index/SKILL.md).
- Every `index.md` MUST provide a 1–2 sentence summary for each linked child document.
