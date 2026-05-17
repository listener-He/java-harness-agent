---
name: "security-review-checklist"
description: "Security checklist for Java backend code reviews. Covers secrets, input validation, authZ, IDOR, data exposure, dependency safety, error handling, and soft-delete safety. Run before delivery for HIGH risk or auth/data changes."
---

# Security Review Checklist

**CRITICAL RULE**: Run this checklist on any HIGH risk change, auth-related code, or data-processing code BEFORE finalizing the response. If any item fails, fix immediately and re-evaluate. Max 2 retries per item before escalating to human security review.

This checklist complements `code-review-checklist` — it does NOT replace it. Run both for HIGH risk changes.

---

## When to Use

- Risk is rated HIGH in the task focus card
- Change touches authentication, authorization, or permission logic
- Change processes, stores, or transmits PII or sensitive data
- New dependency added
- New API endpoint added that accepts external input

## When NOT to Use

- Pure refactoring with no logic change (method rename, extract method, etc.)
- Documentation-only changes
- Test-only changes with no production code modification

---

## Self-Correction Loop

1. **Evaluate**: run each checklist item against the changed code.
2. **Fix**: if a check fails, fix it immediately before moving on.
3. **Re-evaluate**: re-run the failed item after the fix.
4. **Escalate (Max 2 retries)**: if the same item cannot be fixed in 2 attempts due to architectural constraints, STOP and produce an `escalation_note.md` explaining the issue. Ask the human security reviewer for guidance. Do not ship unfixed HIGH severity security issues.

---

## Checklist

### 1. Secret Scanning

- [ ] No hardcoded credentials, API keys, tokens, or passwords anywhere in source code (Java, XML, YAML, properties).
- [ ] No secrets in `application.yml`, `application.properties`, or any config committed to the repo — all secrets reference environment variables or a secrets manager.
- [ ] `.env` files are listed in `.gitignore` and NOT committed.
- [ ] No base64-encoded or obfuscated credentials in comments or string literals.

### 2. Input Validation

- [ ] All external inputs (request body, query params, path vars) are validated at the controller layer using `@Validated` or `@Valid`.
- [ ] MyBatis SQL parameters use `#{}` (parameterized) — NOT `${}` (string interpolation). `${}` is only acceptable for non-user-controlled structural values (e.g., column names from a safe internal enum).
- [ ] No `eval()`, `Runtime.exec()`, `ProcessBuilder`, `ScriptEngine`, or dynamic class loading with user-supplied input.
- [ ] File upload endpoints validate file type by MIME type and magic bytes, not only by file extension.

### 3. Authentication & Authorization

- [ ] Every write endpoint (add/update/delete) has `@ResourceLock` or equivalent concurrency/permission guard.
- [ ] Tenant isolation is enforced — the MyBatis-Plus `TenantLineInnerInterceptor` is active, or manual `tenant_id` filtering is verified.
- [ ] No IDOR vulnerability: user A cannot access user B's resources by manipulating an ID in the request. Ownership is verified server-side (not just by the client-supplied ID).
- [ ] Permission checks happen BEFORE data is fetched — not after.
- [ ] Sensitive operations (password change, account deletion, privilege escalation) require re-authentication or secondary confirmation.

### 4. Data Exposure

- [ ] Response DTOs do not include internal system IDs, passwords, hashed passwords, salt values, or PII fields unnecessarily.
- [ ] No `SELECT *` in XML mappers returning to external callers — only required columns are fetched.
- [ ] Paginated list endpoints do not leak records belonging to other tenants.
- [ ] Log statements do not print passwords, tokens, full card numbers, or other sensitive field values.

### 5. Dependency Safety

- [ ] Any newly added Maven/Gradle dependency has been checked for known CVEs (via `mvn dependency:tree` + OWASP Dependency Check, or equivalent).
- [ ] No new dependency pulls in a transitive dependency with a known HIGH/CRITICAL CVE without explicit justification.
- [ ] Dependency version is pinned — no open-ended version ranges (e.g., `[1.0,)`).

### 6. Error Handling

- [ ] API error responses do not include Java stack traces.
- [ ] Error messages do not reveal internal class names, table names, SQL queries, or file system paths.
- [ ] Exceptions are logged server-side with full detail but returned to clients with only a safe, abstract message and error code.
- [ ] 404 vs 403 distinction is intentional: do not return 404 to hide existence of a resource if the user is simply unauthorized (prefer 403 for authenticated but unauthorized access).

### 7. Soft Delete Safety

- [ ] All queries against soft-deleted tables include `is_deleted = 0` (or the MyBatis-Plus logical delete annotation is active and not bypassed).
- [ ] Soft-deleted records cannot be retrieved via any API path — including by ID lookup, list, or search.
- [ ] Reactivation of soft-deleted records (if supported) requires explicit permission and is logged.

---

## Output Format

At the end of the review, append a brief Security Review Report:

> **Security Review Report:**
> - Checks run: [list of categories]
> - Issues found and fixed: [list any self-corrections made]
> - Escalated items: [list any items that could not be resolved, with escalation_note.md reference]
> - Result: PASS / ESCALATED

---

## Related Skills

- [code-review-checklist](../code-review-checklist/SKILL.md): run alongside this skill for HIGH risk changes
- [verify](../verify/SKILL.md): final evidence-driven validation after all review checks pass
- [linter-severity-standard](../linter-severity-standard/SKILL.md): bypass justification protocol if a check cannot be satisfied
