# Security Baseline (Hard Constraints)

This file is a hard "do-not-violate" list for both design (`openspec.md`) and code review.

Hard rule:
- Any violation MUST be blocked by `guard_hook` or `fail_hook` and rewritten.

## 1. Secrets & Credentials
- [Security-Secret] No hardcoding: DO NOT hardcode passwords, access keys, tokens, or private keys in code.
- [Security-Secret] No plaintext logs: DO NOT log objects containing sensitive fields (passwords, phone numbers, government IDs, full card numbers).
- [Security-Secret] Config hygiene: any secret referenced by `application.yml` or config classes MUST use environment variables (example: `${DB_PASSWORD}`) or encrypted values.

## 2. Authorization & Isolation
- [Security-Auth] Authorization on target ID: for any CRUD API, you MUST verify the operator is allowed to access the target ID (prevent ID enumeration).
- [Security-Auth] Data scoping: list queries MUST include data permission filters by default (example: `tenant_id`, `org_id`) to prevent data leakage.

## 3. Protection & Throttling
- [Security-Limit] Exposure control: services/APIs MUST NOT be exposed publicly unless explicitly required.
- [Security-Limit] Anti-replay / idempotency: all non-query APIs (POST/PUT/DELETE) MUST consider idempotency. DO NOT allow repeated requests to corrupt state.
- [Security-Limit] Export limits: export endpoints MUST have throttling and max rows to prevent OOM or DB overload.

## 4. Data Security
- [Security-Data] SQL injection: use parameterized queries (example: MyBatis `#{}`); DO NOT use string interpolation (example: `${}`) unless the input is provably safe.
- [Security-Data] Soft delete: core business tables SHOULD use soft delete by default. Avoid physical deletes unless explicitly justified.
