---
name: "local-code-intelligence"
description: "Three pure-local tools (BM25 wiki search, Java symbol index, failure memory) for zero-cost context. TRIGGER at Explorer phase before reading any source files, and before writing Allowed Scope — runs wiki_search.py, code_index.py, and failure_memory.py."
---

# Local Code Intelligence

Three always-available tools that run purely locally with no external dependencies,
no API calls, and no token budget consumption. They read pre-built index files and
return structured data for the agent to act on.

---

## When to Use

Invoke at the START of any Explorer or Implement phase, before reading files:
- Scope is unknown → use wiki search instead of blind Knowledge Graph drill-down
- Writing a Focus Card → use code impact query to enumerate callers/importers
- Starting a Change task → use failure memory to pre-warn about similar past failures
- Blast radius feels larger than expected → use code impact query

## When NOT to Use

- Code index doesn't exist yet (run `--build` once after cloning the repo)
- Pure documentation tasks (DocQA, LEARN) — these don't modify code, no impact needed
- As a substitute for actually reading the code — these are hints, not ground truth

---

## Tool 1 — Wiki Search (`wiki_search.py`)

**What:** BM25 keyword search over all `.claude/wiki/**/*.md` files. Returns ranked
document paths with excerpts. Pure Python stdlib, no external libraries.

**When:** Scope unknown, need to find which wiki document covers a topic.

```bash
# Basic search
python3 .claude/scripts/local_intel/wiki_search.py --query "API tenant isolation" --top 3

# JSON output for scripting
python3 .claude/scripts/local_intel/wiki_search.py --query "migration gate DDL" --json

# Rebuild index (after adding new wiki docs)
python3 .claude/scripts/local_intel/wiki_search.py --rebuild
```

**Integration with Context Funnel:**
- Run BEFORE opening `KNOWLEDGE_GRAPH.md` when scope is unknown.
- Take the top result path and read it directly — this replaces 1-2 manual drill-down steps.
- The file you actually READ still counts toward wiki budget; the search itself does not.

**Index location:** `.claude/runs/local_intel/wiki_bm25.json` (gitignored, rebuilt on demand)

---

## Tool 2 — Java Code Index (`code_index.py`)

**What:** Regex-based Java symbol indexer. Builds a call graph and import graph from
all Java source files and MyBatis mapper XMLs. Pure Python, no JVM needed.

**Note on accuracy:** Method-call detection is name-only (not type-resolved).
Results are approximate — use as hints, not proof. A method named `save` may appear
in the callers list even if it's calling a different `save`. Verify with grep when critical.

```bash
# Build / rebuild index (run once after checkout, and after large refactors)
python3 .claude/scripts/local_intel/code_index.py --build

# Who calls this method? (for blast radius estimation)
python3 .claude/scripts/local_intel/code_index.py --who-calls createOrder

# Which mapper XMLs touch this table? (for Scenario B1/B2: DB migration)
python3 .claude/scripts/local_intel/code_index.py --what-touches-table orders

# Full impact analysis of a file change (importers + callers)
python3 .claude/scripts/local_intel/code_index.py --impact-of src/main/java/com/example/service/OrderService.java

# Find symbol by name fragment
python3 .claude/scripts/local_intel/code_index.py --symbol OrderRepository

# Index status
python3 .claude/scripts/local_intel/code_index.py --status
```

**Integration with Focus Card authoring:**
Run `--impact-of <target_file>` BEFORE writing `## Allowed Scope`. Add all impacted
files to the scope list (or explicitly document why they're excluded).

**Integration with impact_gate.py:**
`impact_gate.py` (mounted by `focus_guard` role) uses this index automatically.
If the index is absent, the gate downgrades to WARN (non-blocking).

**Index location:** `.claude/runs/local_intel/code_index.json` (gitignored, rebuild with `--build`)

---

## Tool 3 — Failure Memory (`failure_memory.py`)

**What:** Cross-session append-only store of gate failures and rollbacks. Enables
future sessions to recognize recurring failure patterns before they happen.

```bash
# Query before starting work (pre_hook)
python3 .claude/scripts/local_intel/failure_memory.py query \
  --intent Change --phase Implement --profile STANDARD

# Record a failure (fail_hook — MANDATORY)
python3 .claude/scripts/local_intel/failure_memory.py record \
  --intent Change --profile STANDARD --phase QA \
  --gate linter.py --pattern "missing Javadoc on public method" \
  --task-id "Change:STANDARD:order_service:20260517"

# Record a successful approach (Archive phase)
python3 .claude/scripts/local_intel/failure_memory.py record-success \
  --intent Change --profile PATCH --phase QA \
  --note "Slim spec + single-file change: all gates cleared without bypass"

# Statistics across all sessions
python3 .claude/scripts/local_intel/failure_memory.py stats
```

**Integration with fail_hook:**
Every gate failure MUST be recorded before state rollback. This is enforced by
the `fail_hook` definition in `HOOKS.md`.

**Integration with pre_hook:**
At Explorer phase start (Change intent), query for similar failures. Output is
advisory — include any top matches in the `<Cognitive_Brake>` as warnings.

**Storage:** `.claude/runs/local_intel/failure_memory.json` (gitignored, max 500 records FIFO)

---

## Bootstrap (First-Time Setup)

```bash
# Build both indexes after cloning the repo
python3 .claude/scripts/local_intel/wiki_search.py --rebuild
python3 .claude/scripts/local_intel/code_index.py --build

# Verify
python3 .claude/scripts/local_intel/wiki_search.py --status
python3 .claude/scripts/local_intel/code_index.py --status
```

Add to `.claude/scripts/tools/bootstrap.py` or run manually after large refactors.
Indexes are stored in `.claude/runs/local_intel/` (gitignored).

---

## Related Skills

- [wal-documentation-rules](../wal-documentation-rules/SKILL.md): uses code index to find affected mappers during Scenario B1/B2
- [security-review-checklist](../security-review-checklist/SKILL.md): uses `--what-touches-table` to find all data access paths for sensitive tables
- [systematic-debugging](../systematic-debugging/SKILL.md): uses `--who-calls` to trace call chains during root-cause investigation
- [task-decomposition-guide](../task-decomposition-guide/SKILL.md): uses `--impact-of` to size blast radius before decomposing an EPIC
