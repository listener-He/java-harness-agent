---
name: incident-response
description: "Production emergency triage and post-mortem protocol. Phase 1: rapid triage (classify severity, identify blast radius, issue immediate mitigation). Phase 2: root cause investigation using Hypothesis Falsification. Phase 3: post-mortem with structured Action Items and 5-Why chain. TRIGGER when input-classifier emits Input-Type: Incident (A9) or user reports a production outage, data corruption, security breach, or SLA violation."
---

# Incident Response

Production emergencies require a different mode: triage first, diagnose second, fix third, learn fourth. This skill enforces that order.

**Trigger condition:**
- `input-classifier` emits `Input-Type: Incident`
- User reports: production outage, data corruption event, security breach, SLA violation, on-call page

---

## Phase 1: Triage (Time-boxed: 15 minutes)

### Step 1: Severity Classification

| Severity | Definition | Response SLA |
|---|---|---|
| **P0 — Critical** | Complete service outage, data loss, security breach, revenue-blocking | Immediate — all hands |
| **P1 — High** | Partial outage, degraded performance >50% users, data integrity risk | < 30 min response |
| **P2 — Medium** | Feature broken, <50% users affected, no data risk | < 2 hours response |
| **P3 — Low** | Cosmetic issue, single-user impact, workaround available | Next business day |

Classify immediately. Do not defer severity assignment.

### Step 2: Blast Radius Assessment

```
Affected systems: [list]
Affected user segments: [percentage / segments]
Data at risk: [yes/no — what data, what volume]
Downstream dependencies impacted: [list]
SLA breach: [yes/no — which SLA, how long breached]
```

### Step 3: Immediate Mitigation (before root cause)

For P0/P1: issue mitigation NOW, before diagnosis.

Common mitigations (pick fastest applicable):
- **Rollback**: revert to last known good deployment
- **Feature flag off**: disable the affected feature path
- **Traffic rerouting**: shift traffic to healthy region/instance
- **Rate limiting**: apply emergency rate limit to stop damage spread
- **Manual override**: switch to manual process while system is down

Record: `Mitigation applied: [what] at [time]. Service status: [restored/partial/still down].`

Do NOT wait for root cause to apply mitigation on P0/P1.

---

## Phase 2: Root Cause Investigation

Use the `root-cause-debug` skill with its Hypothesis Falsification Protocol:

1. **Hierarchical Localization**: Module → File → Method → Line
2. **State Hypothesis**: "The failure is caused by [specific mechanism]"
3. **Derive Falsifiable Prediction**: "If this hypothesis is correct, then [observable symptom X] will be present in [specific location]"
4. **Test Prediction**: collect evidence (logs, metrics, traces) WITHOUT applying a fix
5. **Fix**: apply the fix
6. **Counterfactual Verification**: revert the fix → confirm the symptom returns → re-apply

For incidents, add one step before Hypothesis Falsification:

**Timeline Reconstruction** (MUST complete before hypothesizing):
```
[time] — Last known good state
[time] — First anomaly signal (what, where)
[time] — Escalation / alert triggered
[time] — Current state
Change events in window: [deployments, config changes, traffic spikes, external dependency changes]
```

Changes in the window are the primary hypothesis candidates.

---

## Phase 3: Post-Mortem

Complete within 24h of P0/P1 resolution, 72h for P2.

### Post-Mortem Structure

Write to `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_postmortem.md`:

```markdown
# Post-Mortem: [Incident Title]

## Summary
- **Severity**: P0/P1/P2/P3
- **Duration**: [start] → [resolution] = [X hours Y minutes]
- **Impact**: [users/systems affected, data risk, revenue impact]
- **Root Cause**: [one-sentence summary]

## Timeline
[Reconstructed timeline from Phase 2]

## Root Cause Analysis — 5-Why Chain

**Why 1**: Why did [the symptom] occur?
→ Because [immediate cause]

**Why 2**: Why did [immediate cause] occur?
→ Because [underlying cause]

**Why 3**: Why did [underlying cause] occur?
→ Because [deeper cause]

**Why 4**: Why did [deeper cause] occur?
→ Because [systemic cause]

**Why 5**: Why did [systemic cause] occur?
→ Because [root cause — the thing we must fix to prevent recurrence]

Stop at Why N when the answer is "we have no control over this" or when the answer is a policy/process gap (actionable at organizational level).

## What Went Well
- [Thing 1 that helped limit impact or speed recovery]
- [Thing 2]

## What Went Wrong
- [Detection gap — how long before alert fired?]
- [Response gap — how long before mitigation applied?]
- [Recovery gap — how long to full restoration?]

## Action Items

| ID | Action | Owner | Due | Status | Prevents Recurrence? |
|---|---|---|---|---|---|
| AI-001 | [specific, verifiable action] | [team/person] | [date] | OPEN | YES — prevents [specific failure mode] |
| AI-002 | [monitoring improvement] | [team/person] | [date] | OPEN | NO — improves detection speed |

Action Item quality rules:
- Each AI must be a specific, assignable, verifiable task — not "improve monitoring"
- At least one AI must directly address the root cause (Why 5)
- Detection improvements and prevention improvements are both required
- AIs with no owner are not real AIs — assign or drop them

## Lessons Learned
[Non-obvious insights that should influence future design decisions]
```

### Action Item Feed

Feed AIs back into the task queue via `input-classifier` (Input-Type: Bug or Tech-Debt) so they enter the standard lifecycle rather than being lost in a post-mortem document.

---

## Hard Rules

1. **Mitigation before diagnosis** for P0/P1 — do not let systems burn while investigating.
2. **No blame.** Post-mortems identify systemic failures, not human failures. "Person X made a mistake" is not a root cause — "our deployment process allowed this mistake to reach production undetected" is.
3. **AIs must prevent or detect, not just document.** "Write a runbook" is insufficient if it doesn't prevent the failure mode.
4. **5-Why stops at the actionable layer.** If Why 6 would be "because our cloud provider had a bug", stop at Why 5 with "we had no circuit breaker for that dependency".
