# Architecture Index (Baselines & ADRs)

This domain records architecture baselines and ADRs (Architecture Decision Records).

## Hard Rules (MUST)
- When making cross-cutting technical choices (module boundaries, middleware, global patterns), you MUST consult existing ADRs or add a new one.

## Baselines & Guards
- Security baseline: [../preferences/security_rules.md](../preferences/security_rules.md)

## ADR List

| ADR # | Title | Status | Decision Summary |
|---|---|---|---|
| (Example) ADR-001 | Use JWT for stateless auth | Accepted | Reduce Redis dependency; validate at the gateway |

---

## Archive Extraction SOP
If `Propose` makes a global architecture decision, you MUST write it back here during `Archive`.

### Append Template
```markdown
| ADR-{XXX} | {decision title} | Accepted | {one-line reason} |
```
