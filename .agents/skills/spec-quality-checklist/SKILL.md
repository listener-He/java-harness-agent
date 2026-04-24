---
name: "spec-quality-checklist"
description: "Flexible quality gate checklist for AI self-correction. Invoke before finalizing documentation, analysis, or specs to ensure structural clarity and actionable outputs."
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

## Documentation & Specs (`openspec.md`)
- [ ] **Clear Title:** Does the document clearly state its purpose?
- [ ] **Executive Summary:** Is there a 2-3 sentence TL;DR at the top mapping back to the Acceptance Criteria (AC)?
- [ ] **Logical Flow:** Do the sections connect logically (e.g., Context -> Architecture -> Data Model -> API)?
- [ ] **Evidence-Backed:** Are architectural choices backed by specific project constraints or requirements?
- [ ] **Formatting:** Are Markdown tables, bold text, and code snippets used correctly?
- [ ] **Action Items:** Does the spec end with a clear transition to the `Implement` phase?

## Analytical Reports (`explore_report.md` / Root Cause)
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
