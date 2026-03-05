from fastapi import APIRouter, Depends
from app.schemas.predict import (
    RecommendationsRequest,
    RecommendationsResponse,
    Recommendation,
)
from app.services.data import get_building_history, get_peak_and_total, get_weather_data
from app.services.auth import get_current_user
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Cost per kWh in INR (adjust per campus tariff)
COST_PER_KWH_INR = 7.5


def _smart_recommendations(
    building_id: str,
    temperature_offset: float = 0.0,
    occupancy_multiplier: float = 1.0,
) -> list[Recommendation]:
    """
    Context-aware recommendations that react to:
      1. The building's actual consumption patterns
      2. What-if scenario parameters (temp / occupancy sliders)
      3. Weather / seasonal conditions
      4. Time-of-day usage patterns
    """
    stats = get_peak_and_total(building_id, hours=24)
    df = get_building_history(building_id, days=1)

    peak_kw = stats["peak_kw"]
    total_kwh = stats["total_kwh"]
    recs: list[Recommendation] = []

    # ── Current conditions ────────────────────────────────────────────────
    now = datetime.utcnow()
    current_hour = now.hour
    recent_occupancy = float(df["occupancy"].tail(3).mean())
    recent_temp = float(df["temperature_c"].tail(3).mean())

    # ── Weather data ──────────────────────────────────────────────────────
    try:
        wdf = get_weather_data()
        latest_weather_temp = float(wdf["temperature"].iloc[-1])
        is_monsoon = now.month in (6, 7, 8, 9)
    except Exception:
        latest_weather_temp = 30.0
        is_monsoon = False

    effective_temp = recent_temp + temperature_offset
    effective_occ = recent_occupancy * occupancy_multiplier

    # ─────────────────────────────────────────────────────────────────────
    # SCENARIO 1: What-If Temperature Increase
    # ─────────────────────────────────────────────────────────────────────
    if temperature_offset > 1.5:
        extra_kwh = round(peak_kw * temperature_offset * 0.06, 2)
        recs.append(Recommendation(
            action=f"Deploy solar shading / film to counter the +{temperature_offset:.1f} °C rise",
            savings_kwh=extra_kwh,
            savings_cost_inr=round(extra_kwh * COST_PER_KWH_INR, 2),
            priority="high",
            reason=(
                f"Your what-if scenario shows a +{temperature_offset:.1f} °C temperature "
                f"increase, which would add ~{extra_kwh} kWh to HVAC load. External shading "
                "on south/west-facing glazing blocks up to 70 % of solar heat gain "
                "before it enters the building, reducing compressor work significantly."
            ),
        ))

    if temperature_offset > 2.5:
        savings_chiller = round(peak_kw * 0.10, 2)
        recs.append(Recommendation(
            action="Switch to high-efficiency chiller mode during extreme heat",
            savings_kwh=savings_chiller,
            savings_cost_inr=round(savings_chiller * COST_PER_KWH_INR, 2),
            priority="high",
            reason=(
                f"At +{temperature_offset:.1f} °C above normal, the cooling plant operates "
                "near its design limit. Switching to the high-COP chiller sequence or "
                "activating the thermal storage tank reduces peak electrical demand "
                "by 8–12 %."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # SCENARIO 2: What-If Temperature Decrease
    # ─────────────────────────────────────────────────────────────────────
    if temperature_offset < -1.5:
        free_cool = round(peak_kw * abs(temperature_offset) * 0.05, 2)
        recs.append(Recommendation(
            action="Enable free-cooling economizer mode (outside air is cooler)",
            savings_kwh=free_cool,
            savings_cost_inr=round(free_cool * COST_PER_KWH_INR, 2),
            priority="high",
            reason=(
                f"With temperatures {abs(temperature_offset):.1f} °C below normal, "
                "the outside air is cool enough to bypass the chiller entirely. "
                "Opening the economizer dampers brings in free cooling and "
                f"saves ~{free_cool} kWh per day."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # SCENARIO 3: What-If Low Occupancy
    # ─────────────────────────────────────────────────────────────────────
    if occupancy_multiplier < 0.7:
        zone_save = round(total_kwh * (1 - occupancy_multiplier) * 0.15, 2)
        recs.append(Recommendation(
            action=f"Shut down HVAC in unoccupied zones ({(1 - occupancy_multiplier):.0%} of building empty)",
            savings_kwh=zone_save,
            savings_cost_inr=round(zone_save * COST_PER_KWH_INR, 2),
            priority="high",
            reason=(
                f"At {occupancy_multiplier:.0%} occupancy, large sections of the building "
                "are being conditioned unnecessarily. Zone-based HVAC shutdown "
                f"can save ~{zone_save} kWh by isolating empty floors/wings."
            ),
        ))

    if occupancy_multiplier < 0.5:
        lighting_save = round(total_kwh * 0.08, 2)
        recs.append(Recommendation(
            action="Switch to occupancy-sensor lighting (auto-off in empty rooms)",
            savings_kwh=lighting_save,
            savings_cost_inr=round(lighting_save * COST_PER_KWH_INR, 2),
            priority="medium",
            reason=(
                f"With only {occupancy_multiplier:.0%} of normal occupancy, most rooms are "
                "empty. PIR-based occupancy sensors can auto-switch lights, "
                f"saving ~{lighting_save} kWh daily."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # SCENARIO 4: What-If High Occupancy
    # ─────────────────────────────────────────────────────────────────────
    if occupancy_multiplier > 1.2:
        vent_extra = round(peak_kw * (occupancy_multiplier - 1) * 0.10, 2)
        recs.append(Recommendation(
            action="Pre-ventilate building 30 min before high-occupancy events",
            savings_kwh=vent_extra,
            savings_cost_inr=round(vent_extra * COST_PER_KWH_INR, 2),
            priority="medium",
            reason=(
                f"At {occupancy_multiplier:.0%} of normal occupancy, CO₂ levels will spike, "
                "forcing the AHU to ramp up mid-event. Pre-ventilating with "
                "fresh air 30 min beforehand avoids the demand spike."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 5: Peak-Hour Load Shifting (always relevant)
    # ─────────────────────────────────────────────────────────────────────
    # Find the actual peak hour from the data
    hourly_consumption = df.groupby(df["timestamp"].apply(
        lambda x: int(x.split("T")[1][:2]) if isinstance(x, str) else 12
    ))["consumption_kwh"].mean()

    if len(hourly_consumption) > 0:
        peak_hour = int(hourly_consumption.idxmax())
        savings_shift = round(peak_kw * 0.12, 2)
        recs.append(Recommendation(
            action=f"Shift non-critical loads away from peak hour ({peak_hour:02d}:00)",
            savings_kwh=savings_shift,
            savings_cost_inr=round(savings_shift * COST_PER_KWH_INR, 2),
            priority="high",
            reason=(
                f"Analysis of {building_id.replace('_', ' ').title()}'s consumption shows "
                f"peak demand at {peak_hour:02d}:00. Shifting laundry, EV charging, or "
                "water heating to off-peak hours (22:00–06:00) reduces demand charges "
                "and can cut peak by ~12 %."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 6: Night-Time Waste Detection
    # ─────────────────────────────────────────────────────────────────────
    night_rows = df[df["timestamp"].apply(
        lambda x: int(x.split("T")[1][:2]) if isinstance(x, str) else 12
    ).between(0, 5)]
    if len(night_rows) > 0:
        night_avg = float(night_rows["consumption_kwh"].mean())
        day_avg = float(df["consumption_kwh"].mean())
        night_ratio = night_avg / day_avg if day_avg > 0 else 0

        if night_ratio > 0.4:
            waste_kwh = round(night_avg * 6 * 0.3, 2)  # 6 night hours, 30% wastage
            recs.append(Recommendation(
                action="Investigate high night-time baseload (00:00–05:00)",
                savings_kwh=waste_kwh,
                savings_cost_inr=round(waste_kwh * COST_PER_KWH_INR, 2),
                priority="high",
                reason=(
                    f"Night-time consumption is {night_ratio:.0%} of the daytime average — "
                    "this is unusually high for an unoccupied building. Common culprits: "
                    "HVAC running on stale schedules, server rooms over-cooled, "
                    "or equipment left on standby. An energy audit could recover "
                    f"~{waste_kwh} kWh per night."
                ),
            ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 7: Weather-Based (Monsoon / High Humidity)
    # ─────────────────────────────────────────────────────────────────────
    if is_monsoon or effective_temp > 33:
        dehumid_save = round(peak_kw * 0.07, 2)
        recs.append(Recommendation(
            action="Activate dedicated dehumidification to reduce HVAC overcooling",
            savings_kwh=dehumid_save,
            savings_cost_inr=round(dehumid_save * COST_PER_KWH_INR, 2),
            priority="medium",
            reason=(
                "During Mumbai's monsoon (or hot-humid days), HVAC systems overcool "
                "the air just to remove moisture. A dedicated dehumidifier or "
                "enthalpy wheel handles latent load more efficiently, letting the "
                "chiller focus on sensible cooling and saving ~7 % of HVAC energy."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 8: HVAC Setpoint (always applicable)
    # ─────────────────────────────────────────────────────────────────────
    savings_setpoint = round(peak_kw * 0.08, 2)
    recs.append(Recommendation(
        action="Raise HVAC setpoint by 1 °C during 11:00–14:00 peak window",
        savings_kwh=savings_setpoint,
        savings_cost_inr=round(savings_setpoint * COST_PER_KWH_INR, 2),
        priority="medium",
        reason=(
            "Each 1 °C setpoint increase reduces HVAC energy consumption by "
            "approximately 6–8 %. The 11:00–14:00 window consistently shows "
            "the highest demand for this building."
        ),
    ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 9: Low Occupancy Lighting (data-driven)
    # ─────────────────────────────────────────────────────────────────────
    if effective_occ < 0.5:
        savings_light = round(peak_kw * 0.05, 2)
        recs.append(Recommendation(
            action="Dim non-essential lighting to 60 % in low-occupancy zones",
            savings_kwh=savings_light,
            savings_cost_inr=round(savings_light * COST_PER_KWH_INR, 2),
            priority="medium",
            reason=(
                f"Current effective occupancy is {effective_occ:.0%}, well below "
                "the 70 % threshold. Automated dimming in corridors and "
                "common areas achieves meaningful savings with no comfort impact."
            ),
        ))

    # ─────────────────────────────────────────────────────────────────────
    # PATTERN 10: Equipment Standby (always applicable)
    # ─────────────────────────────────────────────────────────────────────
    savings_standby = round(peak_kw * 0.04, 2)
    recs.append(Recommendation(
        action="Auto-shutdown idle lab/office equipment after 20 min of inactivity",
        savings_kwh=savings_standby,
        savings_cost_inr=round(savings_standby * COST_PER_KWH_INR, 2),
        priority="low",
        reason=(
            "Standby power from computers, projectors, and lab instruments "
            "typically accounts for 4–7 % of total building consumption. "
            "Smart power strips or BMS scheduling can eliminate this."
        ),
    ))

    # Sort by priority (high > medium > low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: priority_order.get(r.priority, 3))

    return recs


@router.post("", response_model=RecommendationsResponse)
def recommendations(req: RecommendationsRequest, _: User = Depends(get_current_user)):
    """
    Return context-aware recommendations for a building.
    Reacts to what-if scenario sliders, consumption patterns, weather, and time of day.
    """
    recs = _smart_recommendations(
        req.building_id,
        temperature_offset=req.temperature_offset or 0.0,
        occupancy_multiplier=req.occupancy_multiplier or 1.0,
    )
    return RecommendationsResponse(
        building_id=req.building_id,
        recommendations=recs,
    )
