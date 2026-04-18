# Domain Index (Vocabulary & State)

This index defines the project's vocabulary. The Agent MUST use these terms during `Explorer` and `Propose` to avoid domain drift.

## Core Concepts & State Machines

| Concept | Definition | Related Concepts | Details |
|---|---|---|---|
| (Example) Opportunity | A sales opportunity representing a potential deal | Lead, Account, Deal | `[opportunity_states.md]` |

---

## Archive Extraction SOP
If an `openspec.md` introduces new terms, roles, enum values, or state transitions, the Agent MUST extract them here during `Archive`.

### Append Template
```markdown
| {term} | {1–2 sentence definition and boundary} | {Related Concepts / Synonyms} | `[{details_doc}]` |
```

Anti-bloat rule: if the vocabulary exceeds 30 concepts, you MUST split into per-line dictionaries (example: `dictionary_xxx.md`) and keep this file as a router.
