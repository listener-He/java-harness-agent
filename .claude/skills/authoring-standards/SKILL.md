---
name: authoring-standards
description: "Enforces format rules + Pre-Creation Protocol for Skill, Sub-agent, Rule files. TRIGGER: create any of them. NOT FOR: WHETHER to create (use skill-author), registration (use skill-graph-manager)."
---

# Authoring Standards

## What This Does

Defines the canonical content-format rules for the three framework artifact families and the **Pre-Creation Protocol** that authors must run BEFORE drafting any of them. Acts as the single source of truth for what a "well-formed" Skill / Sub-agent / Rule file looks like in this repo.

The skill exists because format drift across artifact files is the most common silent failure in the framework: a sub-agent that returns a non-standard block breaks `subagent_return_gate.py`, a skill with a fuzzy `description:` defeats routing, a rule file that paraphrases instead of citing the source defeats Gresham's-law protection. This skill makes those failures impossible by enforcing structure at authoring time, not catching them at gate time.

## When to Use

- User says "create a skill"
- User says "create a sub-agent" / "write a new agent"
- User says "add a rule" / "create a rule file"
- You are about to write under `.claude/skills/<name>/SKILL.md`, `.claude/agents/<name>.md`, or `.claude/rules/<name>.md`
- An existing artifact needs a structural rewrite (not just a one-line tweak)

## When NOT to Use

- The user only wants to know **whether** a skill is warranted — that is `skill-author`'s job; run it first, then return here for the actual format
- Registering a finished artifact in the central index — use `skill-graph-manager` / the `skill-index` update flow
- One-line description tweaks on an existing artifact — direct edit
- Authoring documentation outside `.claude/` (use `documentation-curator`)
- Producing a WAL fragment, ADR, or task_brief — those have their own schemas (`wal-documentation-rules`, `architecture-decision-records`, `task_brief_schema.md`)

## Protocol — overview

```
Step 1: Collect Core Elements   (artifact-specific checklist)
Step 2: Clarify Ambiguities     (one AskUserQuestion round, max)
Step 3: Verify Data Sufficiency (request human-provided dataset if insufficient)
Step 4: Draft per Format Rules  (the relevant § below)
Step 5: Self-validate           (run the linter; check fail-modes)
```

Steps 1-3 are **mandatory pre-flight**. Drafting (Step 4) is forbidden until 1-3 produce a green pre-flight checklist. Skipping pre-flight is the #1 cause of artifact rewrites later.

---

## Step 1 — Collect Core Elements

Apply the relevant checklist below. Every "no" is a blocker for Step 4.

### 1.A — When creating a SKILL.md (Skill)

| Element | Required? | Acceptance criterion |
|---|---|---|
| Name (kebab-case, lowercase + digits + hyphens only) | yes | Matches `^[a-z][a-z0-9-]*$`; ≤ 40 chars; unique under `.claude/skills/` |
| Skill type | yes | One of: Procedural / Cognitive / Reference (per `skill-author` §Step 2) |
| Trigger conditions (what user input / phase fires this) | yes | At least 1 concrete keyword OR a clear phase reference |
| NOT-FOR conditions (negative scope) | yes | At least 1 route-elsewhere mapping |
| Expected outcome / output shape | yes | One sentence describing what the agent produces after applying this skill |
| Composes-with / mutual-exclusion notes | recommended | Reference `skill-precedence.md` zone if applicable |
| Lifecycle phase | recommended | One of: Explorer / Propose / Review / Implement / QA / Archive / Maintenance |

### 1.B — When creating a Sub-agent (`.claude/agents/<name>.md`)

