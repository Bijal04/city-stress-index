import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.collectors import (
    tomtom_collector,
    openaq_collector,
    weather_collector,
    numbeo_collector,
    safety_collector,
)
from src.etl_loader          import run_etl
from src.feature_engineering import run as run_feature_engineering
from src.scoring_engine      import run_scoring_engine

def run_all():
    print("=" * 55)
    print("CITY STRESS INDEX — Daily Pipeline Run")
    print(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    collectors = [
        ("Traffic",     tomtom_collector),
        ("Air Quality", openaq_collector),
        ("Weather",     weather_collector),
        ("Cost",        numbeo_collector),
        ("Safety",      safety_collector),
    ]

    failed = []
    for name, collector in collectors:
        print(f"\n--- {name} ---")
        try:
            collector.run()
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append(name)

    print("\n--- Loading into database ---")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    run_etl(date_str=today)

    print("\n--- Feature engineering ---")
    run_feature_engineering()

    print("\n--- Scoring engine ---")
    run_scoring_engine()

    print("\n" + "=" * 55)
    if failed:
        print(f"Completed with failures: {', '.join(failed)}")
    else:
        print("Full pipeline complete.")
        print("Collect → ETL → Features → Scores → Done.")
    print("=" * 55)

if __name__ == "__main__":
    run_all()