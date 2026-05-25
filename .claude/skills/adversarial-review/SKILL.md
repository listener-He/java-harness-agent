---
name: "adversarial-review"
description: "Runs one-round adversarial critique. TRIGGER: HIGH-risk STANDARD — Explorer (Cat A), Propose/Review (Cat B/C). NOT FOR: code review (use code-reviewer); PATCH; >1 round per category."
---

# Adversarial Review

A bounded critique protocol. The adversary is not trying to veto — it is trying to find the one assumption that, if wrong, makes everything downstream wrong.

**Hard rule: ONE round per category per phase.** Each category fires at most once per lifecycle. Endless adversarial loops optimize for objection volume, not decision quality.

---

## Lifecycle Trigger Map

| Phase | Category | Risk threshold | Who triggers |
|---|---|---|---|
| Explorer (after Specification Inference) | **A — Requirements** | STANDARD, any risk | `requirement-engineer` |
| Propose / Review | **B — Design** | STANDARD, risk ≥ MEDIUM | `system-architect` |
| Special scenario start (Greenfield / Migration / EPIC) | **C — Scenario** | Any | Mounted role for that scenario |

**Do NOT trigger for:** PATCH/TRIVIAL tasks; after 1 round of the same category has already completed; when a human domain expert is actively reviewing.

---

## Category A — Requirements Adversarial Frames

> **Core question: Are we solving the right problem?**
> Trigger at: Explorer phase, after Specification Inference and before AC-as-Tests translation.
> The critic receives: the raw requirement / intake output / task_brief draft.

| Input Type | Adversarial Frame |
|---|---|
| **PRD (A1)** | "Assume 2 requirements in this PRD are mutually exclusive. Which pair, and what is the hidden conflict that makes both unachievable simultaneously?" |
| **Vague Idea (A2)** | "Assume the stated goal is a symptom of the real need, not the need itself. What problem is the user actually trying to solve, and does the proposed feature address it?" |
| **Bug Report (A3)** | "Assume this is not a bug but a misunderstood feature behaving as designed. From whose perspective is the current behavior correct, and what would change if we accepted that perspective?" |
| **Performance Complaint (A5)** | "Assume the proposed optimization eliminates the symptom but not the root cause. What systemic pressure remains, and when will it resurface?" |
| **Security Finding (A6)** | "Assume the vulnerable pattern exists in more places than the initial finding identified. Which other code paths share the same pattern and are currently unscanned?" |
| **Compliance / Regulatory (A8)** | "Assume our interpretation of the compliance requirement is the most convenient one rather than the most correct one. What stricter interpretation would a regulator or auditor apply, and does our AC still satisfy it?" |
| **Incident Action Item (A9)** | "Assume the identified root cause is a contributing factor, not the actual root cause. What deeper systemic condition made this incident possible, and would the proposed action item prevent the next incident?" |
| **Multi-stakeholder conflict (C5)** | "Assume one stakeholder's requirement, when fully implemented, makes another's impossible to fulfill. Which requirement pair, and which stakeholder's need is being implicitly deprioritized?" |

---

## Category B — Design Adversarial Frames

> **Core question: Are we solving it the right way?**
> Trigger at: Propose / Review phase, after `brainstorming` selects an option.
> The critic receives: the task_brief (selected design + constraint list).

| Proposal Type | Adversarial Frame |
|---|---|
| **New feature / API** | "Assume this feature will be misused by a legitimate user doing something reasonable. Find 2 ways the current design produces wrong results or silent failures." |
| **DB schema / migration** | "Assume data volume is 50× current estimates and one column's value distribution is extremely skewed. What breaks, degrades, or locks?" |
| **Bug fix** | "Assume this fix is correct for the reported case but introduces a regression. Which adjacent behavior is most likely broken, and why?" |
| **Refactoring** | "Assume there is an undocumented production dependency on the internal behavior being changed. Where would it hide, and how would you detect it?" |
| **Performance optimization** | "Assume the optimization improves the benchmark case but degrades under a different realistic load pattern. What pattern, and why?" |
| **Auth / permission change** | "Assume a privilege escalation is possible through this change via a sequence of valid API calls. Trace the path." |
| **Architecture decision** | "Assume the primary constraint driving this decision doubles in severity 12 months from now. Does the decision still hold, or does it become the most expensive technical debt in the system?" |

