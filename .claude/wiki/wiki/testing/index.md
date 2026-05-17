# Testing & Evidence

This domain defines testing expectations and how to store objective evidence after implementing a feature or fixing a bug.

## Core Testing Strategies
- Unit tests: core service logic SHOULD have unit tests. Isolate dependencies when possible.
- Integration tests: critical DAO (Mapper) and Controller paths SHOULD have connectivity tests when applicable.

## Test Evidence Schema (MUST)
At the end of `QA Test` (or after a bug fix), the Agent MUST generate an objective evidence file named:
- `test_evidence_{feature_name}.md`

This file is used by hooks for verification and is archived during `Archive`.

### Evidence Template
```markdown
# Test Evidence: {feature_or_bug_name}

## 1. Environment & Commands
- Test command: `mvn test -Dtest=...`
- Coverage scope: `[classes/methods from the scope of change]`

## 2. Objective Logs (Snippets)
- Paste the minimal pass logs proving the tests were executed and green.
- Failed retries: `N`

## 3. Covered Edge Cases
- [Pass] Concurrent duplicate submission returns 409.
- [Pass] Cross-tenant query returns 403.
- [Pass] Happy path.

## 4. Coverage Metrics (Optional)
- Line coverage: XX%
- Branch coverage: XX%
```

## Archived Evidence Index
(This section is appended during `Archive`.)

### Append Template
```markdown
- [{YYYY-MM-DD}] {Feature/Bug Name}: `[{evidence_file.md}]`
```

### 2026
- No entries
