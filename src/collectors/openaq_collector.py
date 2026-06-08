import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CITIES

load_dotenv()
API_KEY = os.getenv("OPENAQ_API_KEY")

STATIC_AQI_FALLBACK = {
    "Toronto":  {"avg_pm25": 8.0,  "avg_no2": 18.0, "aqi_estimate": 50},
    "New York": {"avg_pm25": 12.0, "avg_no2": 28.0, "aqi_estimate": 100},
    "London":   {"avg_pm25": 11.0, "avg_no2": 25.0, "aqi_estimate": 50},
    "Mumbai":   {"avg_pm25": 45.0, "avg_no2": 38.0, "aqi_estimate": 150},
    "Tokyo":    {"avg_pm25": 13.0, "avg_no2": 20.0, "aqi_estimate": 100},
}

def get_sensor_param_map(location: dict) -> dict:
    """Build a map of sensorsId -> parameter name from location sensors list."""
    sensor_map = {}
    for sensor in location.get("sensors", []):
        sensor_id = sensor.get("id")
        param     = sensor.get("parameter", {}).get("name", "")
        if sensor_id and param:
            sensor_map[sensor_id] = param
    return sensor_map

def is_active_location(location: dict, cutoff_year: int = 2024) -> bool:
    """Check if location has recent data."""
    last = location.get("datetimeLast", {})
    utc  = last.get("utc", "") if isinstance(last, dict) else ""
    if not utc:
        return False
    try:
        year = int(utc[:4])
        return year >= cutoff_year
    except:
        return False

def fetch_air_quality(city: dict) -> dict:
    headers = {"X-API-Key": API_KEY}

    # Step 1 — find active locations near city
    loc_response = requests.get(
        "https://api.openaq.org/v3/locations",
        headers=headers,
        params={
            "coordinates": f"{city['lat']},{city['lon']}",
            "radius":      25000,
            "limit":       20,
        },
        timeout=10
    )
    loc_response.raise_for_status()
    all_locations = loc_response.json().get("results", [])

    # Filter to only active locations
    active_locations = [l for l in all_locations if is_active_location(l)]
    print(f"  Found {len(all_locations)} locations, {len(active_locations)} active")

    if not active_locations:
        print(f"  No active locations — using static fallback")
        fallback = STATIC_AQI_FALLBACK.get(city["name"], {})
        return {
            "city":         city["name"],
            "timestamp":    datetime.utcnow().isoformat(),
            "avg_pm25":     fallback.get("avg_pm25"),
            "avg_no2":      fallback.get("avg_no2"),
            "aqi_estimate": fallback.get("aqi_estimate"),
            "source":       "static_fallback",
        }

    # Step 2 — for each active location, build sensor map + fetch latest
    pm25_values = []
    no2_values  = []

    for loc in active_locations[:5]:
        loc_id     = loc["id"]
        sensor_map = get_sensor_param_map(loc)

        try:
            r = requests.get(
                f"https://api.openaq.org/v3/locations/{loc_id}/latest",
                headers=headers,
                timeout=10
            )
            r.raise_for_status()
            measurements = r.json().get("results", [])

            for m in measurements:
                sensor_id = m.get("sensorsId")
                value     = m.get("value")
                param     = sensor_map.get(sensor_id, "")

                if value is None or not param:
                    continue
                if param == "pm25":
                    pm25_values.append(value)
                elif param == "no2":
                    no2_values.append(value)

        except Exception as e:
            print(f"  Skipping location {loc_id}: {e}")
            continue

    # Step 3 — if still no data, use fallback
    if not pm25_values and not no2_values:
        print(f"  No measurements returned — using static fallback")
        fallback = STATIC_AQI_FALLBACK.get(city["name"], {})
        return {
            "city":         city["name"],
            "timestamp":    datetime.utcnow().isoformat(),
            "avg_pm25":     fallback.get("avg_pm25"),
            "avg_no2":      fallback.get("avg_no2"),
            "aqi_estimate": fallback.get("aqi_estimate"),
            "source":       "static_fallback",
        }

    avg_pm25 = round(sum(pm25_values) / len(pm25_values), 2) if pm25_values else None
    avg_no2  = round(sum(no2_values)  / len(no2_values),  2) if no2_values  else None

    # Step 4 — calculate AQI
    aqi = None
    if avg_pm25 is not None:
        if avg_pm25 <= 12:    aqi = 50
        elif avg_pm25 <= 35:  aqi = 100
        elif avg_pm25 <= 55:  aqi = 150
        elif avg_pm25 <= 150: aqi = 200
        else:                 aqi = 300

    return {
        "city":         city["name"],
        "timestamp":    datetime.utcnow().isoformat(),
        "avg_pm25":     avg_pm25,
        "avg_no2":      avg_no2,
        "aqi_estimate": aqi,
        "source":       "api",
    }

def run():
    os.makedirs("data/raw/airquality", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching air quality for {city['name']}...")
        try:
            result = fetch_air_quality(city)
            results.append(result)
            print(f"  PM2.5: {result['avg_pm25']}  AQI: {result['aqi_estimate']}  Source: {result['source']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/airquality/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()