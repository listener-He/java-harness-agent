import os
import glob
import argparse

WAL_DIR = "data/wal"

def aggregate():
    if not os.path.exists(WAL_DIR):
        print(f"WAL directory {WAL_DIR} does not exist.")
        return
    
    wal_files = glob.glob(os.path.join(WAL_DIR, "*.md"))
    if not wal_files:
        print("No WAL fragments found to aggregate.")
        return

    print(f"Found {len(wal_files)} WAL fragments ready for compaction:\n")
    for file in wal_files:
        print(f"================ START OF {file} ================")
        with open(file, 'r', encoding='utf-8') as f:
            print(f.read())
        print(f"================ END OF {file} ================\n")

def clean():
    if not os.path.exists(WAL_DIR):
        print(f"WAL directory {WAL_DIR} does not exist.")
        return
    
    wal_files = glob.glob(os.path.join(WAL_DIR, "*.md"))
    if not wal_files:
        print("No WAL fragments to clean.")
        return
        
    count = 0
    for file in wal_files:
        try:
            os.remove(file)
            count += 1
        except Exception as e:
            print(f"Failed to delete {file}: {e}")
            
    print(f"Successfully deleted {count} old WAL fragments. Garbage Collection complete.")

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