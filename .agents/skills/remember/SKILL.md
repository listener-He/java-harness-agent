---
name: remember
description: Review reusable project knowledge and decide what belongs in project memory, notepad, or durable docs. Use when the user wants to preserve or organize useful knowledge discovered during a session.
---

# Remember

## What This Does

Use this skill when the user wants to preserve or organize useful knowledge discovered during a session. The goal is to promote durable, reusable information into the correct long-lived surface instead of letting it sink into chat history.

## When to Use

- User says "remember this", "save this", "note this", "don't forget"
- You identified project knowledge worth persisting (architecture, conventions, stable workflows)
- You need to clean up duplicates or contradictions in existing memory/doc surfaces
- You want to upgrade a short-term note into durable knowledge

## When NOT to Use

- The information is speculative, unverified, or likely to change soon
- The content belongs in source-of-truth docs/config (update the file instead of memory)
- The user is asking for a plan/progress tracking (use task artifacts, not memory)

## Protocol

1. Collect the candidate facts/preferences/methods from the recent conversation
2. Classify each item into one destination:
   - Project memory: durable team/project facts and conventions
   - Short-term note surface: high-signal context for the next few turns
   - Session notes: temporary working notes
   - Durable docs/config files: instructions that belong in the repo itself
3. For each item, propose the best destination and a short title + keywords
4. Write or update only the appropriate surface (do not dump everything into one place)
5. Call out duplicates, conflicts, or outdated entries that should be removed

## Rules

- Prefer project memory for durable team/project knowledge
- Prefer short-term notes for near-term working context
- Keep entries concise and action-oriented
- If uncertain, mark as uncertain instead of storing as fact

## Output Format

- What was saved
- Where it was saved
- Duplicates/conflicts detected (if any)
