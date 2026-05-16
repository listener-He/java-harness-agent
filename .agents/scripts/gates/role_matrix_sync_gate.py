#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Matrix Sync Gate
Verifies role_matrix.json internal consistency:
  1. Every role referenced in mounts exists in the roles dict.
  2. Every role in the roles dict is either mounted or on-demand (known unmounted).
Exit: 0=PASS, 1=WARN, 2=FAIL
"""
import argparse
import json
import sys

ON_DEMAND_ROLES = {
    "librarian",           # @gc / @librarian explicit trigger
    "skill_graph_curator", # only when skill files change
    "subagent_contract_curator",  # only when subagent delegation used
    "security_sentinel",   # kept for Scenario A explicit reference
    "architecture_curator",
    "delivery_capsule_curator",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default=".agents/workflow/role_matrix.json")
    args = parser.parse_args()

    try:
        with open(args.matrix, "r", encoding="utf-8") as f:
            matrix = json.load(f)
    except FileNotFoundError:
        print(f"FAIL: matrix file not found: {args.matrix}")
        return 2
    except json.JSONDecodeError as e:
        print(f"FAIL: invalid JSON in {args.matrix}: {e}")
        return 2

    defined_roles = set(matrix.get("roles", {}).keys())
    mounts = matrix.get("mounts", [])

    mounted_roles: set[str] = set()
    errors: list[str] = []

    for i, mount in enumerate(mounts):
        intent = mount.get("intent", "?")
        profile = mount.get("profile", "?")
        phase = mount.get("phase", "?")
        for role in mount.get("roles", []):
            mounted_roles.add(role)
            if role not in defined_roles:
                errors.append(
                    f"  mount[{i}] ({intent}/{profile}/{phase}): role '{role}' not defined in roles dict"
                )

    warnings: list[str] = []
    for role in defined_roles:
        if role not in mounted_roles and role not in ON_DEMAND_ROLES:
            warnings.append(f"  role '{role}' defined but never mounted and not in ON_DEMAND_ROLES")

    if errors:
        print("FAIL: role_matrix.json has dangling role references:")
        for e in errors:
            print(e)
        return 2

    if warnings:
        print("WARN: role_matrix.json has orphaned role definitions:")
        for w in warnings:
            print(w)
        print("  Add to ON_DEMAND_ROLES in this gate if intentionally unmounted.")
        return 1

    print(f"PASS: {len(defined_roles)} roles defined, {len(mounted_roles)} mounted, {len(mounts)} mount rules — all consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
