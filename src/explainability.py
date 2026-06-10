import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection

def explain_city_score(city_name: str, date_str: str = None) -> dict:
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT
            c.name,
            s.date_id,
            s.total_stress_score,
            s.stress_label,
            s.traffic_score,
            s.air_quality_score,
            s.weather_score,
            s.safety_score,
            s.cost_score,
            f.congestion_index,
            f.aqi_estimate,
            f.temp_c,
            f.weather_stress,
            f.crime_score,
            f.cost_index,
            cf.traffic_7d_avg,
            cf.traffic_trend,
            cf.air_quality_7d_avg,
            cf.air_quality_trend
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        JOIN fact_city_metrics f
          ON f.city_id = s.city_id AND f.date_id = s.date_id
        LEFT JOIN city_features cf
          ON cf.city_id = s.city_id AND cf.date_id = s.date_id
        WHERE c.name   = ?
          AND s.date_id = ?
    """, (city_name, date_str))

    row = cur.fetchone()
    conn.close()

    if not row:
        return {"error": f"No data found for {city_name} on {date_str}"}

    row = dict(row)

    weights = {
        "Traffic":     (row["traffic_score"],     0.35),
        "Air Quality": (row["air_quality_score"],  0.25),
        "Weather":     (row["weather_score"],      0.20),
        "Safety":      (row["safety_score"],       0.10),
        "Cost":        (row["cost_score"],         0.10),
    }

    contributions = {
        name: round(score * weight, 2) if score is not None else 0
        for name, (score, weight) in weights.items()
    }

    sorted_contributions = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    biggest_driver       = sorted_contributions[0][0]

    return {
        "city":              row["name"],
        "date":              row["date_id"],
        "total_score":       row["total_stress_score"],
        "label":             row["stress_label"],
        "biggest_driver":    biggest_driver,
        "contributions":     contributions,
        "component_scores": {
            "Traffic":     row["traffic_score"],
            "Air Quality": row["air_quality_score"],
            "Weather":     row["weather_score"],
            "Safety":      row["safety_score"],
            "Cost":        row["cost_score"],
        },
        "raw_values": {
            "congestion_index": row["congestion_index"],
            "aqi_estimate":     row["aqi_estimate"],
            "temp_c":           row["temp_c"],
            "weather_stress":   row["weather_stress"],
            "crime_score":      row["crime_score"],
            "cost_index":       row["cost_index"],
        },
        "trends": {
            "traffic":     row["traffic_trend"],
            "air_quality": row["air_quality_trend"],
        }
    }

def print_explanation(city_name: str, date_str: str = None):
    result = explain_city_score(city_name, date_str)

    if "error" in result:
        print(result["error"])
        return

    print("=" * 55)
    print(f"STRESS SCORE EXPLANATION")
    print(f"City: {result['city']}   Date: {result['date']}")
    print("=" * 55)
    print(f"\nTotal Stress Score : {result['total_score']} / 100")
    print(f"Stress Label       : {result['label']}")
    print(f"Biggest Driver     : {result['biggest_driver']}")

    print("\n--- Component Contributions ---")
    print(f"{'Component':<15} {'Score':>7}  {'Weight':>7}  {'Contribution':>12}")
    print("-" * 45)

    weights_map = {
        "Traffic": 0.35, "Air Quality": 0.25,
        "Weather": 0.20, "Safety": 0.10, "Cost": 0.10
    }
    for name, contribution in sorted(result["contributions"].items(), key=lambda x: x[1], reverse=True):
        score  = result["component_scores"][name]
        weight = weights_map[name]
        print(f"  {name:<13} {score:>7.1f}  {weight*100:>6.0f}%  {contribution:>12.2f}")

    print("\n--- Raw Values ---")
    for key, val in result["raw_values"].items():
        if val is not None:
            print(f"  {key:<22}: {val}")

    print("\n--- Trends ---")
    for key, val in result["trends"].items():
        if val is not None:
            print(f"  {key:<10}: {val}")

    print("=" * 55)

def run_all_cities_latest():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name FROM dim_city ORDER BY name")
    cities = [r["name"] for r in cur.fetchall()]
    cur.execute("SELECT MAX(date_id) as d FROM city_stress_scores")
    latest_date = cur.fetchone()["d"]
    conn.close()

    for city in cities:
        print_explanation(city, latest_date)
        print()

if __name__ == "__main__":
    run_all_cities_latest()