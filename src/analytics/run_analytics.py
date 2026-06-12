import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analytics.rankings          import run_rankings
from src.analytics.forecasting       import run_forecasting
from src.analytics.anomaly_detection import run_anomaly_detection
from src.analytics.clustering        import run_clustering

def run_all_analytics():
    print("=" * 55)
    print("CITY STRESS INDEX — Full Analytics Suite")
    print(f"Run time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    steps = [
        ("Rankings + Correlations", run_rankings),
        ("Anomaly Detection",       run_anomaly_detection),
        ("Clustering",              run_clustering),
        ("Forecasting",             run_forecasting),
    ]

    for name, fn in steps:
        print(f"\n{'='*55}")
        print(f"Running: {name}")
        print("=" * 55)
        try:
            fn()
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 55)
    print("All analytics complete.")
    print("=" * 55)

if __name__ == "__main__":
    run_all_analytics()