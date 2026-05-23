#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Report Gate (Deterministic)

Validates a research report against research_report_schema.md.

Exit codes:
- 0: PASS
- 1: WARN (one minor issue, e.g. §4 Analysis too thin given §3 Findings density)
- 2: FAIL (frontmatter missing, required section missing, pointer-less Findings, etc.)
"""

import argparse
import os
import re
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

REQUIRED_SECTIONS = [
    "§1 Question",
    "§2 Method",
    "§3 Findings",
    "§4 Analysis",
    "§5 Recommendations",
    "§6 Open Questions",
    "§7 Evidence Index",
]

SPEC_MODE_MARKER = re.compile(r"^\s*spec_mode\s*:\s*RESEARCH\s*$", re.IGNORECASE | re.MULTILINE)
SCOPE_MARKER = re.compile(r"^\s*scope\s*:\s*(quick|deep)\s*$", re.IGNORECASE | re.MULTILINE)
SLUG_MARKER = re.compile(r"^\s*slug\s*:\s*\S+", re.IGNORECASE | re.MULTILINE)
CREATED_MARKER = re.compile(r"^\s*created\s*:\s*\d{4}-\d{2}-\d{2}", re.IGNORECASE | re.MULTILINE)

# Pointer formats accepted in §3 Findings entries. Mirrors schema "Pointer formats".
#   - path:line          e.g. src/main/.../OrderService.java:142
#   - URL                http(s)://...
#   - VERBATIM: "..."
#   - WAL: <path>
#   - 7+ hex commit sha
POINTER_PATTERN = re.compile(
    r"(?:\S+\.[\w]+:\d+"          # file.ext:line
    r"|https?://\S+"              # URL
    r"|VERBATIM:\s*\""            # VERBATIM quote
    r"|WAL:\s*\S+"                # WAL path
    r"|\b[a-f0-9]{7,40}\b)",      # commit sha
    re.IGNORECASE,
)

HEADER_RE = re.compile(r"^##\s+§\d+\s", re.MULTILINE)


def _section_body(content: str, header_label: str) -> str:
    """Return body text after `## <header_label>` up to the next ## §-header (or EOF)."""
    # Match header literally; header_label is e.g. "§1 Question".
    pattern = re.compile(
        rf"^##\s+{re.escape(header_label)}\b[^\n]*\n(.*?)(?=^##\s+§\d+\s|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    m = pattern.search(content)
    return m.group(1) if m else ""


def _bullets(text: str) -> list[str]:
    """Return list of bullet lines (`- ...` or `* ...`). Skips Option ### sub-bullets."""
    out: list[str] = []
    for line in text.splitlines():
        s = line.rstrip()
        # A bullet is a top-level "- " or "* " at any indent ≤ 4 spaces.
        if re.match(r"^\s{0,4}[-*]\s", s):
            out.append(s)
    return out


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _check_frontmatter(content: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    if not SPEC_MODE_MARKER.search(content):
        reasons.append("frontmatter missing or wrong: required `spec_mode: RESEARCH`")
    if not SCOPE_MARKER.search(content):
        reasons.append("frontmatter missing: required `scope: quick` or `scope: deep`")
    if not SLUG_MARKER.search(content):
        reasons.append("frontmatter missing: required `slug: <kebab-or-snake>`")
    if not CREATED_MARKER.search(content):
        reasons.append("frontmatter missing: required `created: YYYY-MM-DD`")
    if reasons:
        return EXIT_FAIL, reasons
    return 0, []


def _check_sections_present(content: str) -> tuple[int, list[str]]:
    missing = []
    for label in REQUIRED_SECTIONS:
        if not re.search(rf"^##\s+{re.escape(label)}\b", content, re.MULTILINE):
            missing.append(label)
    if missing:
        return EXIT_FAIL, [f"missing section(s): {', '.join(missing)}"]
    return 0, []


def _detect_scope(content: str) -> str:
    m = SCOPE_MARKER.search(content)
    return m.group(1).lower() if m else "quick"


def _check_question(content: str) -> tuple[int, list[str]]:
    body = _strip_code_fences(_section_body(content, "§1 Question")).strip()
    if len(body) < 20:
        return EXIT_FAIL, [f"§1 Question too short ({len(body)} chars; need ≥ 20)"]
    return 0, []


def _check_method(content: str) -> tuple[int, list[str]]:
    body = _strip_code_fences(_section_body(content, "§2 Method"))
    bullets = _bullets(body)
    stripped_chars = len(body.strip())
    if len(bullets) < 3 and stripped_chars < 100:
        return EXIT_FAIL, [
            f"§2 Method too thin ({len(bullets)} bullets, {stripped_chars} chars; "
            "need ≥ 3 bullets OR ≥ 100 chars)"
        ]
    return 0, []


def _check_findings(content: str, scope: str) -> tuple[int, list[str]]:
    body = _strip_code_fences(_section_body(content, "§3 Findings"))
    bullets = _bullets(body)
    min_required = 15 if scope == "deep" else 5
    reasons: list[str] = []
    if len(bullets) < min_required:
        reasons.append(
            f"§3 Findings: {len(bullets)} entries; scope={scope} requires ≥ {min_required}"
        )
    # Pointer presence on every bullet (after the §3 minimum is satisfied or not).
    pointerless = [b.strip() for b in bullets if not POINTER_PATTERN.search(b)]
    if pointerless:
        sample = pointerless[0][:80]
        reasons.append(
            f"§3 Findings: {len(pointerless)} bullet(s) without evidence pointer "
            f"(e.g. `{sample}...`)"
        )
    if reasons:
        return EXIT_FAIL, reasons
    return 0, []


def _check_analysis_density(content: str) -> tuple[int, list[str]]:
    findings = _strip_code_fences(_section_body(content, "§3 Findings"))
    analysis = _strip_code_fences(_section_body(content, "§4 Analysis"))
    f_bullets = len(_bullets(findings))
    a_chars = len(analysis.strip())
    if f_bullets >= 5 and a_chars < 100:
        return EXIT_WARN, [
            f"§4 Analysis too thin given §3 density "
            f"({f_bullets} findings, only {a_chars} analysis chars; "
            "synthesis expected when findings ≥ 5)"
        ]
    return 0, []


def _check_evidence_index(content: str) -> tuple[int, list[str]]:
    body = _strip_code_fences(_section_body(content, "§7 Evidence Index"))
    bullets = _bullets(body)
    if not bullets:
        return EXIT_FAIL, ["§7 Evidence Index has no entries (need ≥ 1)"]
    return 0, []


def _check_report(path: str) -> tuple[int, list[str]]:
    if not os.path.exists(path):
        return EXIT_FAIL, [f"report file not found: {path}"]

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Stage 1: frontmatter — block on FAIL since downstream checks rely on `scope`.
    fm_code, fm_reasons = _check_frontmatter(content)
    if fm_code == EXIT_FAIL:
        return EXIT_FAIL, fm_reasons

    # Stage 2: section presence — block on FAIL since downstream checks read sections.
    sec_code, sec_reasons = _check_sections_present(content)
    if sec_code == EXIT_FAIL:
        return EXIT_FAIL, sec_reasons

    scope = _detect_scope(content)
    checks = [
        _check_question(content),
        _check_method(content),
        _check_findings(content, scope),
        _check_analysis_density(content),
        _check_evidence_index(content),
    ]

    final_code = 0
    all_reasons: list[str] = []
    for code, reasons in checks:
        if code > final_code:
            final_code = code
        all_reasons.extend(reasons)
    return final_code, all_reasons


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a research report against research_report_schema.md"
    )
    parser.add_argument("--require", required=True, help="path to the research report")
    args = parser.parse_args()

    code, reasons = _check_report(args.require)
    if code == 0:
        print(f"OK: research_report_gate pass ({args.require})")
        return 0
    if code == EXIT_WARN:
        print("WARN: research_report_gate")
    else:
        print("FAIL: research_report_gate")
    for r in reasons:
        print(f"- {r}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
