import sqlite3
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection

# Weights for the composite stress score — must sum to 1.0
WEIGHTS = {
    "traffic":     0.25,
    "air_quality": 0.25,
    "weather":     0.20,
    "cost":        0.15,
    "safety":      0.15,
}

def load_raw_data() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            f.city_id,
            c.name        AS city_name,
            f.date_id,
            f.congestion_index,
            f.aqi_estimate,
            f.weather_stress,
            f.cost_index,
            f.crime_score
        FROM fact_city_metrics f
        JOIN dim_city c ON f.city_id = c.city_id
        ORDER BY c.name, f.date_id
    """, conn)
    conn.close()
    return df


def normalize_column(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-100. Higher = more stress."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - min_val) / (max_val - min_val) * 100).round(2)


def compute_trend(series: pd.Series, window: int = 7) -> int:
    """
    Compare the last `window` days average to the previous `window` days.
    Returns: 1 (worsening), -1 (improving), 0 (stable)
    """
    if len(series) < window * 2:
        return 0
    recent   = series.iloc[-window:].mean()
    previous = series.iloc[-window * 2:-window].mean()
    if pd.isna(recent) or pd.isna(previous):
        return 0
    diff = recent - previous
    if diff > 2:
        return 1
    elif diff < -2:
        return -1
    return 0


def stress_label(score: float) -> str:
    if score is None or pd.isna(score):
        return "Unknown"
    if score < 25:   return "Low"
    elif score < 50: return "Moderate"
    elif score < 75: return "High"
    else:            return "Critical"


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    results = []

    for city_id, group in df.groupby("city_id"):
        city_name = group["city_name"].iloc[0]
        group = group.copy().sort_values("date_id").reset_index(drop=True)

        print(f"  Computing features for {city_name} ({len(group)} rows)...")

        # --- Normalize each metric globally (across all rows for this city) ---
        group["traffic_norm"]     = normalize_column(group["congestion_index"].fillna(group["congestion_index"].median()))
        group["air_quality_norm"] = normalize_column(group["aqi_estimate"].fillna(group["aqi_estimate"].median()))
        group["weather_norm"]     = normalize_column(group["weather_stress"].fillna(0))
        group["cost_norm"]        = normalize_column(group["cost_index"].fillna(group["cost_index"].median()))
        group["safety_norm"]      = normalize_column(group["crime_score"].fillna(group["crime_score"].median()))

        # --- 7-day rolling averages ---
        group["traffic_7d_avg"]     = group["traffic_norm"].rolling(7,     min_periods=1).mean().round(2)
        group["air_quality_7d_avg"] = group["air_quality_norm"].rolling(7, min_periods=1).mean().round(2)
        group["weather_7d_avg"]     = group["weather_norm"].rolling(7,     min_periods=1).mean().round(2)

        # --- 30-day rolling averages ---
        group["traffic_30d_avg"]     = group["traffic_norm"].rolling(30,     min_periods=1).mean().round(2)
        group["air_quality_30d_avg"] = group["air_quality_norm"].rolling(30, min_periods=1).mean().round(2)
        group["weather_30d_avg"]     = group["weather_norm"].rolling(30,     min_periods=1).mean().round(2)

        # --- 7-day rolling volatility (standard deviation) ---
        group["traffic_volatility"]     = group["traffic_norm"].rolling(7,     min_periods=2).std().round(2)
        group["air_quality_volatility"] = group["air_quality_norm"].rolling(7, min_periods=2).std().round(2)
        group["weather_volatility"]     = group["weather_norm"].rolling(7,     min_periods=2).std().round(2)

        # --- Composite stress score ---
        group["composite_stress_score"] = (
            group["traffic_norm"]     * WEIGHTS["traffic"]     +
            group["air_quality_norm"] * WEIGHTS["air_quality"] +
            group["weather_norm"]     * WEIGHTS["weather"]     +
            group["cost_norm"]        * WEIGHTS["cost"]        +
            group["safety_norm"]      * WEIGHTS["safety"]
        ).round(2)

        # --- Stress label ---
        group["stress_label"] = group["composite_stress_score"].apply(stress_label)

        # --- Per-row trend (compare last 7 days vs previous 7 days) ---
        traffic_trends     = []
        air_trends         = []
        weather_trends     = []

        for i in range(len(group)):
            window_data = group.iloc[:i + 1]
            traffic_trends.append(compute_trend(window_data["traffic_norm"]))
            air_trends.append(compute_trend(window_data["air_quality_norm"]))
            weather_trends.append(compute_trend(window_data["weather_norm"]))

        group["traffic_trend"]     = traffic_trends
        group["air_quality_trend"] = air_trends
        group["weather_trend"]     = weather_trends

        results.append(group)

    return pd.concat(results, ignore_index=True)


def save_features(df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    count  = 0

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO city_features (
                city_id, date_id,
                traffic_norm, air_quality_norm, weather_norm, cost_norm, safety_norm,
                traffic_7d_avg, air_quality_7d_avg, weather_7d_avg,
                traffic_30d_avg, air_quality_30d_avg, weather_30d_avg,
                traffic_volatility, air_quality_volatility, weather_volatility,
                traffic_trend, air_quality_trend, weather_trend,
                composite_stress_score, stress_label
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_id, date_id) DO UPDATE SET
                traffic_norm            = excluded.traffic_norm,
                air_quality_norm        = excluded.air_quality_norm,
                weather_norm            = excluded.weather_norm,
                cost_norm               = excluded.cost_norm,
                safety_norm             = excluded.safety_norm,
                traffic_7d_avg          = excluded.traffic_7d_avg,
                air_quality_7d_avg      = excluded.air_quality_7d_avg,
                weather_7d_avg          = excluded.weather_7d_avg,
                traffic_30d_avg         = excluded.traffic_30d_avg,
                air_quality_30d_avg     = excluded.air_quality_30d_avg,
                weather_30d_avg         = excluded.weather_30d_avg,
                traffic_volatility      = excluded.traffic_volatility,
                air_quality_volatility  = excluded.air_quality_volatility,
                weather_volatility      = excluded.weather_volatility,
                traffic_trend           = excluded.traffic_trend,
                air_quality_trend       = excluded.air_quality_trend,
                weather_trend           = excluded.weather_trend,
                composite_stress_score  = excluded.composite_stress_score,
                stress_label            = excluded.stress_label
        """, (
            int(row["city_id"]),
            row["date_id"],
            row.get("traffic_norm"),
            row.get("air_quality_norm"),
            row.get("weather_norm"),
            row.get("cost_norm"),
            row.get("safety_norm"),
            row.get("traffic_7d_avg"),
            row.get("air_quality_7d_avg"),
            row.get("weather_7d_avg"),
            row.get("traffic_30d_avg"),
            row.get("air_quality_30d_avg"),
            row.get("weather_30d_avg"),
            row.get("traffic_volatility"),
            row.get("air_quality_volatility"),
            row.get("weather_volatility"),
            int(row.get("traffic_trend", 0)),
            int(row.get("air_quality_trend", 0)),
            int(row.get("weather_trend", 0)),
            row.get("composite_stress_score"),
            row.get("stress_label"),
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"\nSaved {count} rows to city_features.")


def run():
    print("=" * 55)
    print("FEATURE ENGINEERING — City Stress Index")
    print("=" * 55)

    print("\nLoading raw data from fact_city_metrics...")
    df = load_raw_data()
    print(f"Loaded {len(df)} rows across {df['city_name'].nunique()} cities.")

    print("\nComputing features...")
    features_df = compute_features(df)

    print("\nSaving to city_features table...")
    save_features(features_df)

    # Quick summary
    conn = get_connection()
    summary = pd.read_sql_query("""
        SELECT
            c.name AS city,
            ROUND(AVG(f.composite_stress_score), 1) AS avg_stress,
            ROUND(MIN(f.composite_stress_score), 1) AS min_stress,
            ROUND(MAX(f.composite_stress_score), 1) AS max_stress,
            (SELECT stress_label FROM city_features
             WHERE city_id = f.city_id
             ORDER BY date_id DESC LIMIT 1) AS current_label
        FROM city_features f
        JOIN dim_city c ON f.city_id = c.city_id
        GROUP BY c.name
        ORDER BY avg_stress DESC
    """, conn)
    conn.close()

    print("\n=== STRESS SCORE SUMMARY ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run()