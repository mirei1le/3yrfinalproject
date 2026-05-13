import sqlite3
import json
from datetime import datetime, timedelta, timezone



# Convert Chromium/WebKit timestamps (microseconds since 1601)
# into readable datetime



def chromium_to_datetime(chromium_ts):
    # If timestamp is missing or zero, return nothing
    if chromium_ts is None or chromium_ts == 0:
        return None
    # Chromium epoch starts at 1601-01-01
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    
    # Add the microseconds to the epoch to get real datetime
    return epoch + timedelta(microseconds=int(chromium_ts))

# Connect to the test browser history database
db = "test_history.db" #fake history db

conn = sqlite3.connect(db)
cur = conn.cursor()

# Extract browser history from the 'urls' table
cur.execute("""
SELECT url, title, visit_count, typed_count, last_visit_time
FROM urls
""")

# Fetch all rows from the database

rows = cur.fetchall()
conn.close()

events = []

for url, title, visit_count, typed_count, last_visit in rows:
    ts = chromium_to_datetime(last_visit)
    events.append({
        "timestamp": ts.isoformat() if ts else "",
        "url": url,
        "title": title,
        "visit_count": visit_count,
        "typed_count": typed_count,
        "source": "browser_edge",
        "action": "visited_url"
    })

with open("browser_events.json", "w") as f:
    json.dump(events, f, indent=4)

print(" browser_events.json created!")