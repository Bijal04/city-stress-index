import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import create_tables
from src.load_dimensions import run as load_dimensions
from src.historical_weather import load_historical_weather_to_db
from src.historical_airquality import load_historical_airquality_to_db
from src.historical_static import load_historical_static
from src.historical_traffic import load_historical_traffic

START_DATE = "2024-01-01"

def run_full_backfill():
    end_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 55)
    print("CITY STRESS INDEX — Full Historical Backfill")
    print(f"Range: {START_DATE} to {end_date}")
    print("=" * 55)

    print("\n[1/6] Creating tables...")
    create_tables()

    print("\n[2/6] Loading dimensions...")
    load_dimensions()

    print("\n[3/6] Historical weather (Open-Meteo)...")
    load_historical_weather_to_db(START_DATE, end_date)

    print("\n[4/6] Historical air quality (Open-Meteo)...")
    load_historical_airquality_to_db(START_DATE, end_date)

    print("\n[5/6] Static cost + safety data...")
    load_historical_static(START_DATE, end_date)

    print("\n[6/6] Synthetic traffic data...")
    load_historical_traffic(START_DATE, end_date)

    print("\n" + "=" * 55)
    print("Backfill complete. Verifying row counts...")

    import sqlite3
    conn = sqlite3.connect("data/city_stress.db")
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) as n FROM fact_city_metrics")
    total = cur.fetchone()["n"]

    cur.execute("""
        SELECT c.name, COUNT(*) as days
        FROM fact_city_metrics f
        JOIN dim_city c ON f.city_id = c.city_id
        GROUP BY c.name
        ORDER BY c.name
    """)
    print(f"\nTotal rows in fact_city_metrics: {total}")
    print("\nRows per city:")
    for row in cur.fetchall():
        print(f"  {row['name']}: {row['days']} days")

    conn.close()

if __name__ == "__main__":
    run_full_backfill()