#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bootstrap a new project with this Java AI engineering framework.

Copies CLAUDE.md (entry point) + .claude/ (framework) into TARGET.
Existing files at the destination are preserved (never overwritten).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

USAGE = """\
Usage: python3 bootstrap.py <target-project-dir>

Copies the framework into <target-project-dir>:
  - CLAUDE.md                          (project entry point)
  - .claude/rules/                     (lifecycle, policy, dispatch-template, skill-precedence)
  - .claude/agents/                    (role definitions)
  - .claude/skills/                    (skill knowledge graph)
  - .claude/scripts/                   (gates, harness, tools, wiki, local_intel)
  - .claude/wiki/                      (KNOWLEDGE_GRAPH, schema, purpose)
  - .claude/workflow/                  (lifecycle examples, artifact templates)
  - .claude/settings.json              (hooks + permissions)
"""

# Source-of-truth rule files (after the #4 refactor that merged 6 → 4).
RULE_FILES = [
    "lifecycle.md",
    "policy.md",
    "dispatch-template.md",
    "skill-precedence.md",
]

TARGET_DIRS = [
    ".claude/rules",
    ".claude/agents",
    ".claude/skills",
    ".claude/scripts/gates",
    ".claude/scripts/harness",
    ".claude/scripts/local_intel",
    ".claude/scripts/tools",
    ".claude/scripts/wiki",
    ".claude/wiki/schema",
    ".claude/wiki/wiki/preferences",
    ".claude/workflow/artifacts",
    ".claude/runs/task-briefs",
    ".claude/runs/launch-specs",
    ".claude/runs/cache",
]

WIKI_FILES = [
    ".claude/wiki/KNOWLEDGE_GRAPH.md",
    ".claude/wiki/purpose.md",
    ".claude/wiki/schema/task_brief_schema.md",
    ".claude/wiki/schema/subagent_contract_schema.md",
]

WORKFLOW_FILES = [
    ".claude/workflow/EXAMPLES.md",
    ".claude/workflow/role_matrix.json",
    ".claude/workflow/artifacts/task_brief.md",
    ".claude/workflow/artifacts/delivery_capsule.md",
]

SCRIPT_DIRS = ["gates", "harness", "local_intel", "tools", "wiki"]

STUB_PREFS = """\
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
"""


def _repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def copy_if_missing(src: str, dst: str) -> None:
    if not os.path.exists(src):
        print(f"  WARN: source missing, skipped: {src}")
        return
    if os.path.exists(dst):
        print(f"  SKIP (exists): {dst}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    print(f"  COPY: {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap the framework into a target project",
        usage=USAGE,
    )
    parser.add_argument("target", help="target project directory")
    args = parser.parse_args()

    target = os.path.abspath(args.target)
    repo_root = _repo_root()

    print(f"=== Bootstrapping framework into {target} ===")

    # 1. Create target structure
    print("[1/4] Preparing target structure...")
    for sub in TARGET_DIRS:
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    print("  Done.")

    # 2. Copy protocol files
    print("[2/4] Copying protocol files...")
    copy_if_missing(os.path.join(repo_root, "CLAUDE.md"),
                    os.path.join(target, "CLAUDE.md"))
    for rule in RULE_FILES:
        copy_if_missing(os.path.join(repo_root, ".claude/rules", rule),
                        os.path.join(target, ".claude/rules", rule))
    agents_dir = os.path.join(repo_root, ".claude/agents")
    if os.path.isdir(agents_dir):
        for fname in sorted(os.listdir(agents_dir)):
            if not fname.endswith(".md"):
                continue
            copy_if_missing(os.path.join(agents_dir, fname),
                            os.path.join(target, ".claude/agents", fname))
    for wf in WIKI_FILES:
        copy_if_missing(os.path.join(repo_root, wf),
                        os.path.join(target, wf))
    for wf in WORKFLOW_FILES:
        copy_if_missing(os.path.join(repo_root, wf),
                        os.path.join(target, wf))
    copy_if_missing(os.path.join(repo_root, ".claude/settings.json"),
                    os.path.join(target, ".claude/settings.json"))
    print("  Done.")

    # 3. Copy scripts
    print("[3/4] Copying scripts...")
    for sub in SCRIPT_DIRS:
        src_dir = os.path.join(repo_root, ".claude/scripts", sub)
        if not os.path.isdir(src_dir):
            continue
        for fname in sorted(os.listdir(src_dir)):
            if fname == "__pycache__":
                continue
            copy_if_missing(os.path.join(src_dir, fname),
                            os.path.join(target, ".claude/scripts", sub, fname))
    # Ensure hook scripts are executable on the target side.
    for fname in ("pre_tool_use_hook.py",
                  "post_tool_use_hook.py",
                  "user_prompt_submit_hook.py"):
        hook_path = os.path.join(target, ".claude/scripts/harness", fname)
        if os.path.isfile(hook_path):
            try:
                os.chmod(hook_path, 0o755)
            except OSError:
                pass
    print("  Done.")

    # 4. Stub preferences
    print("[4/4] Creating stub project preferences...")
    pref_file = os.path.join(target, ".claude/wiki/wiki/preferences/index.md")
    if os.path.isfile(pref_file):
        print(f"  SKIP (exists): {pref_file}")
    else:
        os.makedirs(os.path.dirname(pref_file), exist_ok=True)
        with open(pref_file, "w", encoding="utf-8") as f:
            f.write(STUB_PREFS)
        print(f"  CREATE: {pref_file}")

    print("")
    print("=== Bootstrap complete ===")
    print("Next steps:")
    print(f"  1. Edit {pref_file} with your project-specific constraints.")
    print(f"  2. Review {target}/CLAUDE.md — it is the entry point Claude Code loads on session start.")
    print(f"  3. Optionally trim {target}/.claude/skills/ to only project-relevant skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
