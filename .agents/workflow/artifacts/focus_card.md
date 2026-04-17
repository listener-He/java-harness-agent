# Focus Card

## Goal
- Build and verify workflow hardening gates for agents process.
- Ensure PATCH/STANDARD can run deterministic checks and produce audit evidence.

## Non-Goals
- Do not modify business-domain application code.
- Do not rewrite wiki indexes directly.

## Allowed Scope
- .agents/
- AGENTS.md

## Budgets
- Wiki budget: 3 docs
- Code budget: 8 files
- Stop-Wiki: 3 no-gain reads
- Stop-Code: 2 non-converging reads

## Stop Rules
- If budgets are exhausted and success criteria are not met, stop and ask for clarification using an escalation card.
- If scope does not shrink after two code reads, stop and request missing anchors.

## Escalation Card (Template)
- Goal:
- Current blockers:
- What I tried (with evidence):
- What I need from human:
