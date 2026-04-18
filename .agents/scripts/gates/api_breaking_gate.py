"""
api_breaking_gate.py — 破坏性 API 变更检查

当检测到 Controller 签名变更、RequestBody 字段删除/重命名、HTTP 状态码变更时触发。
验证 openspec.md 包含下游影响分析和版本策略。

用法：
    python3 .agents/scripts/gates/api_breaking_gate.py --spec path/to/openspec.md

退出码：
    0 = PASS
    1 = FAIL（缺少影响分析或版本策略）
"""

import argparse
import sys
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    (
        "消费方列表",
        [r"(消费方|consumer|影响.{0,10}(方|服务|端))\s*[:：]", r"影响的.{0,10}(系统|服务|前端|客户端)"],
        "必须列出受此破坏性变更影响的所有消费方（前端/移动端/其他服务）"
    ),
    (
        "版本策略",
        [r"(版本策略|version.?strat|parallel|deprecat|兼容策略)", r"(新旧并存|标记废弃|下线时间|cut.over)"],
        "必须声明版本策略：parallel（新旧并存）/ deprecate（废弃+下线时间）/ cut（直接切换）"
    ),
    (
        "通知计划",
        [r"(通知|notify|协调|migration.?plan|迁移计划)", r"(告知|联系|通知.{0,10}(前端|移动|消费方))"],
        "必须说明如何通知和协调受影响的消费方"
    ),
]

BREAKING_CHANGE_MARKERS = [
    r"breaking.?change",
    r"破坏性变更",
    r"不兼容变更",
    r"(删除|移除|rename).{0,20}(字段|参数|接口)",
    r"(接口|API).{0,20}(废弃|下线)",
]


def has_breaking_change_section(content: str) -> bool:
    """检查是否有破坏性变更相关章节"""
    for pattern in BREAKING_CHANGE_MARKERS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_section(content: str, patterns: list) -> bool:
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="API Breaking Change Gate")
    parser.add_argument("--spec", required=True, help="openspec.md 路径")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"[FAIL] openspec.md 不存在: {spec_path}", file=sys.stderr)
        sys.exit(1)

    content = spec_path.read_text(encoding="utf-8")
    failures = []

    # 检查是否有破坏性变更章节
    if not has_breaking_change_section(content):
        failures.append(
            "openspec.md 未声明破坏性变更信息 —— "
            "如果此变更确实是破坏性的，请添加'破坏性变更影响分析'章节"
        )

    # 检查三个必要小节
    for section_name, patterns, description in REQUIRED_SECTIONS:
        if not check_section(content, patterns):
            failures.append(f"缺少 [{section_name}]：{description}")

    if failures:
        print("[API Breaking Gate] FAIL")
        for f in failures:
            print(f"  [✗] {f}")
        print()
        print("破坏性 API 变更必须完成影响分析和版本规划才能进入 Phase 4 Implement。", file=sys.stderr)
        sys.exit(1)
    else:
        print("[API Breaking Gate] PASS — 破坏性变更分析完整")
        sys.exit(0)


if __name__ == "__main__":
    main()
