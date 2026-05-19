#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local BM25 Wiki Search
Pure Python stdlib — zero external dependencies.

Indexes all .claude/wiki/**/*.md files (excluding wal/ and archive/)
and ranks by BM25 relevance. Replaces the manual Knowledge-Graph drill-down
when scope is unknown.

Usage:
  python3 wiki_search.py --query "API contract tenant isolation" --top 5
  python3 wiki_search.py --rebuild          # force index rebuild
  python3 wiki_search.py --query "migration" --json
  python3 wiki_search.py --status           # show index stats

Integration:
  Called by Context Funnel Rule 0 before manual drill-down.
  Agent reads the top-K paths and picks which to actually open.

Exit codes: 0=results found, 1=no results / help, 2=error
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

INDEX_PATH = ".claude/runs/local_intel/wiki_bm25.json"
WIKI_ROOT = ".claude/wiki"
SKIP_DIRS = {"wal", "archive", "__pycache__"}

# Below this corpus size, BM25 has too little signal vs. plain substring match.
# Fall back to substring search; switch to BM25 only once the wiki accumulates content.
BM25_MIN_CORPUS = 50

# BM25 hyperparameters (Robertson & Zaragoza, 2009)
K1 = 1.5
B = 0.75

_STOP = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "be",
    "this", "that", "it", "as", "not", "no", "do", "have", "has",
    "can", "will", "should", "must", "may", "all", "any", "each",
    # Chinese stop words
    "的", "是", "在", "和", "与", "或", "不", "也", "都",
})


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9_一-鿿\-]+", text.lower())
    return [t for t in tokens if len(t) >= 2 and t not in _STOP]


def _read_md(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def _collect_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    base = Path(WIKI_ROOT)
    if not base.exists():
        return docs
    for p in base.rglob("*.md"):
        if any(skip in p.parts for skip in SKIP_DIRS):
            continue
        rel = str(p).replace("\\", "/")
        docs[rel] = _read_md(rel)
    return docs


def _build(docs: dict[str, str]) -> dict:
    corpus: dict[str, list[str]] = {k: _tokenize(v) for k, v in docs.items()}
    dl = {k: len(v) for k, v in corpus.items()}
    N = len(dl)
    avgdl = sum(dl.values()) / max(N, 1)

    df: dict[str, int] = {}
    tf: dict[str, dict[str, int]] = {}
    for path, toks in corpus.items():
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
        for t in toks:
            tf.setdefault(t, {})[path] = tf.get(t, {}).get(path, 0) + 1

    # Store excerpt (first 300 chars of each doc) for display
    excerpts = {k: v[:300].replace("\n", " ").strip() for k, v in docs.items()}

    return {
        "N": N, "avgdl": avgdl, "dl": dl,
        "df": df, "tf": tf,
        "docs": list(docs.keys()),
        "excerpts": excerpts,
    }


def _score(query_tokens: list[str], doc: str, idx: dict) -> float:
    N, avgdl = idx["N"], idx["avgdl"]
    dl = idx["dl"].get(doc, 0)
    score = 0.0
    for t in set(query_tokens):
        df = idx["df"].get(t, 0)
        if df == 0:
            continue
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
        freq = idx["tf"].get(t, {}).get(doc, 0)
        tf_norm = (freq * (K1 + 1)) / (freq + K1 * (1 - B + B * dl / max(avgdl, 1)))
        score += idf * tf_norm
    return score


def search(query: str, idx: dict, top_k: int = 5) -> list[dict]:
    q = _tokenize(query)
    if not q:
        return []
    scored = [(doc, _score(q, doc, idx)) for doc in idx["docs"]]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for doc, s in scored:
        if s <= 0.0:
            break
        results.append({
            "path": doc,
            "score": round(s, 4),
            "excerpt": idx.get("excerpts", {}).get(doc, "")[:150],
        })
        if len(results) >= top_k:
            break
    return results


def _substring_fallback(query: str, top_k: int) -> list[dict]:
    """Pure-Python case-insensitive substring search. Used when corpus is too small for BM25
    to discriminate — zero external dependencies, works in any environment."""
    docs = _collect_docs()
    q = query.lower()
    results = []
    for path, content in docs.items():
        pos = content.lower().find(q)
        if pos >= 0:
            start = max(0, pos - 30)
            excerpt = content[start:start + 150].replace("\n", " ").strip()
            results.append({"path": path, "score": 1.0, "excerpt": excerpt})
            if len(results) >= top_k:
                break
    return results


def load_or_build(force: bool = False) -> dict:
    if not force and os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    docs = _collect_docs()
    idx = _build(docs)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False)
    return idx


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BM25 local wiki search (zero external dependencies)"
    )
    parser.add_argument("--query", "-q", default="", help="search query")
    parser.add_argument("--top", type=int, default=5, help="max results (default 5)")
    parser.add_argument("--rebuild", action="store_true", help="force index rebuild")
    parser.add_argument("--status", action="store_true", help="show index stats")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    idx = load_or_build(args.rebuild)

    if args.status or (args.rebuild and not args.query):
        info = {"documents": idx["N"], "avg_doc_length": round(idx["avgdl"], 1),
                "vocab_size": len(idx["df"]), "index_path": INDEX_PATH}
        if args.as_json:
            print(json.dumps(info))
        else:
            print(f"Wiki index: {idx['N']} docs | vocab {len(idx['df'])} terms | avglen {idx['avgdl']:.0f}")
        return 0

    if not args.query:
        parser.print_help()
        return 1

    if idx["N"] < BM25_MIN_CORPUS:
        results = _substring_fallback(args.query, args.top)
    else:
        results = search(args.query, idx, args.top)

    if args.as_json:
        print(json.dumps(results))
        return 0 if results else 1

    if not results:
        print("No relevant wiki documents found.")
        return 1

    print(f"Top {len(results)} results for: \"{args.query}\"")
    for r in results:
        print(f"  [{r['score']:.2f}] {r['path']}")
        if r["excerpt"]:
            print(f"         {r['excerpt'][:120]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
