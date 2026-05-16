---
name: stakeholder-conflict-resolver
description: "Multi-stakeholder requirement conflict resolution protocol. Detects when two or more requirements from different stakeholders are mutually exclusive, partially overlapping, or impose contradictory constraints. Produces a structured conflict map and a resolution decision (negotiate / defer / escalate). TRIGGER when requirement-intake emits Input-Type: Multi-stakeholder (A9 frame) or when adversarial-review Category A finds a CRITICAL mutual-exclusion finding."
---

# Stakeholder Conflict Resolver

When multiple stakeholders contribute requirements, conflicts are inevitable. This skill makes conflicts explicit, structured, and resolvable rather than silently embedding contradictions into the implementation.

**Trigger condition:**
- `requirement-intake` emits `Input-Type: Multi-stakeholder` (A9)
- `adversarial-review` Category A returns CRITICAL finding: mutual exclusion between two requirements
- User reports conflicting instructions from different parties

---

## Phase 0: Conflict Identification

### Step 1: Stakeholder Map

Enumerate each stakeholder and their stated requirements:

```
Stakeholder A: [role] — Requirements: [REQ-xxx, REQ-yyy]
Stakeholder B: [role] — Requirements: [REQ-zzz, REQ-www]
```

### Step 2: Conflict Detection

For each pair of requirements from different stakeholders, classify:

| Conflict Type | Definition | Example |
|---|---|---|
| **Hard Exclusion** | Both cannot be true simultaneously | "All data must be stored in EU" vs "All data must be replicated to US for DR" |
| **Resource Contention** | Both require the same resource with incompatible constraints | "Response time < 100ms" vs "Full audit log every request" |
| **Priority Inversion** | Stakeholder A's P0 is Stakeholder B's won't-have | "Ship by Friday" vs "Full security review before any release" |
| **Scope Overlap** | Both claim ownership of the same behavior | Two teams both defining the user authentication flow |
| **Implicit Conflict** | Each is valid alone, but their interaction produces an unintended result | "Cache all responses" + "Always serve personalized content" |

### Step 3: Conflict Map

Produce a structured conflict map:

```markdown
## Conflict Map

### CONFLICT-001: [Short Name]
- **Type**: Hard Exclusion / Resource Contention / Priority Inversion / Scope Overlap / Implicit
- **REQ-A**: [requirement text] — from [Stakeholder A]
- **REQ-B**: [requirement text] — from [Stakeholder B]
- **Contradiction**: [precise statement of why both cannot be satisfied]
- **Impact if unresolved**: [what breaks in the implementation]
- **Resolution Options**: (see Phase 1)
```

---

## Phase 1: Resolution Protocol

For each conflict, apply the appropriate resolution strategy:

### Strategy 1: Negotiate (prefer this)

Find a formulation that satisfies both stakeholders' underlying intent, even if not their literal requirement:

1. **Identify the underlying need** behind each stated requirement. Requirements are solutions; needs are the problems they solve.
2. **Find the intersection**: what outcome would satisfy both underlying needs?
3. **Propose a unified requirement** that covers the intersection.
4. **Get explicit sign-off** from both stakeholders before proceeding.

Example: "EU-only storage" (compliance) + "US DR" (availability) → "EU primary storage with encrypted replication to US DR region with key custody in EU" — satisfies both compliance and availability needs.

### Strategy 2: Defer

When resolution requires authority the current session doesn't have:

- Mark the conflicting requirements as `BLOCKED — pending stakeholder alignment`
- Document the conflict clearly so the decision-maker can resolve it
- Do NOT implement either requirement until the conflict is resolved
- Do NOT silently pick one without documenting the decision

### Strategy 3: Escalate

When the conflict cannot be resolved at the requirements level:

- Write an escalation brief: `<YYYY-MM-DD>_<slug>_conflict_escalation.md`
- Include: conflict map, resolution options considered, recommendation with rationale
- Present to the responsible authority (product owner, legal, CTO as appropriate)
- Block implementation of the conflicting requirements until a decision is returned

---

## Phase 2: Resolution Output

After resolution:

```markdown
## Resolution Record

### CONFLICT-001: [Short Name]
- **Resolution Strategy**: Negotiate / Defer / Escalate
- **Decision**: [What was decided]
- **Rationale**: [Why this resolution was chosen]
- **Unified Requirement**: [New REQ-xxx that replaces conflicting requirements, if negotiated]
- **Sign-off**: [Who approved this resolution — or "Pending" if deferred/escalated]
- **Impact on Implementation**: [What this means for the technical design]
```

Feed resolved requirements into `product-manager-expert` Mode A (Step 3 onward) or directly into the task queue.

---

## Hard Rules

1. **Never silently resolve.** Every conflict must be in the conflict map, even if trivially resolved.
2. **Never implement under a deferred conflict.** Mark as BLOCKED until sign-off.
3. **Never lower the bar for one stakeholder without explicit consent from the other.** "We'll handle the EU compliance later" is not a resolution — it's a deferral disguised as a decision.
4. **Document the loser.** If one requirement wins over another, record which requirement was set aside and why — it may resurface as a complaint later.
