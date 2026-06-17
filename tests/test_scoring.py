import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.scoring_engine import normalize, get_stress_label

def test_normalize_middle_value():
    result = normalize(50, 0, 100)
    assert result == 50.0

def test_normalize_min_value():
    result = normalize(0, 0, 100)
    assert result == 0.0

def test_normalize_max_value():
    result = normalize(100, 0, 100)
    assert result == 100.0

def test_normalize_clips_above_max():
    result = normalize(150, 0, 100)
    assert result == 100.0

def test_normalize_clips_below_min():
    result = normalize(-10, 0, 100)
    assert result == 0.0

def test_normalize_none_returns_none():
    result = normalize(None, 0, 100)
    assert result is None

def test_stress_label_low():
    assert get_stress_label(20) == "Low"

def test_stress_label_moderate():
    assert get_stress_label(40) == "Moderate"

def test_stress_label_high():
    assert get_stress_label(60) == "High"

def test_stress_label_critical():
    assert get_stress_label(80) == "Critical"

def test_stress_label_boundary_low():
    assert get_stress_label(25) == "Low"

def test_stress_label_boundary_moderate():
    assert get_stress_label(26) == "Moderate"

def test_stress_label_none():
    assert get_stress_label(None) == "Unknown"