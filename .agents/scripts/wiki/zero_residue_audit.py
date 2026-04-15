#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".yml",
    ".yaml",
    ".txt",
}


FORBIDDEN_TOKENS = [
    ".trae/",
    "/.trae/",
    "sitemap.md",
    "project-rules.md",
    "intent-gateway.md",
    "context-funnel.md",
    "hooks.md",
    "lifecycle.md",
    "compaction-rules.md",
    ".agents/intent/",
    ".agents/harness/",
    "catalog/",
]


REQUIRED_PATHS = [
    "AGENTS.md",
    ".agents/README.md",
    ".agents/llm_wiki/KNOWLEDGE_GRAPH.md",
    ".agents/router/ROUTER.md",
    ".agents/router/CONTEXT_FUNNEL.md",
    ".agents/workflow/LIFECYCLE.md",
    ".agents/workflow/HOOKS.md",
    ".agents/workflow/ARCHIVE_WAL.md",
    ".agents/scripts/harness/engine.py",
    ".agents/scripts/wiki/wiki_linter.py",
    ".agents/scripts/wiki/compactor.py",
]


IGNORE_DIRS = {
    ".git",
    "target",
    "node_modules",
    ".idea",
    ".vscode",
}

IGNORE_FILES = {
    ".agents/scripts/wiki/zero_residue_audit.py",
}


LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass
class Finding:
    kind: str
    message: str
    file_path: Optional[str] = None
    line_no: Optional[int] = None


def _is_text_file(path: Path) -> bool:
    if path.is_dir():
        return False
    return path.suffix.lower() in TEXT_SUFFIXES


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        yield p


def _iter_text_files(root: Path) -> Iterable[Path]:
    for p in _iter_files(root):
        if p.is_file() and _is_text_file(p):
            yield p


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _path_exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).exists()


def _extract_links_from_line(line: str) -> List[str]:
    links = []
    for m in LINK_PATTERN.findall(line):
        links.append(m.strip())
    for m in WIKILINK_PATTERN.findall(line):
        links.append(m.strip())
    return links


def _normalize_md_link(raw: str) -> str:
    s = raw.strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()
    if "#" in s:
        s = s.split("#", 1)[0]
    return s.strip()


def _resolve_link(repo_root: Path, current_file: Path, link: str) -> Optional[Path]:
    s = _normalize_md_link(link)
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return None
    if s.startswith("mailto:"):
        return None
    if s.startswith("file://"):
        return None

    if s.startswith("/"):
        s = s.lstrip("/")

    if s.startswith(".agents/"):
        s = s[len(".agents/") :]
        return (repo_root / ".agents" / s).resolve()

    return (current_file.parent / s).resolve()


def check_required_paths(repo_root: Path) -> List[Finding]:
    findings: List[Finding] = []
    for rel in REQUIRED_PATHS:
        if not _path_exists(repo_root, rel):
            findings.append(Finding(kind="MISSING_PATH", message=f"缺失必须文件/目录: {rel}"))
    return findings


def check_forbidden_tokens(repo_root: Path) -> List[Finding]:
    findings: List[Finding] = []
    for p in _iter_text_files(repo_root):
        rel = str(p.relative_to(repo_root))
        if rel in IGNORE_FILES:
            continue
        if rel.startswith(".agents/workflow/runs/zero_residue_report_"):
            continue
        try:
            lines = _read_lines(p)
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            for token in FORBIDDEN_TOKENS:
                if token in line:
                    findings.append(
                        Finding(
                            kind="FORBIDDEN_TOKEN",
                            message=f"命中禁用关键字: {token}",
                            file_path=rel,
                            line_no=i,
                        )
                    )
    return findings


def check_markdown_links(repo_root: Path, roots: List[Path]) -> List[Finding]:
    findings: List[Finding] = []
    md_files: List[Path] = []
    for r in roots:
        if r.is_file() and r.suffix.lower() == ".md":
            md_files.append(r)
        elif r.is_dir():
            md_files.extend([p for p in r.rglob("*.md") if all(part not in IGNORE_DIRS for part in p.parts)])

    md_files = sorted(set([p.resolve() for p in md_files]))

    referenced: set[Path] = set()
    for f in md_files:
        try:
            lines = _read_lines(f)
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            for raw_link in _extract_links_from_line(line):
                target = _resolve_link(repo_root, f, raw_link)
                if target is None:
                    continue
                if target.suffix.lower() != ".md":
                    continue
                if not target.exists():
                    findings.append(
                        Finding(
                            kind="DEAD_LINK",
                            message=f"死链: {raw_link}",
                            file_path=str(f.relative_to(repo_root)),
                            line_no=i,
                        )
                    )
                else:
                    referenced.add(target)

    for f in md_files:
        if f.name in {"index.md", "KNOWLEDGE_GRAPH.md", "purpose.md"}:
            continue
        if f not in referenced:
            if str(f).startswith(str((repo_root / ".agents" / "llm_wiki").resolve())):
                findings.append(
                    Finding(
                        kind="ORPHAN_MD",
                        message="孤岛文件（未被任何 Markdown 引用）",
                        file_path=str(f.relative_to(repo_root)),
                    )
                )

    return findings


def write_report(repo_root: Path, out_path: Path, findings: List[Finding]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = len(findings) == 0
    lines: List[str] = []
    lines.append("# 零残留验收报告 (Zero Residue Audit)\n")
    lines.append(f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"- 仓库根目录: {repo_root}\n")
    lines.append(f"- 结论: {'✅ PASS' if ok else '❌ FAIL'}\n")
    lines.append("\n## 校验范围\n")
    lines.append("- 目录/文件存在性（关键入口与脚本）\n")
    lines.append("- 全仓关键字残留（命中即失败）\n")
    lines.append("- Markdown 死链/孤岛（以 `.agents/llm_wiki` + 入口文档为主）\n")
    lines.append("\n## 禁用关键字\n")
    for t in FORBIDDEN_TOKENS:
        lines.append(f"- `{t}`\n")
    lines.append("\n## 发现项\n")
    if ok:
        lines.append("无。\n")
    else:
        for f in findings:
            where = ""
            if f.file_path:
                where = f.file_path
                if f.line_no:
                    where = f"{where}:{f.line_no}"
                where = f" ({where})"
            lines.append(f"- [{f.kind}] {f.message}{where}\n")
    out_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="", help="输出报告路径（默认写入 .agents/workflow/runs/）")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]

    findings: List[Finding] = []
    findings.extend(check_required_paths(repo_root))
    findings.extend(check_forbidden_tokens(repo_root))

    link_roots = [
        repo_root / "AGENTS.md",
        repo_root / ".agents" / "README.md",
        repo_root / ".agents" / "llm_wiki",
    ]
    findings.extend(check_markdown_links(repo_root, link_roots))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else (repo_root / ".agents" / "workflow" / "runs" / f"zero_residue_report_{stamp}.md")
    if not out_path.is_absolute():
        out_path = (repo_root / out_path).resolve()

    write_report(repo_root, out_path, findings)
    print(str(out_path))

    return 0 if len(findings) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
