---
name: deepinit
description: "Deep codebase initialization. Two outputs: (1) hierarchical AGENTS.md files for human navigation; (2) a machine-readable context_brief.md that other skills (brainstorming, greenfield-scaffold, requirement-intake) can load directly as structured context. TRIGGER when initializing a new repo, onboarding an agent to an unfamiliar codebase, or when requirement-intake needs codebase context and no context_brief.md exists."
---

# deepinit — Deep Codebase Initialization

Two outputs for two audiences:
- **AGENTS.md files**: human-navigable documentation, hierarchical, one per directory
- **`context_brief.md`**: machine-readable structured context for agent skill consumption

Both are generated in one pass. The `context_brief.md` is the primary output for downstream skills.

## Core Concept

AGENTS.md files serve as **AI-readable documentation** that helps agents understand:
- What each directory contains
- How components relate to each other
- Special instructions for working in that area
- Dependencies and relationships

## Core Concept

AGENTS.md files serve as **AI-readable documentation** that helps agents understand:
- What each directory contains
- How components relate to each other
- Special instructions for working in that area
- Dependencies and relationships

## Hierarchical Tagging System

Every AGENTS.md (except root) includes a parent reference tag:

```markdown
<!-- Parent: ../AGENTS.md -->
```

This creates a navigable hierarchy:
```
/AGENTS.md                          ← Root (no parent tag)
├── src/AGENTS.md                   ← <!-- Parent: ../AGENTS.md -->
│   ├── src/components/AGENTS.md    ← <!-- Parent: ../AGENTS.md -->
│   └── src/utils/AGENTS.md         ← <!-- Parent: ../AGENTS.md -->
└── docs/AGENTS.md                  ← <!-- Parent: ../AGENTS.md -->
```

## AGENTS.md Template

```markdown
<!-- Parent: {relative_path_to_parent}/AGENTS.md -->
<!-- Generated: {timestamp} | Updated: {timestamp} -->

# {Directory Name}

## Purpose
{One-paragraph description of what this directory contains and its role}

## Key Files
{List each significant file with a one-line description}

| File | Description |
|------|-------------|
| `file.ts` | Brief description of purpose |

## Subdirectories
{List each subdirectory with brief purpose}

| Directory | Purpose |
|-----------|---------|
| `subdir/` | What it contains (see `subdir/AGENTS.md`) |

## For AI Agents

### Working In This Directory
{Special instructions for AI agents modifying files here}

### Testing Requirements
{How to test changes in this directory}

### Common Patterns
{Code patterns or conventions used here}

## Dependencies

### Internal
{References to other parts of the codebase this depends on}

### External
{Key external packages/libraries used}

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
```

## Execution Workflow

### Step 1: Map Directory Structure

```
Call the @explore agent,
  prompt="List all directories recursively. Exclude: node_modules, .git, dist, build, __pycache__, .venv, coverage, .next, .nuxt"
```

### Step 2: Create Work Plan

Generate todo items for each directory, organized by depth level:

```
Level 0: / (root)
Level 1: /src, /docs, /tests
Level 2: /src/components, /src/utils, /docs/api
...
```

### Step 3: Generate Level by Level

**IMPORTANT**: Generate parent levels before child levels to ensure parent references are valid.

For each directory:
1. Read all files in the directory
2. Analyze purpose and relationships
3. Generate AGENTS.md content
4. Write file with proper parent reference

### Step 4: Compare and Update (if exists)

When AGENTS.md already exists:

1. **Read existing content**
2. **Identify sections**:
   - Auto-generated sections (can be updated)
   - Manual sections (`<!-- MANUAL -->` preserved)
3. **Compare**:
   - New files added?
   - Files removed?
   - Structure changed?
4. **Merge**:
   - Update auto-generated content
   - Preserve manual annotations
   - Update timestamp

### Step 5: Validate Hierarchy

After generation, run validation checks:

| Check | How to Verify | Corrective Action |
|-------|--------------|-------------------|
| Parent references resolve | Read each AGENTS.md, check `<!-- Parent: -->` path exists | Fix path or remove orphan |
| No orphaned AGENTS.md | Compare AGENTS.md locations to directory structure | Delete orphaned files |
| Completeness | List all directories, check for AGENTS.md | Generate missing files |
| Timestamps current | Check `<!-- Generated: -->` dates | Regenerate outdated files |

Validation script pattern:
```bash
# Find all AGENTS.md files
find . -name "AGENTS.md" -type f

# Check parent references
grep -r "<!-- Parent:" --include="AGENTS.md" .
```

## Smart Delegation

| Task | Agent |
|------|-------|
| Directory mapping | `explore` |
| File analysis | `architect` |
| Content generation | `writer` |
| AGENTS.md writes | `writer` |

## Empty Directory Handling

When encountering empty or near-empty directories:

| Condition | Action |
|-----------|--------|
| No files, no subdirectories | **Skip** - do not create AGENTS.md |
| No files, has subdirectories | Create minimal AGENTS.md with subdirectory listing only |
| Has only generated files (*.min.js, *.map) | Skip or minimal AGENTS.md |
| Has only config files | Create AGENTS.md describing configuration purpose |

Example minimal AGENTS.md for directory-only containers:
```markdown
<!-- Parent: ../AGENTS.md -->
# {Directory Name}

## Purpose
Container directory for organizing related modules.

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `subdir/` | Description (see `subdir/AGENTS.md`) |
```

## Parallelization Rules

1. **Same-level directories**: Process in parallel
2. **Different levels**: Sequential (parent first)
3. **Large directories**: Spawn dedicated agent per directory
4. **Small directories**: Batch multiple into one agent

