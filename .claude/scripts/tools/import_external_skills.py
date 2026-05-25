import argparse
import difflib
import json
import re
import zipfile
from pathlib import Path


def _extract_skill_md(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if "SKILL.md" in names:
            name = "SKILL.md"
        else:
            candidates = [n for n in names if n.endswith("SKILL.md")]
            if not candidates:
                raise RuntimeError(f"SKILL.md not found in {zip_path}")
            name = candidates[0]
        return zf.read(name).decode("utf-8")


def _parse_skill_name(skill_md: str, fallback: str) -> str:
    m = re.search(r"^name:\s*\"?([^\"]+?)\"?\s*$", skill_md, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    return fallback


def _default_targets() -> list[dict[str, str]]:
    return [
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/ai-pipeline.zip",
            "fallback_name": "ai-pipeline",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/ai-slop-cleaner.zip",
            "fallback_name": "ai-slop-cleaner",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/architecture-decision-records.zip",
            "fallback_name": "architecture-decision-records",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/blueprint.zip",
            "fallback_name": "blueprint",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/eval-harness.zip",
            "fallback_name": "eval-harness",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/external-research.zip",
            "fallback_name": "external-research",
        },
        {
            "rel_zip": "ai-pipeline（一个使用Ralph保持运行的持续开发循环）/self-improve.zip",
            "fallback_name": "self-improve",
        },
        {
            "rel_zip": "superpowers技能移植/brainstorming.zip",
            "fallback_name": "brainstorming",
        },
        {
            "rel_zip": "superpowers技能移植/dispatching-parallel-agents.zip",
            "fallback_name": "dispatching-parallel-agents",
        },
        {
            "rel_zip": "superpowers技能移植/executing-plans.zip",
            "fallback_name": "executing-plans",
        },
        {
            "rel_zip": "superpowers技能移植/receiving-code-review.zip",
            "fallback_name": "receiving-code-review",
        },
        {
            "rel_zip": "superpowers技能移植/requesting-code-review.zip",
            "fallback_name": "requesting-code-review",
        },
        {
            "rel_zip": "superpowers技能移植/systematic-debugging.zip",
            "fallback_name": "systematic-debugging",
        },
        {
            "rel_zip": "superpowers技能移植/test-driven-development.zip",
            "fallback_name": "test-driven-development",
        },
        {
            "rel_zip": "superpowers技能移植/using-git-worktrees.zip",
            "fallback_name": "using-git-worktrees",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/debug.zip",
            "fallback_name": "debug",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/verify.zip",
            "fallback_name": "verify",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/ultraqa.zip",
            "fallback_name": "ultraqa",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/writing-plans.zip",
            "fallback_name": "writing-plans",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/deepinit.zip",
            "fallback_name": "deepinit",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/release.zip",
            "fallback_name": "release",
        },
        {
            "rel_zip": "oh-my-claudecode技能移植/remember.zip",
            "fallback_name": "remember",
        },
        {
            "rel_zip": "superpowers技能移植/skill-creator.zip",
            "fallback_name": "skill-author",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--targets-json", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    source_root = Path(args.source_root)

    run_dir = repo_root / ".claude" / "runs" / "task-briefs"
    conflict_dir = run_dir / f"{args.slug}_conflicts"
    dest_skills = repo_root / ".claude" / "skills"

    run_dir.mkdir(parents=True, exist_ok=True)
    conflict_dir.mkdir(parents=True, exist_ok=True)
    dest_skills.mkdir(parents=True, exist_ok=True)

    if args.targets_json:
        targets = json.loads(Path(args.targets_json).read_text(encoding="utf-8"))
    else:
        targets = _default_targets()

    imported: list[dict[str, str]] = []
    skipped_identical: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []

    for t in targets:
        rel_zip = t["rel_zip"]
        fallback = t["fallback_name"]

        zip_path = source_root / rel_zip
        upstream = _extract_skill_md(zip_path)
        skill_name = _parse_skill_name(upstream, fallback)

        dest_dir = dest_skills / skill_name
        dest_file = dest_dir / "SKILL.md"

        if dest_file.exists():
            local = dest_file.read_text(encoding="utf-8")
            if local == upstream:
                skipped_identical.append({"skill": skill_name, "zip": rel_zip})
                continue

            conflict_path = conflict_dir / f"{skill_name}.upstream.SKILL.md"
            conflict_path.write_text(upstream, encoding="utf-8")
            ratio = difflib.SequenceMatcher(a=local, b=upstream).ratio()
            conflicts.append(
                {
                    "skill": skill_name,
                    "zip": rel_zip,
                    "similarity": f"{ratio:.3f}",
                    "conflict_path": str(conflict_path),
                }
            )
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(upstream, encoding="utf-8")
        imported.append({"skill": skill_name, "zip": rel_zip, "path": str(dest_file)})

    result = {
        "imported": imported,
        "skipped_identical": skipped_identical,
        "conflicts": conflicts,
        "conflict_dir": str(conflict_dir),
        "source_root": str(source_root),
        "dest_root": str(dest_skills),
    }

    (run_dir / f"{args.slug}_import_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines = []
    report_lines.append("# Skill Import Report")
    report_lines.append("")
    report_lines.append(f"- Source: `{source_root}`")
    report_lines.append(f"- Destination: `{dest_skills}`")
    report_lines.append(f"- Conflict dir: `{conflict_dir}`")
    report_lines.append("")
    report_lines.append("## Imported")
    if imported:
        for it in imported:
            report_lines.append(f"- `{it['skill']}` <= `{it['zip']}`")
    else:
        report_lines.append("- None")
    report_lines.append("")
    report_lines.append("## Skipped (Identical)")
    if skipped_identical:
        for it in skipped_identical:
            report_lines.append(f"- `{it['skill']}`")
    else:
        report_lines.append("- None")
    report_lines.append("")
    report_lines.append("## Conflicts (Local exists)")
    if conflicts:
        report_lines.append("| Skill | Zip | Similarity | Upstream Copy |")
        report_lines.append("|---|---|---:|---|")
        for it in conflicts:
            report_lines.append(
                f"| `{it['skill']}` | `{it['zip']}` | `{it['similarity']}` | `{it['conflict_path']}` |"
            )
    else:
        report_lines.append("- None")
    report_lines.append("")

    (run_dir / f"{args.slug}_import_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
