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

### Rule 0.1: Budget Preflight (MUST)
Before any heavy navigation, internally assess the goal and enforce hard resource budgets.
No need to output a verbose preflight block to chat unless specifically requested.

**Hard Limits:**
- Wiki budget: 3 distinct wiki documents
- Code budget: 8 distinct workspace files
- Same-file pagination reads (different line ranges) do NOT consume additional budget.

**Stop condition:** If any budget is hit, STOP reading and ask the human for guidance or permission to continue.

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

#### 4.4 Stop-Wiki (Elastic) and Fallback to Code
**Wiki "no-gain" definition**: a wiki read did NOT add constraints that affect DB / API / permissions / flow and did NOT reduce rework risk.

- If 3 consecutive wiki reads are "no-gain": SHOULD stop wiki navigation.
- **Wiki-Rot Fallback**: if the wiki appears outdated, contradictory, or lacks implementation details — STOP reading the wiki and shift to workspace code. Code is the ultimate source of truth.
- **Elastic Extension**: if close to a breakthrough, output a `<Confidence_Assessment>` explaining what specific concept is missing and what the next target is (e.g., `Next_Target: architecture/auth_flow.md`). This grants a +2 document budget extension before forcing a hard stop.

#### 4.5 Stop-Code (Elastic)
Code reading must shrink scope on each read.

- After each code read, update the target file/class/method list — it MUST be smaller or more precise than before.
- If scope does not shrink for 2 consecutive reads: SHOULD stop reading.
- **Elastic Extension**: if following a specific call chain (e.g., tracking an interface to its implementation), output a `<Confidence_Assessment>` naming the exact symbol or file needed. This grants a +3 file budget extension before triggering the Escalation Protocol.

### Rule 5: Escalation Protocol (MUST)
If budgets are exhausted OR stop rules trigger without meeting success criteria, request human help — do NOT continue reading.

#### 5.1 Escalation Card Format (Required)
```
- Consumed: wiki X/3, code Y/8
- Confirmed facts: (≤ 5 bullets)
- Missing info: (≤ 2 bullets — must be specific)
- Why blocking: (one sentence)
- Proposed next targets: (≤ 5 file paths or keywords)
- Request: wiki +1 OR code +2 (small step)
- Fallback if still missing: pick one of:
    - Ask 1 critical question
    - Request a concrete anchor (class / table / entrypoint) from human
    - Deliver a minimal viable plan with explicit risks stated
```

#### 5.2 Lifecycle Persistence on Escalation
Set the intent row in `launch_spec_*.md` to `WAITING_APPROVAL`. Include a link to the relevant artifact (e.g., `openspec.md` or the escalation note).

---

## Reverse Funnel — Write-back Rules

Write-back eligibility is defined in [ROUTER.md](ROUTER.md) (by profile and flags).

**Protocol:**
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
- If expertise is unclear: consult [trae-skill-index](../skills/trae-skill-index/SKILL.md).
- Every `index.md` MUST provide a 1–2 sentence summary for each linked child document.