---

## Category C — Special Scenario Frames

> **Core question: What is the highest-risk assumption unique to this scenario type?**
> Trigger at: scenario workflow start, before any design work begins.
> The critic receives: the scenario description + requirement intake output.

| Scenario | Adversarial Frame |
|---|---|
| **Greenfield (C1)** | "Assume the domain model has a fundamental entity boundary error. Which boundary decision, if wrong, will require the most invasive refactoring 6 months from now, and why?" |
| **A→B Migration (C2)** | "Assume behavioral equivalence cannot be fully verified by automated tests. Which business-critical behavior is most likely to silently diverge between A and B, and how would a user first notice?" |
| **System Integration (C3)** | "Assume the external system's contract changes without notice after go-live. Which integration assumption is most fragile, and what is the blast radius?" |
| **Large-scale Refactoring (C4)** | "Assume one behavior that callers depend on is undocumented and will not appear in any test. Which class or method is most likely to harbor such a hidden contract?" |
| **EPIC decomposition (B5)** | "Assume the task decomposition has a hidden sequential dependency that makes parallel execution impossible. Which two tasks, and what shared state forces the ordering?" |

---

## Execution Protocol (All Categories)

### Step 1: Select exactly one frame

Pick the single frame that matches the **highest-risk dimension** of the artifact being reviewed.
If multiple frames apply: pick the one whose failure would be most irreversible.
Do not stack multiple frames in one round — that produces noise, not signal.

### Step 2: Spawn isolated critic

The critic receives:
1. The artifact (requirement / intake output / task_brief) — **verbatim, no paraphrase**
2. The selected frame — **as the mandatory lens, not a suggestion**
3. This instruction: *"Review this through the lens above. You have not seen the author's reasoning. Report findings only — no fixes. Classify each as CRITICAL or MINOR."*

The critic does NOT receive: the author's reasoning, session history, or any softening context.

### Step 3: Classify and terminate

```
CRITICAL: [finding] — [why this causes failure or irreversible harm]
MINOR:    [finding] — [why this is a risk worth noting but not blocking]
```

| Outcome | Action |
|---|---|
| No CRITICAL findings | Proceed. Address MINOR findings inline. Done. |
| CRITICAL finding present | STOP. Roll back to the current phase's start. Revise to address the finding. Do NOT run another adversarial round on the revised artifact — human reviewer takes over if concerns remain. |
| > 5 findings total | Critic is over-indexing. Keep top 2 by severity. Discard rest. |

**No second round within the same category.** Escalate to human if unresolved.

### Step 4: Author response (required)

```
CRITICAL [finding]: [how revised artifact addresses it] OR [why it does not apply — evidence]
MINOR    [finding]: [inline note in section X] OR [accepted risk — reason]
```

---

## Integration Points

| Phase | Action |
|---|---|
| **Explorer** | After Specification Inference (Step 3), before AC-as-Tests (Step 5): run Category A frame for the input type. CRITICAL → revise requirements interpretation; MINOR → note in `## Contradictions`. |
| **product-manager-expert Ingestion Mode** | After Step 2 (codebase validation), before Step 3 (AC translation): run Category A frame for PRD type. |
| **Propose** | After `brainstorming` selects option: run Category B frame. |
| **Review** | If self-reviewing (no separate human reviewer): run Category B frame instead of standard internal review. |
| **Special scenario start** | Greenfield / Migration / Integration / Refactoring / EPIC: run Category C frame before any design work. |
| **Approval Gate note** | If CRITICAL findings were found and addressed: add "Adversarial review (Category X) completed — CRITICAL findings addressed" to approval summary. |
