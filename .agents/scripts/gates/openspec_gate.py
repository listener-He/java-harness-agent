#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSpec Gate (Deterministic)

Validates that an OpenSpec exists and conforms to the schema checker.

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import subprocess
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _schema_checker_path() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "wiki", "schema_checker.py"))


def _run_schema_checker(openspec_path: str) -> tuple[int, list[str]]:
    checker = _schema_checker_path()
    if not os.path.exists(checker):
        return EXIT_WARN, [f"schema checker missing: {checker}"]

    proc = subprocess.run(
        [sys.executable, checker, openspec_path],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    details: list[str] = []
    if out:
        details.append(out)
    if err:
        details.append(err)
    if proc.returncode == 0:
        return 0, []
    return EXIT_FAIL, ["schema check failed"] + details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require", required=True)
    args = parser.parse_args()

    path = args.require
    if not os.path.exists(path):
        print("FAIL: openspec gate")
        print(f"- openspec not found: {path}")
        return EXIT_FAIL

    code, details = _run_schema_checker(path)
    if code == 0:
        print("OK: openspec gate pass")
        return 0
    if code == EXIT_WARN:
        print("WARN: openspec gate")
        for d in details:
            print(f"- {d}")
        return EXIT_WARN
    print("FAIL: openspec gate")
    for d in details:
        print(f"- {d}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())

