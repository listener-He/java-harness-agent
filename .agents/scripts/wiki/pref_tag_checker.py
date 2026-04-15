#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
偏好规则标签体检工具 (Preference Tag Checker)
Agent 可以调用此工具来检查 `preferences/index.md` 里的规则是否遵循了 `[Tag]` 前缀规范。
"""

import os
import sys
import re

DEFAULT_PREF_FILE = ".agents/llm_wiki/wiki/preferences/index.md"

def check_tags(file_path=DEFAULT_PREF_FILE):
    if not os.path.exists(file_path):
        print(f"ℹ️ 偏好文件尚未创建: {file_path}，跳过检查。")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"📊 === 偏好标签规范检查: {file_path} ===")
    
    # 匹配 Markdown 列表项，例如 "- [Global] xxx" 或 "* [Trade] xxx"
    list_pattern = re.compile(r'^\s*[-*]\s+(.*)')
    tag_pattern = re.compile(r'^\[.*?\]')
    
    unTagged_rules = []
    total_rules = 0

    for idx, line in enumerate(lines):
        match = list_pattern.match(line)
        if match:
            total_rules += 1
            rule_content = match.group(1)
            if not tag_pattern.match(rule_content):
                unTagged_rules.append((idx + 1, line.strip()))

    print(f"共发现 {total_rules} 条规则。")
    
    if unTagged_rules:
        print("⚠️  发现未打标签的规则 (建议格式: - [标签] 规则内容):")
        for line_num, content in unTagged_rules:
            print(f"  - 第 {line_num} 行: {content}")
    else:
        if total_rules > 0:
            print("✅ 所有规则均已规范打标！")
        else:
            print("ℹ️ 尚未记录任何规则。")

    print("\n💡 提示: 规范的标签 (如 [Global], [API]) 有助于 Agent 在上下文漏斗中更精准地 Grep 检索。")

if __name__ == "__main__":
    file_to_check = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PREF_FILE
    check_tags(file_to_check)
