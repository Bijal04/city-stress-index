import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "city_stress.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_cities() -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name FROM dim_city ORDER BY name")
    cities = [r["name"] for r in cur.fetchall()]
    conn.close()
    return cities

def get_latest_scores() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            c.name              AS city,
            s.total_stress_score AS score,
            s.stress_label       AS label,
            s.traffic_score,
            s.air_quality_score,
            s.weather_score,
            s.safety_score,
            s.cost_score,
            s.date_id
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        WHERE s.date_id = (SELECT MAX(date_id) FROM city_stress_scores)
        ORDER BY s.total_stress_score DESC
    """, conn)
    conn.close()
    return df

def get_historical_scores(city_name: str = None) -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT
            c.name   AS city,
            s.date_id,
            s.total_stress_score AS score,
            s.stress_label       AS label,
            s.traffic_score,
            s.air_quality_score,
            s.weather_score,
            s.safety_score,
            s.cost_score
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
    """
    if city_name:
        query += f" WHERE c.name = '{city_name}'"
    query += " ORDER BY s.date_id"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def get_all_historical_scores() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            c.name   AS city,
            s.date_id,
            s.total_stress_score AS score,
            s.stress_label       AS label,
            s.traffic_score,
            s.air_quality_score,
            s.weather_score,
            s.safety_score,
            s.cost_score
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        ORDER BY s.date_id, c.name
    """, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def get_forecasts(city_name: str = None) -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT
            c.name          AS city,
            cf.forecast_date,
            cf.model,
            cf.predicted_score,
            cf.lower_bound,
            cf.upper_bound
        FROM city_forecasts cf
        JOIN dim_city c ON cf.city_id = c.city_id
    """
    if city_name:
        query += f" WHERE c.name = '{city_name}'"
    query += " ORDER BY cf.forecast_date"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

def get_anomalies(city_name: str = None) -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT
            c.name        AS city,
            a.date_id,
            a.metric,
            a.value,
            a.z_score,
            a.is_anomaly,
            a.anomaly_type
        FROM city_anomalies a
        JOIN dim_city c ON a.city_id = c.city_id
        WHERE a.is_anomaly = 1
    """
    if city_name:
        query += f" AND c.name = '{city_name}'"
    query += " ORDER BY a.date_id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def get_clusters() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            c.name           AS city,
            cl.cluster_label,
            cl.cluster_name,
            cl.avg_stress_score,
            cl.avg_traffic,
            cl.avg_air_quality,
            cl.avg_weather
        FROM city_clusters cl
        JOIN dim_city c ON cl.city_id = c.city_id
        ORDER BY cl.cluster_label, cl.avg_stress_score DESC
    """, conn)
    conn.close()
    return df

def get_rankings_history() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            c.name           AS city,
            r.date_id,
            r.rank,
            r.total_stress_score AS score,
            r.stress_label   AS label,
            r.rank_change
        FROM city_rankings r
        JOIN dim_city c ON r.city_id = c.city_id
        ORDER BY r.date_id, r.rank
    """, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def get_raw_metrics(city_name: str = None) -> pd.DataFrame:
    conn  = get_connection()
    query = """
        SELECT
            c.name           AS city,
            f.date_id,
            f.congestion_index,
            f.avg_pm25,
            f.aqi_estimate,
            f.temp_c,
            f.feels_like_c,
            f.humidity_pct,
            f.weather_stress,
            f.crime_score,
            f.cost_index
        FROM fact_city_metrics f
        JOIN dim_city c ON f.city_id = c.city_id
    """
    if city_name:
        query += f" WHERE c.name = '{city_name}'"
    query += " ORDER BY f.date_id"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df