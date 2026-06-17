import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import get_connection
from src.logger   import get_logger

logger = get_logger("data_quality")

def check_missing_values() -> dict:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            f.date_id,
            c.name AS city,
            f.congestion_index,
            f.avg_pm25,
            f.temp_c,
            f.cost_index,
            f.crime_score
        FROM fact_city_metrics f
        JOIN dim_city c ON f.city_id = c.city_id
        WHERE f.date_id = (SELECT MAX(date_id) FROM fact_city_metrics)
    """, conn)
    conn.close()

    issues  = {}
    columns = ["congestion_index", "avg_pm25", "temp_c", "cost_index", "crime_score"]

    for col in columns:
        missing = df[col].isna().sum()
        if missing > 0:
            cities = df[df[col].isna()]["city"].tolist()
            issues[col] = {"missing_count": missing, "cities": cities}
            logger.warning(f"Missing values in {col}: {cities}")
        else:
            logger.info(f"{col}: all values present.")

    return issues

def check_duplicates() -> dict:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT city_id, date_id, COUNT(*) as cnt
        FROM fact_city_metrics
        GROUP BY city_id, date_id
        HAVING COUNT(*) > 1
    """, conn)
    conn.close()

    if df.empty:
        logger.info("No duplicate rows found in fact_city_metrics.")
        return {}

    logger.warning(f"Found {len(df)} duplicate city/date combinations.")
    return {"duplicates": df.to_dict("records")}

def check_score_ranges() -> dict:
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT
            c.name AS city,
            s.date_id,
            s.total_stress_score
        FROM city_stress_scores s
        JOIN dim_city c ON s.city_id = c.city_id
        WHERE s.date_id = (SELECT MAX(date_id) FROM city_stress_scores)
    """, conn)
    conn.close()

    issues = {}
    out_of_range = df[
        (df["total_stress_score"] < 0) |
        (df["total_stress_score"] > 100)
    ]

    if not out_of_range.empty:
        logger.warning(f"Scores out of range (0-100): {out_of_range['city'].tolist()}")
        issues["out_of_range"] = out_of_range.to_dict("records")
    else:
        logger.info("All stress scores within valid range (0-100).")

    null_scores = df[df["total_stress_score"].isna()]
    if not null_scores.empty:
        logger.warning(f"Null scores found for: {null_scores['city'].tolist()}")
        issues["null_scores"] = null_scores["city"].tolist()
    else:
        logger.info("No null stress scores found.")

    return issues

def check_row_counts() -> dict:
    conn = get_connection()
    cur  = conn.cursor()

    counts = {}
    for table in ["dim_city", "dim_date", "fact_city_metrics",
                  "city_stress_scores", "city_features"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        counts[table] = count
        logger.info(f"{table}: {count} rows")

    conn.close()

    if counts.get("dim_city", 0) < 5:
        logger.error("dim_city has fewer than 5 cities!")
    if counts.get("fact_city_metrics", 0) < 100:
        logger.error("fact_city_metrics has suspiciously few rows!")

    return counts

def run_data_quality_checks() -> dict:
    logger.info("=" * 50)
    logger.info("Running data quality checks...")
    logger.info("=" * 50)

    results = {
        "missing_values": check_missing_values(),
        "duplicates":     check_duplicates(),
        "score_ranges":   check_score_ranges(),
        "row_counts":     check_row_counts(),
    }

    total_issues = (
        len(results["missing_values"]) +
        len(results["duplicates"]) +
        len(results["score_ranges"])
    )

    if total_issues == 0:
        logger.info("All data quality checks passed.")
    else:
        logger.warning(f"Data quality checks found {total_issues} issue(s).")

    return results

if __name__ == "__main__":
    run_data_quality_checks()