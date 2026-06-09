import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.config import CITIES

CITY_TRAFFIC_PROFILES = {
    "Toronto":  {"base": 45, "weekend_drop": 20, "variance": 15},
    "New York": {"base": 70, "weekend_drop": 25, "variance": 15},
    "London":   {"base": 65, "weekend_drop": 22, "variance": 15},
    "Mumbai":   {"base": 75, "weekend_drop": 10, "variance": 20},
    "Tokyo":    {"base": 40, "weekend_drop": 15, "variance": 12},
}

def generate_congestion(city_name: str, date: datetime) -> float:
    profile    = CITY_TRAFFIC_PROFILES.get(city_name, {"base": 50, "weekend_drop": 15, "variance": 10})
    base       = profile["base"]
    is_weekend = date.weekday() >= 5

    if is_weekend:
        base -= profile["weekend_drop"]

    noise  = random.gauss(0, profile["variance"])
    result = base + noise
    return round(max(0, min(100, result)), 2)

def load_historical_traffic(start_date: str = "2024-01-01", end_date: str = None):
    if end_date is None:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Loading synthetic historical traffic: {start_date} to {end_date}")

    random.seed(42)

    conn   = get_connection()
    cursor = conn.cursor()
    total  = 0

    for city in CITIES:
        print(f"  Processing {city['name']}...", end=" ", flush=True)

        cursor.execute("SELECT city_id FROM dim_city WHERE name = ?", (city["name"],))
        row = cursor.fetchone()
        if not row:
            print("not found, skipping.")
            continue
        city_id = row["city_id"]

        current = datetime.strptime(start_date, "%Y-%m-%d")
        end     = datetime.strptime(end_date,   "%Y-%m-%d")
        count   = 0

        while current <= end:
            date_id    = current.strftime("%Y-%m-%d")
            congestion = generate_congestion(city["name"], current)

            cursor.execute("""
                INSERT OR IGNORE INTO fact_city_metrics (city_id, date_id)
                VALUES (?, ?)
            """, (city_id, date_id))

            cursor.execute("""
                UPDATE fact_city_metrics
                SET congestion_index = ?
                WHERE city_id = ? AND date_id = ?
                  AND congestion_index IS NULL
            """, (congestion, city_id, date_id))

            current += timedelta(days=1)
            count   += 1
            total   += 1

        conn.commit()
        print(f"{count} days loaded.")

    conn.close()
    print(f"\nTraffic backfill complete. Total rows touched: {total}")

if __name__ == "__main__":
    load_historical_traffic()