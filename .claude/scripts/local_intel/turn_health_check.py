#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turn Health Check — observable consistency checks at end of an agent turn.

Runs three lightweight checks based on observable git/filesystem state:
  1. Java compile staleness — if pom.xml exists and recent .java edits do not
     match a fresher .class under target/classes/, suggest `mvn compile`.
  2. Uncommitted change pile-up — if >= 5 files in `git diff --name-only HEAD`,
     suggest stashing or committing.
  3. launch_spec ↔ artifact drift — if an IN_PROGRESS row references a missing
     or archived task_brief, surface the inconsistency.

Each check is silent when there is nothing to surface. The script prints a
single [turn-health] block when ≥1 check has findings. Non-blocking — the
caller (Stop hook) should always exit 0 regardless of this script's output.

Quiet env: CLAUDE_TURN_HEALTH_QUIET=1
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
from pathlib import Path

UNCOMMITTED_THRESHOLD = 5
LAUNCH_DIR = ".claude/runs/launch-specs"


def _git_changed_files() -> list[str]:
    """Files with uncommitted changes vs HEAD (modified, added, renamed)."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
            check=False, capture_output=True, text=True, timeout=2,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]


def _check_java_stale(changed: list[str]) -> str:
    """Only meaningful in Maven/Gradle projects. Skip otherwise."""
    if not (Path("pom.xml").exists() or Path("build.gradle").exists()
            or Path("build.gradle.kts").exists()):
        return ""
    java_files = [f for f in changed if f.endswith(".java") and Path(f).exists()]
    if not java_files:
        return ""
    target_dir = Path("target/classes")
    if not target_dir.exists():
        return (f"{len(java_files)} Java file(s) changed but target/classes/ is missing — "
                f"run `mvn compile` to verify the change builds.")
    # Sample up to 3 files: if any .java is newer than its candidate .class,
    # build is stale. We can't perfectly resolve .java → .class without parsing
    # package declarations, so we approximate using filename stem.
    stale = []
    for jf in java_files[:3]:
        stem = Path(jf).stem
        candidates = list(target_dir.rglob(f"{stem}.class"))
        if not candidates:
            stale.append(jf)
            continue
        java_mtime = Path(jf).stat().st_mtime
        if all(c.stat().st_mtime < java_mtime for c in candidates):
            stale.append(jf)
    if stale:
        return (f"{len(stale)}/{len(java_files)} sampled Java file(s) appear unbuilt "
                f"(.class older than .java or missing) — consider `mvn compile`.")
    return ""


def _check_uncommitted_pile(changed: list[str]) -> str:
    if len(changed) < UNCOMMITTED_THRESHOLD:
        return ""
    return (f"{len(changed)} files changed without a commit — consider committing "
            f"or stashing to keep the diff focused. Sample: "
            f"{', '.join(sorted(changed)[:3])}…")


def _check_launch_spec_drift() -> str:
    if not os.path.isdir(LAUNCH_DIR):
        return ""
    specs = sorted(glob.glob(os.path.join(LAUNCH_DIR, "launch_spec_*.md")))
    if not specs:
        return ""
    latest = specs[-1]
    try:
        text = Path(latest).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    has_in_progress = False
    missing_artifact: str | None = None
    for line in text.splitlines():
        if "IN_PROGRESS" not in line:
            continue
        has_in_progress = True
        cells = [c.strip() for c in line.split("|")]
        for cell in cells:
            m = re.search(r"(\.claude/runs/task-briefs/[^\s|`)]+\.md)", cell)
            if m and not os.path.isfile(m.group(1)):
                missing_artifact = m.group(1)
                break
        if missing_artifact:
            break
    if missing_artifact:
        return (f"launch_spec IN_PROGRESS row references missing artifact: "
                f"{missing_artifact} (was it archived without status update?)")
    if has_in_progress:
        # Implicit check: if IN_PROGRESS exists and artifact is present, OK.
        return ""
    # No IN_PROGRESS row → nothing to drift against.
    return ""


def main() -> int:
    if os.environ.get("CLAUDE_TURN_HEALTH_QUIET") == "1":
        return 0

    changed = _git_changed_files()
    findings: list[str] = []
    for check in (
        _check_java_stale(changed),
        _check_uncommitted_pile(changed),
        _check_launch_spec_drift(),
    ):
        if check:
            findings.append(check)

    if not findings:
        return 0

    print("[turn-health]")
    for f in findings:
        print(f"  - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
