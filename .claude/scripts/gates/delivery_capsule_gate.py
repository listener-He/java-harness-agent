#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delivery Capsule Gate

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


REQUIRED_SECTIONS = [
    "## Business Domain",
    "## API Domain",
    "## Rules Domain",
    "## Evidence",
    "## Wiki Write-back",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"FAIL: delivery capsule not found: {args.file}")
        return EXIT_FAIL

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing:
        print("FAIL: delivery capsule missing required sections")
        for s in missing:
            print(f"- {s}")
        return EXIT_FAIL

    if "## Data Domain" not in content:
        print("WARN: delivery capsule has no data domain section (ok if no schema change)")
        return EXIT_WARN

    print("OK: delivery capsule gate pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
