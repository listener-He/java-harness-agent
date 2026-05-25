# Skill Precedence & Composition Matrix

Single source of truth for "at trigger window X, which skills run, in what order, and what's mutually exclusive."

Background: many skills declare `MANDATORY` in their descriptions. When several MANDATORY skills target the same trigger window, the agent silently picks one — making behavior unpredictable. This file resolves those conflicts.

**Reading rule:** if a skill description says `MANDATORY`, also check this file for layering. The matrix below overrides any skill's standalone MANDATORY claim.

---

## Trigger Windows

### Zone A — Before writing Java code (Implement phase)

These skills are **layered** (all apply, no conflict). Lower layers are foundational; higher layers refine.

| Layer | Skill | Always applies? |
|---|---|---|
| L1 Architecture | [java-architecture-standards](../skills/java-architecture-standards/SKILL.md) | Yes — any Java file |
| L2 Coding style | [java-coding-style](../skills/java-coding-style/SKILL.md) | Yes — any Java file |
| L3 Persistence | [mybatis-sql-standard](../skills/mybatis-sql-standard/SKILL.md) | Only if touching MyBatis mapper/XML/DDL |
| L4 Flow | [test-driven-development](../skills/test-driven-development/SKILL.md) | STANDARD profile only |

**No mutual exclusion.** They compose. If you skip any, document why in task_brief.

---

### Zone B — Code review (after writing code)

These **compete** for the same window. Pick exactly ONE primary reviewer per profile.

| Profile | Primary reviewer | Additional |
|---|---|---|
| Vibe / Patch (PATCH profile) | [code-review-checklist](../skills/code-review-checklist/SKILL.md) (inline, self-correction loop) | — |
| MEDIUM (STANDARD) | [code-reviewer](../agents/code-reviewer.md) sub-agent (isolated context) | — |
| HIGH (STANDARD) | [code-reviewer](../agents/code-reviewer.md) sub-agent | [adversarial-review](../skills/adversarial-review/SKILL.md) Category B (one round) |

**Mutual exclusion:** `code-review-checklist` skill and `code-reviewer` sub-agent are **never both invoked** for the same change — duplicate effort with no error-rate gain. Adversarial review is a **design-level** lens, not a substitute for code review.

Security-sensitive changes (auth, secrets, IDOR risk) additionally run [security-review-checklist](../skills/security-review-checklist/SKILL.md) on top of the primary reviewer.

---

### Zone C — QA (Phase 5)

| Condition | Verification skill | Test-standard skill |
|---|---|---|
| AC count ≤ 3 AND risk ≠ HIGH | [ac-verify](../skills/ac-verify/SKILL.md) | [java-testing-standards](../skills/java-testing-standards/SKILL.md) if Java |
| AC count ≥ 4 OR risk = HIGH | [ultraqa](../skills/ultraqa/SKILL.md) | [java-testing-standards](../skills/java-testing-standards/SKILL.md) if Java |

**Mutual exclusion:** `ac-verify` and `ultraqa` — pick one based on the condition above. `ultraqa` is the structured cycling superset; `ac-verify` is the lightweight single-pass.

`java-testing-standards` is orthogonal (rules for test code itself) and **always composes** with whichever verification skill runs, as long as the tests are Java.

---

### Zone D — Archive phase

| Skill | Role | When |
|---|---|---|
| [wal-documentation-rules](../skills/wal-documentation-rules/SKILL.md) | Foundational rules for WAL writes | Always for STANDARD Archive |
| [knowledge-extractor](../agents/knowledge-extractor.md) sub-agent | Executes WAL writes per the rules | Default executor — preferred over inline |
| [architecture-decision-records](../skills/architecture-decision-records/SKILL.md) | Captures one specific ADR file | Only when an architectural decision was made |
| [remember](../skills/remember/SKILL.md) | Classifies cross-session knowledge | Only when non-obvious constraint was uncovered |

**Composition:** `wal-documentation-rules` is the rulebook; `knowledge-extractor` is the actor that follows it. The other two are conditional add-ons. **No exclusion** — they don't overlap when their conditions are met.

PATCH profile: skip the entire zone. Wiki refresh deferred to a later on-demand `knowledge-extractor` dispatch.

---

### Zone E — Debugging (Scenario DEBUG)

| Skill | When |
|---|---|
| [root-cause-debug](../skills/root-cause-debug/SKILL.md) | Always — bug/error with unknown root cause |

No competition in this window. `root-cause-debug` MUST complete its Phase 1 (root cause) before any fix is proposed.

---

### Zone F — Explorer phase (STANDARD only)

| Skill | When |
|---|---|
| [local-code-intelligence](../skills/local-code-intelligence/SKILL.md) | Always — run wiki_search, code_index, failure_memory |
| [input-classifier](../skills/input-classifier/SKILL.md) | Raw input lacks structured intent+scope+AC |
| [adversarial-review](../skills/adversarial-review/SKILL.md) Category A | HIGH risk only — one round |
| [task-decomposition-guide](../skills/task-decomposition-guide/SKILL.md) | EPIC / PRD / multi-task scope |

**Composition:** these chain, they don't compete. `input-classifier` normalizes input; `local-code-intelligence` gathers context; `adversarial-review` critiques the framing; `task-decomposition-guide` slices large work.

---

### Zone G — Propose/Review phase reasoning tools

These two **compose** (run in order), not compete. Neither replaces the other.

| Order | Skill | Role |
|---|---|---|
| First | [decision-frameworks](../skills/decision-frameworks/SKILL.md) | Build structured options (SWOT / 5-Why / First Principles / Decision Matrix). Use when the problem space is ambiguous or multiple alternatives exist. |
| Second | [cognitive-bias-checklist](../skills/cognitive-bias-checklist/SKILL.md) | Meta-cognitive scan on the reasoning quality. Run AFTER decision-frameworks produces its output — checks for anchoring, confirmation bias, overconfidence, etc. |

**Trigger condition:** Zone G fires only when a design decision is being made (Propose or Review phase). Skip both for PATCH tasks. Skip `cognitive-bias-checklist` if `decision-frameworks` didn't run (no options to scan).

---

## Conflict Resolution Rules

When this matrix and a skill's individual description disagree:

1. **This file wins** for trigger-window selection (which skills run).
2. **The skill's own file wins** for content rules (how the chosen skill executes).
3. If you find a new conflict not covered here, add a row rather than silently picking one skill.

## Global vs Local Skill Priority

When a project skill (`.claude/skills/<name>/SKILL.md`) and a global harness skill share the same name, **the project-local skill wins**. This is enforced by naming project skills with disambiguation suffixes (e.g., `ac-verify` instead of `verify`, `root-cause-debug` instead of `systematic-debugging`, `input-classifier` instead of `requirement-intake`). When in doubt, prefer the name listed under `.claude/skills/` over any same-named global skill.

## Index maintenance

After adding/removing/renaming a skill that participates in any zone above, update this file in the same commit. The [skill-graph-manager](../skills/skill-graph-manager/SKILL.md) skill verifies this in its lint pass.
