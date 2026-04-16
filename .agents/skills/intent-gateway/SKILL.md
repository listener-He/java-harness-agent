---
name: "intent-gateway"
description: "Routes a request into a minimal top-level intent + execution profile, then optionally launches a lifecycle queue."
---

# Intent Gateway Skill

This document is a thin wrapper.

This is the central router. Use it at the start of any new request unless the user explicitly provides a shortcut (see below).

---

## Trigger Condition
- Any new feature work, refactor work, or bugfix SHOULD start here.

## Shortcuts (Explicit > Automatic)
Routing and shortcuts are defined in one place:
- SSOT: `.agents/router/ROUTER.md`

## Execution Protocol
The gateway MUST execute the following in order:
1. Apply explicit shortcut DSL if present (SSOT: `.agents/router/ROUTER.md`).
2. Otherwise, route automatically using the rules in `.agents/router/ROUTER.md`.
3. Collect context using `.agents/router/CONTEXT_FUNNEL.md`.
4. If the selected profile is `STANDARD`, launch via `.agents/router/ROUTER.md` launch spec rules.

## Handoff
- If launched: tell the user which profile and which lifecycle phase you are entering.
- If not launched: deliver the answer/report with citations and stop.
