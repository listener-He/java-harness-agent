#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evidence Probe — collect 5 evidence signals + emit one advisory profile hint.

NOT a classifier. As of P2/P3 (Sensor/Policy/Enforce refactor) this script
is NO LONGER auto-invoked by UserPromptSubmit hook. It is now an explicit
CLI tool the agent calls when it wants a one-shot evidence snapshot
(e.g., from /h-context-check, or directly when reading an ambiguous prompt).

Signals collected (all deterministic, <500ms):
  - blast_radius: code_index.py --impact-of for each file hint
  - failure_history: failure_memory.py summary --days 30 --min-count 2
  - ambiguity: ambiguity_gate._check_intent → OK / WARN / FAIL
  - danger_keywords: static scan against HIGH / MEDIUM tier word lists
                     (display-only — agent decides what to do)
  - intent_class: ambiguity_gate.classify_intent → CHANGE / RESEARCH / OTHER

Output:
  - default (human): a [triage-evidence] block; silent if no evidence worth showing
  - --json: structured dict for downstream consumers

The slow-path 'needs_semantic_review' auto-emission was removed: agent now
decides whether to dispatch the triage-reviewer Haiku sub-agent based on
its own semantic read, not on a keyword heuristic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / ".claude" / "scripts" / "local_intel"))
sys.path.insert(0, str(_REPO_ROOT / ".claude" / "scripts" / "gates"))

import code_index  # noqa: E402
import failure_memory  # noqa: E402
import ambiguity_gate  # noqa: E402

HARD_SKIP_SHORTCUTS = (
    "@learn", "@read",
    "@distill",
)

MIN_LEN_FOR_PROBE = 15

# HIGH-tier keywords. Display-only — agent semantically decides what to do
# with them. They surface in the [triage-evidence] keywords_observed line so
# the caller can grep / decide. (Pre-P5 these also drove an auto-trigger of
# the triage-reviewer sub-agent; that logic was removed — agent owns the
# decision now.) Grouped by category for maintenance.
DANGER_HIGH = (
    # Authentication & authorization
    "auth", "authentication", "authorize", "authorization",
    "sso", "oauth", "oauth2", "oidc", "saml", "jwt",
    "login", "logout", "signin", "sign-in", "signup", "sign-up",
    "signout", "sign-out", "password",
    "permission", "permissions", "rbac", "abac",
    "认证", "鉴权", "授权", "权限", "登录", "登出", "注销", "密码",
    # Credentials / crypto / keys
    "secret", "secrets", "token", "tokens",
    "credential", "credentials",
    "api key", "apikey", "api-key", "access key", "access-key",
    "private key", "public key", "certificate", "x509", "x.509",
    "encrypt", "decrypt", "cipher", "ssl", "tls", "mtls",
    "凭证", "密钥", "私钥", "证书",
    # Mutating DDL / schema migration (existing data at risk)
    "alter table", "drop column", "drop table", "drop index",
    "modify column", "rename column", "rename table",
    "truncate table", "cascade",
    "migration", "migrations", "schema migration", "data migration",
    "迁移", "改表",
    # Anti-patterns banned by project standards
    "hard delete", "hard-delete", "物理删除",
    # Error contract / API breaking
    "error code", "错误码", "errcode",
    "breaking change", "breaking-change", "不兼容",
    # Compliance / PII / security
    "gdpr", "pii", "personal data", "personally identifiable",
    "cve", "vulnerability", "exploit",
    "个人信息", "隐私", "脱敏", "漏洞",
    # Harness routing / policy files (edits cascade to every task)
    "lifecycle", "lifecycle.md", "policy.md", "dispatch-template",
    "skill-precedence", "tasklist-policy", "claude.md", "settings.json",
)

