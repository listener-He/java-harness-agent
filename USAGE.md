# Usage Guide — Load Rules in Your CLI/IDE and Run a Full Loop (EN)

> This guide is for first-timers who want their coding agent to behave like a disciplined teammate: not a chaotic intern.  
> Goal: make it easy to load this repo’s rules in multiple tools (CLI + IDE), then use the same end-to-end loop to deliver work: **requirements → design → implementation → tests → archive**.

---

## TL;DR

1. Copy these into your project root:
   - `.agents/` (workflow engine, skills, wiki, gates)
   - `AGENTS.md` (the “README for agents”)
2. Make your tool *actually load* `AGENTS.md`:
   - Some tools load it natively (Codex, Cursor, Windsurf, Qoder, etc.)
   - Some tools expect a different file name (`GEMINI.md`, `CLAUDE.md`, `.github/copilot-instructions.md`) — use an adapter file, a symlink, or a settings toggle
3. Start working:
   - You can speak normally — the agent can infer whether this is “explain only / quick fix / full delivery loop”
   - `@learn` / `@patch` / `@standard` exist as shortcuts, **not requirements**

---

## 1. What is this repo?

Think of it as **seatbelts + a repeatable workflow** for coding agents.

- Seatbelts: prevent random edits, scope creep, infinite retries, and token burn
- Workflow: guide an agent through a predictable loop that ends with proof (tests) and traceability (archive/logs)

---

## 2. One set of rules, many tools

Different products call it “rules”, “instructions”, “context files”, or “project guidance”, but they all do the same thing: **inject a stable instruction layer into every session**.

This repo uses `AGENTS.md` as the cross-tool standard. Ecosystem reference: <https://agents.md/>.

### 2.1 Recommended: single source of truth

Keep `AGENTS.md` as the single source of truth. When a tool expects a different filename, *point to it* instead of duplicating content:

- Option A: symlink (best on macOS/Linux)
- Option B: copy the file (most reliable on Windows / restricted environments)
- Option C: change the tool’s “context file name” setting (when supported)

Windows symlink note (often requires admin or Developer Mode):
```powershell
New-Item -ItemType SymbolicLink -Path CLAUDE.md -Target AGENTS.md
```

---

## 3. How to load rules in each CLI / IDE (multiple options)

Each section includes 2–4 ways. Pick what fits your environment.

### 3.1 Trae (IDE)

Trae supports **User Rules** and **Project Rules**, stored under `.trae/rules/`. Official docs: <https://docs.trae.ai/ide/rules?_lang=en>.

Recommended (team-friendly):
1. Create a Project Rule in Trae (it creates `.trae/rules/<name>.md`)
2. Put your minimum non-negotiables there (tests, scope boundaries, etc.)
3. Keep `AGENTS.md` as the repo-level canonical rules file (cross-tool compatible)

Optional (less config):
- If your Trae version already recognizes root `AGENTS.md`, you can skip `.trae/rules/`. For teams, a small “Always Apply” Trae rule is still useful as a guardrail.

### 3.2 Cursor (IDE)

Cursor supports `.cursor/rules/*` and also supports `AGENTS.md`. Official docs: <https://cursor.com/docs/rules>.

Option A (simplest): keep only `AGENTS.md` in the project root  
Option B (more control): add `.cursor/rules/*.mdc` for scoped rules (by globs / manual / always-apply)

### 3.3 Codex CLI (Terminal)

Codex discovers instructions in a directory chain and prioritizes `AGENTS.override.md` over `AGENTS.md`. Official docs: <https://developers.openai.com/codex/guides/agents-md>.

Option A (recommended): put `AGENTS.md` in the repo root  
Option B (local temporary override): use `AGENTS.override.md` (don’t commit it)  
Option C (rename support): configure fallback filenames in Codex settings  

### 3.4 Claude Code (Terminal / VS Code / JetBrains)

Claude Code officially reads `CLAUDE.md` from the project root. Official docs: <https://code.claude.com/docs/en/overview>.

To keep `AGENTS.md` as the single truth source, pick one:

Option A (symlink, macOS/Linux):
```bash
ln -s AGENTS.md CLAUDE.md
```

Option B (copy, most reliable):
```bash
cp AGENTS.md CLAUDE.md
```

Option C (minimal adapter file):
Create `CLAUDE.md` with a short note:
- “Primary rules live in AGENTS.md”
- “Read AGENTS.md first and follow its workflow/budgets/gates”

### 3.5 Gemini CLI (Terminal)

Gemini CLI uses hierarchical `GEMINI.md` context files and supports changing the context filename via `settings.json`. It also supports importing other markdown files with `@path/to/file.md`.

Official docs:
- GEMINI.md context system: <https://geminicli.com/docs/cli/gemini-md/>
- settings.json / context.fileName: <https://geminicli.com/docs/reference/configuration/>

Option A (recommended): configure it to look for `AGENTS.md` first
Create `.gemini/settings.json` in your project root:
```json
{
  "context": {
    "fileName": ["AGENTS.md", "GEMINI.md"]
  }
}
```

Option B: keep `GEMINI.md` but avoid duplication via import
```md
# Project instructions

@./AGENTS.md
```

Option C (symlink):
```bash
ln -s AGENTS.md GEMINI.md
```

### 3.6 Windsurf / Cascade (IDE)

