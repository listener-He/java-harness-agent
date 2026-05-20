#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingest Incident — thin envelope around LLM extraction.

This script does almost nothing on purpose. Schema drift in upstream sources
(Sentry/Jira API changes, free-form logs) makes Python parsers brittle. The
LLM reads natural language better than any regex.

Workflow:
  1. Save raw input to .claude/wiki/incidents/<date>_<slug>.raw.txt
  2. Emit a structured extraction prompt on stdout
  3. The calling agent reads the raw + prompt → writes <date>_<slug>.md

Usage:
  cat sentry_alert.txt | python3 ingest_incident.py --source sentry --slug user-login-500-spike
  python3 ingest_incident.py --source jira --slug order-cancel-race --from-file ticket.txt
  python3 ingest_incident.py --source manual --slug payment-double-charge --date 2026-05-13 < notes.txt

Exit codes:
  0 OK
  1 invalid arguments / file IO error
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

INCIDENTS_DIR = Path(".claude/wiki/incidents")
TEMPLATE_PATH = INCIDENTS_DIR / "TEMPLATE.md"

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}[a-z0-9]$")


def _validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.match(slug):
        print(f"error: slug '{slug}' must be kebab-case, 3-62 chars, "
              f"[a-z0-9-] only, no leading/trailing dash", file=sys.stderr)
        sys.exit(1)
    return slug


def _read_raw(args: argparse.Namespace) -> str:
    if args.from_file:
        try:
            return Path(args.from_file).read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(f"error: cannot read --from-file {args.from_file}: {e}",
                  file=sys.stderr)
            sys.exit(1)
    if sys.stdin.isatty():
        print("error: no input provided. Pipe data or use --from-file.",
              file=sys.stderr)
        sys.exit(1)
    return sys.stdin.read()


def _save_raw(raw: str, raw_path: Path) -> None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(raw, encoding="utf-8")


def _emit_extraction_prompt(target_md: Path, raw_path: Path, source: str,
                            slug: str, incident_date: str) -> None:
    print("[ingest-incident]")
    print(f"  raw saved: {raw_path}")
    print(f"  target:    {target_md}")
    print()
    print("Next step: read the raw fact, then write the target .md following "
          "the structure below. The 'Anti-pattern reference' section in "
          f"{TEMPLATE_PATH} has examples of what NOT to write.")
    print()
    print("Required structure:")
    print()
    print(f"---")
    print(f"date: {incident_date}")
    print(f"slug: {slug}")
    print(f"severity: P1 | P2 | P3")
    print(f"source: {source}")
    print(f"status: resolved | ongoing | watch")
    print(f"---")
    print()
    print("## 现象")
    print("<one line: user-visible / monitoring-visible symptom, specific and measurable>")
    print()
    print("## 根因")
    print("<one line: the WHY, not the stack trace>")
    print()
    print("## 受影响代码栈")
    print("<bullet list of file:line, class.method, table name, mapper XML id — "
          "must be greppable by incident_hint.py>")
    print()
    print("## 修复")
    print("<one line: PR / commit / config change / rollback>")
    print()
    print("## 提醒未来 LLM")
    print("**下次改这片代码时考虑：** <1-2 sentences, actionable, briefing-style>")
    print()
    print("KEY FIELD: the '提醒未来 LLM' line is the only one injected into "
          "[failure-memory] downstream. Make it specific and actionable.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest an incident fact source. LLM-driven extraction."
    )
    parser.add_argument("--source", required=True,
                        choices=["sentry", "jira", "log", "manual"])
    parser.add_argument("--slug", required=True,
                        help="kebab-case identifier (e.g. user-login-500-spike)")
    parser.add_argument("--date", default=date.today().isoformat(),
                        help="incident date YYYY-MM-DD (default: today)")
    parser.add_argument("--from-file",
                        help="read raw input from a file (default: stdin)")
    args = parser.parse_args()

    _validate_slug(args.slug)

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        print(f"error: --date must be YYYY-MM-DD, got '{args.date}'",
              file=sys.stderr)
        return 1

    raw = _read_raw(args)
    if not raw.strip():
        print("error: input is empty", file=sys.stderr)
        return 1

    stem = f"{args.date}_{args.slug}"
    raw_path = INCIDENTS_DIR / f"{stem}.raw.txt"
    target_md = INCIDENTS_DIR / f"{stem}.md"

    if target_md.exists():
        print(f"warning: {target_md} already exists — will overwrite raw "
              f"but the LLM should preserve / merge the .md", file=sys.stderr)

    _save_raw(raw, raw_path)
    _emit_extraction_prompt(target_md, raw_path, args.source, args.slug, args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
