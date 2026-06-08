import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.collectors import (
    tomtom_collector,
    openaq_collector,
    weather_collector,
    numbeo_collector,
    safety_collector,
)

def run_all():
    print("=" * 50)
    print("CITY STRESS INDEX — Data Collection Run")
    print("=" * 50)

    collectors = [
        ("Traffic",     tomtom_collector),
        ("Air Quality", openaq_collector),
        ("Weather",     weather_collector),
        ("Cost",        numbeo_collector),
        ("Safety",      safety_collector),
    ]

    results = {}
    for name, collector in collectors:
        print(f"\n--- {name} ---")
        try:
            results[name.lower()] = collector.run()
            print(f"{name} ✓")
        except Exception as e:
            print(f"{name} FAILED: {e}")

    print("\n" + "=" * 50)
    print("All collectors done.")
    print("Check data/raw/ for your JSON files.")
    return results

if __name__ == "__main__":
    run_all()