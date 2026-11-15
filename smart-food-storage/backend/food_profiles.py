"""
food_profiles.py
Centralized food storage profiles and psychrometric envelopes.
All profiles adhere to empirical post-harvest physiology baselines.
"""

from typing import Dict, Any, Optional

DEFAULT_FOOD_PROFILES: Dict[str, Dict[str, Any]] = {
    "tomatoes": {
        "id": "tomatoes",
        "name": "Tomatoes",
        "scientific_name": "Solanum lycopersicum",
        "category": "Climacteric Fruit",
        "temp_min": 12.0,
        "temp_max": 15.0,
        "temp_crit": 30.0,
        "temp_freeze": 0.0,
        "humidity_min": 85.0,
        "humidity_max": 90.0,
        "ideal_shelf_life_hours": 168.0,  # 7 days
        "gas_baseline": 180.0,             # Calibrated MQ-135 clean headspace ADC
        "gas_threshold": 400.0,            # High metabolic off-gas indicator ADC
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.5,
        "description": "Sensitive to chilling injury below 10°C. High temperatures accelerate softening and decay.",
        "icon": "Apple"
    },
    "bananas": {
        "id": "bananas",
        "name": "Bananas",
        "scientific_name": "Musa acuminata",
        "category": "Climacteric Fruit (High Ethylene)",
        "temp_min": 13.0,
        "temp_max": 16.0,
        "temp_crit": 32.0,
        "temp_freeze": 8.0,
        "humidity_min": 85.0,
        "humidity_max": 95.0,
        "ideal_shelf_life_hours": 120.0,  # 5 days (configurable)
        "gas_baseline": 180.0,
        "gas_threshold": 350.0,            # Higher sensitivity to ripening off-gases
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.5,
        "description": "High ethylene producer with acute chilling vulnerability under 12°C and rapid ripening above 18°C.",
        "icon": "Banana"
    },
    "apples": {
        "id": "apples",
        "name": "Apples",
        "scientific_name": "Malus domestica",
        "category": "Pome Fruit (Cold Tolerant)",
        "temp_min": 1.0,
        "temp_max": 4.0,
        "temp_crit": 25.0,
        "temp_freeze": -2.0,
        "humidity_min": 90.0,
        "humidity_max": 95.0,
        "ideal_shelf_life_hours": 720.0,  # 30 days (configurable)
        "gas_baseline": 180.0,
        "gas_threshold": 450.0,
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 1.2,
        "description": "Cold-hardy fruit requiring near-freezing temperatures and elevated humidity to suppress respiration.",
        "icon": "Citrus"
    },
    "leafy_vegetables": {
        "id": "leafy_vegetables",
        "name": "Leafy Vegetables",
        "scientific_name": "Spinacia oleracea / Brassica",
        "category": "High-Transpiration Greens",
        "temp_min": 0.0,
        "temp_max": 4.0,
        "temp_crit": 22.0,
        "temp_freeze": -1.5,
        "humidity_min": 95.0,
        "humidity_max": 100.0,
        "ideal_shelf_life_hours": 120.0,  # 5 days (configurable)
        "gas_baseline": 180.0,
        "gas_threshold": 380.0,
        "weight_temp": 0.30,
        "weight_humidity": 0.25,
        "weight_gas": 0.25,
        "weight_duration": 0.20,
        "stress_multiplier_alpha": 2.0,    # Highly sensitive to desiccation and heat
        "description": "Extreme sensitivity to low humidity resulting in rapid wilting, transpiration loss, and chlorophyll loss.",
        "icon": "Salad"
    }
}


def get_default_profiles() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of the default predefined profiles."""
    import copy
    return copy.deepcopy(DEFAULT_FOOD_PROFILES)


def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """Fetch default profile dictionary by profile id."""
    return get_default_profiles().get(profile_id)
