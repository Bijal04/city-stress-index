import os
import sys
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import get_connection

ANOMALY_METRICS = [
    "congestion_index",
    "aqi_estimate",
    "weather_stress",
    "crime_score",
    "total_stress_score",
]

def load_metrics() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            f.city_id,
            c.name  AS city_name,
            f.date_id,
            f.congestion_index,
            f.aqi_estimate,
            f.weather_stress,
            f.crime_score,
            s.total_stress_score
        FROM fact_city_metrics f
        JOIN dim_city c ON f.city_id = c.city_id
        LEFT JOIN city_stress_scores s
          ON s.city_id = f.city_id AND s.date_id = f.date_id
        ORDER BY f.city_id, f.date_id
    """, conn)
    conn.close()
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df

def detect_zscore_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> pd.DataFrame:
    results = []

    for city_name, group in df.groupby("city_name"):
        city_id = group["city_id"].iloc[0]
        group   = group.sort_values("date_id")

        for metric in ANOMALY_METRICS:
            if metric not in group.columns:
                continue

            series = group[metric].dropna()
            if len(series) < 30:
                continue

            mean   = series.mean()
            std    = series.std()
            if std == 0:
                continue

            for _, row in group.iterrows():
                val = row.get(metric)
                if val is None or pd.isna(val):
                    continue

                z_score    = (val - mean) / std
                is_anomaly = abs(z_score) > threshold
                anomaly_type = None

                if is_anomaly:
                    anomaly_type = "spike" if z_score > 0 else "drop"

                results.append({
                    "city_id":      int(city_id),
                    "city_name":    city_name,
                    "date_id":      row["date_id"].strftime("%Y-%m-%d"),
                    "metric":       metric,
                    "value":        round(float(val), 2),
                    "z_score":      round(float(z_score), 3),
                    "is_anomaly":   int(is_anomaly),
                    "anomaly_type": anomaly_type,
                })

    return pd.DataFrame(results)

def detect_isolation_forest_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    from sklearn.ensemble import IsolationForest

    results = []

    for city_name, group in df.groupby("city_name"):
        city_id = group["city_id"].iloc[0]
        group   = group.sort_values("date_id")

        features = group[ANOMALY_METRICS].dropna()
        if len(features) < 50:
            continue

        model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100,
        )
        preds = model.fit_predict(features)

        for i, (idx, row) in enumerate(features.iterrows()):
            original_row = group.loc[idx]
            is_anomaly   = preds[i] == -1

            results.append({
                "city_id":      int(city_id),
                "city_name":    city_name,
                "date_id":      original_row["date_id"].strftime("%Y-%m-%d"),
                "metric":       "multi_metric",
                "value":        original_row.get("total_stress_score"),
                "z_score":      None,
                "is_anomaly":   int(is_anomaly),
                "anomaly_type": "isolation_forest_outlier" if is_anomaly else None,
            })

    return pd.DataFrame(results)

def save_anomalies(df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    saved  = 0

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO city_anomalies
                (city_id, date_id, metric, value, z_score, is_anomaly, anomaly_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_id, date_id, metric) DO UPDATE SET
                value        = excluded.value,
                z_score      = excluded.z_score,
                is_anomaly   = excluded.is_anomaly,
                anomaly_type = excluded.anomaly_type
        """, (
            int(row["city_id"]),
            row["date_id"],
            row["metric"],
            row["value"],
            row["z_score"],
            int(row["is_anomaly"]),
            row["anomaly_type"],
        ))
        saved += 1

        if saved % 2000 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    return saved

def run_anomaly_detection():
    print("=" * 55)
    print("Analytics — Anomaly Detection")
    print("=" * 55)

    print("\nLoading metrics data...")
    df = load_metrics()
    print(f"  {len(df)} rows loaded.")

    print("\nRunning Z-Score anomaly detection...")
    zscore_anomalies = detect_zscore_anomalies(df)
    flagged_z = zscore_anomalies[zscore_anomalies["is_anomaly"] == 1]
    print(f"  Total rows evaluated: {len(zscore_anomalies)}")
    print(f"  Anomalies flagged:    {len(flagged_z)}")

    print("\nRunning Isolation Forest anomaly detection...")
    iso_anomalies = detect_isolation_forest_anomalies(df)
    flagged_iso = iso_anomalies[iso_anomalies["is_anomaly"] == 1]
    print(f"  Total rows evaluated: {len(iso_anomalies)}")
    print(f"  Anomalies flagged:    {len(flagged_iso)}")

    print("\nSaving all anomaly results...")
    all_anomalies = pd.concat([zscore_anomalies, iso_anomalies], ignore_index=True)
    saved = save_anomalies(all_anomalies)
    print(f"  {saved} rows saved to city_anomalies.")

    print("\n--- Top anomalies (highest Z-Score) ---")
    top = flagged_z.sort_values("z_score", ascending=False).head(10)
    for _, row in top.iterrows():
        print(f"  {row['city_name']:<12} {row['date_id']}  "
              f"{row['metric']:<22} z={row['z_score']:>6.2f}  "
              f"value={row['value']:>7.2f}  {row['anomaly_type']}")

    print("\nAnomaly detection complete.")
    return all_anomalies

if __name__ == "__main__":
    run_anomaly_detection()