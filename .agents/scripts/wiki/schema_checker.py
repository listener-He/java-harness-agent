#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约防腐体检工具 (Schema Checker)
Agent 在生成 <YYYY-MM-DD>_<slug>_openspec.md 后，可选调用此脚本检查关键结构是否缺失。
"""

import os
import sys
import re

EXIT_FAIL = 2

SLIM_MARKER_PATTERN = re.compile(r"^\s*spec_mode\s*:\s*SLIM\s*$", re.IGNORECASE | re.MULTILINE)

FULL_REQUIRED_HEADERS = [
    (re.compile(r"#+\s+.*(API|接口).*", re.IGNORECASE), "API 契约模块"),
    (re.compile(r"#+\s+.*(数据|模型|表结构|Data Model).*", re.IGNORECASE), "数据模型模块"),
    (re.compile(r"#+\s+.*(BDD|验收|Acceptance Criteria).*", re.IGNORECASE), "验收标准模块"),
]

SLIM_REQUIRED_HEADERS = [
    (re.compile(r"#+\s+.*(变更摘要|Change Summary).*", re.IGNORECASE), "变更摘要"),
    (re.compile(r"#+\s+.*(影响面|Scope of Change).*", re.IGNORECASE), "影响面清单"),
    (re.compile(r"#+\s+.*(风险|回滚|Rollback).*", re.IGNORECASE), "风险与回滚"),
    (re.compile(r"#+\s+.*(验证|证据|Verification|Evidence).*", re.IGNORECASE), "验证与证据"),
]

def check_schema(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"📊 === 契约文件体检: {file_path} ===")

    is_slim = bool(SLIM_MARKER_PATTERN.search(content))
    if is_slim:
        print("模式: SLIM")
        required = SLIM_REQUIRED_HEADERS
    else:
        print("模式: FULL")
        required = FULL_REQUIRED_HEADERS

    fail_items = []
    for pattern, name in required:
        if not pattern.search(content):
            fail_items.append(name)

    if fail_items:
        print("发现项:")
        for item in fail_items:
            print(f"  - [FAIL] 缺失: {item}")
    else:
        print("关键结构: ✅ OK")

    warn_items = []
    if not is_slim and "```json" not in content:
        warn_items.append("未发现 ```json 代码块")
        print("发现项:")
        print("  - [WARN] 未发现 ```json 代码块")
    elif not is_slim:
        print("JSON Example: ✅ OK")

    if fail_items:
        print("\n结论: ❌ FAIL")
        return EXIT_FAIL
    if warn_items:
        print("\n结论: ⚠️ WARN")
        return 0
    print("\n结论: ✅ OK")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schema_checker.py <path_to_<YYYY-MM-DD>_<slug>_openspec.md>")
        sys.exit(1)
    raise SystemExit(check_schema(sys.argv[1]))