# MEDIUM-tier keywords. Display only; NOT a Probe Override trigger (only
# HIGH triggers override). Useful as a soft hint that the change touches
# extensible / cross-cutting surfaces. Categorized for the same reason.
DANGER_MEDIUM = (
    # Public API surface
    "public api", "endpoint", "endpoints", "rest", "rest api",
    "graphql", "grpc", "openapi", "swagger",
    "公共 api", "签名", "接口",
    # Harness hook / gate / framework surface
    "hook", "hooks", "gate", "gates",
    "framework", "frameworks", "架构",
    # Additive / generic schema talk (PATCH-able when isolated)
    "create table", "create index", "ddl",
    "schema", "schemas", "backfill", "rollback",
    # Build manifests & dependency surface
    "pom.xml", "build.gradle", "package.json", "requirements.txt",
    "maven", "gradle", "依赖", "dependency",
    # Configuration / environment
    "env var", "environment variable", ".env",
    "config map", "configmap", "feature flag", "环境变量",
    # Concurrency / transactional state
    "transaction", "transactional", "lock", "mutex", "semaphore",
    "事务", "锁",
    # Caching / consistency
    "cache invalidation", "cache eviction", "缓存一致性",
)

FILE_HINT_PAT = re.compile(
    r"""(
        src/[\w/-]+\.java
        | src/[\w/-]+\.xml
        | \.claude/[\w./-]+\.md
        | [A-Z][A-Za-z0-9]+\.java
        | [A-Z][A-Za-z0-9]*(?:Service|Mapper|Controller|Repository|Manager)
    )""",
    re.VERBOSE,
)


def _read_prompt() -> str:
    try:
        raw = sys.stdin.read()
    except Exception:
        return ""
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                for key in ("prompt", "user_prompt", "input", "text"):
                    v = obj.get(key)
                    if isinstance(v, str):
                        return v
        except json.JSONDecodeError:
            pass
    return raw


def _should_skip(prompt: str) -> bool:
    t = prompt.strip().lower()
    if len(t) < MIN_LEN_FOR_PROBE:
        return True
    if any(sc in t for sc in HARD_SKIP_SHORTCUTS):
        return True
    if t.endswith("?") or t.endswith("？"):
        action_verbs = (
            "改", "加", "修", "删", "实现", "新增", "重构", "迁移",
            "fix", "add", "implement", "refactor", "remove", "delete",
            "migrate", "update", "change", "create", "build",
        )
        if not any(v in t for v in action_verbs):
            return True
    return False


def _extract_file_hints(prompt: str) -> list[str]:
    hints: list[str] = []
    for m in FILE_HINT_PAT.finditer(prompt):
        h = m.group(1)
        if h not in hints:
            hints.append(h)
    return hints[:5]


def _probe_blast_radius(hints: list[str]) -> dict:
    if not hints:
        return {"files": 0, "callers": 0, "hints_resolved": 0, "sample": []}

    idx = code_index.load()
    if idx is None:
        return {"files": 0, "callers": 0, "hints_resolved": 0, "sample": []}

    impacted: set[str] = set()
    callers_total = 0
    resolved = 0
    for hint in hints:
        try:
            data = code_index.impact_of(hint, idx)
        except (KeyError, ValueError):
            continue
        impacted_here = data.get("all_impacted") or []
        if impacted_here:
            resolved += 1
            impacted.update(impacted_here)
            callers_total += len(data.get("callers") or [])

    return {
        "files": len(impacted),
        "callers": callers_total,
        "hints_resolved": resolved,
        "sample": sorted(impacted)[:3],
    }


def _probe_failure_history() -> dict:
    try:
        items = failure_memory.summary(days=30, min_count=2, top=3)
    except Exception:
        items = []
    return {
        "recurring": len(items),
        "top_pattern": items[0].get("pattern", "") if items else "",
    }


def _probe_ambiguity(prompt: str) -> str:
    try:
        code, _ = ambiguity_gate._check_intent(prompt[:500])
    except Exception:
        return "OK"
    return {0: "OK", 1: "WARN", 2: "FAIL"}.get(code, "OK")


_WORD_BOUNDARY_RE_CACHE: dict[str, "re.Pattern[str]"] = {}


