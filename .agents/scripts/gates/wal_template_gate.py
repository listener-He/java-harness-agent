"""
wal_template_gate.py — WAL 模板合规检查

验证本次任务产出的所有 WAL 文件格式正确、内容合规。
Archive 阶段必须通过此门控，否则任务不允许标记为 DONE。

用法：
    python3 .agents/scripts/gates/wal_template_gate.py --task-date YYYYMMDD [--wiki-root .agents/llm_wiki]

退出码：
    0 = PASS
    1 = FAIL（WAL 缺失或格式不合规）
    2 = WARN（存在无变化确认行但无实质内容，需人工确认）
"""

import argparse
import sys
import re
from pathlib import Path

REQUIRED_FRONTMATTER_FIELDS = {"date", "task", "profile", "dimension"}
VALID_PROFILES = {"PATCH", "STANDARD"}
VALID_DIMENSIONS = {"domain", "api", "data", "architecture", "preferences", "testing", "reviews"}

PLACEHOLDER_PATTERNS = [
    r"^\s*\{.*\}\s*$",          # 模板占位符 {xxx}
    r"^\s*\(示例\)",             # 示例行（正式 WAL 不应保留示例）
    r"^\s*\*(示例|placeholder)", # 星号包裹的示例
]

NO_CHANGE_MARKERS = [
    "无变化确认",
    "no new knowledge",
    "未产生.*层的新知识",
    "确认无需更新",
]


def parse_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter（--- 包裹的区域）"""
    lines = content.strip().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    return fields


def is_placeholder_content(content: str) -> bool:
    """检查内容是否只有占位符"""
    meaningful_lines = []
    in_frontmatter = False
    fence_count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if stripped.startswith("#"):
            continue
        if not stripped:
            continue
        meaningful_lines.append(stripped)

    if not meaningful_lines:
        return True

    all_placeholder = all(
        any(re.match(p, line) for p in PLACEHOLDER_PATTERNS)
        for line in meaningful_lines
    )
    return all_placeholder


def has_no_change_confirmation(content: str) -> bool:
    """检查是否包含无变化确认行"""
    for marker in NO_CHANGE_MARKERS:
        if re.search(marker, content):
            return True
    return False


def check_wal_file(wal_file: Path) -> tuple[str, str]:
    """
    检查单个 WAL 文件。
    返回 (status, message)，status 为 PASS / WARN / FAIL
    """
    content = wal_file.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(content)

    # 1. frontmatter 完整性
    missing = REQUIRED_FRONTMATTER_FIELDS - set(frontmatter.keys())
    if missing:
        return "FAIL", f"{wal_file.name}: frontmatter 缺少字段 {missing}"

    # 2. profile 合法性
    profile = frontmatter.get("profile", "").upper()
    if profile not in VALID_PROFILES:
        return "FAIL", f"{wal_file.name}: profile='{profile}' 非法，必须是 {VALID_PROFILES}"

    # 3. dimension 合法性
    dimension = frontmatter.get("dimension", "").lower()
    if dimension not in VALID_DIMENSIONS:
        return "FAIL", f"{wal_file.name}: dimension='{dimension}' 非法，必须是 {VALID_DIMENSIONS}"

    # 4. 内容合规
    if is_placeholder_content(content):
        if has_no_change_confirmation(content):
            return "WARN", f"{wal_file.name}: 仅包含无变化确认，无实质内容（可接受，但请人工确认）"
        return "FAIL", f"{wal_file.name}: 内容为空或只有模板占位符，必须填写实质内容或无变化确认"

    return "PASS", f"{wal_file.name}: OK"


def main():
    parser = argparse.ArgumentParser(description="WAL Template Gate")
    parser.add_argument("--task-date", required=True, help="任务日期 YYYYMMDD")
    parser.add_argument("--wiki-root", default=".agents/llm_wiki", help="Wiki 根目录")
    args = parser.parse_args()

    wiki_root = Path(args.wiki_root)
    task_date = args.task_date

    if not wiki_root.exists():
        print(f"[FAIL] Wiki 根目录不存在: {wiki_root}", file=sys.stderr)
        sys.exit(1)

    # 收集本次任务产出的 WAL 文件（按日期前缀匹配）
    wal_files = list(wiki_root.glob(f"wiki/*/wal/{task_date}_*.md"))
    wal_files = [f for f in wal_files if f.name != "WAL_FORMAT.md"]

    if not wal_files:
        print(f"[FAIL] 未找到日期 {task_date} 的 WAL 文件。", file=sys.stderr)
        print("  PATCH/STANDARD 任务在 Archive 阶段必须至少产出 1 个 WAL 文件。", file=sys.stderr)
        print("  即使无新知识，也必须写'无变化确认'行。", file=sys.stderr)
        sys.exit(1)

    results = []
    has_fail = False
    has_warn = False

    for wal_file in sorted(wal_files):
        status, message = check_wal_file(wal_file)
        results.append((status, message))
        if status == "FAIL":
            has_fail = True
        elif status == "WARN":
            has_warn = True

    # 检查 reviews 维度是否写回（每次任务固定要求）
    reviews_wal = [f for f in wal_files if "reviews" in f.name]
    if not reviews_wal:
        results.append(("FAIL", "缺少 reviews 维度 WAL —— 每次任务完成后必须写回 Review 评分记录"))
        has_fail = True

    # 输出结果
    for status, message in results:
        icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  [{status}] {icon} {message}")

    print()
    if has_fail:
        print("[WAL Gate] FAIL — 存在不合规的 WAL 文件，任务不允许标记为 DONE", file=sys.stderr)
        sys.exit(1)
    elif has_warn:
        print("[WAL Gate] WARN — 存在警告，请人工确认后继续")
        sys.exit(2)
    else:
        print(f"[WAL Gate] PASS — {len(wal_files)} 个 WAL 文件全部合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
