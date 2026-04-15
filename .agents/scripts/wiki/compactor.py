#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAL 碎片合并器 (WAL -> Index)
可选工具：把 llm_wiki/wiki/*/wal 下的碎片文件合并进对应域 index.md。
"""

import os
import glob
from datetime import datetime


WIKI_ROOT = ".agents/llm_wiki/wiki"
DOMAINS = ["api", "data", "domain", "architecture"]


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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
        return []
    if not os.path.exists(index_file):
        raise FileNotFoundError(index_file)

    fragments = sorted(glob.glob(os.path.join(wal_dir, "*.md")))
    if not fragments:
        return []

    applied_dir = os.path.join(wal_dir, "applied")
    os.makedirs(applied_dir, exist_ok=True)

    merged = []
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n\n---\n\n## WAL 合并记录 - {domain} - {stamp}\n"
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

    return merged


def main():
    merged_all = []
    for d in DOMAINS:
        merged_all.extend(_merge_domain(d))
    if not merged_all:
        print("ℹ️ 没有可合并的 WAL 碎片。")
        return
    print("✅ 已合并碎片文件：")
    for f in merged_all:
        print(f"- {f}")


if __name__ == "__main__":
    main()
