#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for subagent_stop_hook payload extraction.

Why this exists: the hook depends on Claude Code's SubagentStop payload
shape, which is not formally documented and may change between Claude Code
versions. When that happens, the hook silently dumps the unknown payload
to last_subagent_payload.json and returns 0 — so the regression is invisible
in normal use (sub-agent returns no longer get validated).

This test locks down the known payload shapes. Run it:
  - After any Claude Code upgrade
  - Before editing subagent_stop_hook.py or subagent_return_gate.py
  - As part of `/h-gates` or other manual gate audits

Usage:
  python3 .claude/scripts/harness/test_subagent_stop_hook.py
  exit 0 = all pass; exit 1 = at least one failure (details on stderr)

The test is intentionally vanilla-Python (no unittest/pytest) so it has no
install dependency and reads top-to-bottom.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Import the hook module under test.
_HARNESS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HARNESS_DIR))
import subagent_stop_hook as hook  # noqa: E402


# ----- TEXT_FIELDS direct extraction -----

def test_each_text_field_alone() -> None:
    """Every name in TEXT_FIELDS alone in the payload must yield its text.

    Locks down the bag of field names Claude Code might use. If a new
    version renames the field, this catches it.
    """
    for field in hook.TEXT_FIELDS:
        payload = {field: "hello"}
        got = hook._extract_return_text(payload)
        assert got == "hello", f"field={field!r}: expected 'hello', got {got!r}"


def test_text_field_whitespace_only_is_skipped() -> None:
    """Field present but only whitespace should fall through to other fields."""
    payload = {"response": "   ", "output": "real text"}
    got = hook._extract_return_text(payload)
    assert got == "real text", f"got {got!r}"


# ----- Nested wrappers -----

def test_nested_text_fields() -> None:
    """Text inside subagent/agent/tool_result wrappers."""
    for outer in ("subagent", "agent", "tool_result"):
        for field in hook.TEXT_FIELDS:
            payload = {outer: {field: "nested"}}
            got = hook._extract_return_text(payload)
            assert got == "nested", f"{outer}.{field}: got {got!r}"


# ----- Transcript JSONL parsing -----

def _write_transcript(lines: list[dict]) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for obj in lines:
        f.write(json.dumps(obj) + "\n")
    f.close()
    return Path(f.name)


def test_transcript_role_content_string() -> None:
    """Shape A: {role: assistant, content: "..."}."""
    p = _write_transcript([
        {"role": "user", "content": "ignore"},
        {"role": "assistant", "content": "FOUND"},
    ])
    try:
        got = hook._extract_return_text({"transcript_path": str(p)})
        assert got == "FOUND", f"got {got!r}"
    finally:
        p.unlink()


def test_transcript_message_content_list() -> None:
    """Shape B: {type: assistant, message: {content: [{type:text,text:...}]}}."""
    p = _write_transcript([
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "PART1"},
                    {"type": "text", "text": "PART2"},
                ],
            },
        },
    ])
    try:
        got = hook._extract_return_text({"transcript_path": str(p)})
        assert "PART1" in got and "PART2" in got, f"got {got!r}"
    finally:
        p.unlink()


def test_transcript_inner_message_role() -> None:
    """Shape C: outer has no role; inner 'message' carries role=assistant."""
    p = _write_transcript([
        {
            "message": {
                "role": "assistant",
                "content": "INNER",
            },
        },
    ])
    try:
        got = hook._extract_return_text({"transcript_path": str(p)})
        assert got == "INNER", f"got {got!r}"
    finally:
        p.unlink()


def test_transcript_picks_LAST_assistant() -> None:
    """Multiple assistant turns: pick the most recent."""
    p = _write_transcript([
        {"role": "assistant", "content": "OLD"},
        {"role": "user", "content": "ignore"},
        {"role": "assistant", "content": "NEW"},
    ])
    try:
        got = hook._extract_return_text({"transcript_path": str(p)})
        assert got == "NEW", f"expected last assistant, got {got!r}"
    finally:
        p.unlink()


def test_transcript_missing_file_falls_through() -> None:
    """If transcript_path is set but file is missing, fall through to other fields."""
    got = hook._extract_return_text({
        "transcript_path": "/tmp/nonexistent_xyz_12345.jsonl",
        "response": "fallback",
    })
    assert got == "fallback", f"got {got!r}"


def test_transcript_malformed_lines_skipped() -> None:
    """Garbage lines must be skipped without crashing."""
    p = Path(tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False).name)
    p.write_text(
        "not-json garbage\n"
        '{"role": "assistant"}\n'  # no content field
        '{"role": "assistant", "content": "VALID"}\n',
        encoding="utf-8",
    )
    try:
        got = hook._extract_return_text({"transcript_path": str(p)})
        assert got == "VALID", f"got {got!r}"
    finally:
        p.unlink()


# ----- Failure mode -----

def test_empty_payload_returns_empty() -> None:
    """Empty dict → empty string (caller writes debug dump)."""
    assert hook._extract_return_text({}) == ""


def test_unknown_field_returns_empty() -> None:
    """Catches a future Claude Code rename: any single unrecognized key alone fails."""
    assert hook._extract_return_text({"weirdfield_v2": "x"}) == ""


def test_non_string_content_ignored() -> None:
    """Field present but wrong type (e.g. dict where str expected) should not crash."""
    payload = {"response": {"nested": "x"}, "output": "real"}
    got = hook._extract_return_text(payload)
    assert got == "real", f"got {got!r}"


# ----- Runner -----

TESTS = [
    test_each_text_field_alone,
    test_text_field_whitespace_only_is_skipped,
    test_nested_text_fields,
    test_transcript_role_content_string,
    test_transcript_message_content_list,
    test_transcript_inner_message_role,
    test_transcript_picks_LAST_assistant,
    test_transcript_missing_file_falls_through,
    test_transcript_malformed_lines_skipped,
    test_empty_payload_returns_empty,
    test_unknown_field_returns_empty,
    test_non_string_content_ignored,
]


def main() -> int:
    failed: list[tuple[str, str]] = []
    for t in TESTS:
        try:
            t()
            print(f"✓ {t.__name__}")
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}", file=sys.stderr)
            failed.append((t.__name__, str(e)))
        except Exception as e:
            print(f"✗ {t.__name__}: unexpected {type(e).__name__}: {e}", file=sys.stderr)
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))

    print()
    if failed:
        print(f"FAIL: {len(failed)}/{len(TESTS)} tests failed", file=sys.stderr)
        print("If Claude Code upgraded recently, inspect:", file=sys.stderr)
        print("  .claude/runs/local_intel/last_subagent_payload.json", file=sys.stderr)
        print("  and update TEXT_FIELDS / TRANSCRIPT_FIELDS / parser in subagent_stop_hook.py", file=sys.stderr)
        return 1
    print(f"OK: {len(TESTS)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
