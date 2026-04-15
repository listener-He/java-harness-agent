# Active Specs (OpenSpec)

This index lists `openspec.md` documents that are currently in progress or recently finished and still frequently referenced.

## Hard Rules (MUST)
- When a spec reaches `Archive` and its stable knowledge has been extracted, you MUST move it out of the active list.
- After extraction, long-term knowledge lives in `api/`, `data/`, and `domain/` indexes. The spec remains only for traceability.

## In Progress / Recent

| Feature | Status | Link |
|---|---|---|
| (Example) Add user login | `Phase 4: Implement` | `[20260414_user_login.md]` |

---

## Lifecycle SOP
- After `Propose`: add a new row with status `Phase 3: Review`.
- After `Archive`: remove it from the active list, and move it to "Recently Archived" (or fully transfer to `archive/index.md`).

### Append Template
```markdown
| {feature name} | `{current phase}` | `[{file_name.md}]` |
```

## Recently Archived
(Knowledge extracted into api/data/domain. This section is read-only traceability.)
- No entries
