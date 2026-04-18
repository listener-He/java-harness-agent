"""
dependency_gate.py — Maven 依赖变更安全检查

当检测到 pom.xml 变更时触发，检查新增/升级的依赖是否有说明和潜在风险。
（注：CVE 扫描需要配合 OWASP Dependency-Check 插件；本脚本做基础合规检查）

用法：
    python3 .agents/scripts/gates/dependency_gate.py --pom pom.xml [--spec path/to/openspec.md]

退出码：
    0 = PASS
    1 = FAIL
    2 = WARN
"""

import argparse
import sys
import re
import subprocess
from pathlib import Path

KNOWN_RISKY_GROUPS = [
    "com.alibaba",       # fastjson 等历史有 RCE 漏洞
    "org.apache.log4j",  # Log4Shell
    "org.springframework.boot",  # 主框架升级需谨慎
    "io.netty",
    "org.apache.commons",
]

SNAPSHOT_PATTERN = re.compile(r"-SNAPSHOT", re.IGNORECASE)
RANGE_VERSION_PATTERN = re.compile(r"[\[\(][^,]+,[^\]]+[\]\)]")  # Maven 版本范围


def parse_changed_deps(pom_path: Path) -> list[dict]:
    """
    简单解析 pom.xml 中的 dependency 块（非 diff，读取当前全量）。
    生产使用建议配合 git diff 只分析变更部分。
    """
    content = pom_path.read_text(encoding="utf-8")
    deps = []
    dep_blocks = re.findall(
        r"<dependency>(.*?)</dependency>",
        content,
        re.DOTALL,
    )
    for block in dep_blocks:
        group_match = re.search(r"<groupId>(.*?)</groupId>", block)
        artifact_match = re.search(r"<artifactId>(.*?)</artifactId>", block)
        version_match = re.search(r"<version>(.*?)</version>", block)
        if group_match and artifact_match:
            deps.append({
                "groupId": group_match.group(1).strip(),
                "artifactId": artifact_match.group(1).strip(),
                "version": version_match.group(1).strip() if version_match else "managed",
            })
    return deps


def check_deps(deps: list[dict]) -> tuple[list, list]:
    failures = []
    warnings = []

    for dep in deps:
        gid = dep["groupId"]
        aid = dep["artifactId"]
        ver = dep["version"]

        # SNAPSHOT 版本不允许进入生产
        if SNAPSHOT_PATTERN.search(ver):
            failures.append(f"{gid}:{aid}:{ver} — SNAPSHOT 版本禁止用于生产代码")

        # 版本范围（不固定版本，CI 不可复现）
        if RANGE_VERSION_PATTERN.match(ver):
            warnings.append(f"{gid}:{aid}:{ver} — 使用了版本范围，建议锁定精确版本以保证可复现构建")

        # 已知高风险 groupId
        for risky in KNOWN_RISKY_GROUPS:
            if gid.startswith(risky):
                warnings.append(
                    f"{gid}:{aid}:{ver} — 属于历史高风险 groupId，"
                    "请确认版本无已知 CVE（参考 https://mvnrepository.com/artifact/{gid}/{aid}）"
                )
                break

    return failures, warnings


def check_spec_has_reason(spec_path: Path, deps: list[dict]) -> list[str]:
    """检查 openspec.md 中是否解释了为何引入/升级依赖"""
    warnings = []
    if not spec_path or not spec_path.exists():
        return [
            "建议在 openspec.md 中说明引入/升级依赖的原因（当前未提供 --spec）"
        ]

    content = spec_path.read_text(encoding="utf-8")
    dep_section_exists = bool(re.search(r"(依赖|dependency|引入.{0,10}(jar|库|包))", content, re.IGNORECASE))
    if not dep_section_exists:
        warnings.append("openspec.md 未说明新增/升级依赖的原因，建议补充")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Dependency Gate")
    parser.add_argument("--pom", required=True, help="pom.xml 路径")
    parser.add_argument("--spec", help="openspec.md 路径（可选，用于检查是否说明了依赖原因）")
    args = parser.parse_args()

    pom_path = Path(args.pom)
    if not pom_path.exists():
        print(f"[FAIL] pom.xml 不存在: {pom_path}", file=sys.stderr)
        sys.exit(1)

    deps = parse_changed_deps(pom_path)
    failures, warnings = check_deps(deps)

    spec_path = Path(args.spec) if args.spec else None
    spec_warnings = check_spec_has_reason(spec_path, deps)
    warnings.extend(spec_warnings)

    if failures:
        print("[Dependency Gate] FAIL")
        for f in failures:
            print(f"  [✗] {f}")
        if warnings:
            print()
            for w in warnings:
                print(f"  [⚠] {w}")
        print()
        print("依赖变更存在阻断性问题，必须修复后才能继续。", file=sys.stderr)
        sys.exit(1)
    elif warnings:
        print("[Dependency Gate] WARN")
        for w in warnings:
            print(f"  [⚠] {w}")
        print()
        print("[Dependency Gate] 存在警告，请人工确认后继续。")
        sys.exit(2)
    else:
        print(f"[Dependency Gate] PASS — {len(deps)} 个依赖检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