## Quality Standards

### Must Include
- [ ] Accurate file descriptions
- [ ] Correct parent references
- [ ] Subdirectory links
- [ ] AI agent instructions

### Must Avoid
- [ ] Generic boilerplate
- [ ] Incorrect file names
- [ ] Broken parent references
- [ ] Missing important files

## Example Output

### Root AGENTS.md
```markdown
<!-- Generated: 2024-01-15 | Updated: 2024-01-15 -->

# my-project

## Purpose
A web application for managing user tasks with real-time collaboration features.

## Key Files
| File | Description |
|------|-------------|
| `package.json` | Project dependencies and scripts |
| `tsconfig.json` | TypeScript configuration |
| `.env.example` | Environment variable template |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `src/` | Application source code (see `src/AGENTS.md`) |
| `docs/` | Documentation (see `docs/AGENTS.md`) |
| `tests/` | Test suites (see `tests/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Always install dependencies after modifying the project manifest
- Use TypeScript strict mode
- Follow ESLint rules

### Testing Requirements
- Run tests before committing
- Ensure >80% coverage

### Common Patterns
- Use barrel exports (index.ts)
- Prefer functional components

## Dependencies

### External
- React 18.x - UI framework
- TypeScript 5.x - Type safety
- Vite - Build tool

<!-- MANUAL: Custom project notes can be added below -->
```

### Nested AGENTS.md
```markdown
<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2024-01-15 | Updated: 2024-01-15 -->

# components

## Purpose
Reusable React components organized by feature and complexity.

## Key Files
| File | Description |
|------|-------------|
| `index.ts` | Barrel export for all components |
| `Button.tsx` | Primary button component |
| `Modal.tsx` | Modal dialog component |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `forms/` | Form-related components (see `forms/AGENTS.md`) |
| `layout/` | Layout components (see `layout/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- Each component has its own file
- Use CSS modules for styling
- Export via index.ts

### Testing Requirements
- Unit tests in `__tests__/` subdirectory
- Use React Testing Library

### Common Patterns
- Props interfaces defined above component
- Use forwardRef for DOM-exposing components

## Dependencies

### Internal
- `src/hooks/` - Custom hooks used by components
- `src/utils/` - Utility functions

### External
- `clsx` - Conditional class names
- `lucide-react` - Icons

<!-- MANUAL: -->
```

## Step 6: Generate context_brief.md (MUST — final step)

After all AGENTS.md files are written and validated, synthesize a single machine-readable `context_brief.md` under `.agents/workflow/runs/<YYYY-MM-DD>_<slug>_context_brief.md`.

This file is consumed by: `requirement-intake`, `brainstorming`, `greenfield-scaffold`, `adversarial-review` (Category C), and any skill that needs codebase context without navigating the full file tree.

### context_brief.md Template

```markdown
# Context Brief — {repo-name}
Generated: {YYYY-MM-DD} | Source: deepinit

## 1. Codebase Identity
- **Language / Framework**: {e.g., Java 17 / Spring Boot 3.x}
- **Architecture style**: {e.g., Layered MVC, Hexagonal, Microservice}
- **Entry points**: {main classes or modules where execution starts}
- **Build tool**: {Maven / Gradle / etc.}

## 2. Domain Entities
| Entity | Location | Core Attributes | Lifecycle States |
|---|---|---|---|
| {EntityName} | {package.ClassName} | {key fields} | {states if stateful, else N/A} |

## 3. API Surface
| Method | Path | Auth | Module | Notes |
|---|---|---|---|---|
| {GET/POST/...} | {/path} | {role/public} | {controller class} | {one-line summary} |

## 4. Constraint List (Engineering Red Lines)
These are invariants extracted from the codebase that MUST be preserved by any change:
- {constraint 1 — e.g., "All DB writes must go through @Transactional service layer"}
- {constraint 2 — e.g., "No direct SQL in controllers"}
- {constraint 3}

## 5. Key Dependencies (non-obvious)
| Dependency | Version | Purpose | Notes |
|---|---|---|---|
| {lib} | {ver} | {why it's used} | {any known quirks} |

## 6. Test Coverage Summary
- **Test framework**: {JUnit 5 / Mockito / etc.}
- **Coverage approach**: {unit / integration / both}
- **Known gaps**: {areas without tests, if detectable}

## 7. Open Questions (for requirement-intake)
Things that could not be determined from static analysis — a consuming skill should resolve these:
- {question 1 — e.g., "Authentication strategy not visible from code alone"}
- {question 2}
```

### Quality rules for context_brief.md

- Each Domain Entity row requires an actual class path (`package.ClassName`) — no guesses
- Constraint List entries must be falsifiable: "X must always Y" not "try to do Y"
- If a section cannot be populated from the codebase (e.g., no REST controllers found): write `None detected` — do NOT leave blank or fabricate
- Max 3 Open Questions — if more are needed, surface only the highest-impact ones

---

## Triggering Update Mode

When running on an existing codebase with AGENTS.md files:

1. Detect existing files first
2. Read and parse existing content
3. Analyze current directory state
4. Generate diff between existing and current
5. Apply updates while preserving manual sections
6. Regenerate `context_brief.md` to reflect current state — always overwrite, never merge

## Performance Considerations

- **Cache directory listings** - Don't re-scan same directories
- **Batch small directories** - Process multiple at once
- **Skip unchanged** - If directory hasn't changed, skip regeneration
- **Parallel writes** - Multiple agents writing different files simultaneously
- `context_brief.md` is always generated last, after all AGENTS.md files are complete — it synthesizes across them
