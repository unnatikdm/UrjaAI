from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.db import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    consumption_kwh = Column(Float, nullable=False)
    temperature_c = Column(Float)
    occupancy = Column(Float)
    humidity_pct = Column(Float)

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "consumption_kwh": self.consumption_kwh,
            "temperature_c": self.temperature_c,
            "occupancy": self.occupancy,
            "humidity_pct": self.humidity_pct,
        }
