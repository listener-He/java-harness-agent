#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAL Compactor (WAL -> Index)
Tool to merge fragmented markdown files in llm_wiki/wiki/*/wal into the corresponding domain's index.md.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


WIKI_ROOT = ".agents/llm_wiki"

def _get_all_wal_dirs():
    """Dynamically discover all 'wal' directories recursively under the wiki root."""
    wal_dirs = []
    if os.path.exists(WIKI_ROOT):
        for root, dirs, files in os.walk(WIKI_ROOT):
            if "wal" in dirs:
                wal_dir_path = os.path.join(root, "wal")
                wal_dirs.append(wal_dir_path)
    return wal_dirs

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


def _merge_wal_dir(wal_dir):
    domain_dir = os.path.dirname(wal_dir)
    domain_name = os.path.basename(domain_dir)
    index_file = os.path.join(domain_dir, "index.md")

    if not os.path.exists(index_file):
        return [], False # Skip if index doesn't exist

    fragments = []
    # Use rglob to recursively find .md files inside wal_dir and its subdirectories
    for path in Path(wal_dir).rglob("*.md"):
        if "applied" not in path.parts:
            fragments.append(str(path))
            
    fragments = sorted(fragments)
    if not fragments:
        return [], False

    # Check capacity threshold before compaction
    current_lines = _get_line_count(index_file)
    if current_lines >= REFACTOR_THRESHOLD_LINES:
        print(f"⚠️  [NEEDS_REFACTOR] {index_file} has {current_lines} lines (>= {REFACTOR_THRESHOLD_LINES}).")
        print(f"    Compaction aborted for domain '{domain_name}'. Please mount the 'Knowledge Architect' role to refactor and split the index.")
        return [], True

    applied_dir = os.path.join(wal_dir, "applied")
    os.makedirs(applied_dir, exist_ok=True)

    merged = []
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n\n---\n\n## WAL Compaction - {domain_name} - {stamp}\n"
    _append_to_file(index_file, header)

    for frag in fragments:
        content = _ensure_newline(_read_text(frag)).strip("\n")
        
        # Calculate a flattened unique name if it was in a sub-folder to prevent overwriting
        # e.g. wal/bugs/123.md -> bugs_123.md
        rel_path = os.path.relpath(frag, wal_dir)
        safe_name = rel_path.replace(os.sep, "_")
        dest_path = os.path.join(applied_dir, safe_name)
        
        if not content.strip():
            shutil.move(frag, dest_path)
            continue
            
        block = f"\n\n### {rel_path}\n\n{content}\n"
        _append_to_file(index_file, block)
        shutil.move(frag, dest_path)
        merged.append(frag)

    return merged, False


def main():
    merged_all = []
    needs_refactor = False
    
    wal_dirs = _get_all_wal_dirs()
    
    for wal_dir in wal_dirs:
        merged, refactor_flag = _merge_wal_dir(wal_dir)
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
