---
name: skill-author
description: "Decides whether to author a SKILL.md. TRIGGER: 'create a skill', recurring workflow without one, broken trigger. NOT FOR: one-offs, rules, non-skill artifacts (use authoring-standards)."
---

# Skill Author

A gate-keeper for the skill catalog. Before any SKILL.md is written, this skill decides whether the workflow actually warrants one — and if so, runs the authoring pre-flight that produces a routable, falsifiable contract.

## First Principles

A skill exists for exactly one reason: **LLMs are stateless, and the same recurring task done in two sessions will diverge without a stable contract**. Every other property of a skill follows from this.

| Property | Derives from… |
|---|---|
| Skill must have a **falsifiable trigger** | If the description matches everything, it routes nothing — it's noise in the catalog |
| Skill must have an **explicit boundary** (NOT FOR + route-elsewhere) | The router cannot disambiguate two skills that overlap; the boundary IS the disambiguation |
| Skill must be **repeatable** (≥3 expected firings) | A skill costs ~50–200 description tokens per session. One-off use is a net loss for the catalog |
| Skill must be **repository-specific or hard to infer** | A skill that re-states general knowledge wastes the budget; the LLM already has it |
| Skill must be **composable** (predecessor / successor visible) | Workflows are graphs, not points. A skill with no neighbors is suspect — it's either too narrow or duplicates an existing one |

These five properties form the acceptance bar. If any one is false, do not create the skill.

## When to Use

- User explicitly asks to "create a skill" / "add a skill" / "register this as a skill"
- You detect a workflow that has fired ≥2 times in the current session and would fire again
- An existing skill's TRIGGER misses obvious inputs or matches obvious non-targets (the routing is broken)
- An existing skill's `description` violates the format rules from `authoring-standards` and needs restructuring

## When NOT to Use

| Situation | Why no | Route instead |
|---|---|---|
| One-off task ("just do X this once") | Single-use loses the description-token budget | Inline instructions; no skill |
| Project rule or policy ("never use @PathVariable") | A rule is unconditional; a skill is conditional protocol | `.claude/rules/<name>.md` |
| Authoring a sub-agent or rule file | Different artifact, different format contract | `authoring-standards` |
| Documentation request (README, runbook) | Not a routable workflow | `documentation-curator` |
| Asked "do we need a skill for X?" answer is unclear | Skill creation has cost; uncertainty defaults to NO | Decline; revisit after 1–2 more occurrences |

## Protocol — Pre-flight Before Authoring

Run the pre-flight in order. **Each step is a gate**: failure halts authoring, never silently downgrades. The pre-flight mirrors `authoring-standards` so the two skills compose cleanly.

### Step 1 — Validate Need (binary gate, no judgement calls)

Answer all five Yes/No questions. Five "yes" required to proceed.

| Question | Yes condition |
|---|---|
| **Q1. Will this fire ≥3 times in 2 weeks?** | You can name 3 concrete future occurrences |
| **Q2. Is it repository-specific?** | Generic LLM knowledge would not produce the correct workflow |
| **Q3. Is the trigger statable in one sentence?** | If you write the TRIGGER clause and need a paragraph, the trigger is fuzzy — kill the skill or sharpen the trigger |
| **Q4. Is there a route-elsewhere boundary?** | You can name ≥1 adjacent situation that should NOT match |
| **Q5. Is there no existing skill that 80% covers it?** | If yes overlap, EXTEND the existing skill instead of creating a new one |

Any "no" → halt; either rework or decline.

### Step 2 — Discovery vs Author (decide which path)

After Step 1, decide: **extend existing** vs **create new**.

| Signal | Decision |
|---|---|
| An existing skill's protocol covers the new case with ≤30 lines added | EXTEND that skill |
| The new case requires a different trigger keyword set | CREATE NEW |
| The new case has a fundamentally different output shape | CREATE NEW |
| Two existing skills both could host it | CREATE NEW (and add disambiguation rows to both) |

If EXTEND: jump to Step 5 of the existing skill — no new file, just an edit.

