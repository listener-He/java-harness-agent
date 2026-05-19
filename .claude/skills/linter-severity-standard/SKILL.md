---
name: "linter-severity-standard"
description: "Shared OK/WARN/FAIL severity contract for every gate script under .claude/scripts/gates/. TRIGGER whenever a gate is invoked — agent MUST surface WARN/FAIL inline using the reporting protocol below. New gates MUST pass `_severity_audit.py`."
---

# Linter Severity Standard (OK / WARN / FAIL)

This is the **mandatory contract** every script under `.claude/scripts/gates/` follows so the main agent can mechanically classify gate output. The contract has three parts: exit codes, stdout format, and an agent reporting protocol.

---

## 1. Severity Definitions

| Severity | Exit Code | Semantics | Effect on workflow |
|---|---|---|---|
| **OK** | 0 | Check passed cleanly | Continue |
| **WARN** | 1 | Check found a soft issue; not blocking | Continue, BUT agent must report it and either fix or explicitly acknowledge |
| **FAIL** | 2 | Hard violation; blocks the phase | Stop, fix, re-run. Max 2 retries (anti-loop) then escalate |

WARN is **not** "I'll ignore that". WARN means "user/agent must see this and decide". If you skip a WARN without acknowledgment, the failure is on you.

---

## 2. Gate Output Contract (mandatory format)

Every gate script MUST produce output that satisfies both:

### 2a. Text mode (default)
- **First line** starts with `OK:` / `WARN:` / `FAIL:` followed by the gate name and a one-line summary
- Subsequent lines (`- detail`) hold the per-finding detail
- Stderr only for crashes/exceptions, never for normal findings

Example:
```
WARN: task_brief gate
- AC↔Scope cross-check: no identifier overlap
-   Likely cause: scope too narrow
```

### 2b. JSON mode (opt-in via `--json` flag, when implemented)
- One JSON object on a single line: `{"severity":"WARN","gate":"task_brief_gate","message":"...","details":["...","..."]}`
- Used by orchestration scripts that aggregate multiple gates

### 2c. Constants in source
Every gate MUST declare these constants (or import them from `_severity.py`):
```python
EXIT_WARN = 1
EXIT_FAIL = 2
```
The audit script `_severity_audit.py` scans for this — non-conformers fail CI.

Helpers available in `.claude/scripts/gates/_severity.py`:
- `Severity` enum, `Result` dataclass, `emit(result, as_json=False)`
- Optional. Inline `EXIT_WARN = 1` style is equally valid.

---

## 3. Agent Reporting Protocol (mandatory when invoking any gate)

When the agent runs a gate script, it MUST:

1. **Capture the exit code** — do not rely on text parsing alone
2. **For WARN (exit 1)**: re-emit the findings as a `[WARN] <gate>: <reason>` block in the visible response, then either (a) fix and re-run, or (b) explicitly state "accepting WARN because <reason>". Silent skip is FORBIDDEN.
3. **For FAIL (exit 2)**: stop immediately. Output `[FAIL] <gate>: <reason>` and either fix-and-retry (max 2 attempts) or escalate via `[Plan Invalidation]` per lifecycle.md.
4. **For OK (exit 0)**: continue silently. No need to echo OK lines.

Anti-pattern to avoid: "the gate complained but the change is fine" without naming the WARN. If the agent has reason to accept a WARN, it must say so verbatim.

---

## 4. Per-Gate Specifics (legacy reference)

These are the historical category-level thresholds. They still hold, but the universal contract above is the single source of truth for severity handling.

### 4.1 Wiki Graph (`wiki_linter`)
- FAIL: dead Markdown links
- WARN: orphan files (not referenced + not index/purpose/root), files > 500 lines

### 4.2 Contract Health (`schema_checker` / `task_brief_gate`)
- FAIL (Full Spec): missing API contract / data model / acceptance criteria modules
- FAIL (Full Spec, AC↔Scope cross-check): empty Allowed Scope while ACs exist, or vice versa
- WARN (Full Spec): missing JSON examples; AC↔Scope identifier mismatch (heuristic)
- FAIL (Slim Spec): missing change summary / scope / risk / verification modules

---

## 5. Compliance Check

Run before merging any change to `.claude/scripts/gates/`:
```bash
python3 .claude/scripts/gates/_severity_audit.py
```
- Exit 0: all gates conform
- Exit 1: a gate lacks the `OK:|WARN:|FAIL:` output prefix
- Exit 2: a gate is missing severity constants entirely

Add this to the bootstrap / CI script when there is one.
