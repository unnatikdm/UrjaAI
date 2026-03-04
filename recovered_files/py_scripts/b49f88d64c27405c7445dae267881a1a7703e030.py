from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db import get_db
from app.models.reading import SensorReading
from app.schemas.auth import SensorReadingSchema
from app.services.auth import require_admin
from app.models.user import User

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post("", status_code=201)
def ingest_reading(
    payload: SensorReadingSchema,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),   # admin only
):
    """
    Ingest a single sensor reading from external hardware or a BMS.
    Requires admin role.

    Use this endpoint from your IoT gateway, BMS, or a cron script
    that polls real building sensors.
    """
    reading = SensorReading(
        building_id=payload.building_id,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        consumption_kwh=payload.consumption_kwh,
        temperature_c=payload.temperature_c,
        occupancy=payload.occupancy,
        humidity_pct=payload.humidity_pct,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return {"status": "ok", "id": reading.id, "timestamp": reading.timestamp.isoformat() + "Z"}


@router.get("/latest")
def get_latest_readings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return the most recent reading for each building (admin only)."""
    from app.services.data import KNOWN_BUILDINGS
    result = {}
    for building in KNOWN_BUILDINGS:
        row = (
            db.query(SensorReading)
            .filter(SensorReading.building_id == building)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        result[building] = row.to_dict() if row else None
    return result
