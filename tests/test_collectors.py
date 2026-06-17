import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_config_has_5_cities():
    from src.config import CITIES
    assert len(CITIES) == 5

def test_config_cities_have_required_keys():
    from src.config import CITIES
    for city in CITIES:
        assert "name" in city
        assert "lat"  in city
        assert "lon"  in city

def test_city_coordinates_are_valid():
    from src.config import CITIES
    for city in CITIES:
        assert -90  <= city["lat"] <= 90,  f"Invalid lat for {city['name']}"
        assert -180 <= city["lon"] <= 180, f"Invalid lon for {city['name']}"

def test_static_cost_data_has_all_cities():
    from src.collectors.numbeo_collector import STATIC_COST_DATA
    from src.config import CITIES
    city_names = [c["name"] for c in CITIES]
    for name in city_names:
        assert name in STATIC_COST_DATA, f"Missing static cost data for {name}"

def test_static_cost_data_has_valid_values():
    from src.collectors.numbeo_collector import STATIC_COST_DATA
    for city, data in STATIC_COST_DATA.items():
        assert data["cost_of_living_index"] > 0, f"Invalid cost index for {city}"
        assert data["rent_index"] > 0,           f"Invalid rent index for {city}"

def test_raw_data_files_exist():
    folders = ["data/raw/traffic", "data/raw/airquality",
               "data/raw/weather", "data/raw/cost", "data/raw/safety"]
    for folder in folders:
        assert os.path.exists(folder), f"Missing folder: {folder}"
        files = os.listdir(folder)
        assert len(files) > 0, f"No files in {folder}"