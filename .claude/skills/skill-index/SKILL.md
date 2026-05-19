---
name: "skill-index"
description: "Skill navigator. List active skills, locate archived ones, choose the right sequence per scenario."
---

# Skill Index — Central Navigator

This framework keeps 29 "active" skills auto-loaded by Claude Code. 12 lower-frequency skills are stored under `.claude/skills-archive/` and need to be re-activated on demand (see § Archive).

**Scope:** A typical Claude Code install may surface external skills (`lark-*`, `claude-api`, `loop`, `schedule`, etc.). Those are global utilities — ignore unless asked by name.

---

## Quick Start — Common Scenarios

| Scenario | Skill sequence |
|---|---|
| Any non-trivial input (PRD / bug / signal) | `requirement-intake` → route below |
| Writing a new feature | `brainstorming` → `task-decomposition-guide` → `java-architecture-standards` → `test-driven-development` → `ultraqa` → `wal-documentation-rules` → `remember` |
| Processing a PRD | `product-manager-expert` (Ingestion) → `task-decomposition-guide` → feature flow |
| Fixing a bug | `systematic-debugging` → `test-driven-development` → `verify` |
| Code review / QA | `code-review-checklist` → `java-testing-standards` → `ultraqa` |
| Security or HIGH risk change | `security-review-checklist` → `adversarial-review` → `code-review-checklist` → `verify` |
| Cleanup after AI-heavy session | `ai-slop-cleaner` → `code-review-checklist` |
| Recording a design decision | `architecture-decision-records` |
| Knowledge preservation | `wal-documentation-rules` (Archive) → `remember` (cross-session) |
| Pre-Explorer codebase context | `local-code-intelligence` (BM25 + symbol index + failure memory) |
| **Migration / Greenfield / Incident / EPIC / PRD / Release / Pipeline** | See `.claude/rules/routing.md` Special Scenarios — the matching scenario inlines the archive path to read |

---

## 0. Active (Auto-loaded by Claude Code)

These 29 skills live under `.claude/skills/<name>/SKILL.md` and are visible to the Skill tool without further action.

### 0.0 Default Enabled (13) — daily workflow

