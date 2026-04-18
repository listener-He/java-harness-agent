"""
migration_gate.py — 数据库 Migration 安全检查

在 Phase 3 Review 中，当检测到 Migration 相关变更时自动触发。
验证 openspec.md 包含必要的安全检查章节。

用法：
    python3 .agents/scripts/gates/migration_gate.py --spec path/to/openspec.md [--strict]

退出码：
    0 = PASS
    1 = FAIL（缺少必要的安全检查）
"""

import argparse
import sys
import re
from pathlib import Path

REQUIRED_CHECKLIST_ITEMS = [
    ("回滚 SQL", r"回滚.{0,20}(SQL|sql|已编写|存在)", "必须提供回滚 SQL 或回滚方案"),
    ("测试验证", r"(测试库|沙箱|staging).{0,30}(验证|通过|执行)", "必须在非生产环境验证过 Migration"),
    ("执行时长", r"(预计|执行).{0,20}(时长|时间|分钟|秒)", "必须评估 Migration 执行时长"),
    ("在线影响", r"(停机|灰度|在线|锁表|影响流量|zero.downtime|不影响)", "必须说明是否影响在线流量"),
]

MIGRATION_RISK_SECTION = [
    r"migration.{0,20}安全",
    r"数据库.{0,20}(安全|风险|检查)",
    r"Migration.{0,10}Safety",
    r"Schema.{0,10}(Change|变更).{0,10}(Plan|计划|方案)",
]


def find_section(content: str, patterns: list) -> bool:
    """检查内容中是否存在匹配某类模式的章节"""
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_checklist_item(content: str, item_name: str, pattern: str) -> bool:
    return bool(re.search(pattern, content, re.IGNORECASE | re.DOTALL))


def main():
    parser = argparse.ArgumentParser(description="Migration Gate")
    parser.add_argument("--spec", required=True, help="openspec.md 路径")
    parser.add_argument("--strict", action="store_true", help="严格模式：所有检查项必须通过")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"[FAIL] openspec.md 不存在: {spec_path}", file=sys.stderr)
        sys.exit(1)

    content = spec_path.read_text(encoding="utf-8")
    failures = []
    warnings = []

    # 检查是否有 Migration 安全检查章节
    if not find_section(content, MIGRATION_RISK_SECTION):
        failures.append("openspec.md 缺少 'Migration 安全检查' 章节 —— 请在 Propose 阶段添加")

    # 检查各 checklist 项
    for item_name, pattern, description in REQUIRED_CHECKLIST_ITEMS:
        if not check_checklist_item(content, item_name, pattern):
            if args.strict:
                failures.append(f"缺少 [{item_name}]：{description}")
            else:
                warnings.append(f"建议补充 [{item_name}]：{description}")

    # 输出结果
    if failures:
        print("[Migration Gate] FAIL")
        for f in failures:
            print(f"  [✗] {f}")
        if warnings:
            print()
            for w in warnings:
                print(f"  [⚠] {w}")
        print()
        print("Migration 变更必须通过安全检查才能进入 Phase 4 Implement。", file=sys.stderr)
        sys.exit(1)
    elif warnings:
        print("[Migration Gate] WARN")
        for w in warnings:
            print(f"  [⚠] {w}")
        print()
        print("[Migration Gate] 存在警告，请确认后继续。Agent 需在交付说明中解释为何跳过。")
        sys.exit(0)
    else:
        print(f"[Migration Gate] PASS — Migration 安全检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
