# Research Report Schema

Contract for RESEARCH-profile artifacts. Active at `.claude/runs/reports/`; archived at `.claude/wiki/archive/reports/`.

## Frontmatter (required, exact order)

```yaml
spec_mode: RESEARCH
scope: quick | deep
created: YYYY-MM-DD
slug: <kebab-or-snake>
```

| Field | Rule |
|---|---|
| `spec_mode` | MUST be `RESEARCH` literal |
| `scope` | `quick` → §3 ≥ 5 findings; `deep` → §3 ≥ 15 findings |
| `created` | ISO date; drives archive path |
| `slug` | MUST match filename slug and launch_spec row |

## Required sections (all 7)

`## §1 Question`, `## §2 Method`, `## §3 Findings`, `## §4 Analysis`, `## §5 Recommendations`, `## §6 Open Questions`, `## §7 Evidence Index`

## Per-section rules

| Section | Hard rule | FAIL on |
|---|---|---|
| §1 Question | ≥ 20 chars; phrase as `?` OR explicit goal verb (评估/对比/分析) | < 20 chars |
| §2 Method | ≥ 3 bullets OR ≥ 100 chars | both below |
| §3 Findings | `scope=quick` ≥ 5 / `scope=deep` ≥ 15; every bullet MUST carry ≥ 1 pointer | bullet count below quota OR pointer-less bullet |
| §4 Analysis | when §3 ≥ 5: ≥ 100 chars | violates (WARN only) |
| §5 Recommendations | 0–4 Option blocks (format below); 0 legal with explicit `> No actionable recommendations` line | malformed Option block |
| §6 Open Questions | each bullet uses Q / Why-blocked / Next template | structural drift |
| §7 Evidence Index | ≥ 1 deduplicated pointer | empty |

## §3 Findings — bullet format

```
- **<bold claim>** — evidence: <pointer>
```

Pointer whitelist (any one matches):

| Form | Pattern |
|---|---|
| Source line | `<path>:<line>` |
| Web | `https?://...` (+ retrieval date in §2) |
| Commit | 7–40 hex chars |
| Quote | `VERBATIM: "..."` |
| Wiki/WAL | `WAL: <path>` |

Findings are facts. Interpretations go in §4.

## §4 Analysis — uncertainty markers (MUST use one)

- `[high confidence]` — direct evidence, single reading
- `[inferred]` — pattern across multiple findings
- `[speculative]` — beyond evidence; flag for user validation

## §5 Recommendations — Option block format

```markdown
### Option <N>: <short title>
- **Summary:** one sentence
- **Effort:** S | M | L
- **Risk:** low | medium | high
- **If chosen, run:** <next slash command + slug>
- **Rationale:** 1–3 sentences citing §3/§4
```

## §6 Open Questions — bullet format

```markdown
- **Q:** <question>
  **Why blocked:** data missing | out of scope | requires human judgment | needs experiment
  **Next:** <next investigation> OR "ask user"
```

## §7 Evidence Index — bullet format

```markdown
- <pointer> — <one-line context>
```

## Size limit

- Hard cap: 10000 lines per single report (override of default 3000-line wiki cap; see `policy.md`).
- Approaching cap → split:
  - Main: `<slug>_research.md` keeps §1/§2/§4/§5/§6 + §3 summary
  - Appendix: `<slug>_evidence_<topic>.md` carries full §3 + §7

## Gate

```bash
python3 .claude/scripts/gates/research_report_gate.py --require <path>
```

| Exit | Meaning |
|---|---|
| 0 | PASS |
| 1 | WARN (one minor issue, e.g. §4 thin given §3 density) |
| 2 | FAIL (frontmatter / section / pointer / quota violation) |
