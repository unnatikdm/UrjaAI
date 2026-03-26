from fastapi import APIRouter, Depends
from app.schemas.predict import WhatIfRequest, WhatIfResponse
from app.services import ml as ml_service
from app.services.data import get_peak_and_total
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/whatif", tags=["What-If Analysis"])


@router.post("", response_model=WhatIfResponse)
def whatif(req: WhatIfRequest, _: User = Depends(get_current_user)):
    """
    Simulate the effect of temperature and occupancy changes on energy
    consumption. Returns both the unchanged baseline forecast and a
    modified forecast reflecting the requested changes.
    """
    # Baseline — use default conditions
    baseline = ml_service.run_forecast(
        building_id=req.building_id,
        horizon=24,
    )

    # Modified forecast — apply what-if scenario
    modified = ml_service.run_forecast(
        building_id=req.building_id,
        horizon=24,
        temperature_offset=req.changes.temperature_offset,
        occupancy_multiplier=req.changes.occupancy_multiplier,
    )

    # Compute a human-readable delta summary
    baseline_total = sum(p.consumption for p in baseline)
    modified_total = sum(p.consumption for p in modified)
    delta_kwh = round(modified_total - baseline_total, 2)
    delta_pct = round((delta_kwh / baseline_total) * 100, 1) if baseline_total else 0

    direction = "increase" if delta_kwh > 0 else "decrease"
    delta_summary = (
        f"With a temperature offset of {req.changes.temperature_offset:+.1f} °C "
        f"and occupancy multiplier of {req.changes.occupancy_multiplier:.1f}×, "
        f"total consumption would {direction} by {abs(delta_kwh):.1f} kWh "
        f"({abs(delta_pct):.1f} %) over 24 hours."
    )

    return WhatIfResponse(
        building_id=req.building_id,
        baseline_forecast=baseline,
        modified_forecast=modified,
        delta_summary=delta_summary,
    )
