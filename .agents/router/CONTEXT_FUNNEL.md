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

### Rule 0.1: Budget Awareness (SHOULD)
Before any heavy navigation, be aware of soft budget guides. No need to output a preflight block.

**Soft Guides (not hard ceilings):**
- Wiki budget: ~5 distinct wiki documents
- Code budget: ~12 distinct workspace files
- Web Search budget: ~4 distinct external searches
- Same-file pagination reads do NOT consume additional budget.

**If you're approaching these limits without converging:** STOP and ask human. No escalation ceremony — just ask.

### Rule 1: Start at the root (MUST)
Context collection MUST begin by reading:
- [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)

### Rule 2: Drill down via indexes (MUST)
1. In `KNOWLEDGE_GRAPH.md`, identify the correct domain index (e.g., [domain/index.md](../llm_wiki/wiki/domain/index.md)).
2. Read that `index.md`.
3. Follow the link to the specific document you need.

### Rule 3: Fallback search is last resort (MAY)
Only when the index tree cannot locate the concept, search within `llm_wiki/wiki/`.

### Rule 4: Budgeted Navigation (Simplified)

#### 4.1 Counting Rules
- Wiki budget: one unit per distinct wiki markdown file read.
- Code budget: one unit per distinct workspace file read.
- Pagination of the same file does NOT count.

#### 4.2 Example-First (Code Read Default)
For `Change` intent, attempt to locate a correct in-repo example before broad reading.
- First 2 code reads SHOULD capture one end-to-end example (typically `Controller + Service` or `Entity + Mapper/XML`).
- Only if the example is missing, conflicting, or insufficient: ask human for direction.

#### 4.3 Saturation Gate — Stop Reading When Any Is Met
- **Template acquired**: any 2 of (route shape, DTO validation style, service entry pattern, mapper/SQL pattern, table field pattern)
- **Integration point acquired**: a concrete usage example of the dependency
- **Executable chain acquired**: a known-good call chain exists; remaining work is a mechanical extension

#### 4.4 When to Stop and Ask Human
- Wiki reads not adding DB/API/permissions/flow constraints → shift to code.
- Wiki appears outdated or contradictory → trust code, note the drift.
- If you're near budget limits without converging → STOP and ask human.

### Rule 5: Stuck? Ask Human (MUST)
If budgets are exhausted or you're not converging: STOP and ask human directly. No escalation card template needed — just state:
- What you've confirmed (2-3 bullets)
- What you're missing (1 sentence)
- What you need from the human (1 question or request)

Set the intent row in `launch_spec_*.md` to `WAITING_APPROVAL`.

---

## Reverse Funnel — Write-back Rules

Write-back eligibility is defined in [ROUTER.md](ROUTER.md) (by profile and flags).

**Profile split:**
- **PATCH**: No WAL write-back. Write drift_queue entry only. Wiki refresh deferred to milestone or `@wiki-update`.
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
