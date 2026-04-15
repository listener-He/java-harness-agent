#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约防腐体检工具 (Schema Checker)
Agent 在生成 openspec.md 后，可选调用此脚本检查关键结构是否缺失。
"""

import os
import sys
import re

def check_schema(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"📊 === 契约文件体检: {file_path} ===")
    
    # 必备标题检查
    required_headers = [
        (r'#+\s+.*(API|接口).*', "API 契约模块"),
        (r'#+\s+.*(数据|模型|表结构).*', "数据模型模块"),
        (r'#+\s+.*BDD.*', "BDD 验收标准")
    ]
    
    missing_headers = []
    for pattern, name in required_headers:
        if not re.search(pattern, content, re.IGNORECASE):
            missing_headers.append(name)
            
    if missing_headers:
        print("⚠️  发现缺失关键结构:")
        for m in missing_headers:
            print(f"  - 找不到与 '{m}' 相关的标题结构")
    else:
        print("✅ 关键标题结构完整")

    # 代码块检查
    if "```json" not in content:
        print("⚠️  警告: 文件中未发现 ```json 代码块，前端/QA 可能缺乏可用的 Mock 数据。")
    else:
        print("✅ 包含 JSON 数据样例")
        
    print("\n💡 提示: 这是一个可选的防呆检查，请 Agent 根据具体业务判断是否需要补充。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schema_checker.py <path_to_openspec.md>")
        sys.exit(1)
    check_schema(sys.argv[1])
