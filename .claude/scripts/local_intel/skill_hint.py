#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Hint — symptom-driven, non-blocking.

When a just-edited Java / mapper file contains a known anti-pattern, emit a
one-line [skill-hint] pointing at the relevant SKILL.md. Silent otherwise.

Philosophy: the LLM has each skill's frontmatter description in its system
prompt; this hook does NOT re-state those rules. It only nudges the agent to
consult the deep-dive SKILL.md when actual code shows symptoms — replacing
preflight reading with on-demand reading.

Hard caps to avoid noise:
  - at most 2 skills mentioned per file
  - each skill matched only on its first hit (no per-pattern spam)

Quiet env: CLAUDE_SKILL_HINT_QUIET=1
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# (regex, skill_dir_name, one-line message)
JAVA_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"@PathVariable"),
     "java-architecture-standards",
     "@PathVariable found — Red Line: No Path Variables. Use query string (GET) or request body (POST)."),
    (re.compile(r"throw\s+new\s+RuntimeException\s*\("),
     "java-architecture-standards",
     "RuntimeException thrown — prefer DomainException + AbstractErrorCode for transactional safety."),
    (re.compile(r"^\s*@Autowired\s*$", re.M),
     "java-architecture-standards",
     "field-level @Autowired — use @RequiredArgsConstructor for constructor injection."),
    (re.compile(r"@Data\b"),
     "java-architecture-standards",
     "@Data found — prefer @Getter + @Setter (project Lombok policy)."),
    (re.compile(r"==\s*null|null\s*=="),
     "java-architecture-standards",
     "raw null comparison — use Objects.isNull() / Objects.nonNull()."),
    (re.compile(r"import\s+[\w.]+\.\*\s*;"),
     "java-coding-style",
     "wildcard import — list each imported type explicitly."),
    (re.compile(r'"[^"]*\bJOIN\b[^"]*"', re.IGNORECASE),
     "mybatis-sql-standard",
     "JOIN inside a Java string literal — consider Anti-JOIN: query then assemble in memory."),
]

MAPPER_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\$\{[^}]+\}"),
     "mybatis-sql-standard",
     "${} parameter — SQL injection risk; use #{} or a whitelisted enum mapping."),
    (re.compile(r"<\s*select[^>]*>(?:(?!</select>).)*\bJOIN\b", re.IGNORECASE | re.DOTALL),
     "mybatis-sql-standard",
     "JOIN inside <select> — prefer single-table query + in-memory assembly (Anti-JOIN)."),
    (re.compile(r"\bSELECT\s+\*", re.IGNORECASE),
     "mybatis-sql-standard",
     "SELECT * — list columns explicitly (avoid pulling large TEXT/JSON)."),
]

MAX_SKILLS_PER_FILE = 2


def _pick_patterns(path: str) -> list[tuple[re.Pattern, str, str]]:
    p = path.lower()
    if p.endswith(".java"):
        return JAVA_PATTERNS
    if p.endswith(".xml") and "mapper" in p:
        return MAPPER_PATTERNS
    return []


def main() -> int:
    if os.environ.get("CLAUDE_SKILL_HINT_QUIET") == "1":
        return 0
    if len(sys.argv) < 2:
        return 0

    path = sys.argv[1]
    patterns = _pick_patterns(path)
    if not patterns:
        return 0

    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0

    hits: list[str] = []
    skills_seen: set[str] = set()
    for regex, skill, msg in patterns:
        if skill in skills_seen:
            continue
        if regex.search(content):
            hits.append(f"  - {msg} → see .claude/skills/{skill}/SKILL.md")
            skills_seen.add(skill)
            if len(skills_seen) >= MAX_SKILLS_PER_FILE:
                break

    if not hits:
        return 0

    print("[skill-hint]")
    for h in hits:
        print(h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
