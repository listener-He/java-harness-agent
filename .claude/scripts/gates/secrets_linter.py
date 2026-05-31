#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secrets Linter (High-confidence scan)

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import glob
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


PATTERNS_FAIL = [
    re.compile(r"(?i)\bsecret[_-]?access[_-]?key\b\s*:\s*\"?[A-Za-z0-9+/=._-]{12,}\"?"),
    re.compile(r"(?i)\baccess[_-]?key[_-]?id\b\s*:\s*\"?[A-Za-z0-9+/=._-]{8,}\"?"),
    re.compile(r"(?i)\bapi[_-]?key\b\s*:\s*\"?[A-Za-z0-9+/=._-]{12,}\"?"),
    re.compile(r"(?i)\bpassword\b\s*:\s*\"?.{6,}\"?"),
    re.compile(r"(?i)\btoken\b\s*:\s*\"?[A-Za-z0-9+/=._-]{12,}\"?"),
]

PATTERNS_WARN = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\bsecret\b\s*:\s*\"?.{8,}\"?"),
]

IGNORE_GLOBS = [
    "**/target/**",
    "**/.git/**",
    "**/.idea/**",
    "**/.claude/runs/**",            # canonical runtime artifacts dir
    "**/.claude/workflow/runs/**",   # legacy path (kept until cleanup)
    "**/.claude/router/runs/**",
]

# Paths where a HIGH-confidence pattern is LIKELY a fixture / test value
# rather than a real leaked secret. Match → demote FAIL → WARN (not skip:
# real test secrets DO occasionally leak from test code paths into prod).
# Add a path here only if false-positive rate in that directory is high
# AND committing the file with the pattern won't compromise production.
DOWNGRADE_GLOBS = [
    "**/test/**",
    "**/tests/**",
    "**/__tests__/**",
    "**/fixtures/**",
    "**/testdata/**",
    "**/*_test.*",                    # foo_test.go / foo_test.py
    "**/*Test.java",                  # JUnit FooTest.java
    "**/*Tests.java",                 # FooTests.java
    "**/*.test.ts",                   # foo.test.ts
    "**/*.test.js",
    "**/*.spec.ts",                   # foo.spec.ts
    "**/*.spec.js",
    "**/src/test/**",                 # Maven convention
]


def _normalize_path_for_glob(path: str) -> str:
    """Slash-normalize + ensure leading ./ so '**/' prefix patterns can match
    bare relative paths like '.claude/runs/foo'."""
    p = path.replace("\\", "/")
    if not p.startswith("/") and not p.startswith("./"):
        p = "./" + p
    return p


def _is_ignored(path: str) -> bool:
    p = _normalize_path_for_glob(path)
    for ig in IGNORE_GLOBS:
        if glob.fnmatch.fnmatch(p, ig):
            return True
    return False


def _is_downgrade(path: str) -> bool:
    """True if path is in a test/fixture context where HIGH-confidence pattern
    hits should be demoted to WARN (still surfaced, not blocked)."""
    p = _normalize_path_for_glob(path)
    for dg in DOWNGRADE_GLOBS:
        if glob.fnmatch.fnmatch(p, dg):
            return True
    return False


def _scan_file(path: str) -> tuple[list[str], list[str]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return [], []
    fails, warns = _scan_lines(lines, path)
    if fails and _is_downgrade(path):
        # Demote FAIL → WARN: test fixtures CAN have test passwords; surface
        # but don't block. Tag with "[downgrade:test-path]" so caller knows
        # this isn't a clean PASS.
        warns.extend(f"[downgrade:test-path] {x}" for x in fails)
        fails = []
    return fails, warns


def _scan_lines(lines: list[str], label: str) -> tuple[list[str], list[str]]:
    """Scan a list of text lines for secret patterns. Used by both file scan
    and content-stdin mode. `label` is the prefix for line markers (filename
    or '<stdin>')."""
    fails: list[str] = []
    warns: list[str] = []
    for i, line in enumerate(lines, start=1):
        for pat in PATTERNS_FAIL:
            if pat.search(line):
                fails.append(f"{label}:{i}:{line.strip()}")
        for pat in PATTERNS_WARN:
            if pat.search(line):
                warns.append(f"{label}:{i}:{line.strip()}")
    return fails, warns


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", nargs="+", help="glob patterns (file mode)")
    parser.add_argument("--content-stdin", action="store_true",
                        help="read content from stdin instead of files; "
                             "intended for PreToolUse hook pre-flight check")
    parser.add_argument("--target-path",
                        help="(content-stdin mode) target file path — used "
                             "only for ignore-glob check so Pre and Post "
                             "stay consistent")
    args = parser.parse_args()

    # Pre-flight mode: content arrives on stdin, file does not yet exist.
    if args.content_stdin:
        target = args.target_path or "<stdin>"
        if args.target_path and _is_ignored(args.target_path):
            print("OK: secrets linter pass (target in ignore list)")
            return 0
        try:
            content = sys.stdin.read()
        except Exception:
            return 0
        if not content:
            return 0
        all_fails, all_warns = _scan_lines(content.splitlines(), target)
        # Demote FAIL → WARN if target path is in a test/fixture context.
        # PreToolUse hook respects this: WARN doesn't block; the hook prints
        # the warning to stderr but returns 0.
        if all_fails and args.target_path and _is_downgrade(args.target_path):
            all_warns.extend(f"[downgrade:test-path] {x}" for x in all_fails)
            all_fails = []
    else:
        if not args.paths:
            print("FAIL: --paths required in file mode")
            return EXIT_FAIL
        files: list[str] = []
        for g in args.paths:
            files.extend(glob.glob(g, recursive=True))
        files = [os.path.normpath(p) for p in files if os.path.isfile(p) and not _is_ignored(p)]

        all_fails: list[str] = []
        all_warns: list[str] = []
        for f in sorted(set(files)):
            fails, warns = _scan_file(f)
            all_fails.extend(fails)
            all_warns.extend(warns)

    if all_fails:
        print("FAIL: secrets linter hit high-confidence patterns")
        for x in all_fails[:100]:
            print(f"- {x}")
        if len(all_fails) > 100:
            print(f"... truncated ({len(all_fails)} total)")
        return EXIT_FAIL

    if all_warns:
        print("WARN: secrets linter hit suspicious patterns")
        for x in all_warns[:100]:
            print(f"- {x}")
        if len(all_warns) > 100:
            print(f"... truncated ({len(all_warns)} total)")
        return EXIT_WARN

    print("OK: secrets linter pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
