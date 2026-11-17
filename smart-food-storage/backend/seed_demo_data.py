"""
seed_demo_data.py
Optional utility to populate sample historical telemetry into food_storage.db.
Demonstrates realistic psychrometric transitions and alert escalations.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

import database
from app import process_sensor_reading, DB_PATH

def seed_demo():
    print("Seeding initial demonstration telemetry into food_storage.db...")
    database.init_db(DB_PATH)

    # Start a demonstration session for Rice
    session = database.start_session("rice", "Demonstration Storage Batch #1", DB_PATH)
    session_id = session["id"]

    now = datetime.now(timezone.utc)
    # Generate 20 timestamped readings over the last 2 hours
    # 1. Normal safe cold-chain phase (8 readings: 2.0-3.0°C)
    # 2. Temperature elevation phase (6 readings: up to 18°C)
    # 3. Restoration phase (6 readings: cooling back to 3°C)

    for i in range(20):
        t_offset = now - timedelta(minutes=(20 - i) * 6)
        t_str = t_offset.isoformat()

        if i < 8:
            # Optimal cold storage for cooked rice (1-4°C)
            temp = 2.5 + (i * 0.1)
            humidity = 88.0 - (i * 0.1)
            gas = 185.0 + (i * 1.5)
        elif i < 14:
            # Cold-chain break (ambient thermal exposure)
            temp = 6.0 + ((i - 8) * 2.5)
            humidity = 84.0 - ((i - 8) * 1.2)
            gas = 210.0 + ((i - 8) * 25.0)
        else:
            # Re-cooling
            temp = 18.0 - ((i - 14) * 2.5)
            humidity = 88.0
            gas = 310.0 - ((i - 14) * 20.0)

        process_sensor_reading({
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "gas": round(gas, 0),
            "device_id": "SIM_HEADSPACE_01",
            "source": "simulator",
            "timestamp": t_str
        })

    print("[OK] Demonstration dataset seeded successfully!")

if __name__ == "__main__":
    seed_demo()
