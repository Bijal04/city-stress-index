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

def fetch_traffic(city: dict) -> dict:
    lat = city["lat"]
    lon = city["lon"]

    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData/"
        f"absolute/10/json?point={lat},{lon}&unit=KMPH&key={API_KEY}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    flow = data.get("flowSegmentData", {})
    current_speed   = flow.get("currentSpeed", 0)
    free_flow_speed = flow.get("freeFlowSpeed", 1)

    congestion_index = round((1 - current_speed / free_flow_speed) * 100, 2)

    return {
        "city":                  city["name"],
        "timestamp":             datetime.utcnow().isoformat(),
        "current_speed_kmph":    current_speed,
        "free_flow_speed_kmph":  free_flow_speed,
        "congestion_index":      max(0, congestion_index),
    }

def run():
    os.makedirs("data/raw/traffic", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching traffic for {city['name']}...")
        try:
            result = fetch_traffic(city)
            results.append(result)
            print(f"  Congestion index: {result['congestion_index']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/traffic/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()