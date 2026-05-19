# Preferences Index (Constraints & Anti-Patterns)

Project-specific constraints, security/performance baselines, and do-not-do rules. Consulted before any architecture design or code change.

## Security Baseline
- [Security] [NEVER] Hardcode API keys, secrets, or passwords in code or `application.yml`. Use environment variables or a config center.
- [Security] [MUST] Every API must enforce tenant/user authorization by default. DO NOT allow ID enumeration unless explicitly declared public.

Detailed rules: [security_rules.md](security_rules.md)

## Performance Baseline
- [Performance] [NEVER] Run DB queries or RPC calls inside loops. Use batch queries and in-memory assembly.
- [Performance] [MUST] All query patterns must hit indexes. Full table scans are forbidden without explicit justification.

> Append rule: tag format `[Tag] [Level] {rule}: {what / why}`. Tags: `[Security]`, `[Performance]`, `[DB]`, `[API]`, `[Global]`. Levels: `MUST`, `SHOULD`, `NEVER`.
> Archive SOP: ask human for 1–10 rating. ≤5 → extract anti-pattern. ≥8 → extract praised practice.

## WAL Fragments
