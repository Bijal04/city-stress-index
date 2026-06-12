import os
import sys
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import get_connection

CLUSTER_NAMES = {
    0: "Low Stress",
    1: "Moderate Stress",
    2: "High Stress",
}

def load_city_averages() -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            s.city_id,
            c.name                        AS city_name,
            ROUND(AVG(s.total_stress_score), 2) AS avg_stress,
            ROUND(AVG(s.traffic_score),      2) AS avg_traffic,
            ROUND(AVG(s.air_quality_score),  2) AS avg_air_quality,
            ROUND(AVG(s.weather_score),      2) AS avg_weather,
            ROUND(AVG(s.safety_score),       2) AS avg_safety,
            ROUND(AVG(s.cost_score),         2) AS avg_cost
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        GROUP BY s.city_id, c.name
    """, conn)
    conn.close()
    return df

def run_kmeans(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    from sklearn.cluster      import KMeans
    from sklearn.preprocessing import StandardScaler

    features = ["avg_stress", "avg_traffic", "avg_air_quality",
                "avg_weather", "avg_safety", "avg_cost"]

    X       = df[features].fillna(0).values
    scaler  = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    df = df.copy()
    df["cluster_label"] = labels

    cluster_stress = df.groupby("cluster_label")["avg_stress"].mean()
    sorted_clusters = cluster_stress.sort_values().index.tolist()
    remap = {old: new for new, old in enumerate(sorted_clusters)}
    df["cluster_label"] = df["cluster_label"].map(remap)

    df["cluster_name"] = df["cluster_label"].map(CLUSTER_NAMES)

    return df

def save_clusters(df: pd.DataFrame):
    conn   = get_connection()
    cursor = conn.cursor()
    saved  = 0

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO city_clusters
                (city_id, cluster_label, cluster_name,
                 avg_stress_score, avg_traffic, avg_air_quality, avg_weather)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city_id) DO UPDATE SET
                cluster_label    = excluded.cluster_label,
                cluster_name     = excluded.cluster_name,
                avg_stress_score = excluded.avg_stress_score,
                avg_traffic      = excluded.avg_traffic,
                avg_air_quality  = excluded.avg_air_quality,
                avg_weather      = excluded.avg_weather
        """, (
            int(row["city_id"]),
            int(row["cluster_label"]),
            row["cluster_name"],
            row["avg_stress"],
            row["avg_traffic"],
            row["avg_air_quality"],
            row["avg_weather"],
        ))
        saved += 1

    conn.commit()
    conn.close()
    return saved

def run_clustering():
    print("=" * 55)
    print("Analytics — K-Means City Clustering")
    print("=" * 55)

    print("\nLoading city averages...")
    df = load_city_averages()
    print(f"  {len(df)} cities loaded.")

    print("\nRunning K-Means (k=3)...")
    df = run_kmeans(df, n_clusters=3)

    print("\nSaving clusters...")
    saved = save_clusters(df)
    print(f"  {saved} cities clustered and saved.")

    print("\n--- Cluster results ---")
    for cluster_id in sorted(df["cluster_label"].unique()):
        cluster_cities = df[df["cluster_label"] == cluster_id]
        cluster_name   = CLUSTER_NAMES.get(cluster_id, f"Cluster {cluster_id}")
        print(f"\n  {cluster_name}:")
        for _, row in cluster_cities.sort_values("avg_stress", ascending=False).iterrows():
            print(f"    {row['city_name']:<12} "
                  f"avg stress: {row['avg_stress']:>5.1f}  "
                  f"traffic: {row['avg_traffic']:>5.1f}  "
                  f"air: {row['avg_air_quality']:>5.1f}")

    print("\nClustering complete.")
    return df

if __name__ == "__main__":
    run_clustering()