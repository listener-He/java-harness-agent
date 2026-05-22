---
name: "spec-quality-checklist"
description: "Self-correction gate for AI-generated documents (task_brief, WAL fragments, specs). TRIGGER manually after drafting any task_brief, spec, or WAL fragment — run before submitting to user or executing Python gate scripts. Verifies structural clarity, actionable language, and absence of narrative or vague content."
---

# Spec & Output Quality Checklist

> **Trigger:** Use this checklist to self-correct your outputs (Specs, Reports, Proposals) BEFORE submitting them to the user or triggering python validation gates.

## Universal Checks (All Outputs)
- [ ] **Direction Accuracy:** Did I answer the user's actual underlying question?
- [ ] **Actionability:** Are the next steps explicitly clear?
- [ ] **Edge Cases:** Have I accounted for boundary conditions and common failure modes?
- [ ] **Structural Clarity:** Is the output logically organized with headers, bullet points, and code blocks?
- [ ] **Conciseness:** Is there any fluff or redundant AI preamble that can be removed?
- [ ] **Consistency:** Are terms, variable names, and architectural decisions consistent throughout the text?

## Documentation & Specs (`<YYYY-MM-DD>_<slug>_task_brief.md`)
- [ ] **Clear Title:** Does the document clearly state its purpose?
- [ ] **Executive Summary:** Is there a 2-3 sentence TL;DR at the top mapping back to the Acceptance Criteria (AC)?
- [ ] **Logical Flow:** Do the sections connect logically (e.g., Context -> Architecture -> Data Model -> API)?
- [ ] **Evidence-Backed:** Are architectural choices backed by specific project constraints or requirements?
- [ ] **Formatting:** Are Markdown tables, bold text, and code snippets used correctly?
- [ ] **Action Items:** Does the spec end with a clear transition to the `Implement` phase?

## Analytical Reports (Inline `[Explore]` Block / Root Cause)
- [ ] **Source Attribution:** Are file paths and log snippets clearly referenced?
- [ ] **Methodology:** Did I explain *how* I arrived at this conclusion?
- [ ] **Fact vs. Assumption:** Are my hypotheses clearly distinguished from verified facts?
- [ ] **Limitations:** Did I state what I *don't* know or couldn't verify?

## Proposals & Architecture Design
- [ ] **Problem Definition:** Is the core problem stated in one sentence?
- [ ] **Alternatives:** Were at least 2 alternative approaches considered before making the recommendation?
- [ ] **Justification:** Is the chosen approach defended convincingly (e.g., using Cost-Benefit or SWOT)?
- [ ] **Blast Radius:** Have I explicitly documented the impact on existing systems?
- [ ] **Rollback Plan:** Is there a clear way to revert this change if it fails?

## Requirements & Acceptance Criteria (Semantic Quality)
- [ ] **Single Behavior:** Does each requirement unit describe exactly ONE testable behavior? (Split if it contains "and" with two distinct outcomes)
- [ ] **No Vague Language:** Are words like "correctly", "properly", "handle", "work well", "support" absent? Each AC must name a specific observable output.
- [ ] **Executable:** Can each AC be written directly as a test assertion? (`assertEquals(...)`, `assertThrows(...)`, HTTP status code, exact field value)
- [ ] **Falsifiable:** Is there a condition under which the AC would definitively FAIL? (If no failure condition exists, the AC is not testable)
- [ ] **Conflict-Free:** Do any two ACs contradict each other or contradict existing documented behavior?
- [ ] **Complete:** Does each AC cover at least: (1) happy path, (2) one error/edge case?