| Element | Required? | Acceptance criterion |
|---|---|---|
| Name (kebab-case) | yes | Matches `^[a-z][a-z0-9-]*$`; unique under `.claude/agents/` |
| Description block (TRIGGER + NOT FOR + Returns) | yes | Three explicit clauses joined by `TRIGGER ... NOT for: ... Returns ...` |
| Tools allowlist | yes | Subset of `{Read, Edit, Write, Bash, Grep, Glob}`; reviewers omit `Edit`/`Write` |
| Model tier | yes | `haiku` (deterministic / mechanical) / `sonnet` (judgement) / `opus` (only for cross-cutting design) |
| Role responsibility (one paragraph) | yes | What this agent owns; what it does NOT own |
| Output contract — the 6 mandatory `[…]:` fields | yes | `[Status]` `[Files Changed]` `[Commands Run]` `[ACs Mapped]` `[Issues Found]` `[Next Step]` (per `subagent_return_gate.py`) |
| `[Source Documents Read]` field | yes | Cross-checked by `subagent_return_gate.py` cross-check 5 |
| `[Confidence]` rubric | yes | HIGH / MEDIUM / LOW with explicit criteria for each |
| Severity vocab | yes | HIGH / MEDIUM / LOW only (never CRITICAL/MAJOR/MINOR) |
| Step 0 — Validate dispatch section | yes | References `.claude/rules/dispatch-template.md` |
| Required Reading section | yes | Numbered list, ≥1 entry pointing to the contract |
| When NOT to Act table | yes | At least 3 route-elsewhere rows |
| Fallback Handling table | yes | Covers: tool unavailable / partial input / same-cause-repeat / runaway STOP |
| Anti-Patterns section | yes | Imperative bullets ("Do NOT …") |
| Gate command(s) | yes | Bash block; cite the exact script |
| Lifecycle dispatch trigger (Phase + condition) | yes | Cited from `.claude/rules/lifecycle.md` |

### 1.C — When creating a Rule File (`.claude/rules/<name>.md`)

| Element | Required? | Acceptance criterion |
|---|---|---|
| Filename (kebab-case) | yes | Matches `^[a-z][a-z0-9-]*\.md$`; unique under `.claude/rules/` |
| Top-line single-source-of-truth claim | yes | First non-header line states "Single source of truth for X." with `X` defined |
| Target consumer set | yes | Explicit: main agent / sub-agents (which) / hooks / human reviewer |
| Conflict-resolution clause | yes | "When this file disagrees with Y, this file wins for Z" — or the inverse, citing the precedence file |
| Cross-references via relative paths | yes | `[.claude/rules/lifecycle.md](lifecycle.md)` style; no absolute paths |
| At least 1 decision table | yes | Trigger → action mapping where ≥3 rows |
| Hard rules in HIGH-visibility format | recommended | `<HARD-GATE id="...">` block OR bold + numbered list |
| Maintenance note at end | yes | "Update this file when X / Y / Z" |
| Registered in `CLAUDE.md` "Single Sources of Truth" table | yes if cross-cutting | Add the row in the same commit |

### 1.D — When creating a Command (`.claude/commands/<name>.md`)

| Element | Required? | Acceptance criterion |
|---|---|---|
| Filename | yes | Matches `^h-[a-z][a-z0-9-]*\.md$`. The `h-` prefix is project convention (per user-memory `feedback_custom_command_prefix.md`) to avoid collision with Claude Code built-in slash commands (`/init`, `/review`, `/code-review`, …). Unique under `.claude/commands/`. |
| `description:` (frontmatter) | yes | ≤ 300 chars; trigger-based: `"TRIGGER when <user keyword / hook injection / phase>. NOT FOR: <route-elsewhere case 1>; <case 2>. Returns <one-line outcome>."`. NOT a workflow summary. Cap is looser than Skill §4.A (200) because commands typically carry 2 NOT FOR clauses + a Returns clause; Skills are narrower so 200 suffices. Both share the "trigger-based" structural rule. |
| `argument-hint:` (frontmatter) | yes | `[optional-arg]` (square brackets), `<required-arg>` (angle brackets), or literal `(none)`. Required even when no args so the slash-command UI shows the right hint. |
| Step section ordering | yes | Sequential `## Step N — <title>`. Sub-steps as `### Step Nx — <subtitle>`. Non-sequential numbers (`## Step 7.5`) only as last resort with inline rationale (canonical example: `h-archive.md` Step 7.5, added to minimize diff impact on downstream references). |
| Hard constraints table | yes | Final section before any "Out of scope" addendum. MUST cover: Allowed edit set / Source-code edits FORBIDDEN / Anti-loop policy / Skip-path semantics / Idempotency. |
| Final report block | yes | Last actionable step MUST output a structured `[<Command> Status]: ...` block users can grep. Mirror `h-archive.md` Step 8 pattern. |
| Reference to gate scripts | yes if applicable | Cite `.claude/scripts/gates/*.py` by exact path in the relevant step (no abbreviations). |
| Sub-agent dispatch invocation | yes if applicable | Dispatch prompt body MUST be built strictly per `.claude/rules/dispatch-template.md`; return MUST be parsed via `subagent_return_gate.py` after the sub-agent finishes. |
| Collision check | yes | `find .claude/commands -name "<basename>" -not -path "*/<this-file>"` returns empty |

