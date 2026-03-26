"""
data.py — Building data access layer.

Reads sensor / meter data from CSV files placed in backend/data/.
Returns pandas DataFrames for use by routers and business-logic services.
"""

from __future__ import annotations
import math
import os
import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
WEATHER_CSV = Path(__file__).resolve().parents[2] / "mumbai_weather_2025.csv"


# ─────────────────────────────────────────────────────────────────────────────
# Available buildings
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_BUILDINGS = [
    "main_library",
    "engineering_block",
    "admin_block",
    "sports_complex",
    "hostel_a",
    "hostel_b",
    "cafeteria",
]


def _generate_synthetic_history(building_id: str, days: int = 7) -> pd.DataFrame:
    """
    Fallback: generate a week of synthetic hourly readings when no CSV is found.
    Replace this with real data loading once CSV files are available.
    """
    import random, math

    rows = []
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=days)

    seed = sum(ord(c) for c in building_id)
    rng = random.Random(seed)

    daily_pattern = [
        42, 39, 37, 36, 36, 38,
        45, 58, 75, 92, 105, 112,
        108, 115, 118, 114, 108, 102,
        95, 85, 75, 65, 55, 48,
    ]

    for h in range(days * 24):
        ts = start + timedelta(hours=h)
        base = daily_pattern[ts.hour]
        noise = rng.uniform(-5, 5)
        temp = 22 + 8 * math.sin(math.pi * ts.hour / 12) + rng.uniform(-2, 2)
        occupancy = max(0.0, min(1.0, 0.4 + 0.5 * math.sin(math.pi * (ts.hour - 8) / 10)))

        rows.append({
            "timestamp": ts.isoformat() + "Z",
            "building_id": building_id,
            "consumption_kwh": round(base + noise, 2),
            "temperature_c": round(temp, 1),
            "occupancy": round(occupancy, 2),
            "humidity_pct": round(rng.uniform(40, 80), 1),
        })

    return pd.DataFrame(rows)


def get_building_history(building_id: str, days: int = 7) -> pd.DataFrame:
    """
    Load historical hourly readings for a building.

    Looks for:  backend/data/{building_id}.csv

    CSV must have columns:
        timestamp, building_id, consumption_kwh, temperature_c, occupancy,
        humidity_pct  (all others are ignored)

    Falls back to synthetic data if the CSV does not exist.
    """
    csv_path = DATA_DIR / f"{building_id}.csv"

    if csv_path.exists():
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        df = df.sort_values("timestamp").tail(days * 24).reset_index(drop=True)
        return df

    # Fallback
    return _generate_synthetic_history(building_id, days)


def get_current_conditions(building_id: str) -> dict:
    """
    Return the most recent sensor reading for a building as a plain dict.
    Used by the What-If router as the baseline.
    """
    df = get_building_history(building_id, days=1)
    latest = df.iloc[-1].to_dict()
    return latest


def get_peak_and_total(building_id: str, hours: int = 24) -> dict:
    """
    Compute peak demand (kW) and total consumption (kWh) for the last `hours`.
    """
    df = get_building_history(building_id, days=max(1, hours // 24))
    recent = df.tail(hours)
    return {
        "peak_kw": round(float(recent["consumption_kwh"].max()), 2),
        "total_kwh": round(float(recent["consumption_kwh"].sum()), 2),
    }


def get_weather_data() -> pd.DataFrame:
    """
    Load Mumbai weather data for ML model feature construction.

    Looks for:  backend/mumbai_weather_2025.csv
    Expected columns: date, temperature, humidity, apparent_temp, precipitation

    Falls back to synthetic weather if the file is not found.
    """
    if WEATHER_CSV.exists():
        df = pd.read_csv(WEATHER_CSV)
        df["date"] = pd.to_datetime(df["date"], utc=True)
        return df

    # ── Synthetic fallback ────────────────────────────────────────────────────
    # Generates a year of hourly Mumbai-like weather so ML code always has data.
    rng = random.Random(42)
    rows = []
    start = datetime(2025, 1, 1)
    for h in range(365 * 24):
        ts = start + timedelta(hours=h)
        # Mumbai: 25-35°C, higher humidity in monsoon (Jun-Sep)
        month = ts.month
        base_temp = 28 + 4 * math.sin(math.pi * (month - 3) / 6)
        temp = base_temp + rng.uniform(-3, 3)
        humid = 65 + (20 if 6 <= month <= 9 else 0) + rng.uniform(-10, 10)
        rows.append({
            "date": pd.Timestamp(ts, tz="UTC"),
            "temperature": round(temp, 1),
            "humidity": round(min(100, humid), 1),
            "apparent_temp": round(temp + 2, 1),
            "precipitation": round(rng.uniform(0, 5) if 6 <= month <= 9 else 0, 1),
        })
    return pd.DataFrame(rows)

