import requests
import sqlite3
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.config import CITIES
from src.load_dimensions import load_dim_date

def fetch_historical_weather(city: dict, start_date: str, end_date: str) -> list:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   city["lat"],
        "longitude":  city["lon"],
        "start_date": start_date,
        "end_date":   end_date,
        "daily": [
            "temperature_2m_mean",
            "apparent_temperature_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "relative_humidity_2m_mean",
        ],
        "timezone": "UTC",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily    = data.get("daily", {})
    dates    = daily.get("time", [])
    temps    = daily.get("temperature_2m_mean", [])
    feels    = daily.get("apparent_temperature_mean", [])
    precip   = daily.get("precipitation_sum", [])
    wind     = daily.get("wind_speed_10m_max", [])
    humidity = daily.get("relative_humidity_2m_mean", [])

    records = []
    for i, date in enumerate(dates):
        temp_val     = temps[i]    if i < len(temps)    else None
        feels_val    = feels[i]    if i < len(feels)    else None
        precip_val   = precip[i]   if i < len(precip)   else None
        wind_val     = wind[i]     if i < len(wind)     else None
        humidity_val = humidity[i] if i < len(humidity) else None

        stress = 0
        if feels_val is not None:
            if feels_val > 35:   stress += 40
            elif feels_val > 28: stress += 20
            if feels_val < 0:    stress += 30
            elif feels_val < 5:  stress += 15
        if precip_val is not None:
            if precip_val > 10:  stress += 20
            elif precip_val > 2: stress += 10
        if wind_val is not None:
            if wind_val > 20:    stress += 10
        if humidity_val is not None:
            if humidity_val > 85: stress += 10

        records.append({
            "date":           date,
            "temp_c":         temp_val,
            "feels_like_c":   feels_val,
            "humidity_pct":   humidity_val,
            "wind_speed_mps": round(wind_val / 3.6, 2) if wind_val else None,
            "rain_1h_mm":     round(precip_val / 24, 3) if precip_val else None,
            "weather_stress": min(stress, 100),
        })

    return records

def load_historical_weather_to_db(start_date: str = "2024-01-01", end_date: str = None):
    if end_date is None:
        end_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"Loading historical weather: {start_date} to {end_date}")
    load_dim_date(start_date=start_date, end_date=end_date)

    conn   = get_connection()
    cursor = conn.cursor()
    total  = 0

    for city in CITIES:
        print(f"  Fetching {city['name']}...", end=" ", flush=True)

        cursor.execute("SELECT city_id FROM dim_city WHERE name = ?", (city["name"],))
        row = cursor.fetchone()
        if not row:
            print("city not found in dim_city, skipping.")
            continue
        city_id = row["city_id"]

        try:
            records = fetch_historical_weather(city, start_date, end_date)

            for rec in records:
                cursor.execute("""
                    INSERT OR IGNORE INTO fact_city_metrics (city_id, date_id)
                    VALUES (?, ?)
                """, (city_id, rec["date"]))

                cursor.execute("""
                    UPDATE fact_city_metrics
                    SET temp_c         = ?,
                        feels_like_c   = ?,
                        humidity_pct   = ?,
                        wind_speed_mps = ?,
                        rain_1h_mm     = ?,
                        weather_stress = ?
                    WHERE city_id = ? AND date_id = ?
                """, (
                    rec["temp_c"],
                    rec["feels_like_c"],
                    rec["humidity_pct"],
                    rec["wind_speed_mps"],
                    rec["rain_1h_mm"],
                    rec["weather_stress"],
                    city_id,
                    rec["date"],
                ))
                total += 1

            conn.commit()
            print(f"{len(records)} days loaded.")

        except Exception as e:
            print(f"FAILED — {e}")

    conn.close()
    print(f"\nWeather backfill complete. Total rows touched: {total}")

if __name__ == "__main__":
    load_historical_weather_to_db()