| Skill | Lifecycle Phase(s) | Primary Role |
|---|---|---|
| [brainstorming](../brainstorming/SKILL.md) | Explorer / Propose | Requirement Engineer |
| [task-decomposition-guide](../task-decomposition-guide/SKILL.md) | Propose / Review | System Architect |
| [writing-plans](../writing-plans/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |
| [systematic-debugging](../systematic-debugging/SKILL.md) | Implement / QA | Lead Engineer / Code Reviewer |
| [test-driven-development](../test-driven-development/SKILL.md) | Implement | Lead Engineer |
| [verify](../verify/SKILL.md) | QA / Archive | Code Reviewer / Knowledge Extractor |
| [code-review-checklist](../code-review-checklist/SKILL.md) | QA | Code Reviewer |
| [wal-documentation-rules](../wal-documentation-rules/SKILL.md) | Archive | Knowledge Extractor |
| [skill-graph-manager](../skill-graph-manager/SKILL.md) | Any (skills change) | Skill Graph Curator |
| [java-architecture-standards](../java-architecture-standards/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |
| [java-coding-style](../java-coding-style/SKILL.md) | Implement | Lead Engineer |
| [java-testing-standards](../java-testing-standards/SKILL.md) | QA | Code Reviewer |
| [mybatis-sql-standard](../mybatis-sql-standard/SKILL.md) | Propose / Implement | System Architect / Lead Engineer |

### 0.1 Role-Required & QA-Critical (8)

| Skill | Required When |
|---|---|
| [cognitive-bias-checklist](../cognitive-bias-checklist/SKILL.md) | Requirement Engineer / System Architect — Propose phase |
| [spec-quality-checklist](../spec-quality-checklist/SKILL.md) | Documentation Curator / pre-gate self-check |
| [decision-frameworks](../decision-frameworks/SKILL.md) | System Architect — ambiguous root cause or design choice |
| [linter-severity-standard](../linter-severity-standard/SKILL.md) | Code Reviewer — interpreting gate output |
| [ultraqa](../ultraqa/SKILL.md) | QA phase, AC count ≥ 4 OR HIGH risk |
| [security-review-checklist](../security-review-checklist/SKILL.md) | HIGH risk change touching auth/data/secrets |
| [skill-creator](../skill-creator/SKILL.md) | Adding/updating a SKILL.md |
| [skill-index](./SKILL.md) | This file |

### 0.2 Reactivated — Reasoning, Knowledge & Cleanup (8)

These were moved back from archive because they fit the daily flow.

| Skill | Use When |
|---|---|
| [adversarial-review](../adversarial-review/SKILL.md) | HIGH risk Review phase — one isolated round of critique. Required by lifecycle.md HIGH flow. Detects requirements/design contradictions. |
| [stakeholder-conflict-resolver](../stakeholder-conflict-resolver/SKILL.md) | Downstream from adversarial-review Category A CRITICAL — when conflicting requirements come from different stakeholders (PM / frontend / security / legal), produces structured conflict map + resolution decision. |
| [local-code-intelligence](../local-code-intelligence/SKILL.md) | Explorer phase — BM25 wiki search + Java symbol index + failure memory. Run before reading source files. |
| [remember](../remember/SKILL.md) | Archive phase — classify discovered knowledge into project memory / notepad / docs. |
| [ai-slop-cleaner](../ai-slop-cleaner/SKILL.md) | After AI-heavy session — regression-safe cleanup of dead code, duplicates, over-abstraction. |
| [architecture-decision-records](../architecture-decision-records/SKILL.md) | When an architectural decision is made — capture as ADR. Pairs with HIGH-risk ≥2-ADR requirement. |
| [requirement-intake](../requirement-intake/SKILL.md) | Front door for any non-trivial input (PRD, bug report, signal, security finding) before routing. |
| [product-manager-expert](../product-manager-expert/SKILL.md) | PRD generation (Mode A) or PRD ingestion → AC + implementation queue (Mode B). |

### 0.3 Lifecycle Phase Map (STANDARD)

| Phase | Role | Skills |
|---|---|---|
| Pre-Explorer | — | `requirement-intake` (if input is non-trivial) |
| Explorer | Requirement Engineer | `local-code-intelligence` → brainstorming → (cognitive-bias-checklist) → (spec-quality-checklist) |
| Propose / Review | System Architect | brainstorming (≥2 ADR via `architecture-decision-records`) → task-decomposition-guide → decision-frameworks |
| Review (HIGH only) | Devil's Advocate | `adversarial-review` (one isolated round) |
| Implement | Lead Engineer + Focus Guard | writing-plans → java-architecture-standards / java-coding-style / mybatis-sql-standard → systematic-debugging / test-driven-development |
| QA | Code Reviewer | code-review-checklist → java-testing-standards → ultraqa → (security-review-checklist) |
| Cleanup | Lead Engineer | (optional) `ai-slop-cleaner` |
| Archive | Knowledge Extractor | wal-documentation-rules → verify → `remember` (cross-session lessons) |

For Greenfield / Migration / EPIC / Incident / Pipeline / Release flows, the matching scenario in `.claude/rules/routing.md` inlines the archive path the agent must read.

---

## 1. Archive (Scenario-Mounted, Not Auto-loaded)

The following 12 skills live under `.claude/skills-archive/<name>/SKILL.md`. They are not auto-injected — instead, each is **referenced inline by the rule or agent that needs it**, with the full path written in place. No central lookup table, no "decide whether to activate" step.

### 1.1 Where each archived skill is referenced

| Skill | Referenced from |
|---|---|
| `incident-response` | `.claude/rules/routing.md` → Scenario A |
| `migration-planner` | `.claude/rules/routing.md` → Scenario B |
| `greenfield-scaffold` | `.claude/rules/routing.md` → Scenario GREENFIELD |
| `blueprint` | `.claude/rules/routing.md` → Scenario EPIC |
| `dispatching-parallel-agents` | `.claude/rules/routing.md` → Scenario EPIC |
| `using-git-worktrees` | `.claude/agents/lead-engineer.md` → HIGH-risk / parallel work |
| `ai-pipeline` | `.claude/rules/routing.md` → Scenario PIPELINE |
| `self-improve` | `.claude/rules/routing.md` → Scenario PIPELINE |
| `eval-harness` | `.claude/rules/routing.md` → Scenario PIPELINE |
| `external-research` | `.claude/rules/routing.md` → Scenario D + Scenario PIPELINE |
| `release` | `.claude/rules/routing.md` → Scenario RELEASE |
| `deepinit` | `.claude/rules/routing.md` → Scenario GREENFIELD |

Each referenced location writes the full `.claude/skills-archive/<name>/SKILL.md` path inline. When the rule fires, the agent reads that exact file — no judgment about whether to mount it, no lookup needed.

### 1.2 Why archive (not delete)

Auto-loading 12 rarely-used skill descriptions costs ~1,800 tok on every session. By keeping these out of `.claude/skills/` and inlining their paths at the point of use, the framework retains the full capability surface while paying the cost only when the rule actually fires.

---

## Related

- `.claude/agents/` — role catalog; each role file lists which skills it depends on
- `.claude/rules/routing.md` — when each lifecycle phase fires
- `.claude/skills/skill-creator/SKILL.md` — used when adding a new skill (will prompt you to register here)
