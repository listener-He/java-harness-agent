---
name: "cognitive-bias-checklist"
description: "Cognitive bias checklist for deep analysis and architectural design. Invoke this during Propose/Review phases to prevent hallucinations, overconfidence, and narrow thinking."
---

# Cognitive Bias Detection Checklist

> **Trigger:** Use this checklist during deep analysis tasks (L3/STANDARD/EPIC) when making architectural decisions, judgments, or evaluations.

## Usage Instructions
During your reasoning process, check if you have fallen into any of the following cognitive biases. If you identify one, explicitly note it in your output and correct your reasoning.

## 12 Common Cognitive Biases

### 1. Confirmation Bias
- **Symptom:** Tending to search for evidence that supports your existing views while ignoring contradictory evidence.
- **Self-Check:** Did I only list reasons supporting the recommended solution? Can I find at least 2 strong arguments against this approach?

### 2. Anchoring Effect
- **Symptom:** Relying too heavily on the first piece of information received (e.g., a specific technology or number mentioned casually by the user).
- **Self-Check:** Is my analysis overly influenced by a specific anchor? If I remove that initial suggestion, would my conclusion change?

### 3. Availability Bias
- **Symptom:** Overestimating the likelihood of events that are recent or highly memorable, rather than statistically probable ones.
- **Self-Check:** Is my judgment based on systematic analysis, or just on a memorable recent case/library?

### 4. Sunk Cost Fallacy
- **Symptom:** Reluctance to abandon a flawed path because time/resources have already been invested.
- **Self-Check:** If I were starting from scratch right now, would I still recommend this exact same approach?

### 5. Survivorship Bias
- **Symptom:** Focusing only on successful examples and ignoring failures.
- **Self-Check:** Did I only reference successful use cases? Have I researched cases where this architecture/library failed and why?

### 6. Planning Fallacy
- **Symptom:** Underestimating the time and resources needed, while overestimating the success rate.
- **Self-Check:** Is my complexity/time estimation too optimistic? Have I accounted for edge cases and integration overhead?

### 7. Bike-Shedding (Law of Triviality)
- **Symptom:** Spending excessive time on trivial details while ignoring the most critical problems.
- **Self-Check:** Am I spending too much time debating a minor detail? How much does this specific point actually impact the final system?

### 8. Dunning-Kruger Effect
- **Symptom:** Overconfidence in a domain where you have limited knowledge.
- **Self-Check:** Do I genuinely have enough context about this specific codebase/domain? Should I run more `SearchCodebase` queries before concluding?

### 9. Framing Effect
- **Symptom:** Drawing different conclusions based on how information is presented.
- **Self-Check:** Am I being influenced by the phrasing of the prompt? If the problem were framed differently, would my solution change?

### 10. Straw Man Fallacy
- **Symptom:** Misrepresenting the user's actual requirement to make it easier to solve.
- **Self-Check:** Did I accurately understand the user's core intent? Am I solving an "easier" problem rather than the actual one?

### 11. Bandwagon Effect
- **Symptom:** Choosing a solution just because it is the "popular" or "industry standard" choice, even if it doesn't fit the current context.
- **Self-Check:** Am I recommending this because it's genuinely the best fit for this specific project, or just because it's a buzzword?

### 12. Functional Fixedness
- **Symptom:** Thinking about things only in the way they are traditionally used, ignoring unconventional solutions.
- **Self-Check:** Have I only considered the standard CRUD approach? Are there alternative paradigms (e.g., event-driven, state machine) that fit better?

## Quick Self-Check Routine
Before finalizing a proposal, quickly ask yourself:
1. Did I list counter-arguments?
2. Is my judgment skewed by an anchor?
3. Did I look at failure modes?
4. Would I choose this if starting from scratch?
5. Did I add a 30-50% buffer to my complexity estimate?
6. Did I actually answer the user's real question?
