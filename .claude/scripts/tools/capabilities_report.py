#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the framework capabilities matrix.

Walks .claude/agents/ and .claude/skills/, parses YAML frontmatter, and
combines it with the phase routing baked into .claude/rules/lifecycle.md
to render a single markdown document users can scan in under a minute.

Answers one question: "given <situation>, what should I use?"

Output is overwritten on each run (deterministic; no history needed).

Usage:
  python3 capabilities_report.py                       # writes .claude/CAPABILITIES.md
  python3 capabilities_report.py --out <path>          # custom output
  python3 capabilities_report.py --stdout              # print, do not write
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

AGENTS_DIR = Path(".claude/agents")
SKILLS_DIR = Path(".claude/skills")
DEFAULT_OUT = Path(".claude/CAPABILITIES.md")


# --- frontmatter parsing -----------------------------------------------------

def parse_frontmatter(path: Path) -> dict[str, str]:
    """Tiny YAML frontmatter reader. Single-line `key: value` pairs only.
    Quotes (single or double) around values are stripped."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    body = text[4:end]
    out: dict[str, str] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        v = value.strip().strip('"').strip("'")
        out[key.strip()] = v
    return out


def load_agents() -> list[dict]:
    if not AGENTS_DIR.is_dir():
        return []
    agents = []
    for p in sorted(AGENTS_DIR.glob("*.md")):
        fm = parse_frontmatter(p)
        if not fm.get("name"):
            continue
        agents.append({
            "name": fm["name"],
            "description": fm.get("description", ""),
            "tools": fm.get("tools", "-"),
            "model": fm.get("model", "-"),
            "path": str(p),
        })
    return agents


def load_skills() -> list[dict]:
    if not SKILLS_DIR.is_dir():
        return []
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md)
        if not fm.get("name"):
            continue
        skills.append({
            "name": fm["name"],
            "description": fm.get("description", ""),
            "path": str(skill_md),
        })
    return skills


# --- hardcoded routing (mirrors lifecycle.md / skill-precedence.md) ---------

AGENT_CATEGORIES: dict[str, list[str]] = {
    "Implementation": ["lead-engineer"],
    "Design": ["system-architect", "requirement-engineer"],
    "Review": ["code-reviewer", "focus-guard", "security-sentinel", "ambiguity-gatekeeper"],
    "Knowledge / Governance": [
        "librarian", "knowledge-extractor", "knowledge-architect",
        "documentation-curator", "skill-graph-curator",
    ],
}


PHASE_ROUTING: list[dict] = [
    {
        "phase": "1. Explorer",
        "agent": "主 agent (inline)",
        "skills": ["local-code-intelligence", "requirement-intake", "adversarial-review (HIGH)"],
        "notes": "convert AC to Given/When/Then; run code_index for impact",
    },
    {
        "phase": "2. Propose",
        "agent": "system-architect (HIGH) / 主 agent (MEDIUM)",
        "skills": ["brainstorming", "writing-plans", "cognitive-bias-checklist", "decision-frameworks"],
        "notes": "write task_brief; HIGH writes one ADR per actual irreversible decision (or explicit 'mechanical' note if none)",
    },
    {
        "phase": "3. Review",
        "agent": "code-reviewer",
        "skills": ["adversarial-review (HIGH)", "security-review-checklist (auth/data)"],
        "notes": "PATCH uses inline code-review-checklist skill instead",
    },
    {
        "phase": "Approval Gate (HIGH)",
        "agent": "主 agent + AskUserQuestion",
        "skills": [],
        "notes": "present Human Section; full / partial / reject",
    },
    {
        "phase": "4. Implement",
        "agent": "lead-engineer",
        "skills": [
            "test-driven-development", "java-architecture-standards",
            "java-coding-style", "mybatis-sql-standard (if MyBatis)",
        ],
        "notes": "PreToolUse hook auto-enforces Allowed Scope",
    },
    {
        "phase": "5. QA",
        "agent": "主 agent (inline)",
        "skills": ["verify (≤3 ACs)", "ultraqa (≥4 ACs or HIGH)", "java-testing-standards"],
        "notes": "Evidence Mapping Table for HIGH",
    },
    {
        "phase": "6. Archive",
        "agent": "knowledge-extractor + librarian",
        "skills": ["wal-documentation-rules", "architecture-decision-records", "remember", "skill-graph-manager"],
        "notes": "PATCH skips entirely",
    },
]


QUICK_ROUTING: list[tuple[str, str]] = [
    ("模糊指令，想先澄清", "主 agent 自问一句澄清"),
    ("@vibe / TRIVIAL 改动 (≤3 文件)", "主 agent 直接做"),
    ("@patch / LOW 改动 (4-6 文件)", "Implement → QA → Archive (无 task_brief)"),
    ("@standard / MEDIUM 改动 (公共 API)", "Explorer → Propose → Review → Implement → QA → Archive"),
    ("@standard / HIGH 改动 (DB/auth/error-code)", "上面 + Approval Gate + ADR per actual irreversible decision (零决策时显式标 'mechanical') + adversarial-review"),
    ("整理 / 合并 wiki", "`@gc` → librarian (compact flow)"),
    ("萃取 / 清理过期 wiki", "`@distill` → librarian (distill flow，需人审批)"),
    ("提取知识到 WAL", "`@wiki-update` → knowledge-extractor"),
    ("拆分超长 index (>500 行)", "knowledge-architect"),
    ("写文档 / README / Javadoc / 迁移指南", "documentation-curator (Mode A — free-form documentation)"),
    ("看现在有什么能力", "`@capabilities` → documentation-curator (Mode B — 本报告)"),
    ("生产事故 / hotfix", "Scenario A — incident-response (skills-archive)"),
    ("DB migration / DDL", "Scenario B1 (additive = PATCH) or B2 (mutating = HIGH + Approval Gate) — migration-planner"),
    ("Breaking API change", "Scenario C — api_breaking_gate"),
    ("EPIC / 跨 3+ domain", "task-decomposition-guide + Foreman 派发"),
    ("Bug 根因未知", "Scenario DEBUG — systematic-debugging (Phase 1 强制)"),
]


SHORTCUTS: list[tuple[str, str]] = [
    ("`@read` / `@learn`", "LEARN — 只读，永不写代码"),
    ("`@vibe` / `@patch` / `@quickfix`", "PATCH — 直接做，跳过 Explorer/Propose/WAL"),
    ("`@standard`", "STANDARD — 强制走完整 lifecycle"),
    ("`@gc` / `@librarian`", "MAINTENANCE — librarian 合并 WAL"),
    ("`@distill`", "MAINTENANCE — librarian 萃取（扫描 → 人审批 → 执行）"),
    ("`@wiki-update` / `@milestone`", "MAINTENANCE — knowledge-extractor 提取 WAL"),
    ("`@capabilities`", "MAINTENANCE — 重新生成本报告"),
]


# --- rendering ---------------------------------------------------------------

def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(agents: list[dict], skills: list[dict]) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_index = {a["name"]: a for a in agents}
    skill_index = {s["name"]: s for s in skills}

    lines: list[str] = [
        "# Capabilities Matrix",
        "",
        f"Auto-generated by `python3 .claude/scripts/tools/capabilities_report.py`. Last generated: {ts}.",
        f"Source files: `.claude/agents/` ({len(agents)} agents), `.claude/skills/` ({len(skills)} skills), `.claude/rules/lifecycle.md`.",
        "",
        "> Do not hand-edit — re-run `@capabilities` to refresh.",
        "",
        "---",
        "",
        "## 1. 我该用什么？（快速路由）",
        "",
        _row(["场景", "入口 / Agent / Skill"]),
        _row(["---", "---"]),
    ]
    for situation, action in QUICK_ROUTING:
        lines.append(_row([situation, action]))

    lines += ["", "---", "", "## 2. Phase → Agent / Skill 路由表", ""]
    lines.append(_row(["Phase", "Agent", "Key Skills", "Notes"]))
    lines.append(_row(["---", "---", "---", "---"]))
    for p in PHASE_ROUTING:
        skills_str = ", ".join(p["skills"]) if p["skills"] else "—"
        lines.append(_row([p["phase"], p["agent"], skills_str, p["notes"]]))

    lines += ["", "---", "", f"## 3. Agents ({len(agents)} 个)", ""]
    categorized = {cat: [] for cat in AGENT_CATEGORIES}
    other: list[dict] = []
    placed = set()
    for cat, names in AGENT_CATEGORIES.items():
        for n in names:
            if n in agent_index:
                categorized[cat].append(agent_index[n])
                placed.add(n)
    for a in agents:
        if a["name"] not in placed:
            other.append(a)
    if other:
        categorized["其他 / Uncategorized"] = other

    for cat, items in categorized.items():
        if not items:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        lines.append(_row(["Agent", "When", "Tools", "Model"]))
        lines.append(_row(["---", "---", "---", "---"]))
        for a in items:
            desc = a["description"][:120] + ("…" if len(a["description"]) > 120 else "")
            lines.append(_row([f"`{a['name']}`", desc, a["tools"], a["model"]]))
        lines.append("")

    lines += ["---", "", f"## 4. Skills ({len(skills)} 个) — 按 Zone 分组", ""]
    zones = [
        ("Zone A — Implement (Java)", [
            "java-architecture-standards", "java-coding-style",
            "mybatis-sql-standard", "test-driven-development",
        ]),
        ("Zone B — Code Review", ["code-review-checklist", "adversarial-review", "security-review-checklist"]),
        ("Zone C — QA", ["verify", "ultraqa", "java-testing-standards"]),
        ("Zone D — Archive", [
            "wal-documentation-rules", "architecture-decision-records",
            "remember", "skill-graph-manager",
        ]),
        ("Zone E — Debug", ["systematic-debugging"]),
        ("Zone F — Explorer", [
            "local-code-intelligence", "requirement-intake",
            "task-decomposition-guide", "stakeholder-conflict-resolver",
        ]),
    ]
    zoned = set()
    for zone, names in zones:
        present = [skill_index[n] for n in names if n in skill_index]
        if not present:
            continue
        lines.append(f"### {zone}")
        for s in present:
            zoned.add(s["name"])
            desc = s["description"][:140] + ("…" if len(s["description"]) > 140 else "")
            lines.append(f"- `{s['name']}` — {desc}")
        lines.append("")

    rest = [s for s in skills if s["name"] not in zoned]
    if rest:
        lines.append("### Other (utility / cross-cutting)")
        for s in rest:
            desc = s["description"][:140] + ("…" if len(s["description"]) > 140 else "")
            lines.append(f"- `{s['name']}` — {desc}")
        lines.append("")

    lines += ["---", "", "## 5. Shortcuts", "", _row(["Shortcut", "Effect"]), _row(["---", "---"])]
    for sc, eff in SHORTCUTS:
        lines.append(_row([sc, eff]))

    lines += [
        "",
        "---",
        "",
        "## 6. Special Scenarios (override default routing)",
        "",
        _row(["Scenario", "Trigger", "Mandatory read (skills-archive)"]),
        _row(["---", "---", "---"]),
        _row(["DEBUG", "bug with unknown root cause", "systematic-debugging (Phase 1)"]),
        _row(["EPIC", "≥3 domains / migration / massive refactor", "task-decomposition-guide + dispatching-parallel-agents"]),
        _row(["A — Hotfix", "production incident", "incident-response"]),
        _row(["B — DB Migration", "DDL / system migration", "migration-planner + migration_gate.py"]),
        _row(["C — Breaking API", "remove/rename endpoint", "api_breaking_gate.py"]),
        _row(["D — Performance", "slow query / high latency", "LEARN first; baseline before fix"]),
        _row(["E — Dependency", "pom.xml change", "dependency_gate.py"]),
        _row(["GREENFIELD", "no src/ or `from scratch`", "greenfield-scaffold (+ optional deepinit)"]),
        _row(["RELEASE", "tag / deploy", "release"]),
        _row(["PIPELINE", "@ai-pipeline / full idea→delivery", "ai-pipeline (orchestrator)"]),
        "",
    ]

    return "\n".join(lines).rstrip() + "\n"


# --- entrypoint --------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the framework capabilities matrix.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output markdown path")
    parser.add_argument("--stdout", action="store_true", help="print to stdout instead of writing")
    args = parser.parse_args()

    agents = load_agents()
    skills = load_skills()
    if not agents and not skills:
        print("No agents or skills found — is this the correct project root?", file=sys.stderr)
        return 1

    body = render(agents, skills)
    if args.stdout:
        sys.stdout.write(body)
        return 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {len(agents)} agents + {len(skills)} skills to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
