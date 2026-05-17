#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java Comment Linter (Javadoc policy)

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


CLASS_PUBLIC_RE = re.compile(r"^\s*public\s+(class|interface|enum)\s+\w+")
PUBLIC_METHOD_RE = re.compile(r"^\s*public\s+(?!class|interface|enum)\S+.*\(")
JAVADOC_START_RE = re.compile(r"^\s*/\*\*")


def _iter_java_files(root: str) -> list[str]:
    out: list[str] = []
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".java"):
                out.append(os.path.join(base, f))
    return sorted(out)


def _has_javadoc_before(lines: list[str], idx: int) -> bool:
    j = idx - 1
    while j >= 0 and lines[j].strip() == "":
        j -= 1
    if j < 0:
        return False
    return bool(JAVADOC_START_RE.search(lines[j]))


def _is_target_method_file(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return any(k in p for k in ["/api/", "/service/", "/support/permission/", "/support/datascope/"])


def _scan_file(path: str) -> tuple[list[str], list[str]]:
    missing_class: list[str] = []
    missing_method: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if CLASS_PUBLIC_RE.search(line):
            if not _has_javadoc_before(lines, i):
                missing_class.append(f"{path}:{i+1}: public type missing Javadoc")
        if _is_target_method_file(path) and PUBLIC_METHOD_RE.search(line):
            if not _has_javadoc_before(lines, i):
                missing_method.append(f"{path}:{i+1}: public method missing Javadoc")

    return missing_class, missing_method


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--fail-on-missing", action="store_true", help="Default is WARN; set to FAIL")
    args = parser.parse_args()

    root = args.path
    if not os.path.isdir(root):
        print(f"FAIL: path not found: {root}")
        return EXIT_FAIL

    class_miss: list[str] = []
    method_miss: list[str] = []
    for f in _iter_java_files(root):
        c, m = _scan_file(f)
        class_miss.extend(c)
        method_miss.extend(m)

    total = len(class_miss) + len(method_miss)
    if total == 0:
        print("OK: java comment linter pass")
        return 0

    print("WARN: java comment linter found missing javadocs")
    for x in (class_miss + method_miss)[:200]:
        print(f"- {x}")
    if total > 200:
        print(f"... truncated ({total} total)")

    if args.fail_on_missing:
        print("FAIL: missing javadocs (fail-on-missing enabled)")
        return EXIT_FAIL
    return EXIT_WARN


if __name__ == "__main__":
    raise SystemExit(main())
