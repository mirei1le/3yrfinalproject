import time
import json
import csv
from pathlib import Path
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DIRECTORIES_TO_MONITOR = [
    r"C:\Users\cheryl\ForensicTestUser\Documents",
    r"C:\Users\cheryl\ForensicTestUser\Desktop",
    r"C:\Users\cheryl\ForensicTestUser\Downloads",
    r"C:\Users\cheryl\ForensicTestUser\Pictures",
]

OUTPUT_JSON = Path(__file__).resolve().parent.parent / "outputs" / "monitor_output.json"
OUTPUT_CSV = Path(__file__).resolve().parent.parent / "outputs" / "monitor_output.csv"


def now_iso8601() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class MonitorHandler(FileSystemEventHandler):
    def __init__(self):
        self.records = []

    def _log_event(self, event_type: str, src_path: str, dest_path: str = None):
        record = {
            "event_type": event_type,
            "file_path": src_path,
            "destination_path": dest_path,
            "timestamp": now_iso8601(),
            "source": "monitor",
        }
        print(f"[{record['timestamp']}] {event_type}: {src_path}")
        self.records.append(record)

    def on_created(self, event):
        if not event.is_directory:
            self._log_event("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._log_event("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._log_event("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._log_event("moved", event.src_path, dest_path=event.dest_path)


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
    event_handler = MonitorHandler()
    observer = Observer()

    for directory in DIRECTORIES_TO_MONITOR:
        path = Path(directory)
        if path.exists():
            print(f"[+] Monitoring: {path}")
            observer.schedule(event_handler, str(path), recursive=True)
        else:
            print(f"[!] Skipping missing directory: {path}")

    observer.start()
    print("[+] Real-time monitoring started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Stopping observer...")
        observer.stop()

    observer.join()
    print(f"[+] Total events captured: {len(event_handler.records)}")
    save_json(event_handler.records)
    save_csv(event_handler.records)
    print(f"[+] Saved JSON to: {OUTPUT_JSON}")
    print(f"[+] Saved CSV to:  {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
