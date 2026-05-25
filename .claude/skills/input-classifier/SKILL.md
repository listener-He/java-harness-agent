---
name: "input-classifier"
description: "Classifies raw input as PRD/Idea/Bug/Signal/Perf/Security/Compliance/Feedback → [Intake] routing block. TRIGGER: input has no @shortcut, >1 line. NOT FOR: AC transcription (requirement-engineer)."
---

# Requirement Intake — Input Normalization Layer

The front door for all non-trivial inputs. Runs BEFORE the Intent Signal Matrix.

**Do NOT trigger for:** `@shortcut` commands, single-sentence LEARN questions, session resumes.

---

## Step 1: Classify Input Type

Read the raw input and assign ONE type:

| Type | Key Signals |
|---|---|
| **PRD** | Multi-section document; feature list; user stories; "requirements document", "PRD", "spec" |
| **Idea** | Single vague request; "I want to", "can we", "what if we add"; no concrete spec or metrics |
| **Bug** | Symptom in user language; "doesn't work", "broken", "users can't"; no stack trace |
| **Signal** | Stack trace, exception class, failing test name, error log line with file:line |
| **Performance** | "slow", "timeout", "latency", "takes N seconds"; without a clear cause |
| **Security** | CVE number, "vulnerability", "security audit", "pentest finding", OWASP reference |
| **Compliance** | "regulation", "GDPR", "PCI-DSS", "compliance", "audit requirement", external mandate |
| **Feedback** | Tech lead comment, code review note, architecture review, "the team said we should" |

---

## Step 2: Process by Type

### PRD
1. Extract individual requirement units. Number them.
2. For each unit: identify the domain noun (what system/entity it touches).
3. Draft one testable AC per unit: `Given [context], when [action], then [observable result]`.
4. Flag cross-unit conflicts (two units use contradictory verbs on the same object).
5. Identify dependency order (which requirements block others).
6. Output: prioritized requirement queue → feeds `task-decomposition-guide` → `launch_spec`.

### Idea
1. Identify the ONE most design-constraining unknown (not all unknowns — the single most important one).
2. Ask ONLY that question. Wait for answer.
3. From the answer: write a minimal spec (2–4 sentences, concrete scope).
4. Draft 2–3 AC candidates.
5. Estimate scope: ≤1 file → TRIVIAL; ≤3 files, no schema change → PATCH; wider → STANDARD.

### Bug
1. Extract: affected user flow + symptom + reproducibility (always/sometimes/once).
2. Identify the first system boundary where failure occurs (UI? API? Service? DB?).
3. Route directly to `root-cause-debug` with pre-filled context:
   - Symptom: [extracted]
   - Suspected boundary: [extracted]
   - Reproducibility: [extracted]

### Signal (stack trace / failing test / error log)
1. The signal IS the requirement — no translation needed.
2. Extract: error class + file + line (or failing test method name).
3. Route directly to `root-cause-debug` with the signal as the starting hypothesis anchor.
4. Skip symptom extraction (signal is already precise).

### Performance
1. Check: does the input include a baseline measurement (current latency/throughput)? 
   - NO → first action is measurement, not investigation. Output: `first_step=establish_baseline`.
   - YES → extract the metric and target. Route to Scenario D.
2. Draft AC: `[endpoint] responds in < [target]ms at [load] concurrent users`.

### Security (CVE / audit finding)
1. Map the finding to affected code areas (from CVE description or finding text keywords).
2. Assess blast radius: which APIs, data flows, or user roles are exposed?
3. Draft AC: `[vulnerability type] is not exploitable via [attack vector]`.
4. Route: intent=Change, profile=STANDARD, risk=HIGH, invoke `security-review-checklist`.

### Compliance
1. Extract the constraint: what is specifically forbidden or required by the mandate?
2. Map constraint to code areas (search for affected data types, APIs, storage patterns).
3. Define verification method: how do we prove compliance? (audit log, encryption at rest, data retention policy, etc.)
4. Draft AC in terms of the verifiable behavior, not the regulation text.
5. Route: profile=STANDARD, risk=MEDIUM/HIGH depending on scope.

### Feedback (tech lead / code review / architecture review)
1. Understand the architectural direction the reviewer intends.
2. Separate "refactoring only" (internals change, API preserved) from "behavior change".
3. Map to specific files/classes.
4. Refactoring → profile=PATCH. Behavior change → profile=STANDARD.

---

## Step 3: Emit Normalized Output

After processing, emit the `[Intake]` block. This feeds directly into the `[Intent Check]` line.

```
[Intake]
Input-Type: <PRD | Idea | Bug | Signal | Performance | Security | Compliance | Feedback>
Intent: <Change | Learn | Debug>
Profile: <TRIVIAL | PATCH | STANDARD | EPIC>
Scenario: <none | A | B | C | D | E | Greenfield | Migration | Integration>
Scope-Hints:
  - <likely affected package or file area 1>
  - <likely affected package or file area 2>
AC-Candidates:
  - Given [context], when [action], then [observable result]
  - (2–4 items)
Open-Questions: (max 2 — only truly blocking before any work can start)
  - <question>
Route: → <Explorer | root-cause-debug | task-decomposition-guide | Scenario X | greenfield-scaffold | migration-planner>
```

**Rules:**
- `Open-Questions` is empty unless the answer changes the Profile or Scenario classification.
- AC-Candidates are drafts — they will be refined in Explorer. Do not block on perfect wording.
- If input type is ambiguous between two types: pick the more conservative one (STANDARD over PATCH; Bug over Idea).

---

## Integration

**In CLAUDE.md Initial Action Decision Tree:**
Add as Rule -1 (before Rule 0): "Input has no @shortcut AND is longer than a one-liner? → Apply `input-classifier` before Intent Signal Matrix."

**In ROUTER.md:**
The `[Intake]` block enriches the Intent Signal Matrix. When an `[Intake]` block is present, use its `Intent` and `Profile` as the starting classification (still subject to manual override by user).

**Feeds into:**
- `task-decomposition-guide` (for PRD with multiple requirements)
- `root-cause-debug` (for Bug and Signal types)
- `product-manager-expert` PRD Ingestion Mode (for PRD type)
- Direct Explorer phase (for Idea, Compliance, Feedback types)
- `greenfield-scaffold` (when no existing codebase context)
- `migration-planner` (when A→B migration is implied)
