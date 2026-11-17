"""
food_profiles.py
Centralized food storage profiles and psychrometric envelopes.
All profiles adhere to empirical post-harvest physiology and food safety baselines:
- Cooked Rice: FDA Food Code §3-501.16 & USDA FSIS (TCS Food, Bacillus cereus risk)
- Oranges: USDA Agriculture Handbook 66 & UC Davis Postharvest Technology Center (Citrus sinensis)
"""

from typing import Dict, Any, Optional
import copy

DEFAULT_FOOD_PROFILES: Dict[str, Dict[str, Any]] = {
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
        "ideal_shelf_life_hours": 96.0,  # 4 days (96h) safe refrigerated storage limit (USDA/FDA)
        "gas_baseline": 180.0,             # Calibrated MQ-135 clean headspace ADC baseline
        "gas_threshold": 380.0,            # Off-gas threshold for microbial volatiles and amines ADC
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.8,    # High thermal abuse vulnerability due to rapid Bacillus cereus toxin formation
        "description": "Cooked rice is a high-moisture Time/Temperature Control for Safety (TCS) food requiring continuous refrigeration at 1–4°C (USDA/FDA Food Code). Spoilage risk escalates sharply above 4°C due to rapid Bacillus cereus spore germination. (Note: Raw dry grain requires <15°C and <65% RH for 12–24 month storage).",
        "icon": "Wheat"
    },
    "oranges": {
        "id": "oranges",
        "name": "Oranges",
        "scientific_name": "Citrus sinensis",
        "category": "Non-Climacteric Citrus",
        "temp_min": 3.0,
        "temp_max": 8.0,
        "temp_crit": 25.0,
        "temp_freeze": -1.1,
        "humidity_min": 85.0,
        "humidity_max": 90.0,
        "ideal_shelf_life_hours": 672.0,  # 28 days (4 weeks) optimal refrigerated storage (USDA Handbook 66 / UC Davis)
        "gas_baseline": 180.0,             # Calibrated MQ-135 clean headspace ADC baseline
        "gas_threshold": 400.0,            # Fungal decay volatile accumulation threshold ADC (Penicillium rot)
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.3,    # Moderate post-harvest vulnerability to ambient storage
        "description": "Non-climacteric citrus fruit requiring 3–8°C and 85–90% RH (USDA Handbook 66 / UC Davis). Susceptible to chilling injury (rind pitting) below 2°C; green and blue mold rot (Penicillium digitatum/italicum) accelerates rapidly above 10°C.",
        "icon": "Citrus"
    }
}


def get_default_profiles() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of the default predefined profiles."""
    return copy.deepcopy(DEFAULT_FOOD_PROFILES)


def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """Fetch default profile dictionary by profile id."""
    return get_default_profiles().get(profile_id)
