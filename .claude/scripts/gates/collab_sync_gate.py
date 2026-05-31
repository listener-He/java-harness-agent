#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collab Sync Gate — verify .claude/runs/collabs/*_collab.md state files agree
with the latest launch_spec_*.md `| COLLAB:<token>` markers.

Why this exists:
  h-collab.md Step 6 appends `| COLLAB:<YYYYMMDD>-<slug>` to the launch_spec
  Artifact column when a collab is opened, and h-collab-update.md Step 6
  removes it on sign-off. Both are done by free-form Edit; nothing cross-checks
  consistency. If the agent crashes mid-edit, the user hand-edits one side,
  or a slug is reused, the two halves drift silently — /h-resume reads
  launch_spec, /h-collab-update reads the collab file, and they can disagree.

Detected drift patterns (all four are objective truth checkable from files):

  STALE-IN-SPEC    launch_spec has `| COLLAB:<token>` but the matching collab
                   file has `status: SIGNED_OFF` → h-collab-update Step 6 was
                   not applied; /h-resume will incorrectly report the task as
                   still waiting on external review.

  MISSING-MARKER   collab `status:` is PENDING_REVIEW or BLOCKED but no
                   matching `| COLLAB:<token>` exists in any row of the latest
                   launch_spec → marker was never added or was removed too
                   early; the wait state is invisible to /h-status.

  ORPHAN-COLLAB    collab references `task_brief: <path>` that no longer
                   exists on disk → task was archived or deleted but the
                   collab record was never finalized.

  DUP-COLLAB       multiple `<date>_<slug>_collab.md` files exist for the
                   same slug, more than one of them in a non-SIGNED_OFF
                   status → user re-ran /h-collab with `Overwrite` but the
                   prior file was never closed; or two parallel sessions
                   raced.

Exit codes (linter-severity-standard):
  0 — clean OR no .claude/runs/collabs/ directory (nothing to verify)
  1 — drift found; report lists each pattern with affected files
      **never exit 2.** Collab drift is a UX/visibility issue, not a safety
      red line. Hooks-vs-gates principle (feedback_hook_scope_principle):
      gates block only on objective safety (secrets / scope / mutating DDL).
      State drift here surfaces a warning the human resolves manually via
      /h-collab-update; it is not a basis to refuse work.

Usage:
  python3 .claude/scripts/gates/collab_sync_gate.py
  python3 .claude/scripts/gates/collab_sync_gate.py --launch-spec <path>
  python3 .claude/scripts/gates/collab_sync_gate.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
COLLAB_DIR = _REPO_ROOT / ".claude" / "runs" / "collabs"
LAUNCH_SPEC_DIR = _REPO_ROOT / ".claude" / "runs" / "launch-specs"

# Matches `| COLLAB:<token>` anywhere in a launch_spec row's Artifact column.
# Token format per h-collab.md Step 6: `<YYYYMMDD>-<slug>` (single hyphen
# between date and slug; slug itself may contain hyphens, so we anchor on
# `COLLAB:` and consume until whitespace or `|`).
_MARKER_RE = re.compile(r"\|\s*COLLAB:(?P<token>\S+?)(?=\s*\||\s*$)")

# Collab filename per h-collab.md Step 6: `<YYYYMMDD>_<slug>_collab.md`.
# Slug may contain hyphens but the trailing `_collab.md` is fixed.
_COLLAB_FN_RE = re.compile(r"^(?P<date>\d{8})_(?P<slug>.+)_collab\.md$")

# `status:` line inside collab YAML frontmatter.
_STATUS_RE = re.compile(r"^\s*status:\s*(?P<v>\S+)\s*$", re.MULTILINE)
# `task_brief:` pointer line.
_TASK_BRIEF_RE = re.compile(r"^\s*task_brief:\s*(?P<v>\S+)\s*$", re.MULTILINE)
# `slug:` line (collab file's own slug, used to detect filename/content drift).
_SLUG_RE = re.compile(r"^\s*slug:\s*(?P<v>\S+)\s*$", re.MULTILINE)

ACTIVE_STATUSES = {"PENDING_REVIEW", "BLOCKED"}
TERMINAL_STATUSES = {"SIGNED_OFF"}


