# We need pandas to build and sort the final table of events
import pandas as pd
# We need json to read the .json files that each team member produced
import json
# We need Path to build file paths that work on Windows, Mac, and Linux
from pathlib import Path
# We need re to check whether a piece of text is just a number (e.g. "42")
import re


# ------------------------------------------------------------------
# HELPER FUNCTION 1 — turn a timestamp string into a real date/time
# ------------------------------------------------------------------

# This function takes a timestamp text and converts it into a proper date/time object
def parse_iso(value):

    # If the value is empty or missing, there is nothing to convert — return nothing
    if not value:
        return None

    # Clean up the text: remove extra spaces, and swap the "Z" at the end
    # for "+00:00" because Python understands "+00:00" better than "Z"
    value = str(value).strip().replace("Z", "+00:00")

    # Try to convert the cleaned-up text into a real timestamp
    try:
        # Ask pandas to turn the text into a Timestamp object
        ts = pd.Timestamp(value)

        # If the timestamp has no timezone attached, assume it is UTC
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")

        # If the timestamp has a timezone but it is not UTC, convert it to UTC
        else:
            ts = ts.tz_convert("UTC")

        # Return the finished UTC timestamp
        return ts

    # If anything went wrong during conversion, just return nothing instead of crashing
    except Exception:
        return None


# ------------------------------------------------------------------
# HELPER FUNCTION 2 — print a warning when a timestamp is missing
# ------------------------------------------------------------------

# This function prints a warning message so we know which events have no timestamp
def warn_missing_ts(source, description):

    # Print the warning, showing which source module the event came from
    print(f"  [!] Missing timestamp — source='{source}' | {description[:80]}")


# ------------------------------------------------------------------
# MAIN LIST — we will add every event from every source into here
# ------------------------------------------------------------------

# Initialise an empty list that will hold all events from all sources
timeline_events = []


# ==================================================================
# SOURCE 1 — Registry data collected by Member 1 (cheryl)
# ==================================================================

# Build the path to the registry JSON file
registry_path = Path("../member1_registry_eventlogs/registry_output.json")

# Only try to read the file if it actually exists on disk
if registry_path.exists():

    # Open and read the file, then parse it from JSON text into a Python dictionary
    registry_data = json.loads(registry_path.read_text(encoding="utf-8"))

    # --- Run Keys (programmes that launch automatically when Windows starts) ---

    # Loop through every startup programme entry in the "run_key" section
    for entry in registry_data.get("run_key", []):

        # Try to get the timestamp — check "timestamp" first, then "last_written" as a backup
        raw_ts = entry.get("timestamp") or entry.get("last_written")

        # Add this startup programme as one event in our main list
        timeline_events.append({
            # The date and time this registry key was last changed
            "timestamp":     raw_ts,
            # A short label describing what kind of event this is
            "event_type":    "registry_run_key",
            # Which module collected this data
            "source_module": "Registry",
            # Extra details about this specific event
            "details": {
                "name":        entry.get("name"),
                "description": f"Startup program: {entry.get('name')}",
            },
        })

    # --- Recent Docs (files the user recently opened) ---

    # Loop through every recent document entry in the "recent_docs" section
    for entry in registry_data.get("recent_docs", []):

        # Get the name of the document from this entry (default to empty string if missing)
        name = entry.get("name", "")

        # Skip this entry if: the name is empty, it is the special "MRUListEx" index,
        # or it is just a plain number (those are slot indexes, not real filenames)
        if not name or name == "MRUListEx" or re.fullmatch(r"\d+", str(name)):
            continue

        # Try to get the timestamp — check "timestamp" first, then "last_written" as a backup
        raw_ts = entry.get("timestamp") or entry.get("last_written")

        # Add this recent document as one event in our main list
        timeline_events.append({
            # The date and time this registry key was last changed
            "timestamp":     raw_ts,
            # A short label describing what kind of event this is
            "event_type":    "registry_recent_doc",
            # Which module collected this data
            "source_module": "Registry",
            # Extra details about this specific event
            "details": {
                "name":        name,
                "description": f"Recent document accessed: {name}",
            },
        })

    # Tell the user that registry data loaded successfully
    print("[+] Loaded registry data")

# If the file was not found, print a warning instead of crashing
else:
    print(f"[!] Not found: {registry_path}")


# ==================================================================
# SOURCE 2 — Filesystem scan collected by Member 2 (favour)
# ==================================================================

# Build the path to the filesystem scanner JSON file
fs_path = Path("../member2_filesystem_monitoring/filesystem_output.json")

# Only try to read the file if it actually exists on disk
if fs_path.exists():

    # Open and read the file, then parse it from JSON text into a Python list
    fs_data = json.loads(fs_path.read_text(encoding="utf-8"))

    # Loop through every file record that the scanner found
    for entry in fs_data:

        # Try created_time first, then modified_time, then accessed_time as fallbacks
        raw_ts = (
            entry.get("created_time")
            or entry.get("modified_time")
            or entry.get("accessed_time")
        )

        # Get the full path of the file
        file_path = entry.get("file_path", "")

        # Add this file as one event in our main list
        timeline_events.append({
            # The best available timestamp for this file
            "timestamp":     raw_ts,
            # A short label describing what kind of event this is
            "event_type":    "file_found",
            # Which module collected this data
            "source_module": "Filesystem",
            # Extra details about this specific event
            "details": {
                "file_path":   file_path,
                "description": f"File found: {file_path}",
            },
        })

    # Tell the user that filesystem data loaded successfully
    print("[+] Loaded filesystem data")

# If the file was not found, print a warning instead of crashing
else:
    print(f"[!] Not found: {fs_path}")


# ==================================================================
# SOURCE 3 — Live file monitor also collected by Member 2
# ==================================================================

