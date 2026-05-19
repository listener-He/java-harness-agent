#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Brief Gate (Deterministic)

Validates that a task_brief exists, conforms to the schema checker, and that
its Acceptance Criteria and Allowed Scope sections are coherent with each
other (AC↔Scope cross-validation).

Exit codes:
- 0: PASS
- 1: WARN (cross-check heuristic only — no hard mismatch)
- 2: FAIL (schema missing OR hard scope/AC mismatch)
"""

import argparse
import os
import re
import subprocess
import sys

EXIT_WARN = 1
EXIT_FAIL = 2

# Identifiers we ignore when matching AC text against Scope tokens.
# Mostly Gherkin keywords, English connectives, and project boilerplate that
# would otherwise generate noise matches against generic path segments.
AC_STOPWORDS = {
    "Given", "When", "Then", "And", "But", "Or",
    "The", "This", "That", "These", "Those",
    "User", "System", "Status", "Code", "Error", "Request", "Response",
    "Returns", "Should", "Must", "May", "Will",
    "MUST", "SHOULD", "MAY",
    "AC", "TODO", "FIXME", "NOTE",
}

SLIM_MARKER = re.compile(r"^\s*spec_mode\s*:\s*SLIM\s*$", re.IGNORECASE | re.MULTILINE)
AC_SECTION = re.compile(r"^#+\s+.*(BDD|验收|Acceptance Criteria)", re.IGNORECASE)
HEADER_LINE = re.compile(r"^#+\s")


def _repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _schema_checker_path() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "wiki", "schema_checker.py"))


def _run_schema_checker(task_brief_path: str) -> tuple[int, list[str]]:
    checker = _schema_checker_path()
    if not os.path.exists(checker):
        return EXIT_WARN, [f"schema checker missing: {checker}"]

    proc = subprocess.run(
        [sys.executable, checker, task_brief_path],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    details: list[str] = []
    if out:
        details.append(out)
    if err:
        details.append(err)
    if proc.returncode == 0:
        return 0, []
    return EXIT_FAIL, ["schema check failed"] + details


def _read_allowed_scope(content: str) -> tuple[set[str], list[str]]:
    """Extract '## Allowed Scope' section entries as (exact_paths, prefix_paths)."""
    exact: set[str] = set()
    prefixes: list[str] = []
    in_section = False
    for line in content.splitlines():
        s = line.strip()
        if s == "## Allowed Scope":
            in_section = True
            continue
        if in_section and s.startswith("## "):
            break
        if in_section and s.startswith("-"):
            v = s.lstrip("-").strip()
            if not v or v.lower() == "none":
                continue
            if v.endswith("/") or "/" in v:
                prefixes.append(v.rstrip("/") + "/")
            else:
                exact.add(v)
    return exact, prefixes


def _read_ac_text(content: str) -> str:
    """Return the body of the Acceptance Criteria section (without header)."""
    block: list[str] = []
    in_section = False
    for line in content.splitlines():
        if not in_section:
            if AC_SECTION.match(line):
                in_section = True
            continue
        if HEADER_LINE.match(line):
            break
        block.append(line)
    return "\n".join(block)


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _is_ac_trivial(ac_text: str) -> bool:
    """An AC block is trivial when it has no Given/When/Then or AC-N signal.

    The project's lifecycle.md mandates Given/When/Then ACs, so the absence of
    that signal is itself a violation worth flagging.
    """
    cleaned = _strip_code_fences(ac_text).strip()
    if not cleaned:
        return True
    non_blank = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    if not non_blank:
        return True
    if all(ln.lower().rstrip(".") in {"none", "n/a", "无"} for ln in non_blank):
        return True
    has_signal = any(
        re.search(r"\b(Given|When|Then)\b", ln, re.IGNORECASE)
        or re.match(r"-?\s*AC[-:\s]?\d", ln, re.IGNORECASE)
        for ln in non_blank
    )
    return not has_signal


def _extract_identifiers(text: str) -> set[str]:
    """Pull code-like identifiers (CamelCase / camelCase / methodName()) from prose."""
    cleaned = _strip_code_fences(text)
    ids = set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]{2,})", cleaned))
    return {i for i in ids if i not in AC_STOPWORDS}


def _extract_scope_tokens(exact: set[str], prefixes: list[str]) -> set[str]:
    """Split scope paths into identifier-like tokens (package segments, filenames)."""
    tokens: set[str] = set()
    for path in list(exact) + prefixes:
        for part in re.split(r"[/.\\]", path):
            if part and len(part) >= 3:
                tokens.add(part)
    return tokens


def _ac_scope_cross_check(content: str) -> tuple[int, list[str]]:
    """Verify Allowed Scope and Acceptance Criteria are mutually coherent.

    Slim Spec: skipped (no formal Allowed Scope section expected).
    Hard mismatch (empty one side, non-empty other) → FAIL.
    Both non-empty but no identifier overlap → WARN.
    """
    if SLIM_MARKER.search(content):
        return 0, []

    exact, prefixes = _read_allowed_scope(content)
    scope_empty = not exact and not prefixes

    ac_text = _read_ac_text(content)
    ac_empty = _is_ac_trivial(ac_text)

    if scope_empty and ac_empty:
        return 0, []
    if scope_empty and not ac_empty:
        return EXIT_FAIL, [
            "AC↔Scope mismatch: Acceptance Criteria present but '## Allowed Scope' is empty/missing",
            "  Fix: add an explicit '## Allowed Scope' section with the file paths/prefixes the implementation may touch",
        ]
    if not scope_empty and ac_empty:
        return EXIT_FAIL, [
            "AC↔Scope mismatch: '## Allowed Scope' lists files but Acceptance Criteria is empty/None",
            "  Fix: add Given/When/Then acceptance criteria for the in-scope changes, or remove the scope entries",
        ]

    ac_ids = _extract_identifiers(ac_text)
    scope_tokens = _extract_scope_tokens(exact, prefixes)
    if not ac_ids:
        return EXIT_WARN, [
            "AC text has no extractable code-like identifiers; cross-check is inconclusive",
            "  Hint: reference at least one class/method name in each AC for better traceability",
        ]

    if ac_ids & scope_tokens:
        return 0, []

    sample_ac = sorted(ac_ids)[:5]
    sample_scope = sorted(scope_tokens)[:5]
    return EXIT_WARN, [
        "AC↔Scope cross-check: no identifier in AC text matches any '## Allowed Scope' path component",
        f"  AC identifiers (sample): {', '.join(sample_ac)}",
        f"  Scope tokens (sample): {', '.join(sample_scope)}",
        "  Likely cause: AC describes behavior not covered by Allowed Scope files, OR scope is too narrow",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require", required=True)
    args = parser.parse_args()

    path = args.require
    if not os.path.exists(path):
        print("FAIL: task_brief gate")
        print(f"- task_brief not found: {path}")
        return EXIT_FAIL

    schema_code, schema_details = _run_schema_checker(path)
    if schema_code == EXIT_FAIL:
        print("FAIL: task_brief gate")
        for d in schema_details:
            print(f"- {d}")
        return EXIT_FAIL

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    cross_code, cross_details = _ac_scope_cross_check(content)

    final_code = max(schema_code, cross_code)
    if final_code == 0:
        print("OK: task_brief gate pass (schema + AC↔Scope coherent)")
        return 0
    if final_code == EXIT_WARN:
        print("WARN: task_brief gate")
        for d in schema_details + cross_details:
            print(f"- {d}")
        return EXIT_WARN
    print("FAIL: task_brief gate")
    for d in schema_details + cross_details:
        print(f"- {d}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
