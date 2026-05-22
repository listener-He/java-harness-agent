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
STANDARD_MARKER = re.compile(r"^\s*spec_mode\s*:\s*STANDARD\s*$", re.IGNORECASE | re.MULTILINE)
RISK_MARKER = re.compile(r"^\s*risk\s*:\s*(MEDIUM|HIGH)\b", re.IGNORECASE | re.MULTILINE)
DIMENSIONS_MARKER = re.compile(r"^\s*dimensions\s*:\s*\[(.*?)\]\s*$", re.IGNORECASE | re.MULTILINE)
AC_SECTION = re.compile(r"^#+\s+.*(BDD|验收|Acceptance Criteria)", re.IGNORECASE)
HEADER_LINE = re.compile(r"^#+\s", re.MULTILINE)

# STANDARD spec_mode requires a `risk: MEDIUM|HIGH` marker; missing → FAIL.
STRICT_RISK_MARKER = True

# Spec-floor sections — ALWAYS required for STANDARD regardless of dimensions.
# These prevent security/observability/config-only changes from legally omitting
# NFR/AC documentation.
SPECFLOOR_HEADERS = [
    (re.compile(r"^##\s+1\.\s+Context\b", re.MULTILINE), "## 1. Context"),
    (re.compile(r"^##\s+5\.\s+Business Logic\b", re.MULTILINE), "## 5. Business Logic"),
    (re.compile(r"^##\s+6\.\s+Non-Functional Constraints\b", re.MULTILINE), "## 6. Non-Functional Constraints"),
    (re.compile(r"^##\s+7\.\s+Acceptance Criteria\b", re.MULTILINE), "## 7. Acceptance Criteria"),
]

# Dimension → (section header regex, display name). Starter set.
DIMENSION_SECTION_MAP = {
    "domain":    (re.compile(r"^##\s+2\.\s+Domain Model\b", re.MULTILINE),            "## 2. Domain Model"),
    "api":       (re.compile(r"^##\s+3\.\s+API Contract\b", re.MULTILINE),            "## 3. API Contract"),
    "data":      (re.compile(r"^##\s+4\.\s+Data Model\b", re.MULTILINE),              "## 4. Data Model"),
    "tech_arch": (re.compile(r"^##\s+8\.\s+Technical Architecture\b", re.MULTILINE),  "## 8. Technical Architecture"),
    "patterns":  (re.compile(r"^##\s+9\.\s+Design Patterns Applied\b", re.MULTILINE), "## 9. Design Patterns Applied"),
}
KNOWN_DIMENSIONS = set(DIMENSION_SECTION_MAP.keys())

# Allowed Scope path signatures → suggested dimensions for the heuristic
# backstop. WARN only (never FAIL); path conventions vary across projects.
PATH_SIGNATURE_HINTS = [
    ("controller/",  "api"),
    ("web/",         "api"),
    ("/api/",        "api"),
    ("mapper/",      "data"),
    ("dao/",         "data"),
    ("entity/",      "data"),
    ("migration/",   "data"),
    ("migrations/",  "data"),
    ("/db/",         "data"),
    ("event/",       "domain"),
    ("events/",      "domain"),
    ("aggregate/",   "domain"),
    ("aggregates/",  "domain"),
]

NONE_TOKENS = {"none", "n/a", "无"}


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
            if not v:
                continue
            # Take the first whitespace-delimited token so trailing inline
            # annotations (e.g. "- path (note)") are dropped. Then strip
            # surrounding markdown backticks so "- `path`" parses the same
            # as "- path". Mirrors scope_guard.py's parser.
            v = v.split(None, 1)[0].strip("`")
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


