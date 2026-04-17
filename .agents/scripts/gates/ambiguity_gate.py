#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ambiguity Gate (Deterministic)

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    t = _normalize(text)
    return any(k in t for k in keywords)


def _check_intent(intent: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    t = _normalize(intent)
    if not t:
        return EXIT_FAIL, ["intent is empty"]

    object_signals = [
        "api", "接口", "表", "schema", "rbac", "权限", "菜单", "登录", "鉴权", "datascope", "组织", "部门",
        "agent", "agents", "workflow", "流程", "hook", "hooks", "gate", "gates", "role", "roles", "matrix",
        "wiki", "wal", "lifecycle", "router"
    ]
    action_signals = ["设计", "实现", "修复", "新增", "改造", "优化", "落地", "上线", "测试"]
    success_signals = ["验收", "通过", "可用", "跑通", "门禁", "测试用例", "接口返回", "deliver", "wiki", "文档"]

    has_object = _has_any(t, object_signals)
    has_action = _has_any(t, action_signals)
    has_success = _has_any(t, success_signals)

    if not has_action:
        reasons.append("missing action signal")
    if not has_object:
        reasons.append("missing object signal")
    if not has_success:
        reasons.append("missing success/evidence signal")

    if has_action and has_object:
        if has_success:
            return 0, []
        return EXIT_WARN, reasons
    return EXIT_FAIL, reasons


def _check_anchors_file(path: str) -> tuple[int, list[str]]:
    if not path:
        return 0, []
    if not os.path.exists(path):
        return EXIT_FAIL, [f"anchors file not found: {path}"]

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "## Core Context Anchors" not in content:
        return EXIT_FAIL, ["missing section: ## Core Context Anchors"]

    required_markers = [
        "Business", "业务", "API", "接口", "Rules", "规则", "Risk", "风险", "Evidence", "证据"
    ]
    present = sum(1 for m in required_markers if m in content)
    if present < 2:
        return EXIT_WARN, ["anchors are too thin (<2 required markers)"]
    return 0, []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True)
    parser.add_argument("--anchors-file", default="")
    args = parser.parse_args()

    code1, reasons1 = _check_intent(args.intent)
    code2, reasons2 = _check_anchors_file(args.anchors_file)

    code = max(code1, code2)
    reasons = reasons1 + reasons2

    if code == 0:
        print("OK: ambiguity gate pass")
        return 0
    if code == EXIT_WARN:
        print("WARN: ambiguity gate")
        for r in reasons:
            print(f"- {r}")
        return EXIT_WARN
    print("FAIL: ambiguity gate")
    for r in reasons:
        print(f"- {r}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
