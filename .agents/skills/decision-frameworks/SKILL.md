---
name: "decision-frameworks"
description: "Decision frameworks (SWOT, 5-Why, Decision Matrix) for root cause analysis, architecture selection, and complex problem solving. Invoke during EPIC or DEBUG scenarios."
---

# Decision Frameworks Cheat Sheet

> **Trigger:** Use these frameworks during deep analysis (L3/EPIC/DEBUG) when comparing multiple solutions or conducting root-cause analysis.

## Framework Selection Guide

| Scenario | Recommended Framework | Condition |
|---|---|---|
| Strategic Direction | **SWOT Analysis** | Needs internal/external multi-dimensional evaluation |
| Quantitative Comparison | **Decision Matrix** | 3+ options with quantifiable dimensions |
| ROI Evaluation | **Cost-Benefit Analysis** | Needs to measure economic/time input vs. return |
| Prioritization | **Impact-Effort Matrix** | Multiple tasks/features need ordering |
| Risk Assessment | **Risk Matrix** | Needs to identify and evaluate potential risks |
| Root Cause Analysis | **5-Why Analysis** | Needs to find the fundamental cause of a bug/issue |
| Global Perspective | **First Principles** | Needs to break out of existing paradigms |

---

## 1. SWOT Analysis
**Usage:**
1. List 3-5 Strengths (S) and Weaknesses (W) [Internal].
2. List 3-5 Opportunities (O) and Threats (T) [External].
3. Cross-analyze to form strategies (e.g., Use Strengths to seize Opportunities).

## 2. Decision Matrix
**Usage:**
1. Define 3-5 key evaluation dimensions (e.g., Performance, Maintainability, Cost).
2. Assign weights to each dimension (Total = 100%).
3. Score each option (1-5 scale) across dimensions.
4. Calculate the weighted total to find the objective winner.

## 3. Cost-Benefit Analysis
**Usage:**
1. List all Direct, Indirect, and Opportunity Costs.
2. List all Direct and Indirect Benefits.
3. Quantify them (use numbers or High/Medium/Low).
4. Calculate Net ROI and payback period.

## 4. Impact-Effort Matrix
**Usage:**
Plot tasks on a 2x2 grid based on Impact (High/Low) and Effort (High/Low).
- **High Impact, Low Effort:** Quick Wins (Do First)
- **High Impact, High Effort:** Major Projects (Plan)
- **Low Impact, Low Effort:** Fill-ins (Delegate/Drop)
- **Low Impact, High Effort:** Thankless Tasks (Avoid)

## 5. Risk Matrix
**Usage:**
Plot risks on a 2x2 grid based on Probability (High/Low) and Impact (High/Low).
Formulate mitigation strategies specifically for High Probability + High Impact risks.

## 6. 5-Why Analysis
**Usage:**
1. State the surface-level problem (e.g., "The server crashed").
2. Ask "Why?" up to 5 times to drill down through direct, deep, and systemic causes.
3. The final answer is the Root Cause. Formulate a fix for the Root Cause, not the symptom.

## 7. First Principles Thinking
**Usage:**
1. **Identify Assumptions:** List all "taken for granted" assumptions about the current architecture.
2. **Challenge Assumptions:** Are they strictly necessary?
3. **Deconstruct:** What are the absolute fundamental truths or constraints of this problem?
4. **Reconstruct:** Build a new solution from scratch using only the fundamental truths.
