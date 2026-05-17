# Reviews Index

This domain stores review artifacts and summaries (design reviews, code review checklists, audit reports).

## Hard Rules (MUST)
- If you produce a reusable review report, it MUST be linked from this index.
- Keep entries short and evidence-based. Link to the source files and line ranges when applicable.

## Review Records

| Review Date | Target (PR/Design/Spec) | Reviewer | Key Findings / Status | Report Link |
|---|---|---|---|---|
| (Example) 2026-04-14 | PR-123: User Login | Agent (Code Review) | Passed with minor style fixes | `[cr_user_login.md]` |

---

## Archive Extraction SOP
During `Archive` (or after Phase 3: Review), append a new row for any significant review report generated.

### Append Template
```markdown
| {YYYY-MM-DD} | {Target} | {Reviewer} | {Status/Key Findings} | `[{report_doc_name}]` |
```
