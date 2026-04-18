# AGENTS.md — Entry Point & Hard Constraints

Single entry point. Read this file first on every session start. All links here use paths relative to the repo root.

---

## Hard Safety Constraints (Non-negotiable)

| Constraint | Rule |
|---|---|
| **Budget** | Intelligently calculate initial budget based on task complexity. Default: wiki 3, code 8. Pagination of the same file does NOT count. |
| **Reward Mechanism** | (Elastic extension) Output a `<Confidence_Assessment>` block explaining the specific missing concept/symbol to earn a budget reward (+2 wiki / +3 code) before hitting the hard stop (see [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). |
| **Budget exhausted** | STOP. File an Escalation Card (format in [CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md)). Do not guess paths or continue reading. |
| **Approval Gate** | For MEDIUM/HIGH risk changes: STOP after creating the spec, set status to `WAITING_APPROVAL`, and wait for explicit human approval before writing any code. |
| **Anti-loop** | Max 3 retries for any failing script, test, or linter per task. On exceed: STOP and ask human. Use `bypass_justification.md` only to downgrade trivial failures to WARN. |
| **Scope Guard** | Do not modify files outside the agreed `focus_card.md` scope without explicit human permission. |

---

## [Intent Check] — Mandatory First Output

Before any action (reading files, searching, writing code), the Agent MUST output one `[Intent Check]` line:

```
[Intent Check] intent=<Learn|Change|DocQA|Audit> | profile=@<learn|patch|standard> | risk=<LOW|MEDIUM|HIGH> | scenario=<none|A|B|C|D|E> | emergency=<true|false>
```

**Rules:**
- If the intent is ambiguous (missing action or object signal): output `[Intent Check] AMBIGUOUS — <reason>` and ask one clarifying question before proceeding.
- If a special scenario (A–E) is matched: include `scenario=<letter>` and apply Scenario routing overrides (see [ROUTER.md](.agents/router/ROUTER.md#6-special-scenarios)).
- The `[Intent Check]` line is the only required header. Do not add verbose preamble before it.

---

## Initial Action Decision Tree

```
Session start
├─ User provided explicit file path / class / snippet?
│   └─ YES → Read it directly. Skip wiki funnel.
├─ Resuming an interrupted session?
│   └─ YES → Read router/runs/launch_spec_*.md first. Restore from Status/Phase.
└─ Exploring a domain without explicit scope?
    └─ YES → Start at KNOWLEDGE_GRAPH.md and drill down.
```

---

## Single Sources of Truth (SSOT)

| Topic | File |
|---|---|
| Intent routing, profiles, shortcut DSL | [.agents/router/ROUTER.md](.agents/router/ROUTER.md) |
| Context navigation + write-back | [.agents/router/CONTEXT_FUNNEL.md](.agents/router/CONTEXT_FUNNEL.md) |
| Lifecycle phases + phase gates | [.agents/workflow/LIFECYCLE.md](.agents/workflow/LIFECYCLE.md) |
| Hook definitions (pre/guard/post/fail/loop) | [.agents/workflow/HOOKS.md](.agents/workflow/HOOKS.md) |
| Role mounting by (intent, profile, phase) | [.agents/workflow/ROLE_MATRIX.md](.agents/workflow/ROLE_MATRIX.md) |

---

## Essential Navigation Pointers

| Resource | Path |
|---|---|
| Wiki root index | [.agents/llm_wiki/KNOWLEDGE_GRAPH.md](.agents/llm_wiki/KNOWLEDGE_GRAPH.md) |
| Skill index | [.agents/skills/trae-skill-index/SKILL.md](.agents/skills/trae-skill-index/SKILL.md) |
| Project constraints & anti-patterns | [.agents/llm_wiki/wiki/preferences/index.md](.agents/llm_wiki/wiki/preferences/index.md) |
| Spec / proposal template | [.agents/llm_wiki/schema/openspec_schema.md](.agents/llm_wiki/schema/openspec_schema.md) |

---

## Commit Policy

**Never commit runtime state or caches.** The directories below are runtime-only:

- `.agents/router/runs/`
- `.agents/workflow/runs/`
- `.agents/events/drift_queue/`
- Python caches: `__pycache__/`, `*.pyc`
- Build/IDE artifacts: `target/`, `build/`, `.idea/`, `.vscode/`, `.DS_Store`

**Only commit stable artifacts**: source code, `openspec.md`, delivery capsules, and `wal/` fragments.
