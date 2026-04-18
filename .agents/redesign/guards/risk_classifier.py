#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Classifier - 风险自动分级

根据变更的文件路径自动判定风险等级，替代人工判断。
当检测到高风险时，建议升级到 @careful 模式。

使用方式：
    python risk_classifier.py --files "src/main/java/OrderMapper.xml,src/main/java/OrderService.java"
    python risk_classifier.py --git  # 从 git diff 获取变更文件
"""

import argparse
import re
import subprocess
import sys
from typing import List, Tuple

# 风险模式配置
RISK_PATTERNS = {
    "HIGH": [
        # 数据库相关
        (r".*Mapper\.xml$", "MyBatis 映射文件"),
        (r".*Repository\.java$", "数据仓库"),
        (r".*\.sql$", "SQL 脚本"),
        (r".*Migration.*\.java$", "数据迁移"),
        (r".*flyway.*", "Flyway 迁移"),
        (r".*liquibase.*", "Liquibase 迁移"),

        # 权限/安全相关
        (r".*Permission.*\.java$", "权限逻辑"),
        (r".*Auth.*\.java$", "认证逻辑"),
        (r".*Security.*\.java$", "安全配置"),
        (r".*Rbac.*\.java$", "RBAC 权限"),
        (r".*DataScope.*\.java$", "数据范围"),

        # 配置相关
        (r"application.*\.ya?ml$", "应用配置"),
        (r"application.*\.properties$", "应用配置"),
        (r"bootstrap.*\.ya?ml$", "启动配置"),

        # 核心基础设施
        (r".*Exception.*\.java$", "异常处理"),
        (r".*Config\.java$", "Spring 配置"),
        (r".*Interceptor\.java$", "拦截器"),
        (r".*Filter\.java$", "过滤器"),
        (r".*Aspect\.java$", "切面"),
    ],

    "MEDIUM": [
        # API 层
        (r".*Controller\.java$", "控制器"),
        (r".*Api\.java$", "API 接口"),
        (r".*Feign.*\.java$", "Feign 客户端"),
        (r".*Client\.java$", "外部客户端"),

        # 业务层
        (r".*Service\.java$", "服务层"),
        (r".*ServiceImpl\.java$", "服务实现"),
        (r".*Manager\.java$", "业务管理器"),

        # 依赖变更
        (r"pom\.xml$", "Maven 依赖"),
        (r"build\.gradle$", "Gradle 依赖"),
    ],

    "LOW": [
        # 测试
        (r".*Test\.java$", "测试代码"),
        (r".*Tests\.java$", "测试代码"),
        (r".*Spec\.java$", "测试规格"),
        (r".*/test/.*", "测试目录"),

        # 数据传输对象
        (r".*DTO\.java$", "数据传输对象"),
        (r".*VO\.java$", "视图对象"),
        (r".*Request\.java$", "请求对象"),
        (r".*Response\.java$", "响应对象"),

        # 文档
        (r".*\.md$", "Markdown 文档"),
        (r".*README.*", "README"),

        # 实体 (通常只是字段增加)
        (r".*Entity\.java$", "实体类"),
        (r".*DO\.java$", "数据对象"),
    ]
}

# 升级到 @careful 的触发条件
CAREFUL_THRESHOLDS = {
    "high_risk_count": 1,      # 任意 1 个高风险文件
    "medium_risk_count": 3,    # 3 个以上中风险文件
    "total_file_count": 10,    # 10 个以上文件变更
}


def classify_file(file_path: str) -> Tuple[str, str]:
    """分类单个文件的风险等级"""
    normalized = file_path.replace("\\", "/")

    for risk_level in ["HIGH", "MEDIUM", "LOW"]:
        for pattern, description in RISK_PATTERNS[risk_level]:
            if re.search(pattern, normalized, re.IGNORECASE):
                return risk_level, description

    return "LOW", "其他文件"


def classify_files(files: List[str]) -> dict:
    """分类一组文件"""
    result = {
        "overall_risk": "LOW",
        "should_upgrade_to_careful": False,
        "upgrade_reasons": [],
        "files": {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        },
        "summary": ""
    }

    for f in files:
        risk_level, description = classify_file(f)
        result["files"][risk_level].append({
            "path": f,
            "description": description
        })

    # 计算总体风险
    high_count = len(result["files"]["HIGH"])
    medium_count = len(result["files"]["MEDIUM"])
    total_count = len(files)

    if high_count > 0:
        result["overall_risk"] = "HIGH"
    elif medium_count > 0:
        result["overall_risk"] = "MEDIUM"
    else:
        result["overall_risk"] = "LOW"

    # 判断是否需要升级到 @careful
    if high_count >= CAREFUL_THRESHOLDS["high_risk_count"]:
        result["should_upgrade_to_careful"] = True
        result["upgrade_reasons"].append(
            f"检测到 {high_count} 个高风险文件变更"
        )

    if medium_count >= CAREFUL_THRESHOLDS["medium_risk_count"]:
        result["should_upgrade_to_careful"] = True
        result["upgrade_reasons"].append(
            f"检测到 {medium_count} 个中风险文件变更"
        )

    if total_count >= CAREFUL_THRESHOLDS["total_file_count"]:
        result["should_upgrade_to_careful"] = True
        result["upgrade_reasons"].append(
            f"变更文件数量达到 {total_count} 个"
        )

    # 生成摘要
    result["summary"] = (
        f"风险等级: {result['overall_risk']} | "
        f"HIGH: {high_count}, MEDIUM: {medium_count}, LOW: {len(result['files']['LOW'])}"
    )

    return result


def get_git_changed_files() -> List[str]:
    """从 git diff 获取变更文件列表"""
    files = []

    # 未暂存的变更
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if out:
            files.extend(out.splitlines())
    except Exception:
        pass

    # 已暂存的变更
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "--cached"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if out:
            files.extend(out.splitlines())
    except Exception:
        pass

    # 去重
    return list(set(files))


def print_report(result: dict) -> None:
    """打印分析报告"""
    print("=" * 60)
    print("风险分析报告")
    print("=" * 60)
    print(f"总体风险: {result['overall_risk']}")
    print(f"文件统计: HIGH={len(result['files']['HIGH'])}, "
          f"MEDIUM={len(result['files']['MEDIUM'])}, "
          f"LOW={len(result['files']['LOW'])}")
    print()

    if result["should_upgrade_to_careful"]:
        print("[!] 建议升级到 @careful 模式")
        for reason in result["upgrade_reasons"]:
            print(f"    - {reason}")
        print()

    # 详细列表
    for level in ["HIGH", "MEDIUM"]:
        if result["files"][level]:
            print(f"[{level}] 文件:")
            for f in result["files"][level]:
                print(f"  - {f['path']} ({f['description']})")
            print()

    if result["overall_risk"] == "LOW" and not result["should_upgrade_to_careful"]:
        print("[OK] 变更风险较低，可以继续执行")


def main():
    parser = argparse.ArgumentParser(description="风险自动分级")
    parser.add_argument("--files", help="逗号分隔的文件列表")
    parser.add_argument("--git", action="store_true", help="从 git diff 获取文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    # 获取文件列表
    if args.git:
        files = get_git_changed_files()
    elif args.files:
        files = [f.strip() for f in args.files.split(",") if f.strip()]
    else:
        print("错误: 请指定 --files 或 --git")
        sys.exit(1)

    if not files:
        print("OK: 没有检测到文件变更")
        sys.exit(0)

    # 分析
    result = classify_files(files)

    # 输出
    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)

    # 退出码
    if result["should_upgrade_to_careful"]:
        sys.exit(1)  # 建议升级
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
