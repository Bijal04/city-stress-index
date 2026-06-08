import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.config import CITIES

CITY_COUNTRIES = {
    "Toronto":  "Canada",
    "New York": "United States",
    "London":   "United Kingdom",
    "Mumbai":   "India",
    "Tokyo":    "Japan",
}

def load_dim_city():
    conn   = get_connection()
    cursor = conn.cursor()
    loaded = 0

    for city in CITIES:
        cursor.execute("""
            INSERT OR IGNORE INTO dim_city (name, country, latitude, longitude)
            VALUES (?, ?, ?, ?)
        """, (
            city["name"],
            CITY_COUNTRIES.get(city["name"], "Unknown"),
            city["lat"],
            city["lon"],
        ))
        if cursor.rowcount > 0:
            loaded += 1

    conn.commit()
    conn.close()
    print(f"dim_city: {loaded} new cities inserted.")

def get_season(month: int) -> str:
    if month in [12, 1, 2]:  return "Winter"
    elif month in [3, 4, 5]: return "Spring"
    elif month in [6, 7, 8]: return "Summer"
    else:                    return "Autumn"

def load_dim_date(start_date: str = "2024-01-01", end_date: str = None):
    if end_date is None:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    conn    = get_connection()
    cursor  = conn.cursor()
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end     = datetime.strptime(end_date,   "%Y-%m-%d")
    loaded  = 0

    while current <= end:
        date_id = current.strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT OR IGNORE INTO dim_date
            (date_id, full_date, year, month, month_name,
             day, weekday, week_num, quarter, season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date_id,
            date_id,
            current.year,
            current.month,
            current.strftime("%B"),
            current.day,
            current.strftime("%A"),
            int(current.strftime("%W")),
            (current.month - 1) // 3 + 1,
            get_season(current.month),
        ))

        if cursor.rowcount > 0:
            loaded += 1

        current += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"dim_date: {loaded} new dates inserted ({start_date} to {end_date}).")

def run():
    print("Loading dimension tables...")
    load_dim_city()
    load_dim_date()
    print("Done.")

if __name__ == "__main__":
    run()