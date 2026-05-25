---
name: "skill-graph-manager"
description: "Manage the bidirectional Skill Knowledge Graph. TRIGGER when a skill's purpose, trigger conditions, or lifecycle phase changes — NOT for minor description wording tweaks. Updates links and the central index. Ask user before adding bidirectional links."
---

# Skill Graph Manager

**Focus**: bidirectional linking, skill indexing, and consistent cross-skill navigation.

This skill acts as the automated librarian for the workspace. It ensures that all skills are interconnected in a Knowledge Graph, allowing the LLM to naturally associate related skills (e.g., jumping from `devops-task-planning` to `prd-task-splitter` automatically).

## Trigger Condition (Strict)
- You MUST invoke this skill **every time** a new skill is created or an existing skill's core purpose is modified.
- Do not silently update skills without updating the graph.

---

## The 4-Step Real-Time Correction Mechanism

### Step 1: Analyze the New/Modified Skill
**Action**: Read the new or modified `SKILL.md`. Understand its boundaries, focus, and target audience.

### Step 2: Propose Bidirectional Links
**Action**: Consult the central index (`skill-index/SKILL.md`). Identify 2-5 existing skills that are logically related (e.g., predecessor, successor, sibling, or standard constraints).
- Generate a proposal of which skills should link to the new skill, and which skills the new skill should link to.

### Step 3: Prompt the User for Approval
**Action**: **STOP AND ASK**. Use the `AskUserQuestion` tool or text response to present the proposed links to the user.
> **Example Prompt**:
> "I've detected a change to skill `X`. To maintain the Knowledge Graph, I propose adding bidirectional links between `X` and `[Y, Z]`. 
> Options:
> 1. Approve all proposed links.
> 2. Add/Remove specific links (please specify).
> 3. Skip graph update this time."

### Step 4: Execute the Graph Update
**Action**: Once the user approves:
1. **Update the Target Skill**: Append or update the `## Related Skills` section at the bottom of the new/modified `SKILL.md`.
2. **Update the Related Skills**: Inject the reverse link into the `## Related Skills` section of the related existing skills.
3. **Update the Central Index**: Update `skill-index/SKILL.md` to reflect the new graph topology.

---

## Link Format Standard
Whenever you write a bidirectional link inside a `SKILL.md`, you MUST use this exact Markdown format:

```markdown
## Related Skills
- [<related-skill-1>](../<related-skill-1>/SKILL.md): <Brief explanation of why they are related, e.g., "The predecessor skill for requirements">
- [<related-skill-2>](../<related-skill-2>/SKILL.md): <Brief explanation, e.g., "Provides the coding standards required by this skill">
```

## Related Skills

- [skill-author](../skill-author/SKILL.md): Upstream — `skill-author` Step 7 delegates "register in central index + maintain bidirectional links" to this skill.
- [authoring-standards](../authoring-standards/SKILL.md): Upstream — after drafting an artifact, `authoring-standards` hands off registration to this skill.
- [skill-index](../skill-index/SKILL.md): Maintenance target — every write this skill performs lands in that index file.
