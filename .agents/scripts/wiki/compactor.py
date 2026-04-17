#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAL Compactor (WAL -> Index)
Tool to merge fragmented markdown files in llm_wiki/wiki/*/wal into the corresponding domain's index.md.
"""

import os
import glob
import sys
from datetime import datetime


WIKI_ROOT = ".agents/llm_wiki/wiki"
DOMAINS = ["api", "data", "domain", "architecture", "rules", "specs", "preferences"]
REFACTOR_THRESHOLD_LINES = 400


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_line_count(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def _append_to_file(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def _ensure_newline(text):
    if not text.endswith("\n"):
        return text + "\n"
    return text


def _merge_domain(domain):
    domain_dir = os.path.join(WIKI_ROOT, domain)
    wal_dir = os.path.join(domain_dir, "wal")
    index_file = os.path.join(domain_dir, "index.md")

    if not os.path.exists(wal_dir):
        return [], False
    if not os.path.exists(index_file):
        return [], False # Skip if index doesn't exist

    fragments = sorted(glob.glob(os.path.join(wal_dir, "*.md")))
    if not fragments:
        return [], False

    # Check capacity threshold before compaction
    current_lines = _get_line_count(index_file)
    if current_lines >= REFACTOR_THRESHOLD_LINES:
        print(f"⚠️  [NEEDS_REFACTOR] {index_file} has {current_lines} lines (>= {REFACTOR_THRESHOLD_LINES}).")
        print(f"    Compaction aborted for domain '{domain}'. Please mount the 'Knowledge Architect' role to refactor and split the index.")
        return [], True

    applied_dir = os.path.join(wal_dir, "applied")
    os.makedirs(applied_dir, exist_ok=True)

    merged = []
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n\n---\n\n## WAL Compaction - {domain} - {stamp}\n"
    _append_to_file(index_file, header)

    for frag in fragments:
        content = _ensure_newline(_read_text(frag)).strip("\n")
        if not content.strip():
            os.rename(frag, os.path.join(applied_dir, os.path.basename(frag)))
            continue
        block = f"\n\n### {os.path.basename(frag)}\n\n{content}\n"
        _append_to_file(index_file, block)
        os.rename(frag, os.path.join(applied_dir, os.path.basename(frag)))
        merged.append(frag)

    return merged, False


def main():
    merged_all = []
    needs_refactor = False
    
    for d in DOMAINS:
        merged, refactor_flag = _merge_domain(d)
        merged_all.extend(merged)
        if refactor_flag:
            needs_refactor = True
            
    if needs_refactor:
        print("\n❌ Compaction halted due to capacity limits. Triggering Auto-Refactoring Flow.")
        sys.exit(2)  # Exit code 2 signals the Runner to trigger Knowledge Architect
        
    if not merged_all:
        print("ℹ️ No WAL fragments found to compact.")
        return
        
    print("✅ Compacted the following WAL fragments:")
    for f in merged_all:
        print(f"- {f}")


if __name__ == "__main__":
    main()
