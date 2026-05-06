#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# bootstrap.sh — Quick-start .agents/ protocol skeleton in a new project
#
# Usage:
#   bash .agents/scripts/tools/bootstrap.sh [TARGET_DIR]
#
# Examples:
#   bash .agents/scripts/tools/bootstrap.sh /path/to/new-project
#   bash .agents/scripts/tools/bootstrap.sh          # bootstraps into current dir
#
# Safety: never overwrites existing files (cp -n).

set -euo pipefail

TARGET="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "=== Bootstrap .agents/ protocol skeleton ==="
echo "Source: $REPO_ROOT"
echo "Target: $TARGET"
echo ""

# ── 1. Create directory structure ──────────────────────────────────
echo "[1/5] Creating directory structure..."
mkdir -p "$TARGET/.agents/"{router/runs,workflow/{runs,artifacts},llm_wiki/{wiki/{domain,api,data,architecture,specs,testing,reviews,preferences}/wal,archive,schema},skills,scripts/{gates,wiki,tools,harness},events/drift_queue}
echo "  Done."

# ── 2. Copy protocol files (preserve existing) ────────────────────
echo "[2/5] Copying protocol files..."

copy_if_missing() {
    local src="$1"
    local dst="$2"
    if [ -f "$dst" ]; then
        echo "  SKIP (exists): $dst"
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "  COPY: $dst"
    fi
}

# Core entry point
copy_if_missing "$REPO_ROOT/AGENTS.md" "$TARGET/AGENTS.md"

# Router
copy_if_missing "$REPO_ROOT/.agents/router/ROUTER.md" "$TARGET/.agents/router/ROUTER.md"
copy_if_missing "$REPO_ROOT/.agents/router/CONTEXT_FUNNEL.md" "$TARGET/.agents/router/CONTEXT_FUNNEL.md"

# Workflow
copy_if_missing "$REPO_ROOT/.agents/workflow/LIFECYCLE.md" "$TARGET/.agents/workflow/LIFECYCLE.md"
copy_if_missing "$REPO_ROOT/.agents/workflow/HOOKS.md" "$TARGET/.agents/workflow/HOOKS.md"
copy_if_missing "$REPO_ROOT/.agents/workflow/ROLE_MATRIX.md" "$TARGET/.agents/workflow/ROLE_MATRIX.md"
copy_if_missing "$REPO_ROOT/.agents/workflow/ARCHIVE_WAL.md" "$TARGET/.agents/workflow/ARCHIVE_WAL.md"
copy_if_missing "$REPO_ROOT/.agents/workflow/role_matrix.json" "$TARGET/.agents/workflow/role_matrix.json"

# Wiki
copy_if_missing "$REPO_ROOT/.agents/llm_wiki/KNOWLEDGE_GRAPH.md" "$TARGET/.agents/llm_wiki/KNOWLEDGE_GRAPH.md"
copy_if_missing "$REPO_ROOT/.agents/llm_wiki/purpose.md" "$TARGET/.agents/llm_wiki/purpose.md"
copy_if_missing "$REPO_ROOT/.agents/llm_wiki/schema/openspec_schema.md" "$TARGET/.agents/llm_wiki/schema/openspec_schema.md"
copy_if_missing "$REPO_ROOT/.agents/llm_wiki/schema/subagent_contract_schema.md" "$TARGET/.agents/llm_wiki/schema/subagent_contract_schema.md"

# Artifact templates
copy_if_missing "$REPO_ROOT/.agents/workflow/artifacts/focus_card.md" "$TARGET/.agents/workflow/artifacts/focus_card.md"

echo "  Done."

# ── 3. Copy gate scripts ──────────────────────────────────────────
echo "[3/5] Copying gate scripts..."
for script in "$REPO_ROOT/.agents/scripts/gates/"*.py; do
    bname="$(basename "$script")"
    dst="$TARGET/.agents/scripts/gates/$bname"
    if [ "$bname" = "__pycache__" ]; then continue; fi
    copy_if_missing "$script" "$dst"
done

# Wiki/tools scripts
for script in "$REPO_ROOT/.agents/scripts/wiki/"*.py; do
    bname="$(basename "$script")"
    dst="$TARGET/.agents/scripts/wiki/$bname"
    if [ "$bname" = "__pycache__" ]; then continue; fi
    copy_if_missing "$script" "$dst"
done
for script in "$REPO_ROOT/.agents/scripts/tools/"*.py; do
    bname="$(basename "$script")"
    dst="$TARGET/.agents/scripts/tools/$bname"
    copy_if_missing "$script" "$dst"
done
copy_if_missing "$REPO_ROOT/.agents/scripts/tools/bootstrap.sh" "$TARGET/.agents/scripts/tools/bootstrap.sh"
echo "  Done."

# ── 4. Create stub project preferences ────────────────────────────
echo "[4/5] Creating stub project preferences..."
PREF_FILE="$TARGET/.agents/llm_wiki/wiki/preferences/index.md"
if [ -f "$PREF_FILE" ]; then
    echo "  SKIP (exists): $PREF_FILE"
else
    cat > "$PREF_FILE" << 'PREFEOF'
# Project Preferences & Constraints

> **Instructions:** Replace the stubs below with your project-specific rules.
> Each section should contain actionable constraints the Agent MUST follow.

## Security Rules
- [ ] Describe auth/permission strategy (e.g., JWT, OAuth2, API Key)
- [ ] List sensitive data handling rules (PII, encryption at rest, etc.)

## Database Rules
- [ ] Define soft-delete policy (if applicable)
- [ ] Define tenant isolation strategy (if multi-tenant)
- [ ] List forbidden patterns (e.g., "NO SQL JOIN for cross-domain data")

## API Design Rules
- [ ] Define URL naming convention (e.g., lowercase-hyphenated, verb suffixes)
- [ ] Define parameter passing convention (Query String vs Request Body)
- [ ] List forbidden patterns (e.g., "NO Path Variables")

## Code Style Rules
- [ ] Define indentation (spaces vs tabs, width)
- [ ] Define brace style
- [ ] Define import ordering rules
- [ ] Define Javadoc requirements

## Testing Rules
- [ ] Define minimum coverage expectations
- [ ] Define mock framework preferences
- [ ] Define integration test boundaries

## Anti-Patterns (DO NOT DO)
- [ ] List forbidden libraries/frameworks
- [ ] List forbidden design patterns
- [ ] List migration-specific red lines (e.g., "NO DROP TABLE without DBA approval")
PREFEOF
    echo "  CREATE: $PREF_FILE"
fi

# ── 5. Run self-check ─────────────────────────────────────────────
echo "[5/5] Running initial consistency check..."
CONSISTENCY_GATE="$TARGET/.agents/scripts/gates/consistency_gate.py"
if [ -f "$CONSISTENCY_GATE" ]; then
    python3 "$CONSISTENCY_GATE" && echo "  PASS: Budget values consistent." || echo "  WARN: consistency_gate reported issues (may need project-specific overrides)."
else
    echo "  SKIP: consistency_gate.py not found in target."
fi

echo ""
echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Edit $PREF_FILE with your project-specific constraints."
echo "  2. Review $TARGET/AGENTS.md and adjust project-specific paths if needed."
echo "  3. Copy relevant skills from source .agents/skills/ to target."
echo "  4. Run: python3 .agents/scripts/gates/consistency_gate.py"
