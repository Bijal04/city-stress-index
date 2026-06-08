import json
import os
import sys
import glob
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection

def get_city_id(cursor, city_name: str):
    cursor.execute("SELECT city_id FROM dim_city WHERE name = ?", (city_name,))
    row = cursor.fetchone()
    return row["city_id"] if row else None

def ensure_fact_row(cursor, city_id: int, date_id: str):
    cursor.execute("""
        INSERT OR IGNORE INTO fact_city_metrics (city_id, date_id)
        VALUES (?, ?)
    """, (city_id, date_id))

def load_traffic(date_str: str = None):
    conn    = get_connection()
    cursor  = conn.cursor()
    pattern = f"data/raw/traffic/{date_str}.json" if date_str else "data/raw/traffic/*.json"
    files   = glob.glob(pattern)
    count   = 0

    for filepath in files:
        date_id = os.path.basename(filepath).replace(".json", "")
        with open(filepath) as f:
            records = json.load(f)

        for rec in records:
            city_id = get_city_id(cursor, rec.get("city", ""))
            if not city_id:
                print(f"  Warning: city not found — {rec.get('city')}")
                continue

            ensure_fact_row(cursor, city_id, date_id)

            cursor.execute("""
                UPDATE fact_city_metrics
                SET congestion_index   = ?,
                    current_speed_kmph = ?,
                    free_flow_speed    = ?
                WHERE city_id = ? AND date_id = ?
            """, (
                rec.get("congestion_index"),
                rec.get("current_speed_kmph"),
                rec.get("free_flow_speed_kmph"),
                city_id,
                date_id,
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"  Traffic:     {count} rows updated.")

def load_air_quality(date_str: str = None):
    conn    = get_connection()
    cursor  = conn.cursor()
    pattern = f"data/raw/airquality/{date_str}.json" if date_str else "data/raw/airquality/*.json"
    files   = glob.glob(pattern)
    count   = 0

    for filepath in files:
        date_id = os.path.basename(filepath).replace(".json", "")
        with open(filepath) as f:
            records = json.load(f)

        for rec in records:
            city_id = get_city_id(cursor, rec.get("city", ""))
            if not city_id:
                continue

            ensure_fact_row(cursor, city_id, date_id)

            cursor.execute("""
                UPDATE fact_city_metrics
                SET avg_pm25     = ?,
                    avg_no2      = ?,
                    aqi_estimate = ?
                WHERE city_id = ? AND date_id = ?
            """, (
                rec.get("avg_pm25"),
                rec.get("avg_no2"),
                rec.get("aqi_estimate"),
                city_id,
                date_id,
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"  Air quality: {count} rows updated.")

def load_weather(date_str: str = None):
    conn    = get_connection()
    cursor  = conn.cursor()
    pattern = f"data/raw/weather/{date_str}.json" if date_str else "data/raw/weather/*.json"
    files   = glob.glob(pattern)
    count   = 0

    for filepath in files:
        date_id = os.path.basename(filepath).replace(".json", "")
        with open(filepath) as f:
            records = json.load(f)

        for rec in records:
            city_id = get_city_id(cursor, rec.get("city", ""))
            if not city_id:
                continue

            ensure_fact_row(cursor, city_id, date_id)

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
                rec.get("temp_c"),
                rec.get("feels_like_c"),
                rec.get("humidity_pct"),
                rec.get("wind_speed_mps"),
                rec.get("rain_1h_mm"),
                rec.get("weather_stress_score"),
                city_id,
                date_id,
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"  Weather:     {count} rows updated.")

def load_cost(date_str: str = None):
    conn    = get_connection()
    cursor  = conn.cursor()
    pattern = f"data/raw/cost/{date_str}.json" if date_str else "data/raw/cost/*.json"
    files   = glob.glob(pattern)
    count   = 0

    for filepath in files:
        date_id = os.path.basename(filepath).replace(".json", "")
        with open(filepath) as f:
            records = json.load(f)

        for rec in records:
            city_id = get_city_id(cursor, rec.get("city", ""))
            if not city_id:
                continue

            ensure_fact_row(cursor, city_id, date_id)

            cursor.execute("""
                UPDATE fact_city_metrics
                SET cost_index = ?,
                    rent_index = ?
                WHERE city_id = ? AND date_id = ?
            """, (
                rec.get("cost_of_living_index"),
                rec.get("rent_index"),
                city_id,
                date_id,
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"  Cost:        {count} rows updated.")

def load_safety(date_str: str = None):
    conn    = get_connection()
    cursor  = conn.cursor()
    pattern = f"data/raw/safety/{date_str}.json" if date_str else "data/raw/safety/*.json"
    files   = glob.glob(pattern)
    count   = 0

    for filepath in files:
        date_id = os.path.basename(filepath).replace(".json", "")
        with open(filepath) as f:
            records = json.load(f)

        for rec in records:
            city_id = get_city_id(cursor, rec.get("city", ""))
            if not city_id:
                continue

            ensure_fact_row(cursor, city_id, date_id)

            cursor.execute("""
                UPDATE fact_city_metrics
                SET crime_score = ?
                WHERE city_id = ? AND date_id = ?
            """, (
                rec.get("crime_score"),
                city_id,
                date_id,
            ))
            count += 1

    conn.commit()
    conn.close()
    print(f"  Safety:      {count} rows updated.")

def run_etl(date_str: str = None):
    print("=" * 50)
    print(f"ETL run — {date_str if date_str else 'all files'}")
    print("=" * 50)
    load_traffic(date_str)
    load_air_quality(date_str)
    load_weather(date_str)
    load_cost(date_str)
    load_safety(date_str)

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as n FROM fact_city_metrics")
    total = cursor.fetchone()["n"]
    conn.close()

    print(f"\nfact_city_metrics total rows: {total}")
    print("ETL complete.")

if __name__ == "__main__":
    run_etl()