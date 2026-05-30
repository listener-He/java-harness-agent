#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiki distillation tool — scan for stale/duplicate content, then execute approved cleanup.

Two-phase protocol (driven by the librarian sub-agent):

  scan      Score every wiki/<domain>/*.md candidate by:
              • cross-repo reference count (basename grep, excluding the file itself)
              • git-mtime age in days
              • whether it sits in wal/archive/
              • duplicate H1 title within the same domain
            Apply deterministic rules (NOT semantic similarity) to recommend
            DELETE / MERGE / KEEP, then write a markdown plan file the human
            can review and approve via `[x]` checkboxes.

  execute   Read an approved plan file and apply `git rm` (DELETE) or
            content append + `git rm` (MERGE). Refuses to touch protected
            files or anything outside .claude/wiki/wiki/.

Refusal guarantees (safety):
  • Will not delete index.md / KNOWLEDGE_GRAPH.md / purpose.md
  • Will not touch anything outside .claude/wiki/wiki/
  • Will only act on plan rows marked `[x]`

Usage:
  python3 distill.py scan
  python3 distill.py execute --plan .claude/runs/distill/plan_<ts>.md [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

WIKI_DOMAIN_ROOT = Path(".claude/wiki/wiki")
RUNS_DIR = Path(".claude/runs/distill")
PROTECTED_NAMES = {"index.md", "KNOWLEDGE_GRAPH.md", "purpose.md"}
ARCHIVE_AGE_DAYS = 180

# Trust-tier filter: WAL fragments carrying `origin: human-curated` in their
# YAML frontmatter are exempt from auto-cleanup proposals (DELETE / MERGE).
# Per `wal-documentation-rules` §1 ORIGIN ATTRIBUTION. Missing frontmatter is
# treated as `agent-extracted` for backward compatibility with pre-T2 files.
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_ORIGIN_RE = re.compile(r"^origin:\s*([a-z\-]+)\s*$", re.IGNORECASE | re.MULTILINE)
_VALID_ORIGINS = ("agent-extracted", "human-curated")


def _read_origin(p: Path) -> str:
    """Parse `origin:` from YAML frontmatter; default `agent-extracted` if absent."""
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "agent-extracted"
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return "agent-extracted"
    om = _ORIGIN_RE.search(m.group(1))
    if not om:
        return "agent-extracted"
    val = om.group(1).strip().lower()
    return val if val in _VALID_ORIGINS else "agent-extracted"

# Roots to grep for reference detection. Single files are accepted directly.
SCAN_ROOTS = [
    "src",
    ".claude/wiki",
    ".claude/agents",
    ".claude/skills",
    ".claude/skills-archive",
    ".claude/rules",
    "CLAUDE.md",
]

SCAN_EXTS = {".md", ".py", ".java", ".json", ".xml", ".yaml", ".yml"}


def _candidates(domain: Path) -> list[Path]:
    """All scorable .md files in a domain root and its wal/archive/ subdir."""
    if not domain.is_dir():
        return []
    out: list[Path] = []
    for p in domain.iterdir():
        if p.is_file() and p.suffix == ".md" and p.name not in PROTECTED_NAMES:
            out.append(p)
    archive = domain / "wal" / "archive"
    if archive.is_dir():
        for p in archive.iterdir():
            if p.is_file() and p.suffix == ".md":
                out.append(p)
    return sorted(out)


def _git_mtime_days(p: Path) -> int:
    """Days since the file was last touched in git. Returns -1 if not tracked."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(p)],
            capture_output=True, text=True, timeout=5,
        )
        ts = out.stdout.strip()
        if not ts:
            return -1
        return int((time.time() - int(ts)) / 86400)
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return -1


def _files_to_scan() -> list[Path]:
    """Materialize the scan corpus once, so we don't walk it per candidate."""
    files: list[Path] = []
    for root in SCAN_ROOTS:
        rp = Path(root)
        if not rp.exists():
            continue
        if rp.is_file():
            files.append(rp)
            continue
        for p in rp.rglob("*"):
            if p.is_file() and p.suffix in SCAN_EXTS:
                files.append(p)
    return files


def _ref_count(target: Path, corpus_files: list[Path]) -> int:
    """Count files in corpus that mention the target's basename or stem-link form,
    excluding the target itself. Pure substring match — no regex."""
    name = target.name
    stem_link = f"[{target.stem}]"
    target_resolved = str(target.resolve())
    hits = 0
    for f in corpus_files:
        try:
            if str(f.resolve()) == target_resolved:
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if name in content or stem_link in content:
            hits += 1
    return hits


def _title(p: Path) -> str:
    """Extract first H1 heading; fallback to filename stem."""
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                if line:
                    break
    except OSError:
        pass
    return p.stem


def scan_domain(domain: Path, corpus_files: list[Path]) -> list[dict]:
    files = _candidates(domain)
    if not files:
        return []

    titles_seen: dict[str, list[str]] = {}
    for p in files:
        titles_seen.setdefault(_title(p), []).append(str(p))

    results = []
    for p in files:
        in_archive = "wal/archive" in str(p).replace("\\", "/")
        age_days = _git_mtime_days(p)
        refs = _ref_count(p, corpus_files)
        title = _title(p)
        dups = [other for other in titles_seen.get(title, []) if other != str(p)]
        origin = _read_origin(p)

        # Trust-tier guard runs BEFORE all cleanup rules: human-curated
        # entries are exempt from DELETE / MERGE proposals regardless of
        # refs / age / title duplication. Manual deletion still works;
        # distill.py just never SUGGESTS it.
        if origin == "human-curated":
            rec, reason = "KEEP", "human-curated (protected from auto-cleanup)"
        elif refs == 0:
            rec, reason = "DELETE", "0 references found (dead reference)"
        elif in_archive and age_days >= 0 and age_days > ARCHIVE_AGE_DAYS:
            rec, reason = "DELETE", f"archived for {age_days} days (cold storage cleanup)"
        elif dups:
            rec, reason = "MERGE", f"duplicate title '{title}' shared with {dups[0]}"
        else:
            rec, reason = "KEEP", f"refs={refs}, age={age_days}d"

        results.append({
            "file": str(p), "title": title, "refs": refs, "age_days": age_days,
            "in_archive": in_archive, "duplicates": dups, "origin": origin,
            "recommendation": rec, "reason": reason,
        })
    return results


def render_plan(all_results: dict[str, list[dict]]) -> str:
    lines = [
        f"# Wiki Distillation Plan ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        "",
        "Approve operations by changing `[ ]` to `[x]`, then run:",
        "",
        "    python3 .claude/scripts/wiki/distill.py execute --plan <this-file>",
        "",
        "Only `[x]` rows will be executed. DELETE uses `git rm`; MERGE appends",
        "content to the target then `git rm`s the source. History is preserved.",
        "",
    ]
    # Surface human-curated files at the top so reviewers can see what
    # was deliberately skipped. These rows are informational only — they
    # have no `[ ]` checkbox because they are not action candidates.
    protected = [
        r for results in all_results.values() for r in results
        if r.get("origin") == "human-curated"
    ]
    if protected:
        lines.append("## Protected (human-curated — exempt from auto-cleanup)")
        lines.append("")
        for r in protected:
            lines.append(f"- `KEEP` {r['file']}  — {r['reason']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    for domain in sorted(all_results.keys()):
        results = all_results[domain]
        delete_cands = [r for r in results if r["recommendation"] == "DELETE"]
        merge_cands = [r for r in results if r["recommendation"] == "MERGE"]
        if not delete_cands and not merge_cands:
            continue
        lines.append(f"## {domain}")
        lines.append("")
        if delete_cands:
            lines.append("### DELETE candidates")
            for r in delete_cands:
                lines.append(f"- [ ] `DELETE` {r['file']}  — {r['reason']}")
            lines.append("")
        if merge_cands:
            lines.append("### MERGE candidates")
            for r in merge_cands:
                tgt = r["duplicates"][0]
                lines.append(f"- [ ] `MERGE` {r['file']} → {tgt}  — {r['reason']}")
            lines.append("")
    if len(lines) <= 8:
        lines.append("_No DELETE or MERGE candidates. Wiki is healthy._")
    return "\n".join(lines)


def cmd_scan() -> int:
    if not WIKI_DOMAIN_ROOT.exists():
        print(f"No wiki tree at {WIKI_DOMAIN_ROOT}", file=sys.stderr)
        return 1
    corpus = _files_to_scan()
    all_results: dict[str, list[dict]] = {}
    for d in sorted(WIKI_DOMAIN_ROOT.iterdir()):
        if not d.is_dir():
            continue
        all_results[d.name] = scan_domain(d, corpus)

    plan = render_plan(all_results)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    out_path.write_text(plan, encoding="utf-8")

    total = sum(len(v) for v in all_results.values())
    deletes = sum(1 for v in all_results.values() for r in v if r["recommendation"] == "DELETE")
    merges = sum(1 for v in all_results.values() for r in v if r["recommendation"] == "MERGE")
    protected = sum(1 for v in all_results.values() for r in v if r.get("origin") == "human-curated")
    print(f"Scanned {total} files across {len(all_results)} domain(s).")
    print(f"  DELETE candidates: {deletes}")
    print(f"  MERGE candidates:  {merges}")
    print(f"  PROTECTED (human-curated, exempt from cleanup): {protected}")
    print(f"Plan written: {out_path}")
    return 0


_PLAN_LINE = re.compile(
    r"^\s*-\s*\[(?P<mark>[xX ])\]\s*`(?P<op>DELETE|MERGE)`\s+"
    r"(?P<file>\S+)(?:\s*→\s*(?P<target>\S+))?"
)


def parse_plan(plan_path: Path) -> list[dict]:
    ops = []
    with plan_path.open("r", encoding="utf-8") as f:
        for line in f:
            m = _PLAN_LINE.match(line)
            if not m:
                continue
            if m.group("mark").lower() != "x":
                continue
            ops.append({"op": m.group("op"), "file": m.group("file"), "target": m.group("target")})
    return ops


def _safe_path(path_str: str) -> bool:
    """Refuse anything outside .claude/wiki/wiki/ or any PROTECTED name."""
    p = Path(path_str)
    try:
        p.resolve().relative_to(WIKI_DOMAIN_ROOT.resolve())
    except ValueError:
        return False
    return p.name not in PROTECTED_NAMES


def cmd_execute(plan_path: Path, dry_run: bool) -> int:
    if not plan_path.exists():
        print(f"Plan not found: {plan_path}", file=sys.stderr)
        return 2
    ops = parse_plan(plan_path)
    if not ops:
        print("No approved operations in plan (no `[x]` markers found).")
        return 0

    print(f"{'Would apply' if dry_run else 'Applying'} {len(ops)} operation(s) from {plan_path}")
    for op in ops:
        if not _safe_path(op["file"]):
            print(f"  [REFUSE] outside wiki tree or protected: {op['file']}", file=sys.stderr)
            continue
        # Defense-in-depth: even if a hand-edited plan contains a `[x]` row
        # pointing at a human-curated file, refuse the op. scan_domain
        # already excludes these, so the only way to land here is manual
        # editing of the plan — block it explicitly.
        if _read_origin(Path(op["file"])) == "human-curated":
            print(f"  [REFUSE] human-curated source: {op['file']}", file=sys.stderr)
            continue
        if op["op"] == "DELETE":
            if dry_run:
                print(f"  [DRY] git rm {op['file']}")
            else:
                try:
                    rc = subprocess.run(["git", "rm", op["file"]], check=False, timeout=30)
                except subprocess.TimeoutExpired:
                    print(f"  [TIMEOUT] git rm {op['file']} (30s)", file=sys.stderr)
                    continue
                print(f"  [{'OK' if rc.returncode == 0 else 'FAIL'}] git rm {op['file']}")
        elif op["op"] == "MERGE":
            target = op.get("target")
            if not target or not _safe_path(target):
                print(f"  [REFUSE] merge target missing or unsafe: {target}", file=sys.stderr)
                continue
            if _read_origin(Path(target)) == "human-curated":
                print(f"  [REFUSE] merge target is human-curated: {target}", file=sys.stderr)
                continue
            if dry_run:
                print(f"  [DRY] append {op['file']} into {target}, then git rm")
            else:
                src = Path(op["file"]).read_text(encoding="utf-8")
                with open(target, "a", encoding="utf-8") as f:
                    f.write(f"\n\n<!-- merged from {op['file']} -->\n")
                    f.write(src)
                try:
                    subprocess.run(["git", "rm", op["file"]], check=False, timeout=30)
                except subprocess.TimeoutExpired:
                    print(f"  [TIMEOUT] git rm {op['file']} (30s)", file=sys.stderr)
                    continue
                print(f"  [OK] merged {op['file']} → {target}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Wiki distillation: scan and execute cleanup.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="Scan wiki and emit candidate plan markdown")
    ex = sub.add_parser("execute", help="Execute approved operations from a plan")
    ex.add_argument("--plan", required=True, help="Path to approved plan markdown")
    ex.add_argument("--dry-run", action="store_true", help="Preview without modifying files")
    args = parser.parse_args()
    if args.cmd == "scan":
        return cmd_scan()
    if args.cmd == "execute":
        return cmd_execute(Path(args.plan), args.dry_run)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
