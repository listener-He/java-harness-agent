#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Java Code Symbol Index
Pure Python regex — zero JVM / LSP / external dependencies.

Indexes Java source files to produce:
  - Symbol table:       class/method → file + line number
  - Import graph:       file → list of imported classes
  - Reverse import:     class → files that import it
  - Call graph (approx): file → method names it calls
  - Reverse call graph: method name → files that invoke it
  - SQL table refs:     table name → mapper XML files that reference it
  - @TableName map:     entity class → DB table name

Approximations (by design):
  - Method-call detection is name-only (not type-resolved). False positives
    exist for overloaded names. Use results as HINTS, not ground truth.
  - Inner classes are attributed to the outermost class per file.

Usage:
  python3 code_index.py --build
  python3 code_index.py --who-calls createOrder
  python3 code_index.py --what-touches-table orders
  python3 code_index.py --impact-of src/main/java/com/example/service/OrderService.java
  python3 code_index.py --symbol OrderService
  python3 code_index.py --status

Exit codes: 0=OK, 1=no results, 2=error/no index
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

INDEX_PATH = ".claude/local_intel/code_index.json"
DEFAULT_SRC = ["src/main/java", "src/test/java"]
DEFAULT_MAPPER = ["src/main/resources/mapper", "src/main/resources/mappers"]

_JAVA_KW = frozenset({
    "if", "else", "while", "for", "do", "switch", "case", "break", "continue",
    "return", "new", "this", "super", "throw", "throws", "try", "catch",
    "finally", "assert", "instanceof", "class", "interface", "enum", "record",
    "extends", "implements", "import", "package", "static", "final", "abstract",
    "public", "private", "protected", "void", "int", "long", "double", "float",
    "boolean", "char", "byte", "short", "null", "true", "false", "var",
    "synchronized", "volatile", "transient", "native", "strictfp", "default",
    "yield", "sealed", "permits", "non",
})


# ──────────────────────────── Java parser ────────────────────────────