def _risk_from_frontmatter(content: str) -> tuple[str, int, list[str]]:
    """Detect risk level from the `risk:` frontmatter marker.

    Returns (risk, exit_code_contribution, detail_messages).
    - SLIM mode: returns ("N/A", 0, []) — risk marker not required.
    - STANDARD with valid marker: returns ("MEDIUM"|"HIGH", 0, []).
    - STANDARD with missing marker:
        * STRICT_RISK_MARKER=False → ("HIGH", WARN, [...])  (transition period)
        * STRICT_RISK_MARKER=True  → ("HIGH", FAIL, [...])  (post-archive)
    - STANDARD with malformed marker → ("HIGH", FAIL, [...]) always.
    """
    if SLIM_MARKER.search(content):
        return "N/A", 0, []
    if not STANDARD_MARKER.search(content):
        # No spec_mode at all — schema_checker will already complain; assume HIGH.
        return "HIGH", 0, []
    m = RISK_MARKER.search(content)
    if m:
        return m.group(1).upper(), 0, []
    # Marker missing.
    msg = [
        "risk marker missing: STANDARD spec_mode requires `risk: MEDIUM` or `risk: HIGH` on the line after `spec_mode:`",
        "  Fix: add `risk: MEDIUM` (default) or `risk: HIGH` to the frontmatter",
    ]
    if STRICT_RISK_MARKER:
        return "HIGH", EXIT_FAIL, msg
    return "HIGH", EXIT_WARN, msg + ["  (transition period: defaulting to HIGH)"]


def _section_body(content: str, header_pattern: re.Pattern) -> str:
    """Return body text between a matched header and the next ## header.

    Advances past the rest of the matched header line (any text after the
    matched prefix, e.g. ' (Hard Constraints)' tail) so it is not counted
    as body content.
    """
    m = header_pattern.search(content)
    if not m:
        return ""
    # Skip the rest of the header line.
    nl = content.find("\n", m.end())
    start = nl + 1 if nl != -1 else len(content)
    after = content[start:]
    next_hdr = HEADER_LINE.search(after)
    return after[: next_hdr.start()] if next_hdr else after


def _body_is_empty_or_none(body: str) -> bool:
    """True iff the body has no substantive content (whitespace / None / N/A)."""
    text = re.sub(r"```.*?```", "", body, flags=re.DOTALL)         # strip code fences
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)        # strip HTML comments
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not non_blank:
        return True
    first = non_blank[0].rstrip(".:;,").lower()
    # Common "I have nothing to say" patterns.
    if first in NONE_TOKENS:
        return True
    if first.startswith("none ") or first.startswith("n/a "):
        return True
    return False


def _dimensions_from_frontmatter(content: str) -> tuple[set[str], int, list[str]]:
    """Parse the `dimensions: [a, b, c]` frontmatter line.

    Returns (parsed_dimensions, exit_contribution, detail_messages).
    SLIM mode returns (set(), 0, []) — dimensions are not used.
    """
    if SLIM_MARKER.search(content):
        return set(), 0, []

    m = DIMENSIONS_MARKER.search(content)
    if not m:
        return set(), EXIT_FAIL, [
            "dimensions marker missing: STANDARD spec_mode requires `dimensions: [domain, api, data, tech_arch, patterns]`",
            "  Fix: add `dimensions: [...]` to the frontmatter after `risk:` (empty list `[]` is legal)",
        ]

    raw = m.group(1).strip()
    if not raw:
        return set(), 0, []
    declared = {token.strip().lower() for token in raw.split(",") if token.strip()}

    # Unknown dimensions — WARN, never FAIL.
    unknown = declared - KNOWN_DIMENSIONS
    details: list[str] = []
    code = 0
    if unknown:
        code = EXIT_WARN
        details.append(
            f"unknown dimension(s) in frontmatter: {sorted(unknown)} — known starter set: {sorted(KNOWN_DIMENSIONS)}"
        )
        details.append("  (unknown dimensions are tolerated; to add one permanently, open an ADR and update the schema + gate)")
    return declared, code, details


