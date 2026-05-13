import os
import json
import csv
from pathlib import Path
from datetime import datetime, timezone

# Directories to scan 
DIRECTORIES_TO_SCAN = [
    r"C:\Users\cheryl\ForensicTestUser\Documents",
    r"C:\Users\cheryl\ForensicTestUser\Desktop",
    r"C:\Users\cheryl\ForensicTestUser\Downloads",
    r"C:\Users\cheryl\ForensicTestUser\Pictures",
]

OUTPUT_JSON = Path(__file__).resolve().parent.parent / "outputs" / "filesystem_output.json"
OUTPUT_CSV = Path(__file__).resolve().parent.parent / "outputs" / "filesystem_output.csv"


def to_iso8601(ts: float) -> str:
    """Convert POSIX timestamp to ISO 8601 (UTC)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def scan_directory(root_path: str):
    records = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        for name in filenames:
            file_path = os.path.join(dirpath, name)
            try:
                stats = os.stat(file_path)

                created_time = to_iso8601(getattr(stats, "st_ctime", stats.st_mtime))
                modified_time = to_iso8601(stats.st_mtime)
                accessed_time = to_iso8601(stats.st_atime)

                record = {
                    "file_path": file_path,
                    "created_time": created_time,
                    "modified_time": modified_time,
                    "accessed_time": accessed_time,
                    "source": "filesystem_scanner",
                }
                records.append(record)
            except (FileNotFoundError, PermissionError):
                # Skip files we can't access
                continue

    return records


def save_json(records):
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)


def save_csv(records):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return

    fieldnames = list(records[0].keys())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main():
    all_records = []
    for directory in DIRECTORIES_TO_SCAN:
        if os.path.exists(directory):
            print(f"[+] Scanning: {directory}")
            records = scan_directory(directory)
            all_records.extend(records)
        else:
            print(f"[!] Skipping missing directory: {directory}")

    print(f"[+] Total files processed: {len(all_records)}")
    save_json(all_records)
    save_csv(all_records)
    print(f"[+] Saved JSON to: {OUTPUT_JSON}")
    print(f"[+] Saved CSV to:  {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
