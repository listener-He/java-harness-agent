---
name: brainstorming
description: Turn an idea or requirement into a design with explicit alternatives, ADR-format decisions, and constraint propagation. TRIGGER at Propose phase entry for STANDARD tasks — this IS the Propose phase opener. Hands off to impl-plan once a design option is selected.
---

# Brainstorming — Design with Alternatives and Constraint Propagation

<HARD-GATE>
Do NOT write or modify implementation code until a design has been presented, alternatives documented, and approval received.
</HARD-GATE>

## Hard Compatibility Rules

- Use `.claude/runs/task-briefs/<YYYY-MM-DD>_<slug>_task_brief.md` as the output artifact.
- Keep all scope boundaries explicit (in-scope paths + out-of-scope paths).
- Every design session MUST produce at least 2 alternatives — a single-option "design" is a hidden decision.

---

## Protocol

### Step 1: Context — What Does the Codebase Currently Guarantee?
Before proposing anything:
- Read the relevant domain area (use Context Funnel budget).
- State explicitly: what patterns already exist? What constraints must be preserved?
- Identify the 1–2 architectural invariants that any design MUST respect.

### Step 2: Clarify (Minimal Questions)
Ask only the ONE question whose answer most changes the design space.
Not "what are all your requirements?" — but "is X a hard constraint or a preference?"
If the intake block exists, use its `Open-Questions` first before asking new ones.

### Step 3: Generate Alternatives (MUST — minimum 2)

For EACH option, use ADR format:

```
#### Option [A/B/C]: [Name]

**Approach:** [1–2 sentence description]

**Pros:**
- [concrete advantage]

**Cons / Risks:**
- [concrete disadvantage]

**Failure Condition:** If [assumption X] turns out false, this design breaks because [Y].
```

Explicitly mark ONE option as **Recommended** with a 1-sentence rationale.

### Step 4: Decision + Constraint Propagation

After the user selects (or you recommend) an option:

Emit a **Constraint List** — the implied constraints that ALL subsequent implementation decisions must respect:

```
## Constraint List (from selected design)
- [constraint 1]: [reason this is non-negotiable given the decision]
- [constraint 2]: ...
```

**Before handing off, self-check**: "Would a senior engineer say this design is overcomplicated?" If yes — cut a dimension and rewrite. Bias toward the simplest design that satisfies the ACs; speculative flexibility is the most common over-engineering trap.

This list flows into:
- The Task Brief `## Allowed Scope` (what files must change)
- The Task Brief `## Hard Constraints` (what must not change)
- The QA phase Evidence Mapping Table (each constraint → one test)

### Step 5: Task Brief Output

Present the selected design in task_brief format. Stop for approval before any implementation.

---

## Optional Visual Support

If the topic is inherently visual (UI, flow diagrams), add a Mermaid sequence or state diagram. Otherwise keep it text-first.
