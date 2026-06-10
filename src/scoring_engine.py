import os
import sys
import yaml
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection

'''CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')'''
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')

def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def normalize(value, min_val: float, max_val: float) -> float:
    if value is None or pd.isna(value):
        return None
    normalized = (value - min_val) / (max_val - min_val) * 100
    return round(float(np.clip(normalized, 0, 100)), 2)

def get_stress_label(score: float) -> str:
    if score is None:
        return "Unknown"
    if score <= 25:  return "Low"
    if score <= 50:  return "Moderate"
    if score <= 75:  return "High"
    return "Critical"

def load_data_for_scoring() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            f.city_id,
            c.name       AS city_name,
            f.date_id,
            f.congestion_index,
            f.aqi_estimate,
            f.weather_stress,
            f.crime_score,
            f.cost_index,
            cf.traffic_7d_avg,
            cf.aqi_7d_avg,
            cf.heat_stress_index,
            cf.comfort_score,
            cf.affordability_score,
            cf.traffic_trend,
            cf.aqi_trend,
            cf.crime_trend
        FROM fact_city_metrics f
        JOIN dim_city c          ON f.city_id  = c.city_id
        LEFT JOIN city_features cf ON (f.city_id = cf.city_id AND f.date_id = cf.date_id)
        ORDER BY f.city_id, f.date_id
    """, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def compute_component_scores(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    norm = config["normalization"]
    df   = df.copy()

    # Traffic score — use 7d avg if available, else raw
    traffic_raw = df["traffic_7d_avg"].combine_first(df["congestion_index"])
    df["traffic_score"] = traffic_raw.apply(
        lambda v: normalize(v, norm["traffic"]["min"], norm["traffic"]["max"])
    )

    # Air quality score — use 7d avg if available, else raw
    aqi_raw = df["aqi_7d_avg"].combine_first(df["aqi_estimate"])
    df["air_quality_score"] = aqi_raw.apply(
        lambda v: normalize(v, norm["air_quality"]["min"], norm["air_quality"]["max"])
    )

    # Weather score — use heat stress index + weather stress combined
    df["weather_score"] = df.apply(lambda row: (
        normalize(
            (row["heat_stress_index"] if pd.notna(row["heat_stress_index"]) else 0) * 0.5
            + (row["weather_stress"]  if pd.notna(row["weather_stress"])   else 0) * 0.5,
            norm["weather"]["min"],
            norm["weather"]["max"],
        )
    ), axis=1)

    # Safety score — direct normalize
    df["safety_score"] = df["crime_score"].apply(
        lambda v: normalize(v, norm["safety"]["min"], norm["safety"]["max"])
    )

    # Cost score — use affordability score if available, else normalize cost_index
    df["cost_score"] = df.apply(lambda row: (
        normalize(
            100 - row["affordability_score"]
            if pd.notna(row["affordability_score"])
            else row["cost_index"],
            norm["cost"]["min"],
            norm["cost"]["max"],
        )
    ), axis=1)

    return df

def compute_total_stress_score(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    w  = config["scoring"]["weights"]
    df = df.copy()

    def weighted_score(row):
        components = {
            "traffic":     (row.get("traffic_score"),     w["traffic"]),
            "air_quality": (row.get("air_quality_score"), w["air_quality"]),
            "weather":     (row.get("weather_score"),     w["weather"]),
            "safety":      (row.get("safety_score"),      w["safety"]),
            "cost":        (row.get("cost_score"),        w["cost"]),
        }

        total_weight = 0
        total_score  = 0

        for name, (score, weight) in components.items():
            if score is not None and not pd.isna(score):
                total_score  += score * weight
                total_weight += weight

        if total_weight == 0:
            return None

        adjusted = total_score / total_weight
        return round(adjusted, 2)

    df["total_stress_score"] = df.apply(weighted_score, axis=1)
    df["stress_label"]       = df["total_stress_score"].apply(get_stress_label)

    return df

def compute_contributions(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    w  = config["scoring"]["weights"]
    df = df.copy()

    df["traffic_contribution"]     = (df["traffic_score"]     * w["traffic"]).round(2)
    df["air_quality_contribution"] = (df["air_quality_score"] * w["air_quality"]).round(2)
    df["weather_contribution"]     = (df["weather_score"]     * w["weather"]).round(2)
    df["safety_contribution"]      = (df["safety_score"]      * w["safety"]).round(2)
    df["cost_contribution"]        = (df["cost_score"]        * w["cost"]).round(2)

    return df

def save_scores_to_db(df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    saved  = 0

    for _, row in df.iterrows():
        date_str = row["date_id"].strftime("%Y-%m-%d") if hasattr(row["date_id"], "strftime") else str(row["date_id"])[:10]

        cursor.execute("""
            INSERT INTO city_stress_scores (
                city_id, date_id,
                traffic_score, air_quality_score, weather_score,
                cost_score, safety_score,
                total_stress_score, stress_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_id, date_id) DO UPDATE SET
                traffic_score      = excluded.traffic_score,
                air_quality_score  = excluded.air_quality_score,
                weather_score      = excluded.weather_score,
                cost_score         = excluded.cost_score,
                safety_score       = excluded.safety_score,
                total_stress_score = excluded.total_stress_score,
                stress_label       = excluded.stress_label
        """, (
            int(row["city_id"]),
            date_str,
            row.get("traffic_score"),
            row.get("air_quality_score"),
            row.get("weather_score"),
            row.get("cost_score"),
            row.get("safety_score"),
            row.get("total_stress_score"),
            row.get("stress_label"),
        ))
        saved += 1

        if saved % 1000 == 0:
            conn.commit()
            print(f"  {saved} scores saved...")

    conn.commit()
    conn.close()
    return saved

def run_scoring_engine():
    print("=" * 55)
    print("CITY STRESS INDEX — Scoring Engine")
    print("=" * 55)

    print("\nLoading config...")
    config = load_config()
    weights = config["scoring"]["weights"]
    print(f"  Weights: Traffic {weights['traffic']*100:.0f}% | "
          f"Air {weights['air_quality']*100:.0f}% | "
          f"Weather {weights['weather']*100:.0f}% | "
          f"Safety {weights['safety']*100:.0f}% | "
          f"Cost {weights['cost']*100:.0f}%")

    print("\nLoading data...")
    df = load_data_for_scoring()
    print(f"  {len(df)} rows loaded across {df['city_name'].nunique()} cities.")

    print("\nComputing component scores...")
    df = compute_component_scores(df, config)

    print("Computing total stress scores...")
    df = compute_total_stress_score(df, config)

    print("Computing contribution breakdown...")
    df = compute_contributions(df, config)

    print("\nSaving scores to database...")
    saved = save_scores_to_db(df)
    print(f"  {saved} scores saved to city_stress_scores.")

    print("\n--- Latest scores summary ---")
    latest = df[df["date_id"] == df["date_id"].max()].sort_values("total_stress_score", ascending=False)
    for _, row in latest.iterrows():
        print(f"  {row['city_name']:<12} "
              f"Score: {row['total_stress_score']:>5.1f}  "
              f"Label: {row['stress_label']:<10}  "
              f"Traffic: {row['traffic_score']:>5.1f}  "
              f"Air: {row['air_quality_score']:>5.1f}  "
              f"Weather: {row['weather_score']:>5.1f}")

    print("\nScoring engine complete.")
    return df

if __name__ == "__main__":
    run_scoring_engine()