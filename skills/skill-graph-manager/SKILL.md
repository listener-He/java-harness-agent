---
name: "skill-graph-manager"
description: "MANDATORY mechanism for managing the bidirectional Skill Knowledge Graph. Invoke IMMEDIATELY after creating or modifying ANY skill to update links and the central index."
---

# Skill Graph Manager (技能图谱管理器)

**Focus**: Bidirectional Linking (双向链接), Skill Indexing (技能索引维护), Context Association (大模型上下文联想).

This skill acts as the automated librarian for the workspace. It ensures that all skills are interconnected in a Knowledge Graph, allowing the LLM to naturally associate related skills (e.g., jumping from `devops-task-planning` to `prd-task-splitter` automatically).

## 🛡️ TRIGGER CONDITION (触发机制) - STRICTLY ENFORCED
- You MUST invoke this skill **every time** a new skill is created or an existing skill's core purpose is modified.
- Do not silently update skills without updating the graph.

---

## 📋 The 4-Step Real-Time Correction Mechanism (实时修正机制)

### Step 1: Analyze the New/Modified Skill (分析变更)
**Action**: Read the new or modified `SKILL.md`. Understand its boundaries, focus, and target audience.

### Step 2: Propose Bidirectional Links (提议双向链接)
**Action**: Consult the central index (`trae-skill-index/SKILL.md`). Identify 2-5 existing skills that are logically related (e.g., predecessor, successor, sibling, or standard constraints).
- Generate a proposal of which skills should link to the new skill, and which skills the new skill should link to.

### Step 3: Prompt the User for Approval (提示用户并提供选项)
**Action**: **STOP AND ASK**. Use the `AskUserQuestion` tool or text response to present the proposed links to the user.
> **Example Prompt**:
> "I've detected a change to skill `X`. To maintain the Knowledge Graph, I propose adding bidirectional links between `X` and `[Y, Z]`. 
> Options:
> 1. Approve all proposed links.
> 2. Add/Remove specific links (please specify).
> 3. Skip graph update this time."

### Step 4: Execute the Graph Update (执行图谱更新)
**Action**: Once the user approves:
1. **Update the Target Skill**: Append or update the `## 🔗 关联技能 (Related Skills)` section at the bottom of the new/modified `SKILL.md`.
2. **Update the Related Skills**: Inject the reverse link into the `## 🔗 关联技能 (Related Skills)` section of the related existing skills.
3. **Update the Central Index**: Update `trae-skill-index/SKILL.md` to reflect the new graph topology.

---

## 🔗 Link Format Standard (链接格式规范)
Whenever you write a bidirectional link inside a `SKILL.md`, you MUST use this exact Markdown format:

```markdown
## 🔗 关联技能 (Related Skills)
- [skill-a](../skill-a/SKILL.md): <Brief explanation of why they are related, e.g., "The predecessor skill for requirements">
- [skill-b](../skill-b/SKILL.md): <Brief explanation, e.g., "Provides the coding standards required by this skill">
```
