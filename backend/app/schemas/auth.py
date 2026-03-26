from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class SensorReadingSchema(BaseModel):
    """Schema for POST /ingest payloads from external sensors."""
    building_id: str
    consumption_kwh: float
    temperature_c: Optional[float] = None
    occupancy: Optional[float] = None
    humidity_pct: Optional[float] = None
