---
name: external-research
description: "Large-scale external research for breaking through optimization bottlenecks. Searches GitHub, arXiv, technical blogs, and forums for reference implementations, algorithms, and inspiration. Deeply analyzes findings and injects actionable ideas into the improvement pipeline. TRIGGER when: the AI pipeline detects a score plateau (no improvement for 5+ cycles), user says \"research externally\", \"break the bottleneck\", \"find new approaches\", or asks to search for reference implementations or literature. DO NOT TRIGGER when: the pipeline is making steady progress, or the user just wants a quick web search."
---

# External Research — Breaking Bottlenecks with Outside Knowledge

When internal codebase analysis and iterative improvement have exhausted their potential, this skill searches the broader world for new ideas. It is the pipeline's way of saying: "We're stuck — let's see what others have figured out."

## When to Use

- The AI pipeline has plateaued (score not improving for 5+ cycles)
- User explicitly requests external research ("research externally", "break the bottleneck", "find new approaches")
- User asks to search for reference implementations or literature on a specific problem
- Self-improve's internal researcher has run out of novel ideas within the codebase

**Do NOT use** when:
- The pipeline is making steady progress — internal iteration is sufficient
- The user just wants a quick web search (use WebSearch directly)
- The task is simple enough that external research would be overkill

## Input

| Field | Required | Description |
|---|---|---|
| `objective` | Yes | The original improvement goal |
| `current_score` | Yes | Current benchmark score |
| `target_score` | Yes | Target score (acceptance criteria) |
| `score_gap` | Yes | Difference between current and target |
| `approaches_tried` | Yes | List of approach families and specific hypotheses already attempted, with outcomes |
| `adrs` | Yes | List of ADR files recording prior architectural decisions |
| `codebase_summary` | Yes | Brief description of the codebase, tech stack, and architecture |
| `idea_output_path` | Yes | Path to write the output ideas file (typically `<self-improve-root>/config/idea.md`) |
| `iteration_history_path` | No | Path to full iteration history for deeper analysis |

## Output

Write to `idea_output_path` a structured list of actionable ideas, each containing:

```markdown
## External Research Ideas

### Research Context
- Objective: {objective}
- Current score: {current_score} / Target: {target_score} (gap: {score_gap})
- Approaches exhausted: {list of approach families tried}
- Research date: {date}

---

### Idea 1: {Short Title}

**Source**: {URL or paper citation}
**Approach family**: {architecture|optimization|data|infrastructure|training_config|testing|other}
**Specific technique**: {concrete description of what to do}
**Why it might work**: {reasoning based on the source evidence}
**Estimated impact**: {quantified estimate, e.g., "5-10% improvement"}
**How it differs from prior attempts**: {explicitly state what's new vs what was already tried}
**Trade-offs**: {what we gain vs what we lose}
**ADR conflicts**: {any prior ADR decisions this conflicts with, or "none"}

### Idea 2: {Short Title}
...
```

## Instructions

### Step 1: Analyze the Bottleneck

Before searching externally, deeply understand WHY the pipeline is stuck:

1. Read the iteration history: what approach families have been tried? What were the outcomes?
2. Read the ADRs: what decisions were made and why? Are any of them now suspect?
3. Identify the specific bottleneck: is it algorithmic? architectural? data-related? infrastructure?
4. Formulate the core question: "What technique could {specific improvement} given {specific constraint}?"

This analysis directly informs search queries — vague queries yield vague results.

### Step 2: Search GitHub

Search for reference implementations and alternative architectures:

1. **Repository search**: Find repos that solve the same or similar problems
   - Search queries: combine the problem domain with keywords like "optimization", "high-performance", "alternative", "benchmark"
   - For each promising repo: read README, check star count and recent activity, examine architecture
2. **Code search**: Find specific implementation patterns
   - Search for the specific algorithm, data structure, or pattern that could break the bottleneck
3. **Issue/Discussion search**: Find known solutions to the specific problem
   - Search issues for keywords related to the bottleneck

**For each finding**, extract:
- What approach they use
- Why it works (from their docs/benchmarks)
- Key code patterns or architectural decisions
- Applicability to our codebase

### Step 3: Search arXiv

Search for recent academic research:

1. **Paper search**: Find papers on the specific optimization problem
   - Focus on: optimization algorithms, architecture patterns, evaluation methodologies
   - Prioritize recent papers (last 2 years) for state-of-the-art techniques
2. **Extract practical insights**: Academic papers often contain theoretical insights that can be translated into practical improvements
   - Look for: algorithmic improvements, provably better approaches, new evaluation metrics
3. **Assess practicality**: Filter out purely theoretical work that cannot be implemented within the project's constraints

**For each finding**, extract:
- Core technique and why it's theoretically better
- Practical implementation considerations
- Expected magnitude of improvement
- Required changes to current architecture

