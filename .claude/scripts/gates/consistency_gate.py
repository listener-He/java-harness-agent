#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consistency Gate — Cross-file Budget Integrity Check (LEGACY)

Validates that budget limits (Wiki, Code, Web Search) and hard ceilings
are consistent across protocol files. Originally designed for the
.agents/ era when CONTEXT_FUNNEL.md and ROUTER.md owned the budget
constants. In the current .claude/ framework, CLAUDE.md no longer
publishes budget constants — only an active task_brief.md does.

This gate now degrades gracefully:
- If a referenced file is missing, that file is SKIPPED (not failed)
- If fewer than 2 files have budgets, the gate is a no-op (PASS)
- Only mismatches between files that DO publish budgets are reported

Exit codes (per linter-severity-standard):
- 0: OK (no mismatches OR not enough files to compare)
- 1: WARN (currently unused — declared for convention compliance)
- 2: FAIL (mismatch found between files that both publish budgets)
"""

import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_agents_budgets(text: str) -> dict:
    """Extract base budgets and hard ceilings from CLAUDE.md."""
    result = {}
    # Base: "Wiki ≤ 3, Code ≤ 8, Web Search ≤ 2"
    m = re.search(r"Wiki\s*[≤<=]\s*(\d+).*?Code\s*[≤<=]\s*(\d+).*?Web\s+Search\s*[≤<=]\s*(\d+)", text)
    if m:
        result["wiki_base"] = int(m.group(1))
        result["code_base"] = int(m.group(2))
        result["web_base"] = int(m.group(3))
    # Hard ceilings: "Wiki ≤ 8, Code ≤ 20, Web Search ≤ 6"
    m2 = re.search(r"Wiki\s*[≤<=]\s*(\d+).*?Code\s*[≤<=]\s*(\d+).*?Web\s+Search\s*[≤<=]\s*(\d+)", text[m.end():] if m else text)
    # Actually, the hard ceilings appear later in the Reward Mechanism row.
    # Let's find the second set of numbers after "Hard Ceilings"
    m_ceil = re.search(r"Hard\s+Ceilings.*?Wiki\s*[≤<=]\s*(\d+).*?Code\s*[≤<=]\s*(\d+).*?Web\s+Search\s*[≤<=]\s*(\d+)", text, re.DOTALL)
    if m_ceil:
        result["wiki_ceiling"] = int(m_ceil.group(1))
        result["code_ceiling"] = int(m_ceil.group(2))
        result["web_ceiling"] = int(m_ceil.group(3))
    return result


def _extract_funnel_budgets(text: str) -> dict:
    """Extract base budgets from CONTEXT_FUNNEL.md Rule 0.1 and ceilings from Rule 4.5."""
    result = {}
    # Rule 0.1 base budgets
    m_w = re.search(r"Wiki\s+budget:\s*(\d+)", text)
    m_c = re.search(r"Code\s+budget:\s*(\d+)", text)
    m_wb = re.search(r"Web\s+Search\s+budget:\s*(\d+)", text)
    if m_w:
        result["wiki_base"] = int(m_w.group(1))
    if m_c:
        result["code_base"] = int(m_c.group(1))
    if m_wb:
        result["web_base"] = int(m_wb.group(1))

    # Rule 4.5 hard ceilings table
    # | Wiki | 3 | +3 | +2 | 8 |
    tbl_pattern = re.compile(
        r"\|\s*Wiki\s*\|\s*(\d+)\s*\|\s*[+\d]+\s*\|\s*[+\d]+\s*\|\s*(\d+)\s*\|"
    )
    m = tbl_pattern.search(text)
    if m:
        result["wiki_ceiling"] = int(m.group(2))
    tbl_pattern2 = re.compile(
        r"\|\s*Code\s*\|\s*(\d+)\s*\|\s*[+\d]+\s*\|\s*[+\d]+\s*\|\s*(\d+)\s*\|"
    )
    m2 = tbl_pattern2.search(text)
    if m2:
        result["code_ceiling"] = int(m2.group(2))
    tbl_pattern3 = re.compile(
        r"\|\s*Web\s+Search\s*\|\s*(\d+)\s*\|\s*[+\d]+\s*\|\s*[+\d]+\s*\|\s*(\d+)\s*\|"
    )
    m3 = tbl_pattern3.search(text)
    if m3:
        result["web_ceiling"] = int(m3.group(2))
    return result


def _extract_router_budgets(text: str) -> dict:
    """Extract base budgets and ceilings from ROUTER.md Rule 3.1."""
    result = {}
    m_w = re.search(r"Wiki\s+budget:\s*(\d+)", text)
    m_c = re.search(r"Code\s+budget:\s*(\d+)", text)
    m_wb = re.search(r"Web\s+Search\s+budget:\s*(\d+)", text)
    if m_w:
        result["wiki_base"] = int(m_w.group(1))
    if m_c:
        result["code_base"] = int(m_c.group(1))
    if m_wb:
        result["web_base"] = int(m_wb.group(1))
    m_ceil = re.search(r"Wiki\s*[≤<=]\s*(\d+).*?Code\s*[≤<=]\s*(\d+).*?Web\s*[≤<=]\s*(\d+)", text)
    if m_ceil:
        result["wiki_ceiling"] = int(m_ceil.group(1))
        result["code_ceiling"] = int(m_ceil.group(2))
        result["web_ceiling"] = int(m_ceil.group(3))
    return result


def _extract_focus_card_budgets(text: str) -> dict:
    """Extract budgets from task_brief.md."""
    result = {}
    # "- Wiki budget: 3 docs (hard ceiling: 8)"
    m_w = re.search(r"Wiki\s+budget:\s*(\d+)", text)
    m_w_ceil = re.search(r"Wiki.*?hard\s+ceiling:\s*(\d+)", text, re.IGNORECASE)
    m_c = re.search(r"Code\s+budget:\s*(\d+)", text)
    m_c_ceil = re.search(r"Code.*?hard\s+ceiling:\s*(\d+)", text, re.IGNORECASE)
    m_wb = re.search(r"Web\s+Search\s+budget:\s*(\d+)", text)
    m_wb_ceil = re.search(r"Web\s+Search.*?hard\s+ceiling:\s*(\d+)", text, re.IGNORECASE)
    if m_w:
        result["wiki_base"] = int(m_w.group(1))
    if m_w_ceil:
        result["wiki_ceiling"] = int(m_w_ceil.group(1))
    if m_c:
        result["code_base"] = int(m_c.group(1))
    if m_c_ceil:
        result["code_ceiling"] = int(m_c_ceil.group(1))
    if m_wb:
        result["web_base"] = int(m_wb.group(1))
    if m_wb_ceil:
        result["web_ceiling"] = int(m_wb_ceil.group(1))
    return result


def main() -> int:
    files = {
        "CLAUDE.md": os.path.join(REPO_ROOT, "CLAUDE.md"),
        "CONTEXT_FUNNEL.md": os.path.join(REPO_ROOT, ".claude", "router", "CONTEXT_FUNNEL.md"),
        "ROUTER.md": os.path.join(REPO_ROOT, ".claude", "router", "ROUTER.md"),
        "task_brief.md": os.path.join(REPO_ROOT, ".claude", "workflow", "artifacts", "task_brief.md"),
    }

    extractors = {
        "CLAUDE.md": _extract_agents_budgets,
        "CONTEXT_FUNNEL.md": _extract_funnel_budgets,
        "ROUTER.md": _extract_router_budgets,
        "task_brief.md": _extract_focus_card_budgets,
    }

    parsed = {}
    skipped = []
    for name, path in files.items():
        if not os.path.exists(path):
            skipped.append(name)
            continue
        text = _read(path)
        budgets = extractors[name](text)
        if budgets:
            parsed[name] = budgets

    if skipped:
        print(f"INFO: skipped missing files: {', '.join(skipped)}")

    if len(parsed) < 2:
        print("OK: fewer than 2 files publish budgets — nothing to compare")
        return 0

    errors = []

    # Validate base budgets match across files
    base_keys = ["wiki_base", "code_base", "web_base"]
    base_labels = {"wiki_base": "Wiki", "code_base": "Code", "web_base": "Web Search"}
    for key in base_keys:
        values = {}
        for fname, d in parsed.items():
            if key in d:
                values[fname] = d[key]
        if len(set(values.values())) > 1:
            detail = ", ".join(f"{f}={v}" for f, v in values.items())
            errors.append(f"Base {base_labels[key]} budget mismatch: {detail}")

    # Validate hard ceilings match CLAUDE.md and CONTEXT_FUNNEL.md (the two authoritative sources)
    ceiling_keys = ["wiki_ceiling", "code_ceiling", "web_ceiling"]
    ceiling_labels = {"wiki_ceiling": "Wiki", "code_ceiling": "Code", "web_ceiling": "Web Search"}
    ceiling_sources = ["CLAUDE.md", "CONTEXT_FUNNEL.md"]
    for key in ceiling_keys:
        values = {}
        for fname in ceiling_sources:
            if key in parsed.get(fname, {}):
                values[fname] = parsed[fname][key]
        if len(values) >= 2 and len(set(values.values())) > 1:
            detail = ", ".join(f"{f}={v}" for f, v in values.items())
            errors.append(f"Ceiling {ceiling_labels[key]} mismatch: {detail}")

    # Validate ROUTER.md ceilings
    for key in ceiling_keys:
        if key in parsed.get("ROUTER.md", {}) and key in parsed.get("CLAUDE.md", {}):
            if parsed["ROUTER.md"][key] != parsed["CLAUDE.md"][key]:
                errors.append(
                    f"Ceiling {ceiling_labels[key]}: ROUTER.md={parsed['ROUTER.md'][key]} "
                    f"vs CLAUDE.md={parsed['CLAUDE.md'][key]}"
                )

    # Validate task_brief.md
    for key in base_keys + ceiling_keys:
        if key in parsed.get("task_brief.md", {}) and key in parsed.get("CLAUDE.md", {}):
            if parsed["task_brief.md"][key] != parsed["CLAUDE.md"][key]:
                label = base_labels.get(key) or ceiling_labels.get(key) or key
                errors.append(
                    f"{label}: task_brief.md={parsed['task_brief.md'][key]} "
                    f"vs CLAUDE.md={parsed['CLAUDE.md'][key]}"
                )

    if errors:
        print("FAIL: budget consistency violations detected")
        for e in errors:
            print(f"- {e}")
        return EXIT_FAIL

    print("OK: all budget values consistent across protocol files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
