"""
risk_engine.py
Spoilage-Risk Engine for Smart Food Storage Spoilage Predictor.

Implements the multi-parameter duration-weighted mathematical model:
    R = (Ts * WT) + (Hs * WH) + (Gs * WG) + (Ds * WD)

Subject to:
    Ts, Hs, Gs, Ds in [0, 100]
    WT + WH + WG + WD = 1.0
    R in [0, 100]
"""

from typing import Dict, Any, Tuple


def calculate_temperature_risk(temp: float, profile: Dict[str, Any]) -> float:
    """
    Calculate normalized temperature deviation risk score (Ts in [0, 100]).
    Ts = 0 inside [Tmin, Tmax] and increases with deviation outside this range.
    """
    t_min = float(profile.get("temp_min", 10.0))
    t_max = float(profile.get("temp_max", 15.0))
    t_crit = float(profile.get("temp_crit", 30.0))
    t_freeze = float(profile.get("temp_freeze", 0.0))

    if t_min <= temp <= t_max:
        return 0.0
    elif temp > t_max:
        span = max(0.1, t_crit - t_max)
        raw = ((temp - t_max) / span) * 100.0
        return float(min(100.0, max(0.0, round(raw, 2))))
    else:  # temp < t_min
        span = max(0.1, t_min - t_freeze)
        raw = ((t_min - temp) / span) * 100.0
        return float(min(100.0, max(0.0, round(raw, 2))))


def calculate_humidity_risk(humidity: float, profile: Dict[str, Any]) -> float:
    """
    Calculate normalized humidity deviation risk score (Hs in [0, 100]).
    Hs = 0 inside [Hmin, Hmax] and increases with deviation outside this range.
    """
    h_min = float(profile.get("humidity_min", 85.0))
    h_max = float(profile.get("humidity_max", 90.0))

    if h_min <= humidity <= h_max:
        return 0.0
    elif humidity > h_max:
        span = max(0.1, 100.0 - h_max)
        raw = ((humidity - h_max) / span) * 100.0
        return float(min(100.0, max(0.0, round(raw, 2))))
    else:  # humidity < h_min
        span = max(0.1, h_min)
        raw = ((h_min - humidity) / span) * 100.0
        return float(min(100.0, max(0.0, round(raw, 2))))


def calculate_gas_risk(gas_adc: float, profile: Dict[str, Any]) -> float:
    """
    Calculate normalized gas-response deviation risk score (Gs in [0, 100]).
    Evaluates MQ-135 ADC response relative to calibrated baseline and threshold.
    Note: Reflects relative volatile gas emissions, not definitive chemical concentrations.
    """
    g_0 = float(profile.get("gas_baseline", 180.0))
    g_thresh = float(profile.get("gas_threshold", 400.0))

    if gas_adc <= g_0:
        return 0.0

    span = max(1.0, g_thresh - g_0)
    raw = ((gas_adc - g_0) / span) * 100.0
    return float(min(100.0, max(0.0, round(raw, 2))))


def calculate_duration_risk(accumulated_effective_hours: float, ideal_shelf_life_hours: float) -> float:
    """
    Calculate normalized cumulative storage duration risk score (Ds in [0, 100]).
    Ds is the ratio of effective stress-weighted exposure hours to ideal shelf life.
    """
    shelf_life = max(1.0, float(ideal_shelf_life_hours))
    raw = (max(0.0, accumulated_effective_hours) / shelf_life) * 100.0
    return float(min(100.0, max(0.0, round(raw, 2))))


def calculate_effective_duration_increment(
    delta_hours: float,
    temp_score: float,
    humidity_score: float,
    alpha: float = 1.5
) -> float:
    """
    Calculate the effective time increment modulated by environmental stress multiplier:
        Epenalty = 1.0 + alpha * stress_intensity
    where stress_intensity is proportional to temperature and humidity deviation.
    """
    if delta_hours <= 0:
        return 0.0

    # Determine stress factor (0.0 to 1.0)
    if temp_score > 0 or humidity_score > 0:
        stress_intensity = max(temp_score, humidity_score) / 100.0
        penalty_multiplier = 1.0 + (alpha * stress_intensity)
    else:
        penalty_multiplier = 1.0

    return delta_hours * penalty_multiplier


