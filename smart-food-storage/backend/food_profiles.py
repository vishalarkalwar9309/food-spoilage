"""
food_profiles.py
Centralized food storage modes, psychrometric envelopes, and demonstration adjustments.

Defines exactly three selectable food modes:
1. Normal (General ambient pantry storage, -15% demonstration risk adjustment)
2. Fruits and Snacks (Produce & confectionery storage, -10% demonstration risk adjustment)
3. Rice (Cooked grain storage per USDA/FDA Food Code, +5% demonstration risk adjustment)

Formula:
    display_score = clamp(base_risk_score + mode_adjustment, 0, 100)
"""

from typing import Dict, Any, Optional, Tuple
import copy

MODE_ADJUSTMENTS: Dict[str, float] = {
    "normal": -15.0,
    "fruits_and_snacks": -10.0,
    "rice": 5.0
}

DEFAULT_FOOD_PROFILES: Dict[str, Dict[str, Any]] = {
    "normal": {
        "id": "normal",
        "name": "Normal",
        "scientific_name": "Ambient Household Storage",
        "category": "General Food Storage",
        "temp_min": 15.0,
        "temp_max": 22.0,
        "temp_crit": 35.0,
        "temp_freeze": 0.0,
        "humidity_min": 40.0,
        "humidity_max": 65.0,
        "ideal_shelf_life_hours": 336.0,  # 14 days
        "gas_baseline": 180.0,
        "gas_threshold": 400.0,
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.0,
        "mode_adjustment": -15.0,
        "description": "Standard ambient storage conditions for general household groceries, shelf-stable goods, and dry pantry items (15–22°C, 40–65% RH). Demonstration risk adjustment: -15%.",
        "icon": "Package"
    },
    "fruits_and_snacks": {
        "id": "fruits_and_snacks",
        "name": "Fruits and Snacks",
        "scientific_name": "Fresh Tabletop Produce & Dry Snacks",
        "category": "Fruits & Confectionery",
        "temp_min": 8.0,
        "temp_max": 16.0,
        "temp_crit": 30.0,
        "temp_freeze": 0.0,
        "humidity_min": 50.0,
        "humidity_max": 75.0,
        "ideal_shelf_life_hours": 240.0,  # 10 days
        "gas_baseline": 180.0,
        "gas_threshold": 400.0,
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.2,
        "mode_adjustment": -10.0,
        "description": "Preservation envelope for fresh tabletop fruits, packaged baked goods, and confectioneries (8–16°C, 50–75% RH). Demonstration risk adjustment: -10%.",
        "icon": "Apple"
    },
    "rice": {
        "id": "rice",
        "name": "Rice",
        "scientific_name": "Oryza sativa (Cooked / Prepared Grain)",
        "category": "Prepared Grain (TCS Perishable)",
        "temp_min": 1.0,
        "temp_max": 4.0,
        "temp_crit": 25.0,
        "temp_freeze": -0.5,
        "humidity_min": 85.0,
        "humidity_max": 95.0,
        "ideal_shelf_life_hours": 96.0,  # 4 days
        "gas_baseline": 180.0,
        "gas_threshold": 380.0,
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.8,
        "mode_adjustment": 5.0,
        "description": "Cooked rice is a TCS high-moisture perishable food requiring continuous refrigeration at 1–4°C (USDA/FDA). High Bacillus cereus enterotoxin risk above 4°C. Demonstration risk adjustment: +5%.",
        "icon": "Wheat"
    }
}


def get_default_profiles() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of the default predefined profiles."""
    return copy.deepcopy(DEFAULT_FOOD_PROFILES)


def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """Fetch default profile dictionary by profile id."""
    return get_default_profiles().get(profile_id)


def compute_adjusted_score(base_score: float, mode_id: str) -> Tuple[float, float]:
    """
    Apply mode-based demonstration adjustment:
        display_score = clamp(base_risk_score + mode_adjustment, 0, 100)
    Always calculates from the original unadjusted base score.
    Returns:
        (display_score, mode_adjustment)
    """
    mode_adj = float(MODE_ADJUSTMENTS.get(mode_id, 0.0))
    display_score = round(max(0.0, min(100.0, base_score + mode_adj)), 2)
    return display_score, mode_adj
