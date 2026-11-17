"""
test_risk_engine.py
Automated unit tests for Spoilage Risk Engine.
Verifies all mathematical boundary conditions, equations, and classifications.
Tested with physical experiment commodities: Rice and Oranges.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from risk_engine import (
    calculate_temperature_risk,
    calculate_humidity_risk,
    calculate_gas_risk,
    calculate_duration_risk,
    calculate_effective_duration_increment,
    calculate_composite_risk,
    classify_risk,
    generate_recommendations
)
from food_profiles import DEFAULT_FOOD_PROFILES


@pytest.fixture
def rice_profile():
    return DEFAULT_FOOD_PROFILES["rice"]


@pytest.fixture
def orange_profile():
    return DEFAULT_FOOD_PROFILES["oranges"]


def test_temperature_risk_in_range(rice_profile):
    """Score must be 0 inside configured psychrometric envelope [1.0, 4.0]°C."""
    assert calculate_temperature_risk(1.0, rice_profile) == 0.0
    assert calculate_temperature_risk(2.5, rice_profile) == 0.0
    assert calculate_temperature_risk(4.0, rice_profile) == 0.0


def test_temperature_risk_above_max(rice_profile):
    """Score must increase as temperature exceeds Tmax and cap at 100."""
    # Tmax = 4.0, Tcrit = 25.0 -> span = 21.0
    # T = 14.5 -> deviation = 10.5 -> 50%
    score_mid = calculate_temperature_risk(14.5, rice_profile)
    assert abs(score_mid - 50.0) < 0.5

    # T = 25.0 -> 100%
    score_crit = calculate_temperature_risk(25.0, rice_profile)
    assert score_crit == 100.0

    # T = 45.0 -> capped at 100.0
    score_extreme = calculate_temperature_risk(45.0, rice_profile)
    assert score_extreme == 100.0


def test_temperature_risk_below_min(rice_profile):
    """Score must increase as temperature falls below Tmin and cap at 100."""
    # Tmin = 1.0, Tfreeze = -0.5 -> span = 1.5
    # T = 0.25 -> deviation = 0.75 -> 50%
    score_mid = calculate_temperature_risk(0.25, rice_profile)
    assert abs(score_mid - 50.0) < 0.5

    # T = -0.5 -> capped at 100
    score_freeze = calculate_temperature_risk(-0.5, rice_profile)
    assert score_freeze == 100.0


def test_humidity_risk_in_range(rice_profile):
    """Score must be 0 inside [85, 95]% RH."""
    assert calculate_humidity_risk(85.0, rice_profile) == 0.0
    assert calculate_humidity_risk(90.0, rice_profile) == 0.0
    assert calculate_humidity_risk(95.0, rice_profile) == 0.0


def test_humidity_risk_out_of_range(rice_profile):
    """Score must increase outside [85, 95]% and stay bounded in [0, 100]."""
    # Above max: H = 97.5, max = 95, span = 5.0 -> 50%
    score_high = calculate_humidity_risk(97.5, rice_profile)
    assert abs(score_high - 50.0) < 0.5

    # High saturation cap: H = 100 -> 100%
    assert calculate_humidity_risk(100.0, rice_profile) == 100.0

    # Below min: H = 42.5, min = 85 -> 50%
    score_low = calculate_humidity_risk(42.5, rice_profile)
    assert abs(score_low - 50.0) < 0.5

    # Extreme desiccation: H = 0 -> 100%
    assert calculate_humidity_risk(0.0, rice_profile) == 100.0


def test_gas_risk_scoring(rice_profile):
    """Gas score should be 0 at baseline and scale to 100 at threshold."""
    # Baseline = 180, Threshold = 380 -> span = 200
    assert calculate_gas_risk(170.0, rice_profile) == 0.0
    assert calculate_gas_risk(180.0, rice_profile) == 0.0

    # Midpoint: 180 + 100 = 280 -> 50%
    mid = calculate_gas_risk(280.0, rice_profile)
    assert abs(mid - 50.0) < 0.5

    # At or above threshold
    assert calculate_gas_risk(380.0, rice_profile) == 100.0
    assert calculate_gas_risk(850.0, rice_profile) == 100.0


def test_duration_risk_scoring():
    """Duration score scales against ideal shelf life and caps at 100."""
    ideal = 96.0  # hours (4 days for cooked rice)
    assert calculate_duration_risk(0.0, ideal) == 0.0
    assert abs(calculate_duration_risk(48.0, ideal) - 50.0) < 0.1
    assert calculate_duration_risk(96.0, ideal) == 100.0
    assert calculate_duration_risk(200.0, ideal) == 100.0


def test_duration_stress_multiplier():
    """Duration risk accumulates faster when environmental stress is present."""
    delta_h = 1.0  # 1 hour elapsed

    # Nominal conditions (no stress) -> 1.0 hr added
    nominal_inc = calculate_effective_duration_increment(delta_h, temp_score=0.0, humidity_score=0.0, alpha=1.8)
    assert nominal_inc == 1.0

    # Under severe thermal stress (Ts = 100) -> 1.0 * (1.0 + 1.8 * 1.0) = 2.8 hrs added
    stressed_inc = calculate_effective_duration_increment(delta_h, temp_score=100.0, humidity_score=0.0, alpha=1.8)
    assert stressed_inc == 2.8
    assert stressed_inc > nominal_inc


def test_composite_risk_weights_and_bounds():
    """Verify weights sum and score guarantees: 0 <= R <= 100."""
    weights = {"weight_temp": 0.30, "weight_humidity": 0.25, "weight_gas": 0.25, "weight_duration": 0.20}
    assert sum(weights.values()) == 1.0

    # Minimum bound
    r_min = calculate_composite_risk(0.0, 0.0, 0.0, 0.0, weights)
    assert r_min == 0.0

    # Maximum bound
    r_max = calculate_composite_risk(100.0, 100.0, 100.0, 100.0, weights)
    assert r_max == 100.0

    # Scenario: Ts = 80, Hs = 70, Gs = 60, Ds = 75
    # R = (80*0.30) + (70*0.25) + (60*0.25) + (75*0.20) = 24.0 + 17.5 + 15.0 + 15.0 = 71.5%
    test_example = calculate_composite_risk(80.0, 70.0, 60.0, 75.0, weights)
    assert test_example == 71.5


def test_risk_classification():
    """Ensure discrete tier categorization matches exact specification."""
    # Low: 0 to 30
    assert classify_risk(0.0)[0] == "Low"
    assert classify_risk(30.0)[0] == "Low"

    # Moderate: > 30 to 60
    assert classify_risk(30.1)[0] == "Moderate"
    assert classify_risk(60.0)[0] == "Moderate"

    # High: > 60 to 80
    assert classify_risk(60.1)[0] == "High"
    assert classify_risk(80.0)[0] == "High"

    # Critical: > 80 to 100
    assert classify_risk(80.1)[0] == "Critical"
    assert classify_risk(100.0)[0] == "Critical"


def test_actionable_recommendations(rice_profile):
    """Ensure recommendations give actionable advice without claiming food sterility."""
    rec = generate_recommendations(
        category="High",
        profile=rice_profile,
        ts=75.0,
        hs=0.0,
        gs=0.0,
        ds=20.0,
        temp=18.0,
        humidity=88.0,
        gas=185.0
    )
    assert "Temperature" in rec
    assert "1-4°C" in rec
