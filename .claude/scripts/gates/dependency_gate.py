#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Gate (pom.xml change checker)

Parses a pom.xml and compares it against a baseline (git HEAD version)
to detect dependency additions, removals, and version changes.

Risk classification:
- FAIL: removing a dependency that is used in production scope
- WARN: adding a new dependency, or major/minor version bump
- PASS: patch version bump only, or no dependency changes

Exit codes:
- 0: PASS
- 1: WARN
- 2: FAIL
"""

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

EXIT_WARN = 1
EXIT_FAIL = 2

NS = {"m": "http://maven.apache.org/POM/4.0.0"}

PROD_SCOPES = {"compile", "runtime", None}
TEST_SCOPES = {"test", "provided"}


def _parse_deps(pom_content: str) -> dict[str, dict]:
    deps: dict[str, dict] = {}
    try:
        root = ET.fromstring(pom_content)
    except ET.ParseError as e:
        return {}

    for dep in root.findall(".//m:dependency", NS):
        group = (dep.findtext("m:groupId", namespaces=NS) or "").strip()
        artifact = (dep.findtext("m:artifactId", namespaces=NS) or "").strip()
        version = (dep.findtext("m:version", namespaces=NS) or "").strip()
        scope = (dep.findtext("m:scope", namespaces=NS) or "").strip() or None
        key = f"{group}:{artifact}"
        deps[key] = {"version": version, "scope": scope}
    return deps


def _get_baseline(pom_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{pom_path}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def _version_bump_level(old: str, new: str) -> str:
    old_parts = re.split(r"[.\-]", old.lstrip("v"))
    new_parts = re.split(r"[.\-]", new.lstrip("v"))
    for i in range(min(len(old_parts), len(new_parts))):
        if old_parts[i] != new_parts[i]:
            if i == 0:
                return "major"
            if i == 1:
                return "minor"
            return "patch"
    return "patch"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pom", required=True, help="Path to pom.xml")
    args = parser.parse_args()

    pom_path = args.pom
    if not os.path.exists(pom_path):
        print(f"FAIL: pom.xml not found: {pom_path}")
        return EXIT_FAIL

    with open(pom_path, "r", encoding="utf-8") as f:
        current_content = f.read()

    current_deps = _parse_deps(current_content)
    if not current_deps:
        print("WARN: dependency_gate — could not parse pom.xml dependencies")
        return EXIT_WARN

    baseline_content = _get_baseline(pom_path)
    if baseline_content is None:
        print("WARN: dependency_gate — no git baseline found (new file?); skipping diff")
        return EXIT_WARN

    baseline_deps = _parse_deps(baseline_content)

    added = {k: current_deps[k] for k in current_deps if k not in baseline_deps}
    removed = {k: baseline_deps[k] for k in baseline_deps if k not in current_deps}
    changed = {
        k: {"old": baseline_deps[k], "new": current_deps[k]}
        for k in current_deps
        if k in baseline_deps and baseline_deps[k]["version"] != current_deps[k]["version"]
    }

    if not added and not removed and not changed:
        print("OK: dependency_gate pass — no dependency changes")
        return 0

    overall = 0
    lines: list[str] = []

    for key, info in removed.items():
        scope = info.get("scope")
        if scope not in TEST_SCOPES:
            lines.append(f"FAIL: removed production dependency {key} (scope={scope or 'compile'})")
            overall = EXIT_FAIL
        else:
            lines.append(f"WARN: removed test/provided dependency {key} (scope={scope})")
            overall = max(overall, EXIT_WARN)

    for key, info in added.items():
        scope = info.get("scope")
        lines.append(f"WARN: added dependency {key}@{info['version']} (scope={scope or 'compile'})")
        overall = max(overall, EXIT_WARN)

    for key, versions in changed.items():
        old_v = versions["old"]["version"]
        new_v = versions["new"]["version"]
        level = _version_bump_level(old_v, new_v)
        if level in ("major", "minor"):
            lines.append(f"WARN: {level} version bump {key}: {old_v} → {new_v}")
            overall = max(overall, EXIT_WARN)
        else:
            lines.append(f"INFO: patch version bump {key}: {old_v} → {new_v}")

    label = "FAIL" if overall == EXIT_FAIL else "WARN"
    print(f"{label}: dependency_gate")
    for line in lines:
        print(f"- {line}")
    if overall == EXIT_FAIL:
        print("Action: create bypass_justification.md with compatibility evidence to downgrade to WARN.")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
