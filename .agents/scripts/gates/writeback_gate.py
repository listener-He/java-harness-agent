#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write-back Gate (WAL presence check)

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import glob
import os
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

WIKI_ROOT = ".agents/llm_wiki/wiki"


def _find(pattern: str) -> list[str]:
    return [os.path.normpath(p) for p in glob.glob(pattern, recursive=True)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True, help="YYYYMMDD")
    parser.add_argument("--require-data", action="store_true", help="Require data WAL as well")
    parser.add_argument("--require", action="append", default=[], help="Wal types: domain,api,rules,data,architecture")
    args = parser.parse_args()

    topic = args.topic.strip().lower().replace(" ", "_")
    date = args.date.strip()

    required_types = [x.strip().lower() for x in (args.require or []) if x and x.strip()]
    if not required_types:
        required_types = ["domain", "api", "rules"]
    if args.require_data and "data" not in required_types:
        required_types.append("data")

    required = []
    for t in required_types:
        if t == "domain":
            required.append((f"{WIKI_ROOT}/domain/wal/{date}_{topic}_domain_append.md", "domain WAL"))
        elif t == "api":
            required.append((f"{WIKI_ROOT}/api/wal/{date}_{topic}_api_append.md", "api WAL"))
        elif t == "rules":
            required.append((f"{WIKI_ROOT}/domain/wal/{date}_{topic}_rules_append.md", "rules WAL"))
        elif t == "data":
            required.append((f"{WIKI_ROOT}/data/wal/{date}_{topic}_data_append.md", "data WAL"))
        elif t == "architecture":
            required.append((f"{WIKI_ROOT}/architecture/wal/{date}_{topic}_*append.md", "architecture WAL (glob)"))
        else:
            print(f"WARN: unknown require type: {t}")

    missing = []
    for path, label in required:
        if "*" in path:
            if not _find(path):
                missing.append((label, path))
        else:
            if not os.path.exists(path):
                missing.append((label, path))

    if missing:
        print("FAIL: missing required WAL files")
        for label, path in missing:
            print(f"- {label}: {path}")
        return EXIT_FAIL

    extra = _find(f"{WIKI_ROOT}/**/wal/{date}_{topic}_*.md")
    if not extra:
        print("WARN: no WAL files matched topic/date")
        return EXIT_WARN

    print("OK: write-back gate pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
