# Preferences Index (Constraints & Anti-Patterns)

This domain stores project-specific constraints, preferences, and do-not-do rules.

Hard rules:
- Before any architecture design or code change, you MUST read the relevant rules in this domain.
- These rules are enforced via hooks. If violated during `Propose` or `Implement`, the workflow MUST fail and roll back.

## Core Preferences
- None yet

## Constraints (Security, Architecture, Performance)

### Security Baseline
- No secrets in code: DO NOT hardcode API keys, secrets, or passwords in code or `application.yml`. Use environment variables or a config center.
- Authorization first: every API MUST enforce tenant/user authorization by default. DO NOT allow ID enumeration unless explicitly public.
- Detailed rules: [security_rules.md](security_rules.md)

### Performance Baseline
- No N+1: DO NOT run DB queries or RPC calls inside loops. Use batch queries and in-memory assembly.
- Avoid full table scans: all query patterns MUST hit indexes.

## Archive Extraction SOP
During `Archive`, the Agent MUST ask the human for a 1–10 rating.
- If rating <= 5, extract the root cause as an anti-pattern and append it here.
- If rating >= 8, extract the praised practice and append it to Core Preferences.

### Append Template
```markdown
- **{short rule}**: {what to do / what not to do, and why}
```
