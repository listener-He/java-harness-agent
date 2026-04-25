import os
import glob
import argparse
from pathlib import Path

WIKI_ROOT = ".agents/llm_wiki"

def get_all_wal_files():
    wal_files = []
    # Recursively find all .md files inside any directory named "wal" under WIKI_ROOT
    # Support arbitrary nesting inside the "wal" directory itself (e.g., wal/sub/dir/file.md)
    # We ignore any file that is inside an "applied" directory
    for path in Path(WIKI_ROOT).rglob("**/wal/**/*.md"):
        if "applied" not in path.parts:
            wal_files.append(str(path))
    return sorted(wal_files)

def aggregate():
    if not os.path.exists(WIKI_ROOT):
        print(f"Wiki root directory {WIKI_ROOT} does not exist.")
        return
    
    wal_files = get_all_wal_files()
    if not wal_files:
        print("No uncompacted WAL fragments found to aggregate.")
        return

    print(f"Found {len(wal_files)} WAL fragments ready for compaction:\n")
    for file in wal_files:
        print(f"================ START OF {file} ================")
        with open(file, 'r', encoding='utf-8') as f:
            print(f.read())
        print(f"================ END OF {file} ================\n")

def clean():
    if not os.path.exists(WIKI_ROOT):
        print(f"Wiki root directory {WIKI_ROOT} does not exist.")
        return
    
    wal_files = get_all_wal_files()
    if not wal_files:
        print("No uncompacted WAL fragments to clean.")
        return
        
    count = 0
    for file in wal_files:
        try:
            os.remove(file)
            count += 1
        except Exception as e:
            print(f"Failed to delete {file}: {e}")
            
    print(f"Successfully deleted {count} uncompacted WAL fragments. Garbage Collection complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Librarian GC Tool for WAL fragments")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate and print all WAL fragments for LLM to read")
    parser.add_argument("--clean", action="store_true", help="Delete all merged WAL fragments")
    args = parser.parse_args()

    if args.aggregate:
        aggregate()
    elif args.clean:
        clean()
    else:
        parser.print_help()