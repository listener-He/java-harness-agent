#!/usr/bin/env bash
# Bootstrap a new project with this Java AI engineering framework.
# Copies CLAUDE.md (entry point) + .claude/ (framework) into TARGET.
# Existing files at the destination are preserved (never overwritten).

set -eu

if [ $# -lt 1 ]; then
    cat <<USAGE
Usage: $0 <target-project-dir>

Copies the framework into <target-project-dir>:
  - CLAUDE.md                          (project entry point)
  - .claude/rules/                     (routing, lifecycle, hooks, etc.)
  - .claude/agents/                    (role definitions)
  - .claude/skills/                    (skill knowledge graph)
  - .claude/scripts/                   (gates, harness, tools, wiki, local_intel)
  - .claude/wiki/                      (KNOWLEDGE_GRAPH, schema, purpose)
  - .claude/workflow/                  (lifecycle examples, artifact templates)
  - .claude/settings.json              (hooks + permissions)
USAGE
    exit 1
fi

TARGET="$1"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "=== Bootstrapping framework into $TARGET ==="

# ── 1. Create target structure ────────────────────────────────────
echo "[1/4] Preparing target structure..."
mkdir -p "$TARGET/.claude/rules" \
         "$TARGET/.claude/agents" \
         "$TARGET/.claude/skills" \
         "$TARGET/.claude/scripts/gates" \
         "$TARGET/.claude/scripts/harness" \
         "$TARGET/.claude/scripts/local_intel" \
         "$TARGET/.claude/scripts/tools" \
         "$TARGET/.claude/scripts/wiki" \
         "$TARGET/.claude/wiki/schema" \
         "$TARGET/.claude/wiki/wiki/preferences" \
         "$TARGET/.claude/workflow/artifacts" \
         "$TARGET/.claude/runs/task-briefs" \
         "$TARGET/.claude/runs/launch-specs" \
         "$TARGET/.claude/runs/cache"
echo "  Done."

# ── 2. Copy protocol files (preserve existing) ────────────────────
echo "[2/4] Copying protocol files..."

copy_if_missing() {
    local src="$1"
    local dst="$2"
    if [ ! -e "$src" ]; then
        echo "  WARN: source missing, skipped: $src"
        return
    fi
    if [ -e "$dst" ]; then
        echo "  SKIP (exists): $dst"
    else
        mkdir -p "$(dirname "$dst")"
        cp -R "$src" "$dst"
        echo "  COPY: $dst"
    fi
}

# Entry point
copy_if_missing "$REPO_ROOT/CLAUDE.md" "$TARGET/CLAUDE.md"

# Rules
for rule in routing.md lifecycle.md hooks.md safety-constraints.md writeback-policy.md; do
    copy_if_missing "$REPO_ROOT/.claude/rules/$rule" "$TARGET/.claude/rules/$rule"
done

# Agents
for agent in "$REPO_ROOT/.claude/agents/"*.md; do
    [ -e "$agent" ] || continue
    copy_if_missing "$agent" "$TARGET/.claude/agents/$(basename "$agent")"
done

# Wiki
copy_if_missing "$REPO_ROOT/.claude/wiki/KNOWLEDGE_GRAPH.md" "$TARGET/.claude/wiki/KNOWLEDGE_GRAPH.md"
copy_if_missing "$REPO_ROOT/.claude/wiki/purpose.md" "$TARGET/.claude/wiki/purpose.md"
copy_if_missing "$REPO_ROOT/.claude/wiki/schema/task_brief_schema.md" "$TARGET/.claude/wiki/schema/task_brief_schema.md"
copy_if_missing "$REPO_ROOT/.claude/wiki/schema/subagent_contract_schema.md" "$TARGET/.claude/wiki/schema/subagent_contract_schema.md"

# Workflow templates
copy_if_missing "$REPO_ROOT/.claude/workflow/EXAMPLES.md" "$TARGET/.claude/workflow/EXAMPLES.md"
copy_if_missing "$REPO_ROOT/.claude/workflow/role_matrix.json" "$TARGET/.claude/workflow/role_matrix.json"
copy_if_missing "$REPO_ROOT/.claude/workflow/artifacts/task_brief.md" "$TARGET/.claude/workflow/artifacts/task_brief.md"
copy_if_missing "$REPO_ROOT/.claude/workflow/artifacts/delivery_capsule.md" "$TARGET/.claude/workflow/artifacts/delivery_capsule.md"

# Settings (hooks + permissions)
copy_if_missing "$REPO_ROOT/.claude/settings.json" "$TARGET/.claude/settings.json"

echo "  Done."

# ── 3. Copy scripts ───────────────────────────────────────────────
echo "[3/4] Copying scripts..."
for dir in gates harness local_intel tools wiki; do
    src_dir="$REPO_ROOT/.claude/scripts/$dir"
    [ -d "$src_dir" ] || continue
    for f in "$src_dir/"*; do
        [ -e "$f" ] || continue
        bname="$(basename "$f")"
        if [ "$bname" = "__pycache__" ]; then continue; fi
        copy_if_missing "$f" "$TARGET/.claude/scripts/$dir/$bname"
    done
done
# Ensure hook wrapper is executable in target
chmod +x "$TARGET/.claude/scripts/harness/post_tool_use_hook.sh" 2>/dev/null || true
echo "  Done."

# ── 4. Create stub project preferences ────────────────────────────
echo "[4/4] Creating stub project preferences..."
PREF_FILE="$TARGET/.claude/wiki/wiki/preferences/index.md"
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

echo ""
echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Edit $PREF_FILE with your project-specific constraints."
echo "  2. Review $TARGET/CLAUDE.md — it is the entry point Claude Code loads on session start."
echo "  3. Optionally trim $TARGET/.claude/skills/ to only project-relevant skills."
