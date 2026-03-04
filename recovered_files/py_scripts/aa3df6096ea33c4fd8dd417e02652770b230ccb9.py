from fastapi import APIRouter, Depends
from app.schemas.predict import PredictRequest, PredictResponse
from app.services import ml as ml_service
from app.services.auth import get_current_user
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/predict", tags=["Forecast"])


@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest, _: User = Depends(get_current_user)):
    """
    Return an hourly energy-consumption forecast for the requested building.
    Results include confidence intervals and optionally incorporate
    what-if modifier overrides.
    """
    forecast = ml_service.run_forecast(
        building_id=req.building_id,
        horizon=req.horizon,
        modifiers=req.what_if_modifiers,
        temperature_offset=(
            req.what_if_modifiers.temperature - 25
            if req.what_if_modifiers and req.what_if_modifiers.temperature
            else 0.0
        ),
        occupancy_multiplier=(
            req.what_if_modifiers.occupancy
            if req.what_if_modifiers and req.what_if_modifiers.occupancy
            else 1.0
        ),
    )

    return PredictResponse(
        building_id=req.building_id,
        generated_at=datetime.utcnow().isoformat() + "Z",
        forecast=forecast,
    )