def _rel(p: Path) -> str:
    """Path relative to repo root if possible, else absolute. Test fixtures and
    explicit `--collab-dir` overrides may legitimately point outside the repo."""
    try:
        return str(p.relative_to(_REPO_ROOT))
    except ValueError:
        return str(p)


def _latest_launch_spec() -> Path | None:
    if not LAUNCH_SPEC_DIR.is_dir():
        return None
    candidates = sorted(LAUNCH_SPEC_DIR.glob("launch_spec_*.md"))
    return candidates[-1] if candidates else None


def _markers_in_launch_spec(spec_path: Path) -> dict[str, str]:
    """Return {marker_token: row_excerpt}. Row excerpt for reporting only."""
    out: dict[str, str] = {}
    try:
        for raw in spec_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            for m in _MARKER_RE.finditer(raw):
                token = m.group("token")
                # First occurrence wins; later duplicates show up as DUP via
                # the marker→collab mapping in main(), not by overwriting here.
                out.setdefault(token, raw.strip())
    except OSError:
        pass
    return out


def _scan_collabs() -> list[dict]:
    """Return one dict per collab file with parsed metadata."""
    if not COLLAB_DIR.is_dir():
        return []
    results: list[dict] = []
    for p in sorted(COLLAB_DIR.iterdir()):
        if not p.is_file() or not p.name.endswith("_collab.md"):
            continue
        m = _COLLAB_FN_RE.match(p.name)
        if not m:
            # Filename doesn't match the convention — skip silently rather than
            # flag as drift; could be a hand-named file the user keeps on
            # purpose.
            continue
        date_token = m.group("date")
        slug = m.group("slug")
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        status_m = _STATUS_RE.search(content)
        task_brief_m = _TASK_BRIEF_RE.search(content)
        slug_m = _SLUG_RE.search(content)
        results.append({
            "path": _rel(p),
            "date_token": date_token,
            "slug_fn": slug,                          # slug from filename
            "slug_content": slug_m.group("v") if slug_m else "",
            "status": (status_m.group("v") if status_m else "").upper(),
            "task_brief": task_brief_m.group("v") if task_brief_m else "",
            "marker_token": f"{date_token}-{slug}",   # the form h-collab.md writes
        })
    return results


def _check(collabs: list[dict], markers: dict[str, str]) -> list[dict]:
    """Return list of drift records. Each record:
        {pattern, slug, detail, files: [<paths>]}
    """
    drifts: list[dict] = []

    # Index collabs by slug for cross-checks.
    by_slug: dict[str, list[dict]] = defaultdict(list)
    for c in collabs:
        by_slug[c["slug_fn"]].append(c)

    # Pattern 1: STALE-IN-SPEC — marker present, collab SIGNED_OFF
    # Pattern 2: MISSING-MARKER — collab active, no matching marker
    for c in collabs:
        token = c["marker_token"]
        status = c["status"]
        if status in TERMINAL_STATUSES and token in markers:
            drifts.append({
                "pattern": "STALE-IN-SPEC",
                "slug": c["slug_fn"],
                "detail": (
                    f"collab status={status} but launch_spec still carries "
                    f"`| COLLAB:{token}`; run /h-collab-update --signoff "
                    f"to clean, or manually remove marker"
                ),
                "files": [c["path"], "<latest launch_spec>"],
            })
        elif status in ACTIVE_STATUSES and token not in markers:
            drifts.append({
                "pattern": "MISSING-MARKER",
                "slug": c["slug_fn"],
                "detail": (
                    f"collab status={status} but no `| COLLAB:{token}` in "
                    f"latest launch_spec; /h-resume will not surface the wait"
                ),
                "files": [c["path"], "<latest launch_spec>"],
            })

    # Pattern 3: ORPHAN-COLLAB — task_brief path missing on disk
    for c in collabs:
        tb = c["task_brief"]
        if not tb:
            continue
        tb_path = (_REPO_ROOT / tb).resolve() if not Path(tb).is_absolute() else Path(tb)
        if not tb_path.exists():
            # Active task_brief moved to archive at Archive phase — check
            # the archive copy before flagging orphan.
            archive_guess = _REPO_ROOT / ".claude" / "wiki" / "archive" / Path(tb).name
            if archive_guess.exists():
                # task archived but collab not signed off → still a drift if
                # collab is active; benign if SIGNED_OFF.
                if c["status"] in ACTIVE_STATUSES:
                    drifts.append({
                        "pattern": "ORPHAN-COLLAB",
                        "slug": c["slug_fn"],
                        "detail": (
                            f"task_brief archived to {_rel(archive_guess)} "
                            f"but collab status={c['status']}; finalize or "
                            f"delete the collab record"
                        ),
                        "files": [c["path"]],
                    })
            else:
                drifts.append({
                    "pattern": "ORPHAN-COLLAB",
                    "slug": c["slug_fn"],
                    "detail": f"task_brief path does not exist: {tb}",
                    "files": [c["path"]],
                })

    # Pattern 4: DUP-COLLAB — same slug, > 1 active file
    for slug, group in by_slug.items():
        active = [c for c in group if c["status"] in ACTIVE_STATUSES]
        if len(active) > 1:
            drifts.append({
                "pattern": "DUP-COLLAB",
                "slug": slug,
                "detail": (
                    f"{len(active)} active collab files for slug `{slug}`; "
                    f"finalize older ones via /h-collab-update --signoff"
                ),
                "files": [c["path"] for c in active],
            })

    return drifts


