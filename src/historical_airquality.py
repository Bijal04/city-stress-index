import requests
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.config import CITIES
from src.load_dimensions import load_dim_date

def fetch_historical_airquality(city: dict, start_date: str, end_date: str) -> list:
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude":   city["lat"],
        "longitude":  city["lon"],
        "hourly":     ["pm2_5", "nitrogen_dioxide"],
        "start_date": start_date,
        "end_date":   end_date,
        "timezone":   "UTC",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    hourly = data.get("hourly", {})
    times  = hourly.get("time", [])
    pm25   = hourly.get("pm2_5", [])
    no2    = hourly.get("nitrogen_dioxide", [])

    daily_pm25 = {}
    daily_no2  = {}

    for i, t in enumerate(times):
        date = t[:10]
        if i < len(pm25) and pm25[i] is not None:
            daily_pm25.setdefault(date, []).append(pm25[i])
        if i < len(no2) and no2[i] is not None:
            daily_no2.setdefault(date, []).append(no2[i])

    records = []
    all_dates = sorted(set(daily_pm25.keys()) | set(daily_no2.keys()))

    for date in all_dates:
        pm_vals  = daily_pm25.get(date, [])
        no2_vals = daily_no2.get(date, [])

        avg_pm25 = round(sum(pm_vals)  / len(pm_vals),  2) if pm_vals  else None
        avg_no2  = round(sum(no2_vals) / len(no2_vals), 2) if no2_vals else None

        aqi = None
        if avg_pm25 is not None:
            if avg_pm25 <= 12:    aqi = 50
            elif avg_pm25 <= 35:  aqi = 100
            elif avg_pm25 <= 55:  aqi = 150
            elif avg_pm25 <= 150: aqi = 200
            else:                 aqi = 300

        records.append({
            "date":     date,
            "avg_pm25": avg_pm25,
            "avg_no2":  avg_no2,
            "aqi":      aqi,
        })

    return records

def load_historical_airquality_to_db(start_date: str = "2024-01-01", end_date: str = None):
    if end_date is None:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Loading historical air quality: {start_date} to {end_date}")
    load_dim_date(start_date=start_date, end_date=end_date)

    conn   = get_connection()
    cursor = conn.cursor()
    total  = 0

    for city in CITIES:
        print(f"  Fetching {city['name']}...", end=" ", flush=True)

        cursor.execute("SELECT city_id FROM dim_city WHERE name = ?", (city["name"],))
        row = cursor.fetchone()
        if not row:
            print("city not found, skipping.")
            continue
        city_id = row["city_id"]

        try:
            records = fetch_historical_airquality(city, start_date, end_date)

            for rec in records:
                cursor.execute("""
                    INSERT OR IGNORE INTO fact_city_metrics (city_id, date_id)
                    VALUES (?, ?)
                """, (city_id, rec["date"]))

                cursor.execute("""
                    UPDATE fact_city_metrics
                    SET avg_pm25     = ?,
                        avg_no2      = ?,
                        aqi_estimate = ?
                    WHERE city_id = ? AND date_id = ?
                """, (
                    rec["avg_pm25"],
                    rec["avg_no2"],
                    rec["aqi"],
                    city_id,
                    rec["date"],
                ))
                total += 1

            conn.commit()
            print(f"{len(records)} days loaded.")

        except Exception as e:
            print(f"FAILED — {e}")

    conn.close()
    print(f"\nAir quality backfill complete. Total rows touched: {total}")

if __name__ == "__main__":
    load_historical_airquality_to_db()