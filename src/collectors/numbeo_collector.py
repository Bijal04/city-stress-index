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

STATIC_COST_DATA = {
    "Toronto":  {"cost_of_living_index": 72.4,  "rent_index": 48.1},
    "New York": {"cost_of_living_index": 100.0, "rent_index": 86.3},
    "London":   {"cost_of_living_index": 81.2,  "rent_index": 62.7},
    "Mumbai":   {"cost_of_living_index": 28.3,  "rent_index": 12.4},
    "Tokyo":    {"cost_of_living_index": 83.1,  "rent_index": 39.6},
}

def fetch_cost_of_living(city: dict) -> dict:
    slug    = CITY_SLUG_MAP.get(city["name"], city["name"].replace(" ", "-"))
    url     = f"https://www.numbeo.com/cost-of-living/in/{slug}"
    headers = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    cost_index = None
    rent_index = None
    source     = "unknown"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup  = BeautifulSoup(response.text, "html.parser")

        # use the correct table class found from debugging
        table = soup.find("table", {"class": "data_wide_table"})

        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    try:
                        val = float(value)
                        if "Cost of Living Index" in label:
                            cost_index = val
                        if "Rent Index" in label:
                            rent_index = val
                    except ValueError:
                        pass

        if cost_index is not None:
            source = "scraped"
        else:
            raise ValueError("Could not parse indices from table")

    except Exception as e:
        print(f"  Scraping failed ({e}), using static fallback")
        fallback   = STATIC_COST_DATA.get(city["name"], {})
        cost_index = fallback.get("cost_of_living_index")
        rent_index = fallback.get("rent_index")
        source     = "static_fallback"

    return {
        "city":                 city["name"],
        "timestamp":            datetime.utcnow().isoformat(),
        "cost_of_living_index": cost_index,
        "rent_index":           rent_index,
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
            print(f"  Cost index: {result['cost_of_living_index']}  Rent: {result['rent_index']}  Source: {result['source']}")
        except Exception as e:
            print(f"  ERROR for {city['name']}: {e}")

    filename = f"data/raw/cost/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved → {filename}")
    return results

if __name__ == "__main__":
    run()