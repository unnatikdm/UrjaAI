"""Sensor Reading Models - Stores IoT sensor data from campus buildings"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db import Base


class SensorReading(Base):
    """Individual sensor reading from building IoT devices"""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    consumption_kwh = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    occupancy = Column(Integer, nullable=True)
    humidity_pct = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "consumption_kwh": self.consumption_kwh,
            "temperature_c": self.temperature_c,
            "occupancy": self.occupancy,
            "humidity_pct": self.humidity_pct
        }
