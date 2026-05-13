import winreg
import json

# Function to read registry keys
def read_registry_key(hive, path):
    results = []
    try:
        key = winreg.OpenKey(hive, path)
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                results.append({
                    "name": name,
                    "value": str(value)
                })
                i += 1
            except OSError:
                break
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return results


# Extract Run Key (Startup Programs)
run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

run_data = read_registry_key(winreg.HKEY_CURRENT_USER, run_path)

# Extract RecentDocs

recent_docs_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"

recent_docs = read_registry_key(winreg.HKEY_CURRENT_USER, recent_docs_path)

# Store results in a dictionary
output = {
    "run_key": run_data,
    "recent_docs": recent_docs
}

# Save to JSON
with open("registry_output.json", "w") as f:
    json.dump(output, f, indent=4)

print("Registry extraction complete. Output saved to registry_output.json")