Windsurf supports `AGENTS.md` (or `agents.md`) and automatically scopes instructions based on file location (root = always-on, subdirs = directory-scoped). Official docs: <https://docs.windsurf.com/windsurf/cascade/agents-md>.

Option A (recommended): root `AGENTS.md`  
Option B (advanced): add nested `AGENTS.md` for module-specific rules  

### 3.7 GitHub Copilot (IDE / Copilot CLI / Cloud Agent)

Copilot supports:
- `.github/copilot-instructions.md` (repo-wide)
- `.github/instructions/*.instructions.md` (path-scoped)
- `AGENTS.md` (agent instructions, nearest file in the directory tree)

Official docs:
- Repo instructions: <https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot>
- Copilot CLI instructions: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>

Recommended (best compatibility):
1. Keep root `AGENTS.md`
2. Add `.github/copilot-instructions.md` that points to it (one sentence is enough)

### 3.8 Qoder (IDE / CLI)

Qoder rules live under `.qoder/rules`, and its docs explicitly state **AGENTS.md compatibility**. Official docs: <https://docs.qoder.com/user-guide/rules>.

Option A (recommended): keep root `AGENTS.md` (Qoder will recognize it)  
Option B (stronger enforcement): also add “Always Apply” rules under `.qoder/rules`  

### 3.9 CodeBuddy Code (CLI)

CodeBuddy can be customized via:
- project/user Sub-Agent files under `.codebuddy/agents/*.md` (YAML frontmatter) — docs: <https://www.codebuddy.ai/docs/cli/sub-agents>
- CLI system-prompt parameters (including `--system-prompt-file`) — docs: <https://www.codebuddy.ai/docs/cli/cli-reference>

Two stable options:

Option A (quick, explicit): load `AGENTS.md` as the system prompt file
```bash
codebuddy -p --system-prompt-file ./AGENTS.md "Summarize the rules you loaded."
```

Option B (team-friendly): create a project sub-agent that always reads `AGENTS.md` first
1. Create `.codebuddy/agents/project.md`
2. In its prompt: instruct it to read `AGENTS.md` before doing any work

### 3.10 Aider (Terminal)

Aider recommends providing coding conventions via a read-only file using `--read` (and you can persist this in config). Official docs: <https://aider.chat/docs/usage/conventions.html>.

Option A (recommended): always load rules when starting aider
```bash
aider --read AGENTS.md
```

Option B (persistent): configure always-read conventions via `.aider.conf.yml` (see docs above)

---

## 4. How to use it after rules are loaded (no “magic symbols” required)

You don’t have to use `@anything`. Just speak normally — the router can infer the mode.

### A. “Explain only” (read-only)

Say things like:
- “Explain the folder structure and the main entry points.”
- “What does the lifecycle mean? Give me a concrete example.”

Expected behavior:
- reads, explains, does not write code

### B. “Quick fix” (small changes / bug fix)

Say things like:
- “Fix this NullPointerException and add a unit test to prevent regression.”
- “Add parameter validation here and verify by running the build.”

Expected behavior:
- small scoped edits
- verification (compile/test) after changes

### C. “Full delivery loop” (design → implement → test → archive)

Say things like:
- “Build a minimal Todo API feature. First propose a plan (files to change, tests to add, how to verify). Wait for my approval before implementing.”

Expected behavior:
1. clarifies requirements
2. proposes a plan/spec and waits for approval
3. implements and runs verification
4. archives a summary of what changed

### Optional shortcuts (not required)

If you want to be explicit, you can use:
- `@learn` (force read-only explanation)
- `@patch` (force quick fix)
- `@standard` (force full loop)

But **this is optional** — treat it as a shortcut, not the only way to trigger a mode.

---

## 5. End-to-end example: a minimal Todo API loop

This is a globally understandable demo project: no industry-specific vocabulary.

### 5.1 Requirements (copy/paste)

```
We want a minimal Todo API loop:
1) Add POST /todos: create a todo (title required, max 100 chars)
2) Add GET /todos: list todos (support filtering by done=true/false)
3) Must include unit tests: happy path create, empty title error, list filter
4) First produce a plan/spec (files to change, tests to add, how to verify). After I approve, implement it.
```

### 5.2 Design stage (what “good output” looks like)

You should see:
- scope boundaries (which files will be changed)
- API shape and validation rules
- test plan (exact commands)
- risk assessment (quick fix vs full loop)

Your job here: approve or adjust.

### 5.3 Implementation stage (write + minimal verification)

Key expectations:
- edits stay within the declared scope
- verification runs (compile/tests)
- no infinite retry loops; if something is unclear, it stops and asks

### 5.4 Test stage (proof)

At minimum:
- run unit tests (or the project’s equivalent)
- explain failures clearly (if any), retry within limits

### 5.5 Archive stage (leave a trail)

You should end with:
- a summary suitable for a PR description
- proof of verification (commands + outcomes)
- workflow artifacts stored under `.agents/workflow/runs/` (no random files dumped into repo root)

---

## 6. Troubleshooting: “rules didn’t load”

Fastest check:

```
List the rule/instruction files you loaded (names + paths) and restate the top 3 non-negotiable constraints.
```

If the tool doesn’t mention `AGENTS.md` (or its adapter), it’s not loaded.

Common causes:
- wrong filename for that tool
- wrong directory (tool launched outside repo root)
- symlink permissions (Windows) — use copy instead
- instructions too long — shrink to “top 30 lines” first, then expand
