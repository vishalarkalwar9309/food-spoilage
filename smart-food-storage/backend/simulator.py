"""
simulator.py
Sensor Simulator for Smart Food Storage Spoilage Predictor.
Generates realistic simulated sensor telemetry across 5 distinct operational modes.
Feeds simulated telemetry through the exact same ingestion and risk calculation pipeline.
"""

import random
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable


SIMULATION_MODES = {
    "normal": "Normal Safe Conditions",
    "high_temp": "High Temperature Stress",
    "high_humidity": "High Humidity (Condensation)",
    "elevated_gas": "Elevated Metabolic Gas (VOC / Ethylene)",
    "combined_stress": "Combined Unfavorable Conditions (Severe Abuse)"
}


class SensorSimulator:
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.current_mode: str = "normal"
        self.callback = callback
        self.is_running: bool = False
        self.interval_seconds: float = 4.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.last_reading: Optional[Dict[str, Any]] = None

    def set_mode(self, mode: str) -> str:
        """Set simulation mode."""
        if mode not in SIMULATION_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Choose from: {list(SIMULATION_MODES.keys())}")
        self.current_mode = mode
        return self.current_mode

    def get_mode(self) -> str:
        """Get current simulation mode."""
        return self.current_mode

    def generate_reading_values(self, profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Generate temperature, humidity, and gas ADC values appropriate for
        the specified food profile and current simulation mode.
        Adds subtle random fluctuations to mimic physical sensor telemetry.
        """
        t_min = float(profile.get("temp_min", 12.0))
        t_max = float(profile.get("temp_max", 15.0))
        t_crit = float(profile.get("temp_crit", 30.0))
        h_min = float(profile.get("humidity_min", 85.0))
        h_max = float(profile.get("humidity_max", 90.0))
        g_0 = float(profile.get("gas_baseline", 180.0))
        g_thresh = float(profile.get("gas_threshold", 400.0))

        noise_t = random.uniform(-0.3, 0.3)
        noise_h = random.uniform(-0.5, 0.5)
        noise_g = random.uniform(-5.0, 5.0)

        if self.current_mode == "normal":
            target_t = ((t_min + t_max) / 2.0) + noise_t
            target_h = ((h_min + h_max) / 2.0) + noise_h
            target_g = g_0 + 5.0 + noise_g

        elif self.current_mode == "high_temp":
            # Significant thermal elevation
            target_t = t_max + ((t_crit - t_max) * 0.75) + noise_t
            target_h = ((h_min + h_max) / 2.0) + noise_h
            target_g = g_0 + 15.0 + noise_g

        elif self.current_mode == "high_humidity":
            # Humidity exceeds maximum threshold (risking mold/condensation)
            target_t = ((t_min + t_max) / 2.0) + noise_t
            if h_max >= 100.0:
                target_h = 100.0
                target_g = g_0 + 60.0 + noise_g  # Microbial anaerobiosis from standing moisture
            else:
                target_h = min(99.5, h_max + 7.5 + noise_h)
                target_g = g_0 + 20.0 + noise_g

        elif self.current_mode == "elevated_gas":
            # Elevated off-gas response
            target_t = ((t_min + t_max) / 2.0) + noise_t
            target_h = ((h_min + h_max) / 2.0) + noise_h
            target_g = g_thresh + 25.0 + noise_g

        elif self.current_mode == "combined_stress":
            # Simultaneous thermal, humidity, and gas deviation
            target_t = t_max + ((t_crit - t_max) * 0.85) + noise_t
            target_h = max(55.0, h_min - 18.0 + noise_h)  # Acute desiccation
            target_g = g_thresh + 45.0 + noise_g

        else:
            target_t = ((t_min + t_max) / 2.0) + noise_t
            target_h = ((h_min + h_max) / 2.0) + noise_h
            target_g = g_0 + noise_g

        # Bounding to physically possible sensor ranges
        clamped_t = round(max(-20.0, min(60.0, target_t)), 1)
        clamped_h = round(max(5.0, min(100.0, target_h)), 1)
        clamped_g = round(max(0.0, min(1023.0, target_g)), 0)

        return {
            "temperature": clamped_t,
            "humidity": clamped_h,
            "gas": clamped_g
        }

    def generate_single_payload(self, profile: Dict[str, Any], device_id: str = "SIM_HEADSPACE_01") -> Dict[str, Any]:
        """Generate a complete payload dictionary."""
        readings = self.generate_reading_values(profile)
        payload = {
            "temperature": readings["temperature"],
            "humidity": readings["humidity"],
            "gas": readings["gas"],
            "device_id": device_id,
            "source": "simulator",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.last_reading = payload
        return payload

    def start(self, get_active_profile_fn: Callable[[], Dict[str, Any]], interval_seconds: float = 4.0):
        """Start background simulation thread. Thread-safe, ensures single loop."""
        with self._lock:
            if self.is_running:
                return

            self.interval_seconds = max(1.0, interval_seconds)
            self._stop_event.clear()
            self.is_running = True

            def _run():
                while not self._stop_event.is_set():
                    try:
                        profile = get_active_profile_fn()
                        payload = self.generate_single_payload(profile)
                        if self.callback:
                            self.callback(payload)
                    except Exception as e:
                        print(f"[Simulator Error] {e}")
                    self._stop_event.wait(self.interval_seconds)

            self._thread = threading.Thread(target=_run, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop background simulation thread."""
        with self._lock:
            if not self.is_running:
                return
            self.is_running = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
            self._thread = None
