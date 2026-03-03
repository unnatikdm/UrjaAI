"""
ml.py — ML integration surface.

Partner: implement the two functions below by:
  1. Loading your trained model from app/models/
  2. Replacing the TODO bodies with real inference calls.

Everything else in the backend is already wired up — these are the ONLY
functions you need to change.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from app.schemas.predict import (
    ForecastPoint,
    FeatureContribution,
    WhatIfModifiers,
)

# ─────────────────────────────────────────────────────────────────────────────
# STUB DATA (used until ML models are integrated)
# ─────────────────────────────────────────────────────────────────────────────

_DAILY_PATTERN = [
    42, 39, 37, 36, 36, 38,   # 00-05
    45, 58, 75, 92, 105, 112,  # 06-11
    108, 115, 118, 114, 108, 102,  # 12-17
    95, 85, 75, 65, 55, 48,   # 18-23
]

_FEATURE_STUBS: list[FeatureContribution] = [
    FeatureContribution(feature="temperature", contribution=0.31),
    FeatureContribution(feature="hour_of_day", contribution=0.24),
    FeatureContribution(feature="occupancy", contribution=0.20),
    FeatureContribution(feature="day_of_week", contribution=0.12),
    FeatureContribution(feature="humidity", contribution=0.08),
    FeatureContribution(feature="solar_irradiance", contribution=-0.05),
]


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC INTERFACE — partner fills these in
# ─────────────────────────────────────────────────────────────────────────────

def run_forecast(
    building_id: str,
    horizon: int = 24,
    modifiers: Optional[WhatIfModifiers] = None,
    temperature_offset: float = 0.0,
    occupancy_multiplier: float = 1.0,
) -> list[ForecastPoint]:
    """
    Return hourly energy-consumption forecast for `building_id`.

    Parameters
    ----------
    building_id          : campus building identifier
    horizon              : number of hours to forecast
    modifiers            : optional what-if overrides from /predict
    temperature_offset   : °C delta applied on top of current reading
    occupancy_multiplier : scale factor applied to occupancy baseline

    Returns
    -------
    list[ForecastPoint]  : one entry per hour

    # TODO: ML ─────────────────────────────────────────────────────────────
    # 1. Load your trained model: model = joblib.load("app/models/forecast.pkl")
    # 2. Build feature vector from building_id, hour, temperature_offset,
    #    occupancy_multiplier, and any other inputs your model needs.
    # 3. Run inference:  predictions = model.predict(feature_matrix)
    # 4. Build and return a list[ForecastPoint] from predictions.
    # ────────────────────────────────────────────────────────────────────────
    """
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    points: list[ForecastPoint] = []

    occ_factor = occupancy_multiplier
    temp_factor = 1.0 + temperature_offset * 0.015  # 1.5 % per °C (stub rule)

    for h in range(horizon):
        ts = now + timedelta(hours=h)
        base = _DAILY_PATTERN[ts.hour] * occ_factor * temp_factor
        points.append(
            ForecastPoint(
                timestamp=ts.isoformat() + "Z",
                consumption=round(base, 2),
                lower_bound=round(base * 0.92, 2),
                upper_bound=round(base * 1.08, 2),
            )
        )
    return points


def get_explanation(building_id: str) -> tuple[str, list[FeatureContribution]]:
    """
    Return a plain-English explanation and SHAP-style feature contributions
    for the most recent forecast of `building_id`.

    Returns
    -------
    (explanation_text, feature_contributions)

    # TODO: ML ─────────────────────────────────────────────────────────────
    # 1. Load your SHAP explainer or equivalent.
    # 2. Run shap_values = explainer(feature_matrix)
    # 3. Format shap_values into list[FeatureContribution].
    # 4. Generate explanation_text from the top contributors.
    # ────────────────────────────────────────────────────────────────────────
    """
    text = (
        f"The forecast for {building_id} is approximately 15 % above the "
        "7-day average, primarily driven by high outdoor temperature and "
        "above-normal occupancy levels during peak hours (10:00–15:00)."
    )
    return text, _FEATURE_STUBS
