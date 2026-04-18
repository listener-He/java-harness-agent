#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Logger - 审计日志

轻量级记录器，在任务完成后记录关键信息。
不阻塞流程，仅供事后审计。

使用方式：
    python audit_logger.py log --mode quick --task "修复登录按钮样式"
    python audit_logger.py log --mode standard --task "新增订单导出功能" --files "OrderController.java,OrderService.java"
    python audit_logger.py log --mode careful --task "添加数据权限" --spec "spec_20240101.md"
    python audit_logger.py list
    python audit_logger.py list --last 10
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from typing import List, Optional

AUDIT_DIR = ".agents/redesign/audit"
AUDIT_FILE = f"{AUDIT_DIR}/audit_log.jsonl"


def _ensure_dir():
    os.makedirs(AUDIT_DIR, exist_ok=True)


def _get_git_info() -> dict:
    """获取当前 git 信息"""
    info = {
        "branch": "",
        "commit": "",
        "changed_files": []
    }

    try:
        info["branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        pass

    try:
        info["commit"] = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if out:
            info["changed_files"] = out.splitlines()
    except Exception:
        pass

    return info


def log_task(
    mode: str,
    task: str,
    files: Optional[List[str]] = None,
    spec: Optional[str] = None,
    risk_level: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """记录一次任务"""
    _ensure_dir()

    git_info = _get_git_info()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "task": task,
        "files": files or git_info["changed_files"],
        "file_count": len(files) if files else len(git_info["changed_files"]),
        "spec": spec,
        "risk_level": risk_level,
        "notes": notes,
        "git": git_info
    }

    # 追加到日志文件
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def list_logs(last_n: int = 20) -> List[dict]:
    """列出最近的日志"""
    if not os.path.exists(AUDIT_FILE):
        return []

    logs = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    return logs[-last_n:]


def print_logs(logs: List[dict]) -> None:
    """打印日志列表"""
    if not logs:
        print("暂无审计日志")
        return

    print("=" * 70)
    print("审计日志")
    print("=" * 70)

    for entry in logs:
        ts = entry.get("timestamp", "")[:19]
        mode = entry.get("mode", "?")
        task = entry.get("task", "")[:40]
        file_count = entry.get("file_count", 0)
        risk = entry.get("risk_level", "")

        mode_badge = {
            "quick": "[Q]",
            "standard": "[S]",
            "careful": "[C]"
        }.get(mode, "[?]")

        risk_badge = {
            "HIGH": "(!)",
            "MEDIUM": "(*)",
            "LOW": ""
        }.get(risk, "")

        print(f"{ts} {mode_badge}{risk_badge} {task} ({file_count} files)")

    print()
    print(f"共 {len(logs)} 条记录")


def generate_summary(days: int = 7) -> dict:
    """生成汇总报告"""
    from datetime import timedelta

    logs = list_logs(last_n=1000)
    cutoff = datetime.now() - timedelta(days=days)

    recent = []
    for log in logs:
        try:
            ts = datetime.fromisoformat(log["timestamp"])
            if ts >= cutoff:
                recent.append(log)
        except Exception:
            pass

    summary = {
        "period": f"最近 {days} 天",
        "total_tasks": len(recent),
        "by_mode": {
            "quick": 0,
            "standard": 0,
            "careful": 0
        },
        "by_risk": {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        },
        "total_files_changed": 0
    }

    for log in recent:
        mode = log.get("mode", "")
        if mode in summary["by_mode"]:
            summary["by_mode"][mode] += 1

        risk = log.get("risk_level", "")
        if risk in summary["by_risk"]:
            summary["by_risk"][risk] += 1

        summary["total_files_changed"] += log.get("file_count", 0)

    return summary


def main():
    parser = argparse.ArgumentParser(description="审计日志")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # log 子命令
    log_p = subparsers.add_parser("log", help="记录任务")
    log_p.add_argument("--mode", required=True, choices=["quick", "standard", "careful"])
    log_p.add_argument("--task", required=True, help="任务描述")
    log_p.add_argument("--files", help="变更文件列表 (逗号分隔)")
    log_p.add_argument("--spec", help="spec 文件路径")
    log_p.add_argument("--risk", choices=["HIGH", "MEDIUM", "LOW"])
    log_p.add_argument("--notes", help="备注")

    # list 子命令
    list_p = subparsers.add_parser("list", help="列出日志")
    list_p.add_argument("--last", type=int, default=20, help="显示最近 N 条")

    # summary 子命令
    summary_p = subparsers.add_parser("summary", help="生成汇总")
    summary_p.add_argument("--days", type=int, default=7, help="统计天数")

    args = parser.parse_args()

    if args.command == "log":
        files = None
        if args.files:
            files = [f.strip() for f in args.files.split(",") if f.strip()]

        entry = log_task(
            mode=args.mode,
            task=args.task,
            files=files,
            spec=args.spec,
            risk_level=args.risk,
            notes=args.notes
        )
        print(f"OK: 已记录 ({entry['timestamp'][:19]})")

    elif args.command == "list":
        logs = list_logs(args.last)
        print_logs(logs)

    elif args.command == "summary":
        summary = generate_summary(args.days)
        print(f"统计周期: {summary['period']}")
        print(f"总任务数: {summary['total_tasks']}")
        print(f"按模式: quick={summary['by_mode']['quick']}, "
              f"standard={summary['by_mode']['standard']}, "
              f"careful={summary['by_mode']['careful']}")
        print(f"按风险: HIGH={summary['by_risk']['HIGH']}, "
              f"MEDIUM={summary['by_risk']['MEDIUM']}, "
              f"LOW={summary['by_risk']['LOW']}")
        print(f"总变更文件: {summary['total_files_changed']}")


if __name__ == "__main__":
    main()
