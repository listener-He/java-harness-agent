#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consistency Gate — Cross-file Budget Integrity Check

Validates that budget limits (Wiki, Code, Web Search) and hard ceilings
are consistent across all protocol files:
- AGENTS.md
- .agents/router/CONTEXT_FUNNEL.md
- .agents/router/ROUTER.md
- .agents/workflow/artifacts/task_brief.md

Exit codes:
- 0: PASS (all files consistent)
- 2: FAIL (mismatch found)
"""

import os
import re
import sys

EXIT_FAIL = 2

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_agents_budgets(text: str) -> dict:
    """Extract base budgets and hard ceilings from AGENTS.md."""
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
        "AGENTS.md": os.path.join(REPO_ROOT, "AGENTS.md"),
        "CONTEXT_FUNNEL.md": os.path.join(REPO_ROOT, ".agents", "router", "CONTEXT_FUNNEL.md"),
        "ROUTER.md": os.path.join(REPO_ROOT, ".agents", "router", "ROUTER.md"),
        "task_brief.md": os.path.join(REPO_ROOT, ".agents", "workflow", "artifacts", "task_brief.md"),
    }

    extractors = {
        "AGENTS.md": _extract_agents_budgets,
        "CONTEXT_FUNNEL.md": _extract_funnel_budgets,
        "ROUTER.md": _extract_router_budgets,
        "task_brief.md": _extract_focus_card_budgets,
    }

    parsed = {}
    for name, path in files.items():
        if not os.path.exists(path):
            print(f"FAIL: file not found: {path}")
            return EXIT_FAIL
        text = _read(path)
        parsed[name] = extractors[name](text)

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

    # Validate hard ceilings match AGENTS.md and CONTEXT_FUNNEL.md (the two authoritative sources)
    ceiling_keys = ["wiki_ceiling", "code_ceiling", "web_ceiling"]
    ceiling_labels = {"wiki_ceiling": "Wiki", "code_ceiling": "Code", "web_ceiling": "Web Search"}
    ceiling_sources = ["AGENTS.md", "CONTEXT_FUNNEL.md"]
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
        if key in parsed.get("ROUTER.md", {}) and key in parsed.get("AGENTS.md", {}):
            if parsed["ROUTER.md"][key] != parsed["AGENTS.md"][key]:
                errors.append(
                    f"Ceiling {ceiling_labels[key]}: ROUTER.md={parsed['ROUTER.md'][key]} "
                    f"vs AGENTS.md={parsed['AGENTS.md'][key]}"
                )

    # Validate task_brief.md
    for key in base_keys + ceiling_keys:
        if key in parsed.get("task_brief.md", {}) and key in parsed.get("AGENTS.md", {}):
            if parsed["task_brief.md"][key] != parsed["AGENTS.md"][key]:
                label = base_labels.get(key) or ceiling_labels.get(key) or key
                errors.append(
                    f"{label}: task_brief.md={parsed['task_brief.md'][key]} "
                    f"vs AGENTS.md={parsed['AGENTS.md'][key]}"
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