### Step 4: Search Technical Blogs & Documentation

Search for engineering experience and best practices:

1. **Engineering blogs**: Company engineering blogs often share real-world optimization stories
   - Search for: performance optimization case studies, architecture migration stories
2. **Official documentation**: Framework/tool docs may reveal features not yet utilized
   - Check for: configuration options, performance tuning guides, lesser-known features
3. **Performance tuning guides**: Platform-specific optimization advice
   - Look for: language-specific optimizations, runtime tuning, compiler flags

### Step 5: Search Forums & Communities

Search for practitioner solutions:

1. **Stack Overflow**: Specific technical Q&A
2. **Reddit/Discord communities**: Broader discussion and experience sharing
3. **GitHub Discussions**: Project-specific optimization advice

### Step 6: Deep Analysis & Filtering

Synthesize all findings into actionable ideas:

1. **Cross-reference with prior attempts**: Every idea must explicitly state how it differs from what was already tried. Ideas that merely repeat failed approaches must explain why the outcome might be different this time.

2. **Cross-reference with ADRs**: Check each idea against existing architectural decisions:
   - If an idea conflicts with an ADR: note the conflict, explain why revisiting the decision might be warranted
   - If an idea aligns with an ADR: note the reinforcement

3. **Feasibility assessment**: For each idea, assess:
   - Can it be implemented within the current codebase structure?
   - Does it require new dependencies? (prefer ideas that don't)
   - What is the estimated implementation complexity?
   - What is the risk of regression?

4. **Impact estimation**: Rank ideas by estimated impact (high/medium/low confidence)

5. **Diversity check**: Ensure ideas span at least 3 different approach families. If all ideas are in the same family, search more broadly.

### Step 7: Write Output

Write the structured ideas to `idea_output_path` following the output format above.

**Quality requirements**:
- Minimum 3 ideas, maximum 10
- Every idea must have a specific, citable source
- Every idea must explain how it differs from prior attempts
- Ideas sorted by: confidence × estimated impact (highest first)
- At least 2 different approach families represented

### Step 8: Report

Present a summary to the user:

```
=== External Research Complete ===

Bottleneck analysis: {why we're stuck}
Sources searched: GitHub ({N} repos), arXiv ({N} papers), Blogs ({N} posts), Forums ({N} threads)

Ideas generated: {count}
- High confidence: {count}
- Medium confidence: {count}
- Low confidence: {count}

Approach families covered: {list}

Top 3 ideas:
1. {title} ({approach_family}, {estimated_impact})
2. {title} ({approach_family}, {estimated_impact})
3. {title} ({approach_family}, {estimated_impact})

Ideas written to: {idea_output_path}
```

## Hard Constraints

These constraints are **absolute** and must NOT be relaxed regardless of what external research finds:

1. **Original goal objective** — do not lower the bar or redefine "done"
2. **Acceptance criteria (target score)** — do not adjust the target downward
3. **Evaluation benchmark** — do not weaken the test suite or change grading criteria
4. **Regression thresholds** — do not allow more regression

New ideas must achieve the **SAME target with DIFFERENT means**, not a different (easier) target. If external research suggests the target is unrealistic, report this to the user but do NOT unilaterally lower it.

## Failure Strategy

| Situation | Action |
|---|---|
| No relevant findings on GitHub | Expand search terms, try adjacent domains, continue to arXiv |
| No relevant papers on arXiv | Try different keyword combinations, search citation graphs |
| All findings are impractical | Report honestly — sometimes the bottleneck is fundamental. Suggest whether the user should reconsider the target. |
| Findings conflict with hard constraints | Discard the finding. Do NOT suggest relaxing constraints. |
| Search returns too many results | Narrow queries with more specific terms, filter by recency and relevance |
| Cannot access a source | Note the source, try alternative access (cache, mirrors), do not skip without trying |

## Pipeline Integration

This skill is a **conditional phase** in the AI pipeline loop. It sits between cycles as Phase 6 (conditionally triggered):

```
Phase 5 (ai-slop-cleaner)
     │
     ▼
Acceptance Check ─── Goal met? ──→ Deliver & Exit
     │
     │ NO
     ▼
Bottleneck Check ─── Score plateaued 5+ cycles? ──→ Phase 6: external-research
     │                                                    │
     │ NO                                                 ▼
     │                                              Re-enter loop
     ▼                                             (Phase 4 or Phase 1)
Re-enter loop (Phase 4)
```

After external-research completes, the pipeline re-enters at:
- **Phase 4 (self-improve)** if the new ideas are incremental improvements within the current architecture
- **Phase 1 (blueprint)** if the findings suggest a fundamentally different approach requiring re-planning

This skill can also be used **standalone** outside the pipeline when the user wants targeted external research on a specific problem.