def calculate_composite_risk(
    ts: float,
    hs: float,
    gs: float,
    ds: float,
    weights: Dict[str, float]
) -> float:
    """
    Calculate composite spoilage risk score:
        R = (Ts * WT) + (Hs * WH) + (Gs * WG) + (Ds * WD)
    Guaranteed bounded in [0.0, 100.0].
    """
    wt = float(weights.get("weight_temp", 0.30))
    wh = float(weights.get("weight_humidity", 0.25))
    wg = float(weights.get("weight_gas", 0.25))
    wd = float(weights.get("weight_duration", 0.20))

    total_weight = wt + wh + wg + wd
    if round(total_weight, 4) != 1.0 and total_weight > 0:
        # Normalize weights if not exactly summing to 1.0
        wt /= total_weight
        wh /= total_weight
        wg /= total_weight
        wd /= total_weight

    score = (ts * wt) + (hs * wh) + (gs * wg) + (ds * wd)
    return float(min(100.0, max(0.0, round(score, 2))))


def classify_risk(risk_score: float) -> Tuple[str, str]:
    """
    Classify composite risk score into severity tier and corresponding color code.
    Tiers:
        0 - 30: Low (Green)
        > 30 - 60: Moderate (Yellow)
        > 60 - 80: High (Orange)
        > 80 - 100: Critical (Red)
    """
    if risk_score <= 30.0:
        return "Low", "green"
    elif risk_score <= 60.0:
        return "Moderate", "yellow"
    elif risk_score <= 80.0:
        return "High", "orange"
    else:
        return "Critical", "red"


def generate_recommendations(
    category: str,
    profile: Dict[str, Any],
    ts: float,
    hs: float,
    gs: float,
    ds: float,
    temp: float,
    humidity: float,
    gas: float
) -> str:
    """
    Generate actionable preservation recommendations based on active risk drivers.
    Includes explicit reminder regarding environmental risk estimation.
    """
    food_name = profile.get("name", "Perishable Produce")
    t_min = profile.get("temp_min", 12.0)
    t_max = profile.get("temp_max", 15.0)
    h_min = profile.get("humidity_min", 85.0)
    h_max = profile.get("humidity_max", 90.0)

    advice_items = []

    def fmt_val(v):
        try:
            fv = float(v)
            return str(int(fv)) if fv.is_integer() else str(fv)
        except Exception:
            return str(v)

    t_span_str = f"{fmt_val(t_min)}-{fmt_val(t_max)}°C"
    h_span_str = f"{fmt_val(h_min)}-{fmt_val(h_max)}%"

    if ts > 0:
        if temp > t_max:
            advice_items.append(f"Temperature ({temp:.1f}°C) exceeds optimal range ({t_span_str}). Relocate to refrigerated or chilled environment.")
        elif temp < t_min:
            advice_items.append(f"Temperature ({temp:.1f}°C) is below recommended minimum ({fmt_val(t_min)}°C). Prevent chilling injury or freezing.")

    if hs > 0:
        if humidity > h_max:
            advice_items.append(f"High relative humidity ({humidity:.1f}%) exceeds envelope ({h_span_str}). Improves headspace ventilation to avoid condensation.")
        elif humidity < h_min:
            advice_items.append(f"Low relative humidity ({humidity:.1f}%) is below optimal ({h_span_str}). Protect against desiccation and wilting.")

    if gs > 30:
        advice_items.append(f"Elevated volatile off-gas response (ADC: {int(gas)}). Possible ripening senescence or anaerobic decomposition. Inspect headspace.")

    if ds > 70:
        advice_items.append("Cumulative exposure duration near shelf life limit. Prioritize immediate culinary use or secondary processing.")

    if category == "Low":
        remedy = f"Optimal storage conditions maintained for {food_name}. Normal physiological dormancy."
    elif category == "Moderate":
        remedy = f"Incipient storage stress detected. " + (" ".join(advice_items) if advice_items else "Verify storage container seal.")
    elif category == "High":
        remedy = f"Elevated degradation risk! " + (" ".join(advice_items) if advice_items else "Transfer produce immediately to target environment.")
    else:  # Critical
        remedy = f"CRITICAL SPOILAGE RISK. Severe thermal/metabolic abuse detected. " + (" ".join(advice_items) if advice_items else "Inspect food tissue immediately before consumption.")

    return remedy
