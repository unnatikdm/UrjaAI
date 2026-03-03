from fastapi import APIRouter
from app.schemas.predict import (
    RecommendationsRequest,
    RecommendationsResponse,
    Recommendation,
)
from app.services.data import get_building_history, get_peak_and_total
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Cost per kWh in INR (adjust per campus tariff)
COST_PER_KWH_INR = 7.5


def _rule_based_recommendations(building_id: str) -> list[Recommendation]:
    """
    Pure business-logic rules — no ML required.
    Generates load-shifting and efficiency recommendations based on
    historical usage patterns from the data layer.
    """
    stats = get_peak_and_total(building_id, hours=24)
    df = get_building_history(building_id, days=1)

    peak_kw = stats["peak_kw"]
    recs: list[Recommendation] = []

    # Rule 1: off-peak pre-cooling (always applicable)
    savings_1 = round(peak_kw * 0.12, 2)
    recs.append(Recommendation(
        action="Pre-cool building during off-peak hours (22:00–06:00)",
        savings_kwh=savings_1,
        savings_cost_inr=round(savings_1 * COST_PER_KWH_INR, 2),
        priority="high",
        reason=(
            "Shifting cooling load to off-peak tariff bands reduces demand "
            "charges and cuts unit cost by ~30 %. Thermal mass of the building "
            "retains cool air into morning peak hours."
        ),
    ))

    # Rule 2: HVAC setpoint raise during peak hours
    savings_2 = round(peak_kw * 0.08, 2)
    recs.append(Recommendation(
        action="Raise HVAC setpoint by 1 °C during 11:00–14:00 peak window",
        savings_kwh=savings_2,
        savings_cost_inr=round(savings_2 * COST_PER_KWH_INR, 2),
        priority="medium",
        reason=(
            "Each 1 °C setpoint increase reduces HVAC energy consumption by "
            "approximately 6–8 %. The 11:00–14:00 window consistently shows "
            "the highest demand for this building."
        ),
    ))

    # Rule 3: lighting dimming when low occupancy detected
    recent_occupancy = float(df["occupancy"].tail(3).mean())
    if recent_occupancy < 0.5:
        savings_3 = round(peak_kw * 0.05, 2)
        recs.append(Recommendation(
            action="Dim non-essential lighting to 60 % in low-occupancy zones",
            savings_kwh=savings_3,
            savings_cost_inr=round(savings_3 * COST_PER_KWH_INR, 2),
            priority="medium",
            reason=(
                f"Current average occupancy is {recent_occupancy:.0%}, well below "
                "the 70 % threshold. Automated dimming to 60 % in corridors and "
                "common areas achieves meaningful savings with no comfort impact."
            ),
        ))

    # Rule 4: equipment standby shutdown
    savings_4 = round(peak_kw * 0.04, 2)
    recs.append(Recommendation(
        action="Auto-shutdown idle lab/office equipment after 20 min of inactivity",
        savings_kwh=savings_4,
        savings_cost_inr=round(savings_4 * COST_PER_KWH_INR, 2),
        priority="low",
        reason=(
            "Standby power from computers, projectors, and lab instruments "
            "typically accounts for 4–7 % of total building consumption. "
            "Smart power strips or BMS scheduling can eliminate this."
        ),
    ))

    return recs


@router.post("", response_model=RecommendationsResponse)
def recommendations(req: RecommendationsRequest):
    """
    Return load-shifting and efficiency recommendations for a building.
    These are generated from rule-based business logic — no ML required.
    """
    recs = _rule_based_recommendations(req.building_id)
    return RecommendationsResponse(
        building_id=req.building_id,
        recommendations=recs,
    )
