#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAL Fragment Compactor

Merges wal/ fragments into their parent domain index.md files.
Designed for low-conflict windows (human-triggered or CI).

Protocol:
  1. Scan each domain's wal/ directory for unapplied fragments.
  2. Append each fragment's content after the domain index's ## WAL Fragments section.
  3. Move processed fragments to wal/applied/.
  4. If a fragment fails to parse, move it to wal/archive/ with a warning.

Usage:
  python3 wiki_compactor.py                    # compact all domains
  python3 wiki_compactor.py --domain api       # compact single domain
  python3 wiki_compactor.py --dry-run          # preview without modifying
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

WIKI_ROOT = ".claude/wiki/wiki"
DOMAINS = ["api", "data", "domain", "architecture", "specs", "testing", "reviews", "preferences"]


def _find_fragments(domain: str) -> list[Path]:
    """Return unapplied .md fragments in domain's wal/ dir, excluding applied/ and archive/ subdirs."""
    wal_dir = Path(WIKI_ROOT) / domain / "wal"
    if not wal_dir.exists():
        return []
    fragments = []
    for p in wal_dir.iterdir():
        if p.is_file() and p.suffix == ".md":
            fragments.append(p)
    return sorted(fragments)


def _read_index(domain: str) -> tuple[list[str], Path]:
    """Read the domain index file. Returns (lines, path)."""
    index_path = Path(WIKI_ROOT) / domain / "index.md"
    if not index_path.exists():
        return [], index_path
    with open(index_path, "r", encoding="utf-8") as f:
        return f.readlines(), index_path


def _append_fragment(lines: list[str], fragment: Path) -> list[str]:
    """Append fragment content to lines after ## WAL Fragments section."""
    with open(fragment, "r", encoding="utf-8") as f:
        content = f.read().strip()

    fragment_name = fragment.stem
    date_str = fragment_name[:8] if len(fragment_name) >= 8 else fragment_name

    # Find ## WAL Fragments marker to append after
    wal_marker = "## WAL Fragments"
    for i, line in enumerate(lines):
        if line.strip() == wal_marker:
            # Append after this section, before next ## heading
            insert_at = i + 1
            # Skip existing entries until next ## heading or end
            while insert_at < len(lines) and not lines[insert_at].startswith("## "):
                insert_at += 1

            new_entry = [
                f"\n### {fragment_name}\n",
                content + "\n",
            ]
            return lines[:insert_at] + new_entry + lines[insert_at:]

    # No WAL Fragments section found — add one at end
    new_section = [
        "\n## WAL Fragments\n",
        f"### {fragment_name}\n",
        content + "\n",
    ]
    return lines + new_section


def _move_fragment(fragment: Path, dest: str) -> None:
    """Move fragment to wal/<dest>/ directory."""
    target_dir = fragment.parent / dest
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / fragment.name
    fragment.rename(target)


def compact_domain(domain: str, dry_run: bool = False) -> int:
    """Compact a single domain. Returns number of fragments processed."""
    index_lines, index_path = _read_index(domain)
    fragments = _find_fragments(domain)

    if not fragments:
        return 0

    if not index_lines:
        print(f"[WARN] No index.md found for domain '{domain}', skipping")
        return 0

    count = 0
    for fragment in fragments:
        print(f"[{'DRY' if dry_run else 'APPLY'}] {domain}: merging {fragment.name}")

        if not dry_run:
            new_lines = _append_fragment(index_lines, fragment)
            with open(index_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            _move_fragment(fragment, "applied")
            index_lines = new_lines  # update for next fragment in same domain

        count += 1

    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WAL Fragment Compactor — merge wal/ fragments into domain indexes"
    )
    parser.add_argument("--domain", "-d", choices=DOMAINS, help="Compact single domain only")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else DOMAINS
    total = 0

    for domain in domains:
        total += compact_domain(domain, dry_run=args.dry_run)

    if total == 0:
        print("No unapplied WAL fragments found.")
    else:
        print(f"\n{'Would have processed' if args.dry_run else 'Processed'} {total} fragment(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
