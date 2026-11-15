"""
test_risk_engine.py
Automated unit tests for Spoilage Risk Engine.
Verifies all mathematical boundary conditions, equations, and classifications.
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
def tomato_profile():
    return DEFAULT_FOOD_PROFILES["tomatoes"]


@pytest.fixture
def banana_profile():
    return DEFAULT_FOOD_PROFILES["bananas"]


def test_temperature_risk_in_range(tomato_profile):
    """Score must be 0 inside configured psychrometric envelope [12, 15]°C."""
    assert calculate_temperature_risk(12.0, tomato_profile) == 0.0
    assert calculate_temperature_risk(13.5, tomato_profile) == 0.0
    assert calculate_temperature_risk(15.0, tomato_profile) == 0.0


def test_temperature_risk_above_max(tomato_profile):
    """Score must increase as temperature exceeds Tmax and cap at 100."""
    # Tmax = 15, Tcrit = 30 -> span = 15
    # T = 22.5 -> deviation = 7.5 -> 50%
    score_mid = calculate_temperature_risk(22.5, tomato_profile)
    assert abs(score_mid - 50.0) < 0.5

    # T = 30 -> 100%
    score_crit = calculate_temperature_risk(30.0, tomato_profile)
    assert score_crit == 100.0

    # T = 45 -> capped at 100.0
    score_extreme = calculate_temperature_risk(45.0, tomato_profile)
    assert score_extreme == 100.0


def test_temperature_risk_below_min(tomato_profile):
    """Score must increase as temperature falls below Tmin and cap at 100."""
    # Tmin = 12, Tfreeze = 0 -> span = 12
    # T = 6 -> deviation = 6 -> 50%
    score_mid = calculate_temperature_risk(6.0, tomato_profile)
    assert abs(score_mid - 50.0) < 0.5

    # T = -5 -> capped at 100
    score_freeze = calculate_temperature_risk(-5.0, tomato_profile)
    assert score_freeze == 100.0


def test_humidity_risk_in_range(tomato_profile):
    """Score must be 0 inside [85, 90]% RH."""
    assert calculate_humidity_risk(85.0, tomato_profile) == 0.0
    assert calculate_humidity_risk(88.0, tomato_profile) == 0.0
    assert calculate_humidity_risk(90.0, tomato_profile) == 0.0


def test_humidity_risk_out_of_range(tomato_profile):
    """Score must increase outside [85, 90]% and stay bounded in [0, 100]."""
    # Above max: H = 95, max = 90, span = 10 -> 50%
    score_high = calculate_humidity_risk(95.0, tomato_profile)
    assert abs(score_high - 50.0) < 0.5

    # High saturation cap: H = 100 -> 100%
    assert calculate_humidity_risk(100.0, tomato_profile) == 100.0

    # Below min: H = 42.5, min = 85 -> 50%
    score_low = calculate_humidity_risk(42.5, tomato_profile)
    assert abs(score_low - 50.0) < 0.5

    # Extreme desiccation: H = 0 -> 100%
    assert calculate_humidity_risk(0.0, tomato_profile) == 100.0


def test_gas_risk_scoring(tomato_profile):
    """Gas score should be 0 at baseline and scale to 100 at threshold."""
    # Baseline = 180, Threshold = 400 -> span = 220
    assert calculate_gas_risk(170.0, tomato_profile) == 0.0
    assert calculate_gas_risk(180.0, tomato_profile) == 0.0

    # Midpoint: 180 + 110 = 290 -> 50%
    mid = calculate_gas_risk(290.0, tomato_profile)
    assert abs(mid - 50.0) < 0.5

    # At or above threshold
    assert calculate_gas_risk(400.0, tomato_profile) == 100.0
    assert calculate_gas_risk(850.0, tomato_profile) == 100.0


def test_duration_risk_scoring():
    """Duration score scales against ideal shelf life and caps at 100."""
    ideal = 168.0  # hours
    assert calculate_duration_risk(0.0, ideal) == 0.0
    assert abs(calculate_duration_risk(84.0, ideal) - 50.0) < 0.1
    assert calculate_duration_risk(168.0, ideal) == 100.0
    assert calculate_duration_risk(300.0, ideal) == 100.0


def test_duration_stress_multiplier():
    """Duration risk accumulates faster when environmental stress is present."""
    delta_h = 1.0  # 1 hour elapsed

    # Nominal conditions (no stress) -> 1.0 hr added
    nominal_inc = calculate_effective_duration_increment(delta_h, temp_score=0.0, humidity_score=0.0, alpha=1.5)
    assert nominal_inc == 1.0

    # Under severe thermal stress (Ts = 100) -> 1.0 * (1.0 + 1.5 * 1.0) = 2.5 hrs added
    stressed_inc = calculate_effective_duration_increment(delta_h, temp_score=100.0, humidity_score=0.0, alpha=1.5)
    assert stressed_inc == 2.5
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

    # Illustrative scenario from patent proposal (Par. 112):
    # Ts = 80, Hs = 70, Gs = 60, Ds = 75
    # R = (80*0.30) + (70*0.25) + (60*0.25) + (75*0.20) = 24.0 + 17.5 + 15.0 + 15.0 = 71.5%
    proposal_example = calculate_composite_risk(80.0, 70.0, 60.0, 75.0, weights)
    assert proposal_example == 71.5


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


def test_actionable_recommendations(tomato_profile):
    """Ensure recommendations give actionable advice without claiming food sterility."""
    rec = generate_recommendations(
        category="High",
        profile=tomato_profile,
        ts=75.0,
        hs=0.0,
        gs=0.0,
        ds=20.0,
        temp=25.0,
        humidity=88.0,
        gas=185.0
    )
    assert "Temperature" in rec
    assert "12-15°C" in rec
