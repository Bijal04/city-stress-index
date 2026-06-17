import sqlite3
import pytest
import os

DB_PATH = os.path.join("data", "city_stress.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_database_exists():
    assert os.path.exists(DB_PATH), "Database file does not exist"

def test_all_tables_exist():
    conn   = get_conn()
    cur    = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()

    required = [
        "dim_city", "dim_date", "fact_city_metrics",
        "city_stress_scores", "city_features",
        "city_rankings", "city_forecasts",
        "city_anomalies", "city_clusters",
    ]
    for table in required:
        assert table in tables, f"Missing table: {table}"

def test_dim_city_has_5_cities():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dim_city")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 5, f"Expected 5 cities, got {count}"

def test_dim_date_has_enough_rows():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dim_date")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 700, f"Expected 700+ dates, got {count}"

def test_fact_city_metrics_has_data():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fact_city_metrics")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 100, f"Expected 100+ rows, got {count}"

def test_stress_scores_in_valid_range():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM city_stress_scores
        WHERE total_stress_score < 0 OR total_stress_score > 100
    """)
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0, f"Found {count} scores outside 0-100 range"

def test_no_duplicate_city_dates():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT city_id, date_id, COUNT(*) as cnt
            FROM fact_city_metrics
            GROUP BY city_id, date_id
            HAVING COUNT(*) > 1
        )
    """)
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0, f"Found {count} duplicate city/date combinations"

def test_forecasts_exist():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM city_forecasts")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 100, f"Expected 100+ forecast rows, got {count}"

def test_clusters_exist():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM city_clusters")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 5, f"Expected 5 cluster rows, got {count}"