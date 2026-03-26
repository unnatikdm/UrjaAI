"""
services/scheduler.py — APScheduler background job for sensor data ingestion.

Runs every 15 minutes and writes a synthetic sensor reading for every campus
building into the `sensor_readings` table. Replace or extend the
`_generate_reading()` function to pull from real BMS / IoT hardware.
"""
from __future__ import annotations
import math
import random
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db import SessionLocal
from app.models.reading import SensorReading
from app.services.data import KNOWN_BUILDINGS

_DAILY_PATTERN = [
    42, 39, 37, 36, 36, 38,
    45, 58, 75, 92, 105, 112,
    108, 115, 118, 114, 108, 102,
    95, 85, 75, 65, 55, 48,
]

_rng = random.Random()


def _generate_reading(building_id: str) -> SensorReading:
    """
    Produce a realistic-looking synthetic reading for the current timestamp.

    TODO: Replace with a real BMS / sensor API call:
        response = requests.get(f"{BMS_URL}/buildings/{building_id}/latest")
        data = response.json()
        return SensorReading(building_id=building_id, **data)
    """
    now = datetime.now(timezone.utc)
    base = _DAILY_PATTERN[now.hour]
    seed = sum(ord(c) for c in building_id) + now.minute
    _rng.seed(seed)

    temp = 22 + 8 * math.sin(math.pi * now.hour / 12) + _rng.uniform(-2, 2)
    occupancy = max(0.0, min(1.0, 0.4 + 0.5 * math.sin(math.pi * (now.hour - 8) / 10)))
    noise = _rng.uniform(-4, 4)

    return SensorReading(
        building_id=building_id,
        timestamp=now.replace(tzinfo=None),   # store as naive UTC
        consumption_kwh=round(base + noise, 2),
        temperature_c=round(temp, 1),
        occupancy=round(occupancy, 2),
        humidity_pct=round(_rng.uniform(40, 80), 1),
    )


def _ingest_all_buildings() -> None:
    """Job function — called by APScheduler every 15 minutes."""
    db = SessionLocal()
    try:
        readings = [_generate_reading(b) for b in KNOWN_BUILDINGS]
        db.add_all(readings)
        db.commit()
        print(f"[Scheduler] Ingested {len(readings)} readings at {datetime.utcnow().isoformat()}Z")
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Error: {e}")
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _ingest_all_buildings,
        trigger=IntervalTrigger(minutes=15),
        id="ingest_sensor_readings",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),   # run immediately on startup
    )
    return scheduler