### Step 3 — Choose Skill Type

| Type | Meaning | Test it's this type |
|---|---|---|
| Procedural | Step-by-step executable workflow | The protocol is a numbered list of actions |
| Cognitive | Thinking protocol / decision gates | The protocol is a checklist of questions |
| Reference | Repository-specific standards | The protocol is a table of rules with no execution flow |

If a skill straddles types, it's usually two skills. Split.

### Step 4 — Draft per `authoring-standards` § 4.A

The format rules live in `authoring-standards` (§ 4.A — Skill format). Do not duplicate them here; open that skill and follow the template. Hand over: name, type, the TRIGGER clause, the NOT FOR clause, the predecessor/successor skills (for Related Skills section).

Critical reminders from the joint contract:
- `description` ≤ 200 chars; English; **TRIGGER + NOT FOR + one verb of what it does** all present
- The description is the routing handle — the router never opens SKILL.md
- Code blocks for commands and templates only; never for narrative
- Body ≤ 500 lines; split if larger

#### Zone A Carve-out (Daily-Rules pattern) — `description` length exemption

The 200-char rule applies to **routing-style skills** whose description is purely a router hint. A second design pattern exists by explicit license from `CLAUDE.md` § 5 ("Skill Files: Reference, Not Preflight Reading"): **Daily-Rules skills** whose description is *itself* the rulebook, so the agent makes the day-to-day decision without opening `SKILL.md`.

Zone A skills (per `CLAUDE.md` § 5) are EXEMPT from the 200-char cap but MUST still:
- Start with a verb (or be a YAML block scalar — `description: |` — whose first body line starts with a noun + verb-phrase, e.g. "Layer 1 (Architecture) for Java backend. Daily decisions you can make WITHOUT opening SKILL.md:")
- Carry a TRIGGER clue (it can be the topic noun — e.g. "TRIGGER when touching mapper XML")
- May omit NOT FOR (Zone A skills apply universally to their domain — there is no "route elsewhere" because the skill IS the domain authority)
- End the description with `Open SKILL.md when deciding: <decisions that justify opening the file>` (preserves the second purpose: when to open the file for deeper reference)

Current Zone A members (closed set; adding to it requires editing this file + `CLAUDE.md` § 5 in the same commit):
1. `java-architecture-standards` — Layer 1 architectural Red Lines
2. `java-coding-style` — Layer 2 style rules
3. `mybatis-sql-standard` — Layer 3 persistence rules
4. `test-driven-development` — TDD daily discipline

