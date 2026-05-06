---
name: skill-creator
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment. Guides the full skill creation lifecycle with TDD-inspired validation.
---

# Skill Creator

## What This Does

Create or update a reusable skill (`SKILL.md`) in a way that improves model routing and stays compatible with this repo’s workflow and gates.

## When to Use

- User asks to create or add a skill
- You identify a repeatable workflow that should be standardized
- You need to improve an existing skill’s clarity, triggers, or protocol

## When NOT to Use

- One-off tasks that do not benefit from reuse
- Project rules/policies (use repo rules/docs instead of a skill)

## Protocol

### Step 1: Validate the Need

Create/modify a skill only if:
- The workflow is repeatable (you expect it to recur)
- It is repository-specific or hard to infer without local context
- The trigger conditions can be stated unambiguously

### Step 2: Choose the Skill Type

| Type | Meaning | Example |
|---|---|---|
| Procedural | Step-by-step executable workflow | Root-cause tracing |
| Cognitive | Thinking protocol / decision gates | Bias checks, decision matrix |
| Reference | Repo-specific standards and constraints | SQL or Java standards |

### Step 3: Write `SKILL.md`

Every skill MUST include YAML frontmatter:

```yaml
---
name: skill-name-with-hyphens
description: Use when [clear trigger conditions + what it does]
---
```

Frontmatter rules:
- `name` uses lowercase letters, numbers, and hyphens only
- `description` is English, ≤ 200 chars, and includes both:
  - what it does
  - when to invoke (trigger conditions)
- Do NOT summarize the whole workflow in `description`

Body structure (recommended):

```markdown
# Skill Title

## What This Does
1–2 sentences describing the core outcome.

## When to Use
- Trigger conditions

## When NOT to Use
- Non-trigger conditions

## Protocol
Step-by-step instructions.

## Examples (Optional)
Input/output examples.
```

### Step 4: Quality Checklist

- [ ] `name` uses only letters, numbers, hyphens
- [ ] `description` starts with “Use when…”
- [ ] `description` includes triggers and avoids step-by-step summaries
- [ ] Protocol is actionable and bounded
- [ ] Includes relevant trigger keywords (errors, symptoms, tools)

### Step 5: Validate the Skill

Test with one typical scenario:
1. Create a prompt that should trigger the skill
2. Follow the protocol
3. Confirm outputs match intent
4. If not, revise and re-test

### Step 6: Save and Register

Save to:
- Project skills: `.agents/skills/<skill-name>/SKILL.md`

After saving:
1. Update the central index: `.agents/skills/trae-skill-index/SKILL.md`
2. Run the index gate: `skill_index_linter.py` (missing links must be fixed)
3. Use `skill-graph-manager` to maintain bidirectional related-skill links (requires user approval)

## Common Mistakes

| Mistake | Fix |
|------|------|
| Description summarizes workflow | Keep it trigger-based and short |
| Too generic | Focus on repo-specific patterns |
| Too specific | Extract reusable principles |
| Missing triggers | Add concrete trigger keywords and symptoms |
| Invalid name | Use only letters, numbers, hyphens |

## Examples

**Good skill:**
```yaml
---
name: async-race-condition-debugging
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently across runs
---
```

**Bad skill:**
```yaml
---
name: debugging
description: Use when you need to debug code by reading errors, reproducing issues, and fixing root causes
---
```
This is too generic because it describes a workflow rather than crisp triggers.