def _parse_java(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return {}

    result: dict = {
        "file": path, "package": "", "classes": [], "imports": [],
        "methods": [], "calls": [], "annotations": [], "table_name": "",
    }

    # Package
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", content, re.M)
    if m:
        result["package"] = m.group(1)

    # Imports
    result["imports"] = re.findall(r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;", content, re.M)

    # @TableName("actual_table")
    m2 = re.search(r'@TableName\s*\(\s*(?:value\s*=\s*)?"(\w+)"', content)
    if m2:
        result["table_name"] = m2.group(1).lower()

    # Top-level class name (first match, outer class)
    cls_m = re.search(
        r"(?:public|private|protected)?\s*(?:abstract\s+|final\s+|sealed\s+)*"
        r"(?:class|interface|enum|record|@interface)\s+(\w+)",
        content,
    )
    primary_class = cls_m.group(1) if cls_m else Path(path).stem
    result["classes"] = re.findall(
        r"(?:class|interface|enum|record)\s+(\w+)", content
    )

    # Methods  (modifier* returnType name ( )
    method_pat = re.compile(
        r"^\s+(?:(?:public|private|protected|static|final|abstract|"
        r"synchronized|default|native|strictfp)\s+)+"
        r"(?:[\w<>\[\],\s?]+?)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*[{;]",
        re.M,
    )
    for mm in method_pat.finditer(content):
        name = mm.group(1)
        if name in _JAVA_KW or name[0].isupper():
            continue
        line = content[: mm.start()].count("\n") + 1
        result["methods"].append({
            "class": primary_class,
            "method": name,
            "qualified": f"{primary_class}.{name}",
            "line": line,
        })

    # Method calls (name followed by '(' — approximate)
    call_names: set[str] = set()
    for cm in re.finditer(r"\b(\w+)\s*\(", content):
        n = cm.group(1)
        if n not in _JAVA_KW and not n[0].isupper() and len(n) > 2:
            call_names.add(n)
    result["calls"] = list(call_names)

    # Annotations used
    result["annotations"] = list(set(re.findall(r"@(\w+)", content)))

    return result


def _parse_xml(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return {"file": path, "tables": [], "namespace": ""}

    tables: set[str] = set()
    for pat in [r"FROM\s+`?(\w+)`?", r"INTO\s+`?(\w+)`?",
                r"UPDATE\s+`?(\w+)`?", r"JOIN\s+`?(\w+)`?",
                r'tableName\s*=\s*"(\w+)"']:
        tables.update(t.lower() for t in re.findall(pat, content, re.I))
    # exclude SQL keywords that look like table names
    tables -= {"null", "true", "false", "select", "where", "limit", "order", "group"}

    ns_m = re.search(r'namespace\s*=\s*"([\w.]+)"', content)
    namespace = ns_m.group(1) if ns_m else ""

    return {"file": path, "tables": list(tables), "namespace": namespace}


# ──────────────────────────── Index build ────────────────────────────

def build(src_dirs: list[str] | None = None,
          mapper_dirs: list[str] | None = None) -> dict:
    src_dirs = src_dirs or DEFAULT_SRC
    mapper_dirs = mapper_dirs or DEFAULT_MAPPER

    java_files = [
        str(p).replace("\\", "/")
        for d in src_dirs if os.path.isdir(d)
        for p in Path(d).rglob("*.java")
    ]
    xml_files = [
        str(p).replace("\\", "/")
        for d in mapper_dirs if os.path.isdir(d)
        for p in Path(d).rglob("*.xml")
    ]

    symbols: dict[str, dict] = {}          # qualified → {file, line, class}
    file_symbols: dict[str, list[str]] = {}
    file_imports: dict[str, list[str]] = {}
    reverse_imports: dict[str, list[str]] = {}  # short class → files importing it
    reverse_calls: dict[str, list[str]] = {}    # method name → files that call it
    table_to_mappers: dict[str, list[str]] = {}
    entity_to_table: dict[str, str] = {}

    for jf in java_files:
        parsed = _parse_java(jf)
        if not parsed:
            continue
        file_imports[jf] = parsed["imports"]
        file_symbols[jf] = []

        for imp in parsed["imports"]:
            short = imp.split(".")[-1]
            reverse_imports.setdefault(short, [])
            if jf not in reverse_imports[short]:
                reverse_imports[short].append(jf)

        for m in parsed["methods"]:
            q = m["qualified"]
            symbols[q] = {"file": jf, "line": m["line"], "class": m["class"]}
            file_symbols[jf].append(q)

        for call_name in parsed["calls"]:
            reverse_calls.setdefault(call_name, [])
            if jf not in reverse_calls[call_name]:
                reverse_calls[call_name].append(jf)

        if parsed.get("table_name") and parsed.get("classes"):
            entity_to_table[parsed["classes"][0]] = parsed["table_name"]

    for xf in xml_files:
        parsed = _parse_xml(xf)
        for table in parsed["tables"]:
            table_to_mappers.setdefault(table, [])
            if xf not in table_to_mappers[table]:
                table_to_mappers[table].append(xf)

    return {
        "symbols": symbols,
        "file_symbols": file_symbols,
        "file_imports": file_imports,
        "reverse_imports": reverse_imports,
        "reverse_calls": reverse_calls,
        "table_to_mappers": table_to_mappers,
        "entity_to_table": entity_to_table,
        "java_files": java_files,
        "xml_files": xml_files,
    }


def save(index: dict) -> None:
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load() -> dict | None:
    if not os.path.exists(INDEX_PATH):
        return None
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────── Query API ──────────────────────────────

def who_calls(method_name: str, index: dict) -> list[str]:
    """Files that invoke this method name (approximate, name-only match)."""
    name = method_name.split(".")[-1]
    return list(set(index["reverse_calls"].get(name, [])))


def what_touches_table(table: str, index: dict) -> list[str]:
    """Mapper XML files that reference this table name."""
    return index["table_to_mappers"].get(table.lower(), [])


def find_symbol(name: str, index: dict) -> list[dict]:
    """Find all symbols (class.method) matching a name fragment."""
    name_lower = name.lower()
    results = []
    for q, info in index["symbols"].items():
        if name_lower in q.lower():
            results.append({"symbol": q, **info})
    return results


def impact_of(file_path: str, index: dict) -> dict:
    """
    Given a changed file, return all potentially impacted files.

    Strategy:
    1. Find all class names and method names defined in the file.
    2. Importers: files that import any of those classes.
    3. Callers: files that call any of those method names (by name).
    4. Union of importers + callers (excluding the file itself).
    """
    norm = file_path.replace("\\", "/")
    owned = index["file_symbols"].get(norm, [])
    class_names = {q.split(".")[0] for q in owned if "." in q}
    method_names = {q.split(".")[-1] for q in owned if "." in q}

    # If the file isn't indexed yet, derive class name from filename
    if not class_names:
        stem = Path(norm).stem
        class_names = {stem}

    importers = set()
    for cls in class_names:
        importers.update(index["reverse_imports"].get(cls, []))

    callers = set()
    for m in method_names:
        callers.update(index["reverse_calls"].get(m, []))

    all_impacted = (importers | callers) - {norm}

    return {
        "changed_file": norm,
        "owned_symbols": owned,
        "class_names": sorted(class_names),
        "importers": sorted(importers - {norm}),
        "callers": sorted(callers - {norm}),
        "all_impacted": sorted(all_impacted),
    }


# ──────────────────────────── CLI ────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local Java code symbol index (pure Python regex)"
    )
    parser.add_argument("--build", action="store_true", help="build / rebuild index")
    parser.add_argument("--src", nargs="*", help="override source dirs")
    parser.add_argument("--mapper", nargs="*", help="override mapper dirs")
    parser.add_argument("--who-calls", metavar="METHOD")
    parser.add_argument("--what-touches-table", metavar="TABLE")
    parser.add_argument("--impact-of", metavar="FILE")
    parser.add_argument("--symbol", metavar="NAME", help="search symbol by name fragment")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.build:
        print("Building code index...")
        idx = build(args.src, args.mapper)
        save(idx)
        print(f"Done: {len(idx['java_files'])} Java files | "
              f"{len(idx['symbols'])} symbols | "
              f"{len(idx['xml_files'])} mapper XMLs | "
              f"{len(idx['table_to_mappers'])} tables indexed")
        return 0

    idx = load()

    if args.status:
        if not idx:
            print("No index. Run --build first.")
            return 2
        info = {
            "java_files": len(idx["java_files"]),
            "symbols": len(idx["symbols"]),
            "xml_files": len(idx["xml_files"]),
            "tables": len(idx["table_to_mappers"]),
            "index_path": INDEX_PATH,
        }
        print(json.dumps(info) if args.as_json else
              f"Code index: {info['java_files']} files | {info['symbols']} symbols | "
              f"{info['tables']} tables")
        return 0

    if not idx:
        print("No code index. Run: python3 code_index.py --build", file=sys.stderr)
        return 2

    if args.who_calls:
        r = who_calls(args.who_calls, idx)
        print(json.dumps(r) if args.as_json else
              "\n".join(f"  {f}" for f in r) or "  (none found)")
        return 0 if r else 1

    if args.what_touches_table:
        r = what_touches_table(args.what_touches_table, idx)
        print(json.dumps(r) if args.as_json else
              "\n".join(f"  {f}" for f in r) or "  (none found)")
        return 0 if r else 1

    if args.impact_of:
        r = impact_of(args.impact_of, idx)
        if args.as_json:
            print(json.dumps(r))
        else:
            print(f"Impact of: {r['changed_file']}")
            print(f"  Classes defined:  {r['class_names']}")
            print(f"  Importers  ({len(r['importers'])}): {r['importers'][:5]}")
            print(f"  Callers    ({len(r['callers'])}): {r['callers'][:5]}")
            print(f"  Total impacted:   {len(r['all_impacted'])} files")
        return 0

    if args.symbol:
        r = find_symbol(args.symbol, idx)
        if args.as_json:
            print(json.dumps(r))
        else:
            for item in r[:20]:
                print(f"  {item['symbol']}  ({item['file']}:{item['line']})")
        return 0 if r else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
