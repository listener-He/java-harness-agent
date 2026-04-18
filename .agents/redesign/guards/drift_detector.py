#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drift Detector - 注意力漂移检测器

替代原有的硬预算约束 (wiki=3, code=8)，改用智能检测。
Agent 在每次读取文件后调用此模块评估搜索效率。

设计理念：
- 不预设硬上限
- 检测搜索收益递减
- 检测循环读取模式
- 建议而非强制停止

使用方式：
    python drift_detector.py record <file_path> <gained:true|false>
    python drift_detector.py check
    python drift_detector.py reset
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

STATE_FILE = ".agents/redesign/guards/.drift_state.json"

# 阈值配置 (可调整)
CONFIG = {
    "consecutive_no_gain_limit": 3,    # 连续无收益次数上限
    "total_reads_soft_limit": 15,      # 总读取软上限
    "efficiency_threshold": 0.3,       # 效率阈值 (有效读取/总读取)
    "loop_detection_window": 6,        # 循环检测窗口
    "loop_unique_threshold": 2,        # 窗口内唯一文件数阈值
}


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return _empty_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _empty_state()


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _empty_state() -> dict:
    return {
        "session_start": datetime.now().isoformat(),
        "reads": [],
        "useful_reads": 0,
        "consecutive_no_gain": 0,
    }


def record_read(file_path: str, gained: bool) -> dict:
    """记录一次文件读取"""
    state = _load_state()
    state["reads"].append({
        "file": file_path,
        "gained": gained,
        "time": datetime.now().isoformat()
    })

    if gained:
        state["useful_reads"] += 1
        state["consecutive_no_gain"] = 0
    else:
        state["consecutive_no_gain"] += 1

    _save_state(state)
    return check_drift(state)


def check_drift(state: Optional[dict] = None) -> dict:
    """检查当前搜索状态"""
    if state is None:
        state = _load_state()

    result = {
        "should_stop": False,
        "severity": "OK",
        "reason": "",
        "stats": {
            "total_reads": len(state["reads"]),
            "useful_reads": state["useful_reads"],
            "consecutive_no_gain": state["consecutive_no_gain"],
            "efficiency": 0.0 if len(state["reads"]) == 0 else state["useful_reads"] / len(state["reads"])
        },
        "suggestions": []
    }

    # 检查 1: 连续无收益
    if state["consecutive_no_gain"] >= CONFIG["consecutive_no_gain_limit"]:
        result["should_stop"] = True
        result["severity"] = "WARN"
        result["reason"] = f"连续 {state['consecutive_no_gain']} 次读取无新收益"
        result["suggestions"].append("建议停止搜索，用已有信息开始执行")

    # 检查 2: 总读取过多且效率低
    total = len(state["reads"])
    if total > CONFIG["total_reads_soft_limit"]:
        efficiency = result["stats"]["efficiency"]
        if efficiency < CONFIG["efficiency_threshold"]:
            result["should_stop"] = True
            result["severity"] = "FAIL"
            result["reason"] = f"已读取 {total} 个文件，但有效率仅 {efficiency:.1%}"
            result["suggestions"].append("搜索效率过低，请重新聚焦目标")
            result["suggestions"].append("考虑向用户确认搜索方向是否正确")

    # 检查 3: 循环读取
    if _detect_loop(state):
        result["should_stop"] = True
        result["severity"] = "WARN"
        result["reason"] = "检测到循环读取相同文件"
        result["suggestions"].append("请总结已知信息，不要继续重复读取")

    return result


def _detect_loop(state: dict) -> bool:
    """检测是否在循环读取"""
    reads = state["reads"]
    window = CONFIG["loop_detection_window"]
    threshold = CONFIG["loop_unique_threshold"]

    if len(reads) < window:
        return False

    recent_files = [r["file"] for r in reads[-window:]]
    unique_files = len(set(recent_files))

    return unique_files <= threshold


def reset_state() -> None:
    """重置状态 (新任务开始时调用)"""
    _save_state(_empty_state())


def print_status() -> None:
    """打印当前状态"""
    state = _load_state()
    result = check_drift(state)

    print("=" * 50)
    print("搜索状态报告")
    print("=" * 50)
    print(f"总读取: {result['stats']['total_reads']} 个文件")
    print(f"有效读取: {result['stats']['useful_reads']} 个")
    print(f"效率: {result['stats']['efficiency']:.1%}")
    print(f"连续无收益: {result['stats']['consecutive_no_gain']} 次")
    print()

    if result["should_stop"]:
        print(f"[{result['severity']}] {result['reason']}")
        for s in result["suggestions"]:
            print(f"  - {s}")
    else:
        print("[OK] 搜索状态正常")

    # 最近读取的文件
    if state["reads"]:
        print()
        print("最近读取:")
        for r in state["reads"][-5:]:
            gained = "+" if r["gained"] else "-"
            print(f"  [{gained}] {r['file']}")


def main():
    parser = argparse.ArgumentParser(description="注意力漂移检测器")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # record 子命令
    record_p = subparsers.add_parser("record", help="记录一次文件读取")
    record_p.add_argument("file_path", help="读取的文件路径")
    record_p.add_argument("gained", choices=["true", "false"], help="是否有收获")

    # check 子命令
    subparsers.add_parser("check", help="检查当前搜索状态")

    # reset 子命令
    subparsers.add_parser("reset", help="重置状态")

    # status 子命令
    subparsers.add_parser("status", help="打印详细状态")

    args = parser.parse_args()

    if args.command == "record":
        gained = args.gained.lower() == "true"
        result = record_read(args.file_path, gained)

        if result["should_stop"]:
            print(f"[{result['severity']}] {result['reason']}")
            for s in result["suggestions"]:
                print(f"  - {s}")
            sys.exit(1 if result["severity"] == "WARN" else 2)
        else:
            print("OK")

    elif args.command == "check":
        result = check_drift()
        if result["should_stop"]:
            print(f"[{result['severity']}] {result['reason']}")
            sys.exit(1 if result["severity"] == "WARN" else 2)
        else:
            print("OK: 搜索状态正常")

    elif args.command == "reset":
        reset_state()
        print("OK: 状态已重置")

    elif args.command == "status":
        print_status()


if __name__ == "__main__":
    main()