def _section_completeness_check(content: str, dimensions: set[str]) -> tuple[int, list[str]]:
    """Spec-floor + dimension-gated section completeness check.

    Spec-floor (§1/§5/§6/§7): always required, header present AND body non-empty.
    Dimension-gated (§2/§3/§4/§8/§9): required iff the corresponding dimension
    is in `dimensions`. When required, both header AND body must be present
    and substantive (not None / N/A). When NOT required, the section MAY be
    omitted entirely; if a header IS present with None body, that is tolerated
    (legacy briefs and back-compat).
    """
    if SLIM_MARKER.search(content):
        return 0, []

    details: list[str] = []
    code = 0

    # Spec-floor — header MUST be present; body MUST be substantive.
    for pattern, name in SPECFLOOR_HEADERS:
        if not pattern.search(content):
            details.append(f"spec-floor missing: {name} (header absent — required regardless of dimensions)")
            code = EXIT_FAIL
            continue
        body = _section_body(content, pattern)
        if _body_is_empty_or_none(body):
            details.append(f"spec-floor empty: {name} body is None/empty — spec-floor sections MUST be substantive")
            code = EXIT_FAIL

    # Dimension-gated — required iff declared.
    for dim in sorted(dimensions):
        if dim not in DIMENSION_SECTION_MAP:
            continue  # unknown dims already WARNed in _dimensions_from_frontmatter
        pattern, name = DIMENSION_SECTION_MAP[dim]
        if not pattern.search(content):
            details.append(f"declared dimension '{dim}' but section '{name}' missing")
            code = EXIT_FAIL
            continue
        body = _section_body(content, pattern)
        if _body_is_empty_or_none(body):
            details.append(
                f"declared dimension '{dim}' but section '{name}' body is empty/None — "
                f"declared dimensions require substantive content"
            )
            code = EXIT_FAIL

    if code != 0:
        details.append("  Fix: see .claude/wiki/schema/task_brief_schema.md (spec-floor + dimension-gated rules)")
    return code, details


def _heuristic_dimension_check(content: str, dimensions: set[str]) -> tuple[int, list[str]]:
    """Scan Allowed Scope for path signatures that suggest undeclared dimensions.

    WARN-only (never FAIL): path conventions vary across projects, so this is
    advisory — heuristic-as-backstop.
    """
    if SLIM_MARKER.search(content):
        return 0, []

    exact, prefixes = _read_allowed_scope(content)
    all_paths = list(exact) + prefixes
    if not all_paths:
        return 0, []

    suggestions: dict[str, list[str]] = {}
    for path in all_paths:
        path_lower = path.lower()
        for signature, suggested_dim in PATH_SIGNATURE_HINTS:
            if signature in path_lower and suggested_dim not in dimensions:
                suggestions.setdefault(suggested_dim, []).append(f"'{signature}' (in {path})")

    if not suggestions:
        return 0, []

    details = ["heuristic dimension check: path signatures suggest undeclared dimension(s):"]
    for dim, hits in sorted(suggestions.items()):
        details.append(f"  - dimension '{dim}' suggested by: {', '.join(hits[:3])}")
    details.append("  Hint: add the dimension to `dimensions:` or explain in §1 Context why the signature is misleading")
    return EXIT_WARN, details


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
    risk, risk_code, risk_details = _risk_from_frontmatter(content)
    dimensions, dim_code, dim_details = _dimensions_from_frontmatter(content)
    section_code, section_details = _section_completeness_check(content, dimensions)
    heuristic_code, heuristic_details = _heuristic_dimension_check(content, dimensions)

    final_code = max(schema_code, cross_code, risk_code, dim_code, section_code, heuristic_code)
    all_details = (
        schema_details + cross_details + risk_details
        + dim_details + section_details + heuristic_details
    )
    if final_code == 0:
        dims_repr = ",".join(sorted(dimensions)) or "[]"
        print(
            f"OK: task_brief gate pass (schema + AC↔Scope + risk={risk} + dimensions={dims_repr} + sections complete)"
        )
        return 0
    if final_code == EXIT_WARN:
        print("WARN: task_brief gate")
        for d in all_details:
            print(f"- {d}")
        return EXIT_WARN
    print("FAIL: task_brief gate")
    for d in all_details:
        print(f"- {d}")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
