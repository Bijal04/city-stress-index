import sqlite3
import os

DB_PATH = os.path.join("data", "city_stress.db")

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_city (
            city_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL UNIQUE,
            country   TEXT NOT NULL,
            latitude  REAL NOT NULL,
            longitude REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date_id    TEXT PRIMARY KEY,
            full_date  TEXT NOT NULL,
            year       INTEGER NOT NULL,
            month      INTEGER NOT NULL,
            month_name TEXT    NOT NULL,
            day        INTEGER NOT NULL,
            weekday    TEXT    NOT NULL,
            week_num   INTEGER NOT NULL,
            quarter    INTEGER NOT NULL,
            season     TEXT    NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_city_metrics (
            metric_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id            INTEGER NOT NULL,
            date_id            TEXT    NOT NULL,
            congestion_index   REAL,
            current_speed_kmph REAL,
            free_flow_speed    REAL,
            avg_pm25           REAL,
            avg_no2            REAL,
            aqi_estimate       REAL,
            temp_c             REAL,
            feels_like_c       REAL,
            humidity_pct       REAL,
            wind_speed_mps     REAL,
            rain_1h_mm         REAL,
            weather_stress     REAL,
            cost_index         REAL,
            rent_index         REAL,
            crime_score        REAL,
            created_at         TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES dim_city (city_id),
            FOREIGN KEY (date_id) REFERENCES dim_date (date_id),
            UNIQUE (city_id, date_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_stress_scores (
            score_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id            INTEGER NOT NULL,
            date_id            TEXT    NOT NULL,
            traffic_score      REAL,
            air_quality_score  REAL,
            weather_score      REAL,
            cost_score         REAL,
            safety_score       REAL,
            total_stress_score REAL,
            stress_label       TEXT,
            created_at         TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES dim_city (city_id),
            FOREIGN KEY (date_id) REFERENCES dim_date (date_id),
            UNIQUE (city_id, date_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_features (
            feature_id              INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id                 INTEGER NOT NULL,
            date_id                 TEXT    NOT NULL,

            -- Normalized scores (0-100)
            traffic_norm            REAL,
            air_quality_norm        REAL,
            weather_norm            REAL,
            cost_norm               REAL,
            safety_norm             REAL,

            -- Rolling averages (7-day)
            traffic_7d_avg          REAL,
            air_quality_7d_avg      REAL,
            weather_7d_avg          REAL,

            -- Rolling averages (30-day)
            traffic_30d_avg         REAL,
            air_quality_30d_avg     REAL,
            weather_30d_avg         REAL,

            -- Volatility (7-day standard deviation)
            traffic_volatility      REAL,
            air_quality_volatility  REAL,
            weather_volatility      REAL,

            -- Trend (-1 = improving, 0 = stable, 1 = worsening)
            traffic_trend           INTEGER,
            air_quality_trend       INTEGER,
            weather_trend           INTEGER,

            -- Final composite score
            composite_stress_score  REAL,
            stress_label            TEXT,

            created_at              TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id) REFERENCES dim_city (city_id),
            FOREIGN KEY (date_id) REFERENCES dim_date  (date_id),
            UNIQUE (city_id, date_id)
        )
    """)

    conn.commit()
    conn.close()
    print("All 5 tables created successfully.")
    print("  dim_city")
    print("  dim_date")
    print("  fact_city_metrics")
    print("  city_stress_scores")
    print("  city_features")

if __name__ == "__main__":
    create_tables()