def _format_text(drifts: list[dict], spec_path: Path | None,
                 n_collabs: int) -> str:
    spec_label = _rel(spec_path) if spec_path else "<none>"
    if not drifts:
        return (
            f"OK: collab_sync_gate — {n_collabs} collab file(s) consistent "
            f"with {spec_label}"
        )
    lines = [
        f"WARN: collab_sync_gate — {len(drifts)} drift(s) across "
        f"{n_collabs} collab file(s); latest spec: {spec_label}"
    ]
    for d in drifts:
        lines.append(
            f"- [{d['pattern']}] slug={d['slug']}: {d['detail']}"
        )
        for f in d["files"]:
            lines.append(f"    · {f}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Verify collab/*_collab.md ↔ launch_spec COLLAB markers."
    )
    p.add_argument("--launch-spec", default=None,
                   help="Override launch_spec path (default: latest in "
                        ".claude/runs/launch-specs/)")
    p.add_argument("--collab-dir", default=None,
                   help="Override collab dir (default: .claude/runs/collabs/)")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit JSON instead of text")
    args = p.parse_args()

    global COLLAB_DIR
    if args.collab_dir:
        COLLAB_DIR = Path(args.collab_dir).resolve()

    if args.launch_spec:
        spec_path: Path | None = Path(args.launch_spec).resolve()
        if not spec_path.exists():
            print(
                f"FAIL: collab_sync_gate — launch_spec not found: {args.launch_spec}",
                file=sys.stderr,
            )
            return 2
    else:
        spec_path = _latest_launch_spec()

    collabs = _scan_collabs()
    markers = _markers_in_launch_spec(spec_path) if spec_path else {}

    if not collabs:
        # Nothing to verify. Match research_report_gate "no input" semantics:
        # silent OK, not WARN — absence is the steady state for projects that
        # never use /h-collab.
        msg = (
            f"OK: collab_sync_gate — no collab files under {_rel(COLLAB_DIR)}"
        )
        if args.as_json:
            print(json.dumps({"severity": "OK", "gate": "collab_sync_gate",
                              "message": msg, "drifts": []}))
        else:
            print(msg)
        return 0

    drifts = _check(collabs, markers)

    if args.as_json:
        print(json.dumps({
            "severity": "OK" if not drifts else "WARN",
            "gate": "collab_sync_gate",
            "launch_spec": _rel(spec_path) if spec_path else None,
            "collab_count": len(collabs),
            "drifts": drifts,
        }, ensure_ascii=False))
    else:
        print(_format_text(drifts, spec_path, len(collabs)))

    return 0 if not drifts else 1


if __name__ == "__main__":
    raise SystemExit(main())
