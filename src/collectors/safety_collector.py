import requests
import json
import os
from datetime import datetime, timedelta
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CITIES

SAFETY_SOURCES = {
    "Toronto": {
        "url": "https://services.arcgis.com/S9th0jAJ7bqgIRjw/arcgis/rest/services/Major_Crime_Indicators_Open_Data/FeatureServer/0/query",
        "params": {
            "where":             "1=1",
            "outFields":         "OCC_DATE",
            "resultRecordCount": 100,
            "f":                 "json",
        }
    },
    "New York": {
        "url":    "https://data.cityofnewyork.us/resource/5uac-w243.json",
        "params": {
            "$limit": 100,
        }
    },
}

STATIC_SCORES = {
    "London": 45,
    "Mumbai": 60,
    "Tokyo":  15,
}

def fetch_safety(city: dict) -> dict:
    name = city["name"]

    if name in SAFETY_SOURCES:
        source = SAFETY_SOURCES[name]
        try:
            response = requests.get(source["url"], params=source["params"], timeout=15)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                count = len(data)
            else:
                count = len(data.get("features", []))

            crime_score = min(round((count / 100) * 50, 2), 100)
            source_type = "api"
        except Exception as e:
            print(f"  API failed, using static fallback: {e}")
            crime_score = STATIC_SCORES.get(name, 50)
            count       = None
            source_type = "static_fallback"
    else:
        crime_score = STATIC_SCORES.get(name, 50)
        count       = None
        source_type = "static_estimate"

    return {
        "city":               name,
        "timestamp":          datetime.utcnow().isoformat(),
        "crime_score":        crime_score,
        "incident_count_30d": count,
        "source":             source_type,
    }

def run():
    os.makedirs("data/raw/safety", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching safety data for {city['name']}...")
        try:
            result = fetch_safety(city)
            results.append(result)
            print(f"  Crime score: {result['crime_score']}  Source: {result['source']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/safety/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()