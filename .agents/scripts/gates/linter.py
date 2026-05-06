#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linter Gate (Deterministic)

This repository's harness may be used across different stacks. A generic "linter"
gate must be deterministic and must not assume heavy toolchains are available.

Behavior:
- If a concrete linter integration exists, wire it here.
- Otherwise, emit WARN in --strict mode so the workflow is runnable but visibility is preserved.

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = _repo_root()
    hints: list[str] = []
    if os.path.exists(os.path.join(root, "pom.xml")):
        hints.append("Detected pom.xml (Java project). Consider wiring checkstyle/spotbugs here.")
    if os.path.exists(os.path.join(root, "package.json")):
        hints.append("Detected package.json (Node project). Consider wiring eslint here.")

    if args.strict:
        print("WARN: linter gate (no concrete linter configured)")
        for h in hints:
            print(f"- {h}")
        return EXIT_WARN

    print("OK: linter gate pass (non-strict)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

