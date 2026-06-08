import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CITIES

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def fetch_weather(city: dict) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat":   city["lat"],
        "lon":   city["lon"],
        "appid": API_KEY,
        "units": "metric",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    main       = data.get("main", {})
    wind       = data.get("wind", {})
    rain       = data.get("rain", {})

    temp        = main.get("temp",       0)
    feels_like  = main.get("feels_like", 0)
    humidity    = main.get("humidity",   0)
    wind_speed  = wind.get("speed",      0)
    rain_1h     = rain.get("1h",         0)

    stress_score = 0
    if feels_like > 35:   stress_score += 40
    elif feels_like > 28: stress_score += 20
    if feels_like < 0:    stress_score += 30
    elif feels_like < 5:  stress_score += 15
    if rain_1h > 10:      stress_score += 20
    elif rain_1h > 2:     stress_score += 10
    if wind_speed > 20:   stress_score += 10
    if humidity > 85:     stress_score += 10

    return {
        "city":                 city["name"],
        "timestamp":            datetime.utcnow().isoformat(),
        "temp_c":               temp,
        "feels_like_c":         feels_like,
        "humidity_pct":         humidity,
        "wind_speed_mps":       wind_speed,
        "rain_1h_mm":           rain_1h,
        "weather_stress_score": min(stress_score, 100),
    }

def run():
    os.makedirs("data/raw/weather", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching weather for {city['name']}...")
        try:
            result = fetch_weather(city)
            results.append(result)
            print(f"  Temp: {result['temp_c']}°C  Stress: {result['weather_stress_score']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/weather/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()