# Build the path to the live monitor JSON file
monitor_path = Path("../member2_filesystem_monitoring/monitor_output.json")

# Only try to read the file if it actually exists on disk
if monitor_path.exists():

    # Open and read the file, then parse it from JSON text into a Python list
    monitor_data = json.loads(monitor_path.read_text(encoding="utf-8"))

    # Loop through every real-time file event that the monitor recorded
    for entry in monitor_data:

        # Get the type of event, e.g. "created", "deleted", "moved"
        event_type = entry.get("event_type", "unknown")

        # Get the file path where the event happened
        file_path = entry.get("file_path", "")

        # Get the destination path (only relevant if a file was moved or renamed)
        dest_path = entry.get("destination_path", "")

        # Build a human-readable description, e.g. "created: C:\Users\..."
        desc = f"{event_type}: {file_path}"

        # If there is a destination path, add it to the description with an arrow
        if dest_path:
            desc += f" → {dest_path}"

        # Add this monitor event to our main list
        timeline_events.append({
            # The date and time this event was recorded
            "timestamp":     entry.get("timestamp"),
            # A short label combining "monitor_" with the event type
            "event_type":    f"monitor_{event_type}",
            # Which module collected this data
            "source_module": "Monitor",
            # Extra details about this specific event
            "details": {
                "file_path":        file_path,
                # Store destination path, or None if this was not a move event
                "destination_path": dest_path or None,
                "description":      desc,
            },
        })

    # Tell the user that monitor data loaded successfully
    print("[+] Loaded monitor data")

# If the file was not found, print a warning instead of crashing
else:
    print(f"[!] Not found: {monitor_path}")


# ==================================================================
# SOURCE 4 — Browser history collected by Member 3
# ==================================================================

# Build the path to the browser history JSON file
browser_path = Path("outputs/browser_events.json")

# Only try to read the file if it actually exists on disk
if browser_path.exists():

    # Open and read the file, then parse it from JSON text into a Python list
    browser_data = json.loads(browser_path.read_text(encoding="utf-8"))

    # Loop through every website visit that was recorded
    for entry in browser_data:

        # Get the timestamp of when the site was visited
        raw_ts = entry.get("timestamp")

        # Get the web address (URL) of the page that was visited
        url = entry.get("url", "")

        # Get the title of the page, e.g. "Google" or "YouTube"
        title = entry.get("title", "")

        # Add this browser visit as one event in our main list
        timeline_events.append({
            # The date and time the page was visited
            "timestamp":     raw_ts,
            # A short label describing what kind of event this is
            "event_type":    "browser_visit",
            # Which module collected this data
            "source_module": "Browser",
            # Extra details about this specific event
            "details": {
                "url":         url,
                "title":       title,
                "description": f"Visited: {url} — {title}",
            },
        })

    # Tell the user that browser data loaded successfully
    print("[+] Loaded browser data")

# If the file was not found, print a warning instead of crashing
else:
    print(f"[!] Not found: {browser_path}")


# ==================================================================
# BUILD THE FINAL TIMELINE
# ==================================================================

# If the events list is still empty, nothing loaded — warn the user and stop
if not timeline_events:
    print("\n[!] No events loaded — check that the paths above exist.")

# Otherwise, build the timeline from all the events we collected
else:

    # Initialise an empty list to hold the final cleaned-up rows for the CSV
    rows = []

    # Go through every event we collected across all sources
    for ev in timeline_events:

        # Try to convert the raw timestamp text into a proper UTC date/time object
        ts = parse_iso(ev.get("timestamp"))

        # If the timestamp could not be converted, print a warning for that event
        if ts is None:
            warn_missing_ts(
                ev.get("source_module", "?"),
                ev["details"].get("description", ""),
            )

        # If we have a valid timestamp, format it as ISO-8601 UTC
        # Example result: 2026-04-14T14:22:10.123Z
        if ts:
            # Format the timestamp and trim microseconds down to milliseconds, then add "Z"
            formatted_ts = ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        # If there is no timestamp, store a blank string so the CSV cell is empty
        else:
            formatted_ts = ""

        # Build the final row for this event and add it to the rows list
        rows.append({
            # The standardised UTC timestamp (or blank if missing)
            "timestamp":     formatted_ts,
            # The short event type label, e.g. "browser_visit"
            "event_type":    ev.get("event_type", ""),
            # The name of the module that collected this event
            "source_module": ev.get("source_module", ""),
            # The plain-English description of what happened
            "description":   ev["details"].get("description", ""),
            # All the extra details packed into a JSON string for further analysis
            "details_json":  json.dumps(ev.get("details", {})),
        })

    # Turn the list of rows into a pandas DataFrame (basically a spreadsheet in memory)
    df = pd.DataFrame(rows)

    # Create a True/False column: True if the row has a timestamp, False if it is blank
    has_time = df["timestamp"] != ""

    # Sort the table so that events with timestamps come first (oldest to newest),
    # and events with no timestamp go at the very bottom
    df = pd.concat([
        # Rows that have a timestamp, sorted from earliest to latest
        df[has_time].sort_values("timestamp"),
        # Rows with no timestamp, kept in the order they were collected
        df[~has_time],
    # Reset the row numbers so they run cleanly from 0 at the top
    ]).reset_index(drop=True)

    # Save the finished timeline table as a CSV file in the current folder
    df.to_csv("timeline_final.csv", index=False)

    # Print a summary so the user knows how many events ended up in the file
    print(f"\n[+] Done! timeline_final.csv created with {len(df)} events.")
    # Show how many events had a proper timestamp
    print(f"    Timestamped : {has_time.sum()}")
    # Show how many were missing a timestamp and remind the user to fix those source modules
    print(f"    No timestamp: {(~has_time).sum()} (check warnings above — source modules need fixing)")