def _kw_match(keyword: str, lowered_text: str) -> bool:
    if keyword.isascii() and keyword.isalnum():
        pat = _WORD_BOUNDARY_RE_CACHE.get(keyword)
        if pat is None:
            pat = re.compile(rf"\b{re.escape(keyword)}\b")
            _WORD_BOUNDARY_RE_CACHE[keyword] = pat
        return pat.search(lowered_text) is not None
    return keyword in lowered_text


def _scan_danger_keywords(prompt: str) -> tuple[list[str], list[str]]:
    t = prompt.lower()
    high = [k for k in DANGER_HIGH if _kw_match(k, t)]
    medium = [k for k in DANGER_MEDIUM if _kw_match(k, t)]
    return high, medium


def _format_evidence(blast: dict, failure: dict, ambiguity: str,
                     high_kw: list[str], medium_kw: list[str],
                     intent_class: str) -> str:
    """Render evidence as text. Pure formatter — no classification, no escalation.

    The single 'profile_hint' line is advisory only; the literal suffix
    '(you decide)' is intentional — the calling agent owns the decision.
    """
    lines = ["[triage-evidence]"]

    if blast["files"] > 0:
        sample = ", ".join(blast["sample"])
        lines.append(
            f"files_impacted: {blast['files']} "
            f"(callers={blast['callers']}, sample: {sample})"
        )
    if failure["recurring"] > 0:
        lines.append(
            f"recurring_failures_30d: {failure['recurring']} "
            f"(top: {failure['top_pattern']})"
        )
    if ambiguity != "OK":
        lines.append(f"ambiguity_check: {ambiguity}")
    if high_kw or medium_kw:
        lines.append(f"keywords_observed: {', '.join(high_kw + medium_kw)}")
    if intent_class == "RESEARCH":
        lines.append("intent_class: RESEARCH (analyze / feasibility verb detected)")

    if intent_class == "RESEARCH":
        lines.append("profile_hint: RESEARCH (verb-driven; you decide)")
    elif high_kw or blast["files"] >= 7 or failure["recurring"] >= 3:
        lines.append("profile_hint: STANDARD-tier signals present (you decide)")
    elif blast["files"] >= 3 or ambiguity == "FAIL":
        lines.append("profile_hint: PATCH-tier signals (you decide)")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evidence probe — emit [triage-evidence] block"
    )
    parser.add_argument("--prompt-file",
                        help="read prompt from file (default: stdin)")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--quiet-on-skip", action="store_true",
                        help="silent exit when heuristic skip triggers")
    args = parser.parse_args()

    if os.environ.get("CLAUDE_TRIAGE_QUIET") == "1":
        return 0

    if args.prompt_file:
        try:
            with open(args.prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
        except OSError:
            print("(triage: prompt file not found)", file=sys.stderr)
            return 1
    else:
        prompt = _read_prompt()

    if _should_skip(prompt):
        if args.as_json and not args.quiet_on_skip:
            print(json.dumps({"skipped": True}))
        return 0

    hints = _extract_file_hints(prompt)
    blast = _probe_blast_radius(hints)
    failure = _probe_failure_history()
    ambiguity = _probe_ambiguity(prompt)
    high_kw, medium_kw = _scan_danger_keywords(prompt)
    intent_class = ambiguity_gate.classify_intent(prompt[:500])

    text = _format_evidence(blast, failure, ambiguity, high_kw, medium_kw, intent_class)

    if args.as_json:
        # Extract profile_hint from rendered text (single source of truth for the rule).
        hint_line = next(
            (ln.split(": ", 1)[1] for ln in text.splitlines()
             if ln.startswith("profile_hint:")),
            "",
        )
        result = {
            "intent_class": intent_class,
            "profile_hint": hint_line,
            "blast_radius": blast,
            "failure_history": failure,
            "ambiguity": ambiguity,
            "danger_keywords": {"high": high_kw, "medium": medium_kw},
            "file_hints": hints,
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # Human-readable: silent if no evidence beyond the bare header.
    if text.strip() == "[triage-evidence]":
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
