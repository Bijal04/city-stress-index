import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import get_connection

def load_scores() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            s.city_id,
            c.name       AS city_name,
            s.date_id,
            s.total_stress_score,
            s.stress_label,
            s.traffic_score,
            s.air_quality_score,
            s.weather_score,
            s.safety_score,
            s.cost_score
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        ORDER BY s.date_id, s.total_stress_score DESC
    """, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def compute_rankings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rank"] = df.groupby("date_id")["total_stress_score"].rank(
        ascending=False, method="dense"
    ).astype(int)

    df = df.sort_values(["city_id", "date_id"])
    df["prev_rank"] = df.groupby("city_id")["rank"].shift(7)
    df["rank_change"] = (df["prev_rank"] - df["rank"]).fillna(0).astype(int)

    return df

def save_rankings(df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    saved  = 0

    for _, row in df.iterrows():
        date_str = row["date_id"].strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO city_rankings
                (date_id, city_id, rank, total_stress_score, stress_label, rank_change)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date_id, city_id) DO UPDATE SET
                rank               = excluded.rank,
                total_stress_score = excluded.total_stress_score,
                stress_label       = excluded.stress_label,
                rank_change        = excluded.rank_change
        """, (
            date_str,
            int(row["city_id"]),
            int(row["rank"]),
            row["total_stress_score"],
            row["stress_label"],
            int(row["rank_change"]),
        ))
        saved += 1

        if saved % 1000 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    return saved

def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["traffic_score", "air_quality_score", "weather_score",
            "safety_score", "cost_score", "total_stress_score"]
    corr = df[cols].corr().round(3)
    return corr

def compute_seasonal_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date_id"].dt.month
    df["season"] = df["month"].map({
        12: "Winter", 1: "Winter",  2: "Winter",
        3:  "Spring", 4: "Spring",  5: "Spring",
        6:  "Summer", 7: "Summer",  8: "Summer",
        9:  "Autumn", 10: "Autumn", 11: "Autumn",
    })

    seasonal = df.groupby(["city_name", "season"])["total_stress_score"].agg(
        mean_score="mean",
        max_score="max",
        min_score="min",
        count="count"
    ).round(2).reset_index()

    return seasonal

def run_rankings():
    print("=" * 55)
    print("Analytics — Rankings + Correlations")
    print("=" * 55)

    print("\nLoading scores...")
    df = load_scores()
    print(f"  {len(df)} rows loaded.")

    print("\nComputing rankings...")
    df = compute_rankings(df)

    print("Saving rankings to database...")
    saved = save_rankings(df)
    print(f"  {saved} ranking rows saved.")

    print("\n--- Latest rankings ---")
    latest = df[df["date_id"] == df["date_id"].max()].sort_values("rank")
    for _, row in latest.iterrows():
        change_str = (f"+{row['rank_change']}" if row["rank_change"] > 0
                      else str(int(row["rank_change"])))
        print(f"  #{int(row['rank'])} {row['city_name']:<12} "
              f"Score: {row['total_stress_score']:>5.1f}  "
              f"({row['stress_label']})  "
              f"7d change: {change_str}")

    print("\n--- Correlation matrix ---")
    corr = compute_correlation_matrix(df)
    print(corr.to_string())

    print("\n--- Seasonal analysis ---")
    seasonal = compute_seasonal_analysis(df)
    for city in seasonal["city_name"].unique():
        print(f"\n  {city}:")
        city_data = seasonal[seasonal["city_name"] == city].sort_values("mean_score", ascending=False)
        for _, row in city_data.iterrows():
            print(f"    {row['season']:<8} avg: {row['mean_score']:>5.1f}  "
                  f"max: {row['max_score']:>5.1f}  min: {row['min_score']:>5.1f}")

    print("\nRankings complete.")
    return df

if __name__ == "__main__":
    run_rankings()