A new skill is NOT Zone A by default. Authoring a Zone A skill requires explicit user confirmation that the description-as-rulebook tradeoff (higher per-session token cost; agent doesn't open SKILL.md) is wanted.

### Step 5 — Falsifiability Check (the test you can run alone)

Before validating with a real prompt, ask yourself **two falsifiability questions**:

1. **False-positive test**: Write a user prompt that looks like it should match this skill but should NOT (it belongs to another skill or no skill). Does your TRIGGER clause exclude it? If not, the TRIGGER is too broad — refine.
2. **False-negative test**: Write a user prompt that SHOULD match this skill but uses different wording than your TRIGGER keywords. Does the description still match? If not, the TRIGGER is too narrow — add keyword variants.

Both tests pass → proceed. One fails → revise the description.

### Step 6 — Trigger Simulation (live test)

Feed three hypothetical prompts through the router (mentally — does Claude's skill description matcher fire?). At minimum:

- One **true positive** — clearly belongs
- One **adjacent miss** — looks similar, should route elsewhere
- One **off-target** — clearly doesn't belong, should silent-pass

A skill that fails any of these in simulation will fail in production. Fix before Step 7.

### Step 7 — Save and Register

Save to `.claude/skills/<skill-name>/SKILL.md`. Then:

1. Update the central index: `.claude/skills/skill-index/SKILL.md` (add a table row in the matching section: Default Enabled / Role-Required / Reactivated)
2. Run the index linter:
   ```bash
   python3 .claude/scripts/gates/skill_index_linter.py \
       --index .claude/skills/skill-index/SKILL.md \
       --skills-dir .claude/skills \
       --fail-on-missing
   ```
   Must report `OK: skill index linter pass`. Dead links → fix and re-run.
3. Dispatch `skill-graph-manager` to maintain bidirectional `## Related Skills` links (requires user approval per its protocol).

## Quality Checklist (final gate before commit)

- [ ] `name` matches `^[a-z][a-z0-9-]*$`; unique under `.claude/skills/`
- [ ] `description` ≤ 200 chars; English; contains TRIGGER + NOT FOR + one verb
- [ ] `description` does NOT summarize the workflow — only routes
- [ ] Protocol is bounded — every step ends in a decision (proceed / halt / route)
- [ ] At least one trigger keyword AND one boundary keyword in the description
- [ ] Skill type chosen explicitly (Procedural / Cognitive / Reference)
- [ ] Falsifiability tests both pass (Step 5)
- [ ] Trigger simulation passes 3/3 (Step 6)
- [ ] `## Related Skills` section names ≥1 predecessor or successor
- [ ] `skill_index_linter.py` exits 0

Skipping any check is a contract violation. There is no "optional" row.

## Common Mistakes

| Mistake | Why it fails | Fix |
|------|------|------|
| `description` summarizes the workflow | Routing becomes a paragraph match; precision drops | Keep ≤ 200 chars, TRIGGER-shaped |
| Description too generic ("debugging skill") | Matches everything; matches nothing actionable | Add concrete trigger keywords |
| Description too specific ("Flyway 9.8 migration recovery") | Doesn't generalize beyond one version | Drop version, broaden scope or leave inline |
| No NOT FOR clause | Router cannot disambiguate against adjacent skills | Add ≥1 route-elsewhere |
| Skill is actually a rule | A rule is unconditional; you've encoded "always do X" | Move to `.claude/rules/<name>.md` |
| Solo skill (no neighbors) | Workflows are graphs; an isolated node is usually a doc | Either link to predecessors/successors or decline |
| Skipped Step 1 ("looks useful, just write it") | Speculative skills bloat the catalog | Run Q1–Q5 honestly; decline if any fails |
| Step 5 skipped, found false positives in production | The trigger eats neighboring inputs | Rewrite TRIGGER with the FP example explicitly excluded |

## Examples

### Good — concrete trigger, explicit boundary

```yaml
---
name: async-race-condition-debugging
description: "Use when tests have race conditions, timing dependencies, or pass/fail inconsistently across runs. TRIGGER: flaky test, time-of-day-dependent failure, intermittent CI failure. NOT FOR: deterministic bug (use root-cause-debug)."
---
```

Why it's good: trigger keywords are specific (flaky, time-of-day, intermittent), boundary is explicit (deterministic → other skill).

### Bad — workflow summary, no boundary

```yaml
---
name: debugging
description: "Use when you need to debug code by reading errors, reproducing issues, and fixing root causes"
---
```

Why it fails: this is a workflow narrative, not a router hint. Matches every bug report. Has no NOT FOR. Will conflict with `root-cause-debug`, `java-build-resolver`, `test-runner`, and others.

### Failure case — solo skill (should have been declined)

```yaml
---
name: rename-staging-tables
description: "Rename staging tables to drop the _stg suffix after backfill"
---
```

Why it fails: this fires once per project. No recurrence → no skill. Inline the instructions in the migration task instead.

## Related Skills

- [authoring-standards](../authoring-standards/SKILL.md): Successor — once Step 4 chooses to author, `authoring-standards` § 4.A provides the strict template and section rules.
- [skill-graph-manager](../skill-graph-manager/SKILL.md): Successor — Step 7 hands off to it for index registration and bidirectional link maintenance.
- [skill-index](../skill-index/SKILL.md): Registration target — every new skill MUST get a row here.
- [spec-quality-checklist](../spec-quality-checklist/SKILL.md): Optional self-review pass after Step 5; catches narrative-style content and vague language.
