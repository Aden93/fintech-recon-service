import json
import requests
import time

API_URL = "http://localhost:8000/events"

def seed_data():
    print("Loading sample_events.json...")
    with open("sample_events.json", "r") as file:
        events = json.load(file)

    success_count = 0
    ignored_count = 0
    error_count = 0

    print(f"Sending {len(events)} events to {API_URL}...")
    start_time = time.time()

    for event in events:
        response = requests.post(API_URL, json=event)
        if response.status_code == 202:
            data = response.json()
            if data.get("status") == "success":
                success_count += 1
            else:
                ignored_count += 1 # Idempotent duplicates
        else:
            error_count += 1

    print(f"Done in {round(time.time() - start_time, 2)} seconds.")
    print(f"Success: {success_count} | Ignored (Duplicates): {ignored_count} | Errors: {error_count}")

if __name__ == "__main__":
    # Ensure dependencies for this script are installed locally: pip install requests
    seed_data()