---

## Step 2 — Clarify Ambiguities

Run a single `AskUserQuestion` round (max 4 questions) when ANY of the following is true after Step 1:

| Ambiguity signal | Question to ask |
|---|---|
| Trigger condition uses vague verbs ("when X happens") with no concrete keyword | "Which exact keyword or lifecycle phase fires this artifact?" |
| Could overlap with an existing artifact | "Should this supersede `<existing>`, complement it, or replace one mode of it?" |
| Tool list unclear (sub-agent) | "Does this sub-agent need write access (`Edit`/`Write`) or is it read-only?" |
| Model tier unclear (sub-agent) | "Is this mechanical (haiku), judgement (sonnet), or cross-cutting design (opus)?" |
| Output shape unclear | "What does the main agent do with this artifact's output? (parse a block / read prose / act on a file)" |
| Risk tier unclear (rule file) | "Should violating this rule HARD-GATE the workflow, or just emit a WARN?" |
| Severity vocab not specified | "Use this project's standard HIGH/MEDIUM/LOW, or does this artifact have a custom scale?" |

### Default Convergence Rule

Every Step 2 question MUST be issued via `AskUserQuestion` with at least one option marked `(Recommended)`. The Recommended value MUST be derived from an **existing analog** (the same artifact family under `.claude/skills/`, `.claude/agents/`, or `.claude/rules/` — Step 3 form #2) OR an explicit project convention cited in `policy.md` / `skill-precedence.md` / `lifecycle.md`. If neither source yields a defensible default for a given question, do NOT manufacture one — drop the question here and let Step 3 catch the gap.

**Folding answers** into the Step 1 checklist:

| User response | Action |
|---|---|
| Explicit pick (one of the offered options) | Record value verbatim |
| `(Recommended)` selected | Record value + `assumed-from <analog-path-or-rule>` annotation |
| "I don't know" / "you decide" / "你看着办" | Adopt the Recommended; record value + `assumed-from <analog-path-or-rule>` annotation; **continue** (NOT a halt trigger) |
| Active rejection without alternative | Re-ask once, narrower scope; if still no signal → fall through to Step 3 halt |
| User offers a new option ("Other") | Record verbatim; flag for review at Step 5 self-validate |

Anti-fabrication preserved: defaults are only legal when traceable to an analog or named convention; they never come from training-data heuristics or "what feels right". An earlier version of this protocol treated "you decide" itself as a halt signal — that conflated *information void* with *user-delegated default* and produced excessive halts on moderately specified requests. Step 3 still owns the halt path, but only when supporting-data forms are genuinely insufficient (not merely "user said you decide").

---

## Step 3 — Verify Data Sufficiency

The user's request alone is rarely enough to author a quality artifact. Before drafting, you MUST verify that you have ≥2 of these forms of supporting data:

1. **Concrete trigger examples** — ≥2 sample inputs that should fire the artifact, with the expected outcome of each
2. **An existing analog in the codebase** — a similar artifact under `.claude/skills/`, `.claude/agents/`, or `.claude/rules/` that this new one will mirror or contrast with
3. **A boundary counter-example** — at least 1 case that should NOT fire this artifact (route elsewhere)
4. **Reference to a gate / hook / script** that this artifact will interact with
5. **A reference document** (PRD, spec, or external standard) the artifact must conform to

If **fewer than 2** of these are present, STOP and ask the user for new data using this exact template:

```
[Authoring Halted — insufficient data]

Before I draft <artifact-type> `<proposed-name>`, I need the following from you:

1. <missing-data-item-1>  — e.g., "Please paste 2 concrete examples of input that should trigger this skill"
2. <missing-data-item-2>  — e.g., "Please point me at the existing sub-agent this should mirror, or confirm there is no analog"

Optional but helpful:
- <optional-item-1>       — e.g., "What gate script will consume this artifact's output?"

I will resume drafting once you provide the above.
```

Under no circumstances may you fabricate examples, infer trigger conditions from training-data convention, or stub the artifact in the hope the user will fill it in later. **Insufficient data → ESCALATE, do not draft.**

Resume drafting only after the user-provided dataset closes the gap to ≥2 of the 5 forms above.

---

## Step 4 — Draft per Format Rules

Pick the relevant § below. Each is a strict template — sections appear in the order listed, with the exact headers.

### § 4.A — Skill format (`SKILL.md`)

```markdown
---
name: <kebab-case-name>
description: "<≤200 chars; begins with 'TRIGGER when…' or a noun phrase ending in TRIGGER clause; includes NOT FOR clause; cites composes-with skills if Zone-A/B/C/D/E/F/G applicable>"
---

# <Title Case Name>

## What This Does
<1-2 sentences. The core outcome. Not the workflow.>

## When to Use
- <Trigger 1 — keyword or phase>
- <Trigger 2>
...

## When NOT to Use
- <Anti-trigger 1 with route elsewhere>
- <Anti-trigger 2>
...

## Protocol
### Step 1: <name>
<actionable>

### Step 2: <name>
<actionable>

...

## Anti-Patterns
| Mistake | Fix |
|---|---|
| <…> | <…> |

## Composes With
- <other-skill> — <relationship: prerequisite / mutually exclusive / pairs with>

## Examples (optional)

**Good:** `<example>`
**Bad:** `<example with explanation>`
```

Format rules:
- **`description:` is the routing handle.** It must include both TRIGGER conditions AND NOT-FOR conditions. The router never opens `SKILL.md`; the description IS the contract.
- Body ≤ 500 lines. If larger, split per `wiki_linter.py` cap or break into a multi-skill cluster.
- Code blocks only for commands, file paths, or templates — not for narrative
- No `[Status]:` block (that's a sub-agent contract, not a skill contract)
- Section order is fixed; do not reorder

### § 4.B — Sub-agent format (`agents/<name>.md`)

```markdown
---
name: <kebab-case-name>
description: <DESCRIPTION_BODY — ≤500 chars; 3 explicit clauses>
tools: <subset of Read, Edit, Write, Bash, Grep, Glob>
model: <haiku | sonnet | opus>
---

# <Title Case Name>

<one paragraph: what this agent owns; what it does NOT own; reference to relevant skill list>

## When to Act
- <Phase + condition 1>
- <Phase + condition 2>
...

## When NOT to Act (route elsewhere)
| Situation | Right agent / skill |
|---|---|
| <…> | <…> |
| <≥3 rows total> | <…> |

## Step 0 — Validate dispatch
Validate dispatch prompt structure per [.claude/rules/dispatch-template.md](../rules/dispatch-template.md). Missing required section → return `[Status]: ESCALATE` with `[Reason]: <…>`.

## Required Reading Before <verb>
1. <Source 1 — your contract>
2. <Source 2>
...

## Process
### 1. <step>
<actionable>

### 2. <step>
<actionable>

...

## Fallback Handling
| Situation | Action |
|---|---|
| <tool unavailable> | <`[Status]: ESCALATE` with `[Reason]: …`> |
| <partial input> | <continue with available; record gap; downgrade `[Confidence]`> |
| <same-cause repeat> | <STOP; `[Status]: ESCALATE`> |
| <runaway exploration > N steps> | <STOP; `[Status]: ESCALATE` with `[Reason]: runaway exploration; checked X,Y,Z>` |
| <≥4 rows total> | <…> |

## Anti-Patterns
- Do NOT <…>
- Do NOT <…>
...

## Gate
```bash
python3 .claude/scripts/<...>.py <args>
```

## Output Format
Return ONLY this block, no preamble. The main agent parses it via `subagent_return_gate.py`.

```
[Status]: PASS | PARTIAL | FAIL | ESCALATE | BOUNDARY_EXCEPTION
[Files Changed]: <relative paths with +N/-M, or "none">
[Commands Run]: <each command + exit code, or "none">
[ACs Mapped]: <AC-id → evidence → PASS/FAIL/SKIP, or "none">
[Issues Found]: <numbered list, or "none">
[Source Documents Read]: <comma-sep paths Read'd>
[Confidence]: HIGH | MEDIUM | LOW
[Next Step]: <one sentence>

# Role-specific fields (when applicable):
[<Field>]: <…>
```

`[Confidence]` rubric:
- **HIGH** — <criteria>
- **MEDIUM** — <criteria>
- **LOW** — <criteria>

If `[Status]: ESCALATE` or `BOUNDARY_EXCEPTION`, also include `[Reason]: <one line>`.
```

Format rules:
- **`[Status]` set is fixed**: `PASS | PARTIAL | FAIL | ESCALATE | BOUNDARY_EXCEPTION`. No `WARN`, no `OK`, no custom additions.
- **6 mandatory fields**: parse failure if any missing — checked by `subagent_return_gate.py` REQUIRED_FIELDS
- **`[Source Documents Read]`** is technically optional but the gate emits a WARN if absent on `[Status]: PASS` — treat as mandatory
- **`[Confidence]`** is new (added by `authoring-standards`); the rubric must be artifact-specific, not boilerplate
- **Severity vocab**: HIGH / MEDIUM / LOW. Never CRITICAL/MAJOR/MINOR.
- **Tools**: review agents (code-reviewer, database-reviewer, ambiguity-gatekeeper, security-sentinel, test-runner, java-build-resolver) MUST omit `Edit` and `Write` — they propose, they don't modify
- **Model tier defaults**: haiku for deterministic script-runners (`security-sentinel`, `test-runner`, `java-build-resolver`); sonnet for judgement (`code-reviewer`, `system-architect`, `lead-engineer`, `requirement-engineer`); opus is reserved
- **Section order is fixed**; do not reorder
- **Cross-references** use relative paths: `../rules/dispatch-template.md`, `../skills/<x>/SKILL.md`

### § 4.C — Rule file format (`rules/<name>.md`)

```markdown
# <Title>

Single source of truth for: <topic — be specific>. <One sentence explaining what depends on this file.>

Background (optional 1 paragraph): <why this file was needed; what failure it prevents>

**Reading rule:** <when consumers must consult this file — usually keyed off skill descriptions or phase boundaries>

---

## §1 — <First major decision area>

<decision table with ≥3 rows>

| Trigger | Action |
|---|---|
| <…> | <…> |

---

## §2 — <Second area>

...

---

## §<N> — Conflict resolution

When this file and <other file> disagree:
1. **This file wins** for <topic-X>
2. **<other file> wins** for <topic-Y>
3. New conflict not covered → add a row, do NOT silently pick one

## §<N+1> — Maintenance

Update this file when:
- <signal-1>
- <signal-2>
- <signal-3>

When this file changes, also update:
- `CLAUDE.md` "Single Sources of Truth" table (if not already listed)
- <other cross-referencing files>
```

Format rules:
- **First non-header line** declares the single-source-of-truth claim
- **Tables over bullet lists** when ≥3 items map trigger → action
- **HARD-GATE blocks** for unbypassable rules: `<HARD-GATE id="<slug>">…</HARD-GATE>`
- **Cross-references** use relative paths; absolute paths forbidden
- **No code blocks** except for command examples and small templates
- **No prose-only paragraphs** longer than 3 sentences — break into a table or bullet list
- **File size cap**: 800 lines for rule files (rules must be skimmable). At cap, split by topic.
- **Maintenance section** is the last section; do not append commentary after it
- **Register in `CLAUDE.md`** "Single Sources of Truth" table if the file is cross-cutting (loaded by hooks, referenced from ≥2 other files)

### § 4.D — Command format (`commands/<name>.md`)

````markdown
---
description: TRIGGER when <user keyword / hook injection / phase boundary>. NOT FOR: <route-elsewhere case 1>; <case 2>. Returns <one-line outcome>.
argument-hint: [optional-arg] | <required-arg> | (none)
---

<One-paragraph: what this command does, why it exists, relationship to adjacent commands.>

## Step 0 — Resolve target (optional; only if input is ambiguous)

Use `AskUserQuestion` if `$ARGUMENTS` is empty AND no implicit target can be derived from `.claude/runs/`.

## Step 1 — <action>

<actionable steps; cite scripts by exact path>

```bash
python3 .claude/scripts/<area>/<script>.py <args>
```

## Step 2 — <action>

...

## Step N — Final report

Output exactly this block, nothing else:

```
[<Command> Status]: COMPLETE | PARTIAL | FAILED
[<key field 1>]: <value or "n/a">
[<key field 2>]: <value>
...
[Next]: <one sentence — what user should do next>
```

## Hard constraints

| Rule | Value |
|---|---|
| Allowed edit set | <specific paths or "none — read-only command"> |
| Source-code edits | FORBIDDEN |
| Anti-loop | Max 2 retries per step; second failure → STOP, surface error |
| Skip path | <how user opts out — e.g., "Step 2 select None → Step 4 still runs"> |
| Idempotency | <safe-to-rerun semantics> |
````

Format rules:
- **`description:` is the routing handle** — same trigger-based rule as § 4.A (≤ 200 chars; explicit TRIGGER + NOT FOR clauses). The slash-command UI surfaces this line before the user even invokes; precision matters.
- **`h-` prefix mandatory** — per project convention (user-memory `feedback_custom_command_prefix.md`). Avoids collision with Claude Code built-ins (`/init`, `/review`, `/code-review`, `/security-review`, `/loop`, `/run`, `/verify`, …). Without this convention slash-command routing becomes ambiguous.
- **Step headers sequentially numbered** — agents execute top-to-bottom; non-sequential numbers (e.g., inserting `## Step 1.5` mid-flow) only as last resort with rationale; canonical example: `h-archive.md` Step 7.5 added to minimize diff against downstream references.
- **Final report block always last** — gives users a structured grep/parse handle (`[X Status]: COMPLETE`). Without this the command produces narrative prose only, defeating composability with other commands and CI scripts.
- **Sub-agent dispatches**: prompt body MUST be built from `.claude/rules/dispatch-template.md`; return validated by `subagent_return_gate.py`. Do NOT inline a custom dispatch shape — it bypasses scope_guard and ACs-mapped contracts.
- **Hard constraints table required** — at minimum cover: Allowed edit set / Source-code edits / Anti-loop / Skip path / Idempotency. Skipping this section is the main route to commands that silently mutate source code or cycle without an exit condition.
- **No code blocks** except for: commands to run, file path templates, AskUserQuestion question text, Final report template.
- **Cross-references**: relative or repo-rooted paths only (e.g., `.claude/rules/...`); never absolute `/Users/...`.
- **Canonical exemplar (structure only)**: when in doubt, mirror `.claude/commands/h-archive.md` for SECTION STRUCTURE (Step / Hard constraints / Final report). NOTE its `description:` predates §4.D and is workflow-style; do NOT copy that pattern — use the trigger-based template above.
- **Grandfather note**: 18 of 20 existing `/h-*` commands (at §4.D introduction time, 2026-05-30) carry workflow-style descriptions predating this rule. They are de-facto exempt pending bulk migration; the rule applies as authored to all NEW commands and to substantive rewrites of existing commands. Tracker: see task `F8` (bulk-migrate workflow-style → trigger-based) and `F9` (trim h-reflect description to ≤ 300).

---

## Step 5 — Self-validate

After drafting, run the relevant linter:

| Artifact | Linter | Expected |
|---|---|---|
| Skill | `python3 .claude/scripts/wiki/wiki_linter.py` (when wiki-linked) + manual: `name` matches regex, `description` ≤ 200 chars | OK / WARN acceptable; FAIL → fix |
| Sub-agent | `python3 .claude/scripts/gates/subagent_return_gate.py --return-file <sample-output> --task-kind <kind>` against a sample emitted block; visually verify 6 mandatory `[…]:` fields | OK on a synthetic PASS sample |
| Rule file | manual: `grep '^# ' <file>` shows exactly 1 H1; `grep '## §' <file>` shows ≥2 sections; cross-references resolve; size under cap | all checks pass |

Plus run the universal smoke checks:

```bash
# 1. Filename and location
ls .claude/<skills|agents|rules>/<...>
# 2. Frontmatter parsable (skills + sub-agents only)
head -20 <file>
# 3. Cross-references resolve
grep -oE '\(\.\./[^)]+\)' <file> | while read r; do test -e "${r#(}" && echo OK || echo "MISS $r"; done
# 4. No duplicate name elsewhere
find .claude -name "<basename>" -not -path "*/<this-file>"
```

If any check fails → fix and re-validate. Three failures of the same check → STOP and ask the user.

---

## Anti-Patterns

| Mistake | Why it's wrong | Fix |
|---|---|---|
| Skip Step 3 ("just stub it, I'll fill it later") | Stubs become permanent; bad triggers pollute routing | Halt, request the dataset |
| Step 2 `AskUserQuestion` without a `(Recommended)` option | "你看着办" cannot be folded → forces an unnecessary Step 3 halt; defeats the Default Convergence Rule | Every option list must include `(Recommended)` derived from an existing analog or a named convention (`policy.md` / `skill-precedence.md` / `lifecycle.md`). No analog → drop the question, let Step 3 surface the gap. |
| Pre-fill all 5 sub-agent dimensions to look thorough (`dimensions: [domain, api, data, tech_arch, patterns]`) | Defeats the spec-floor + dimension-gated model | Pick honestly; `[]` is legal |
| Use `[Status]: WARN` or `[Status]: OK` in a sub-agent | Breaks `subagent_return_gate.py` STATUS_VALUES check | Use `PASS | PARTIAL | FAIL | ESCALATE | BOUNDARY_EXCEPTION` only |
| Severity vocab `CRITICAL/MAJOR/MINOR` | Inconsistent with project standard | Use HIGH/MEDIUM/LOW |
| Paraphrase the user's input into `[Source Documents]` | Gresham's law — bad summary drives out good source | Use `VERBATIM:"""..."""` if no source file |
| Skill `description:` summarizes the whole workflow | Router can't pattern-match; agent invokes wrong skill | Keep it trigger-based, ≤200 chars |
| Rule file with prose paragraphs > 3 sentences | Skimmability lost; consumers stop reading | Break into table or bullet list |
| Cross-reference via absolute path (`/Users/.../`) | Breaks on every other dev's machine | Relative path |
| Author a sub-agent that grants `Edit`/`Write` to a reviewer role | Reviewer propose-only contract violated | Drop Edit/Write from `tools:` |
| Forget to register in `skill-index` after authoring a skill | Skill exists on disk but routing never finds it | Run `skill-graph-manager` after Step 5 |
| Cite a non-existent gate script in `## Gate` | Sub-agent will ESCALATE at first dispatch | Verify path with `ls` before writing |

---

## Composes With

| Skill / Agent | Relationship |
|---|---|
| `skill-author` | Prerequisite — decides WHETHER a skill is warranted; then `authoring-standards` defines HOW to format it |
| `skill-graph-manager` | Successor — registers the new artifact in the central index AFTER authoring |
| `skill-index` | Read for navigation context; update if you add a new skill |
| `spec-quality-checklist` | Optional self-validation pass after Step 4 |
| `documentation-curator` | Mutually exclusive — `documentation-curator` writes free-form docs; this skill governs framework artifacts |

---

## Examples

### Example 1 — Authoring a new sub-agent

User: "Create a sub-agent that runs `mvn dependency:tree` and flags conflicting versions."

**Step 1 — Collect Core Elements:**
- Name: `dependency-conflict-detector` ✓
- Description: missing — ask
- Tools: Read, Bash, Grep, Glob (no Edit/Write — proposes only) ✓
- Model: haiku (mechanical scan) ✓
- Output contract: 6 fields + [Confidence] — needs definition
- Severity vocab: HIGH/MEDIUM/LOW — needs mapping to conflict types

**Step 2 — Clarify (one round):**
1. "Does this run automatically on `pom.xml` changes, or only on explicit dispatch?"
2. "Should an unresolvable conflict BLOCK Archive, or only WARN?"
3. "Tool list: Read + Bash + Grep + Glob, no Edit/Write — confirm?"

**Step 3 — Verify Data Sufficiency:**
- Existing analog: `java-build-resolver` ✓
- Concrete trigger example: needed — ask user for 1 historical case
- Gate / hook interaction: `pre_tool_use_hook.py` on `pom.xml`? — ask user

**If user can supply the example + gate context → Step 4. Otherwise → halt with template.**

### Example 2 — Authoring a new rule file

User: "Write a rule file for how PRs should be sized."

**Step 1:** Topic claim unclear — "PR sizing" could mean LOC, file count, AC count.
**Step 2 — Clarify:** ask 1 question to pin the metric.
**Step 3 — Verify Data:**
- No existing analog in `.claude/rules/`
- No reference document supplied
- No concrete trigger examples
- Only 0 of 5 supporting-data forms present
- **Halt → request from user**: "Please provide 2 examples of PR sizes you'd accept and 2 you'd reject, plus a reference (link or paste) to any external sizing policy."

### Example 3 — Authoring a new skill

User: "Make a skill for handling Flyway migration failures."

**Step 1:**
- Name: `flyway-migration-recovery` ✓
- Type: Procedural ✓
- Trigger: keyword "Flyway" + "failed" / migration repair scenarios
- NOT FOR: schema design (use `system-architect`); rollback design (use `architecture-decision-records`)
- Composes with: `root-cause-debug` (after symptom triage), `database-reviewer` (post-fix review)

**Step 2:** clear — skip.
**Step 3 — Verify Data Sufficiency:**
- Concrete trigger examples: ≥2 historical failures — ask user
- Existing analog: none in skills/
- Boundary counter-example: schema design ≠ migration recovery — yes
- Gate interaction: `migration_gate.py` — yes
- 2 of 5 present (boundary + gate) — borderline. Ask user for ≥1 historical failure to enrich.

**If user supplies → Step 4. If not → halt.**

---

## Related Skills

- [skill-author](../skill-author/SKILL.md): Predecessor — decides WHETHER a new skill is warranted; once "yes", hands off to `authoring-standards` for the format rules.
- [skill-graph-manager](../skill-graph-manager/SKILL.md): Successor — after authoring, it registers the artifact in `skill-index` and maintains bidirectional links.
- [skill-index](../skill-index/SKILL.md): Registration target — every new skill / sub-agent gets a navigation row here.
- [spec-quality-checklist](../spec-quality-checklist/SKILL.md): Optional self-validation partner at Step 5 — flags narrative content, vague language, structural gaps.

## Maintenance

Update this file when:
- A new artifact family is added under `.claude/` that has its own format contract (e.g. `.claude/templates/`)
- `subagent_return_gate.py` adds a new required or recommended field
- The project introduces a new severity scale that supersedes HIGH/MEDIUM/LOW
- A new HARD-GATE pattern is added to `policy.md` or `lifecycle.md`
- The Pre-Creation Protocol proves insufficient (a poorly-authored artifact slipped through)

When this file changes, also update:
- `CLAUDE.md` "Single Sources of Truth" table (add the row if not present)
- `.claude/skills/skill-index/SKILL.md` (Default Enabled table)
- `.claude/skills/skill-graph-manager/SKILL.md` graph (bidirectional links to composes-with skills)
