#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Breaking API Change Gate

Reads an <YYYY-MM-DD>_<slug>_openspec.md file and checks whether it declares a breaking change
without a required migration guide section.

"Breaking" is defined as any of:
- Removing an existing endpoint (method + path)
- Renaming a field in a request/response schema
- Changing a field from optional to required
- Changing the HTTP method of an existing endpoint
- Removing or changing an authentication/permission requirement

The gate does NOT parse code — it checks the *spec document* for:
1. A "## Breaking Changes" section (MUST be present if breaking signals detected).
2. A "## Migration Guide" section (MUST be present when Breaking Changes is present).

Exit codes:
- 0: PASS
- 1: WARN (breaking section present but migration guide thin)
- 2: FAIL (breaking signals detected but sections missing)
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

BREAKING_SIGNALS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(remove|delete|drop)\b.*(endpoint|api|route|path)", re.IGNORECASE), "endpoint removal"),
    (re.compile(r"\b(rename|renamed)\b.*(field|parameter|param|property)", re.IGNORECASE), "field rename"),
    (re.compile(r"\b(optional\s+→\s+required|now\s+required)", re.IGNORECASE), "field optionality change"),
    (re.compile(r"\b(change|changed)\b.*(http\s+method|GET|POST|PUT|DELETE|PATCH)", re.IGNORECASE), "HTTP method change"),
    (re.compile(r"\b(breaking|backward.incompatible|non-backward)", re.IGNORECASE), "explicit breaking label"),
    (re.compile(r"\bpermission\b.*(change|modify|remove|update)", re.IGNORECASE), "permission strategy change"),
]

BREAKING_SECTION = "## Breaking Changes"
MIGRATION_SECTION = "## Migration Guide"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openspec", required=True, help="Path to <YYYY-MM-DD>_<slug>_openspec.md")
    args = parser.parse_args()

    path = args.openspec
    if not os.path.exists(path):
        print(f"FAIL: openspec not found: {path}")
        return EXIT_FAIL

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    detected: list[str] = []
    for pattern, label in BREAKING_SIGNALS:
        if pattern.search(content):
            detected.append(label)

    has_breaking_section = BREAKING_SECTION in content
    has_migration_section = MIGRATION_SECTION in content

    if not detected and not has_breaking_section:
        print("OK: api_breaking_gate pass — no breaking changes detected")
        return 0

    if detected and not has_breaking_section:
        print("FAIL: api_breaking_gate")
        print(f"- Breaking signals detected: {', '.join(detected)}")
        print(f"- Missing required section: '{BREAKING_SECTION}'")
        print(f"- Missing required section: '{MIGRATION_SECTION}'")
        print("Action: add '## Breaking Changes' and '## Migration Guide' to <YYYY-MM-DD>_<slug>_openspec.md before Implement.")
        return EXIT_FAIL

    if has_breaking_section and not has_migration_section:
        print("FAIL: api_breaking_gate")
        print(f"- '## Breaking Changes' section found but '## Migration Guide' is missing.")
        print("Action: add '## Migration Guide' describing how callers should adapt.")
        return EXIT_FAIL

    migration_content = content.split(MIGRATION_SECTION, 1)[-1].strip()
    if len(migration_content.splitlines()) < 3:
        print("WARN: api_breaking_gate")
        print("- '## Migration Guide' section is too thin (< 3 lines). Expand it before delivery.")
        return EXIT_WARN

    print("OK: api_breaking_gate pass — breaking changes documented with migration guide")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
