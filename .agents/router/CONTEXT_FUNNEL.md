# Context Funnel (Navigation + Write-back)

This document defines two symmetric rules:
- Forward navigation: how the Agent MUST collect context without blind searching.
- Reverse write-back: how the Agent MUST write stable knowledge back to the wiki during `Archive`.

## Forward Funnel (Navigation Rules)

### Rule 0: Direct Read when scope is explicit (MUST)
If the user provides an explicit scope (file path, directory, class/method name, or pasted snippet) and the goal is learning/explanation:
- Do a direct read of the target scope first.
- Use the wiki funnel only if additional background context is needed after the first read.
- DO NOT start by drilling down the Knowledge Graph for this scenario.

### Rule 0.1: Implicit Budget & Preflight Check (MUST)
Before any heavy navigation, the Agent MUST internally assess the goal and strictly adhere to the resource budgets.
There is NO NEED to write out a heavy "Preflight block" in the chat unless specifically requested.
- Budgets (Hard Limits): `wiki=3 docs`, `code=8 files` (same-file pagination reads do NOT count).
- Stop conditions: If budgets are hit, the Agent MUST stop reading and ask the human for guidance or permission to continue.

### Rule 1: Always start at the root (MUST)
Context collection MUST start by reading:
- [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)

### Rule 2: Drill down via indexes (MUST)
1. In `KNOWLEDGE_GRAPH.md`, pick the correct domain index (example: [domain/index.md](../llm_wiki/wiki/domain/index.md)).
2. Read that `index.md`.
3. From the `index.md`, follow the link to the specific document you need and read it.

### Rule 3: Fallback search is last resort (MAY)
Only when the index tree cannot locate the concept, the Agent MAY use keyword search within:
- `llm_wiki/wiki/`

### Rule 4: Budgeted Navigation (MUST)
This rule prevents runaway context collection.

#### 4.1 Counting Rules
- Wiki budget counts per distinct wiki document read (each markdown file).
- Code budget counts per distinct workspace file read.
- Reading a different line range (pagination) of the same file does NOT consume additional budget.

#### 4.2 Example-First (Code Read Default)
For `Change` intent, the Agent MUST first attempt to locate a correct in-repo example before broad reading.
- The first 2 code reads SHOULD be used to capture one end-to-end example (typically `Controller + Service` or `Entity + Mapper/XML`).
- Only if the example is missing, conflicting, or insufficient, the Agent MAY enter escalation within the remaining budget.

#### 4.3 Saturation Gate (Stop Reading When Enough)
Stop reading and move to decision/implementation when ANY is met:
- Template acquired: any 2 of (route shape, DTO validation style, service entry pattern, mapper/sql pattern, table field pattern)
- Integration point acquired: a concrete example of the dependency usage (e.g., `Provide/Template` call shape)
- Executable chain acquired: a known good call chain exists and the remaining work is a mechanical extension

#### Rule 4.4 Stop-Wiki (Elastic) & Fallback to Code
Definition (wiki “no-gain”): reading did NOT add constraints that affect DB/API/permissions/flow and did NOT reduce rework risk.
- If 3 consecutive wiki reads are “no-gain”, the Agent SHOULD stop wiki navigation.
- **Wiki-Rot Fallback**: If the Agent detects that the Wiki might be outdated, contradictory, or lacks implementation details, it MUST stop reading the Wiki and **shift attention to the workspace code**. The workspace code is the ultimate source of truth.
- **Elastic Extension**: If the Agent believes it is close to a breakthrough, it MAY output a `<Confidence_Assessment>` explaining what specific concept is missing and request an extension (e.g., `Next_Target: [architecture/auth_flow.md]`). The system will grant a +2 document budget extension before forcing a hard stop.

### Rule 4.5 Stop-Code (Elastic)
Code reading must generally shrink scope.
- After each code read, the Agent MUST update the scope (target file/class/method list) and it MUST be smaller or more precise.
- If scope does not shrink for 2 consecutive code reads, the Agent SHOULD stop reading.
- **Elastic Extension**: If the Agent needs to follow a specific call chain to complete its understanding (e.g., tracking an interface to its implementation), it MAY output a `<Confidence_Assessment>` detailing the exact symbol or file it needs to read next. The system will grant a +3 file budget extension before triggering Escalation Protocol.

### Rule 5: Escalation Protocol (MUST)
If budgets are exhausted OR stop rules trigger and success criteria are not met, the Agent MUST request human help instead of continuing to read.

#### 5.1 Escalation Card (Required Format)
- Consumed: `wiki X/3`, `code Y/8`
- Confirmed facts (<= 5 bullets)
- Missing info (<= 2 bullets, must be specific)
- Why it is blocking (one sentence)
- Proposed next targets (<= 5 file paths / keywords)
- Request: `wiki +1` or `code +2` (small step)
- Fallback if still missing: pick one of:
  - ask 1 critical question
  - request a concrete anchor (class/table/entrypoint) from human
  - deliver a minimal viable plan with explicit risks

#### 5.2 Lifecycle Persistence
When escalation blocks the workflow, set the intent row in `launch_spec_*.md` to `WAITING_APPROVAL` and include a link to the relevant artifact (e.g., `openspec.md` or the escalation note).

## Reverse Funnel (Write-back Rules)
This section defines the method for writing back knowledge when write-back is enabled.

Whether write-back is enabled (defaults, switches, and conflicts) is defined in [ROUTER.md](ROUTER.md).

1. Find the mount point by reading [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md).
2. DO NOT edit shared `index.md` directly. Write a WAL fragment into the target domain `wal/` directory (example: `../llm_wiki/wiki/api/wal/YYYYMMDD_feature_x_api_append.md`).
3. Merge and split are done in a low-conflict window (typically by a human). If an index exceeds the hard limit, it MUST be split.

## Hard Constraints
- Links inside `.agents/` MUST use relative paths from the current file.
- If you cannot decide what expertise to apply, consult [trae-skill-index](../skills/trae-skill-index/SKILL.md).
- Every `index.md` MUST provide a 1–2 sentence summary for each linked child document.
