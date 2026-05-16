# Preferences Index (Constraints & Anti-Patterns)

This domain stores project-specific constraints, preferences, and do-not-do rules.

Hard rules:
- [Global] [MUST] Before any architecture design or code change, read the relevant rules in this domain.
- [Global] [MUST] These rules are enforced via hooks. Violations during `Propose` or `Implement` MUST trigger fail_hook and rollback.

## Core Preferences

(None yet)

## Constraints (Security, Architecture, Performance)

### Security Baseline

- [Security] [NEVER] Hardcode API keys, secrets, or passwords in code or `application.yml`. Use environment variables or a config center.
- [Security] [MUST] Every API must enforce tenant/user authorization by default. DO NOT allow ID enumeration unless explicitly declared public.

Detailed rules: [security_rules.md](security_rules.md)

### Performance Baseline

- [Performance] [NEVER] Run DB queries or RPC calls inside loops. Use batch queries and in-memory assembly.
- [Performance] [MUST] All query patterns must hit indexes. Full table scans are forbidden without explicit justification.

## Archive Extraction SOP

During `Archive`, the Agent MUST ask the human for a 1–10 rating.
- [Global] [MUST] If rating <= 5, extract the root cause as an anti-pattern and append it here.
- [Global] [MUST] If rating >= 8, extract the praised practice and append it to Core Preferences.

### Append Template

```
[{Tags}] [{Level}] {short rule}: {what to do / what not to do, and why}
```

*`[Tags]`: `[Security]`, `[Performance]`, `[DB]`, `[API]`, `[Global]`, etc. `[Level]`: `MUST`, `SHOULD`, or `NEVER`.*

---

## WAL Fragments
- [20260506_wal_compaction_preferences.md](wal/20260506_wal_compaction_preferences.md) — Runtime artifact path standardization
