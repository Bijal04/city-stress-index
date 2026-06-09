import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.config import CITIES

STATIC_DATA = {
    "Toronto":  {"cost_index": 72.4,  "rent_index": 48.1, "crime_score": 45.0},
    "New York": {"cost_index": 100.0, "rent_index": 86.3, "crime_score": 50.0},
    "London":   {"cost_index": 81.2,  "rent_index": 62.7, "crime_score": 45.0},
    "Mumbai":   {"cost_index": 28.3,  "rent_index": 12.4, "crime_score": 60.0},
    "Tokyo":    {"cost_index": 83.1,  "rent_index": 39.6, "crime_score": 15.0},
}

def load_historical_static(start_date: str = "2024-01-01", end_date: str = None):
    if end_date is None:
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Loading static cost + safety data: {start_date} to {end_date}")

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

        static  = STATIC_DATA.get(city["name"], {})
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end     = datetime.strptime(end_date,   "%Y-%m-%d")
        count   = 0

        while current <= end:
            date_id = current.strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT OR IGNORE INTO fact_city_metrics (city_id, date_id)
                VALUES (?, ?)
            """, (city_id, date_id))

            cursor.execute("""
                UPDATE fact_city_metrics
                SET cost_index  = ?,
                    rent_index  = ?,
                    crime_score = ?
                WHERE city_id = ? AND date_id = ?
                  AND cost_index IS NULL
            """, (
                static.get("cost_index"),
                static.get("rent_index"),
                static.get("crime_score"),
                city_id,
                date_id,
            ))

            current += timedelta(days=1)
            count   += 1
            total   += 1

        conn.commit()
        print(f"{count} days loaded.")

    conn.close()
    print(f"\nStatic backfill complete. Total rows touched: {total}")

if __name__ == "__main__":
    load_historical_static()