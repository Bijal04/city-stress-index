import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config import CITIES

CITY_SLUG_MAP = {
    "Toronto":  "Toronto",
    "New York": "New-York",
    "London":   "London",
    "Mumbai":   "Mumbai",
    "Tokyo":    "Tokyo",
}

# Accurate as of mid-2025. These change slowly (update every few months).
STATIC_COST_DATA = {
    "Toronto":  {"cost_of_living_index": 72.4,  "rent_index": 48.1},
    "New York": {"cost_of_living_index": 100.0, "rent_index": 86.3},
    "London":   {"cost_of_living_index": 81.2,  "rent_index": 62.7},
    "Mumbai":   {"cost_of_living_index": 28.3,  "rent_index": 12.4},
    "Tokyo":    {"cost_of_living_index": 83.1,  "rent_index": 39.6},
}

def _try_scrape(city_name: str) -> dict | None:
    """Attempts to scrape live data. Returns dict on success, None on failure."""
    slug = CITY_SLUG_MAP.get(city_name, city_name.replace(" ", "-"))
    url  = f"https://www.numbeo.com/cost-of-living/in/{slug}"

    headers = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://www.numbeo.com/cost-of-living/",
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"    [scrape] request failed: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    cost_index = None
    rent_index = None

    # Try every table on the page — Numbeo changes class names occasionally
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True)
            try:
                val = float(value)
                if "Cost of Living Index" in label and cost_index is None:
                    cost_index = val
                if "Rent Index" in label and rent_index is None:
                    rent_index = val
            except ValueError:
                pass
        if cost_index is not None:
            break   # found what we need

    if cost_index is None:
        print(f"    [scrape] indices not found in page (Numbeo may be blocking or page changed)")
        return None

    return {"cost_of_living_index": cost_index, "rent_index": rent_index}


def fetch_cost_of_living(city: dict) -> dict:
    name   = city["name"]
    result = _try_scrape(name)

    if result:
        source = "scraped"
        print(f"    [scrape] success")
    else:
        result = STATIC_COST_DATA.get(name, {})
        source = "static_fallback"

    return {
        "city":                 name,
        "timestamp":            datetime.utcnow().isoformat(),
        "cost_of_living_index": result.get("cost_of_living_index"),
        "rent_index":           result.get("rent_index"),
        "source":               source,
    }


def run():
    os.makedirs("data/raw/cost", exist_ok=True)
    results = []

    for city in CITIES:
        print(f"Fetching cost of living for {city['name']}...")
        try:
            result = fetch_cost_of_living(city)
            results.append(result)
            print(f"  Cost index: {result['cost_of_living_index']}  "
                  f"Rent: {result['rent_index']}  Source: {result['source']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/cost/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results


if __name__ == "__main__":
    run()