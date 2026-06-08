import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CITIES

load_dotenv()
API_KEY = os.getenv("TOMTOM_API_KEY")

# Bounding boxes: minLon, minLat, maxLon, maxLat
CITY_BBOX = {
    "Toronto":  "-79.6393,43.5810,-79.1154,43.8555",
    "New York": "-74.2591,40.4774,-73.7004,40.9176",
    "London":   "-0.5104,51.2868,0.3340,51.6919",
    "Mumbai":   "72.7760,18.8920,73.0760,19.2720",
    "Tokyo":    "139.5814,35.5244,139.9114,35.8174",
}

def fetch_traffic(city: dict) -> dict:
    name = city["name"]
    bbox = CITY_BBOX.get(name)

    url = (
        f"https://api.tomtom.com/traffic/services/5/incidentDetails"
        f"?bbox={bbox}&fields={{incidents{{type,geometry{{type}},properties{{iconCategory}}}}}}"
        f"&language=en-GB&timeValidityFilter=present&key={API_KEY}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    incidents = data.get("incidents", [])
    total     = len(incidents)

    # Score: 0–100 based on incident count
    # 0 incidents = 0, 50+ incidents = 100
    congestion_index = min(round((total / 1000) * 100, 2), 100)

    return {
        "city":             name,
        "timestamp":        datetime.utcnow().isoformat(),
        "incident_count":   total,
        "congestion_index": congestion_index,
    }

def run():
    os.makedirs("data/raw/traffic", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching traffic for {city['name']}...")
        try:
            result = fetch_traffic(city)
            results.append(result)
            print(f"  Incidents: {result['incident_count']}  Congestion index: {result['congestion_index']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/traffic/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()