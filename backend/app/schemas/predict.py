from datetime import datetime
from typing import Optional, List # Re-added List
from pydantic import BaseModel


# ──────────────────────────────────────────────
# /predict  request & response
# ──────────────────────────────────────────────

class WhatIfModifiers(BaseModel):
    temperature: Optional[float] = None   # °C absolute value
    occupancy: Optional[float] = None     # 0.0 – 1.0 fraction


class PredictRequest(BaseModel):
    building_id: str
    horizon: int = 24                     # hours ahead
    what_if_modifiers: Optional[WhatIfModifiers] = None


class ForecastPoint(BaseModel):
    timestamp: str
    consumption: float                    # kWh
    lower_bound: float
    upper_bound: float


class PredictResponse(BaseModel):
    building_id: str
    generated_at: str
    forecast: list[ForecastPoint]


# ──────────────────────────────────────────────
# /recommendations  request & response
# ──────────────────────────────────────────────

class RecommendationsRequest(BaseModel):
    building_id: str


class Recommendation(BaseModel):
    action: str
    savings_kwh: float
    savings_cost_inr: float
    priority: str                         # "high" | "medium" | "low"
    reason: str


class RecommendationsResponse(BaseModel):
    building_id: str
    recommendations: list[Recommendation]


# ──────────────────────────────────────────────
# /explain  request & response
# ──────────────────────────────────────────────

class ExplainRequest(BaseModel):
    building_id: str


class FeatureContribution(BaseModel):
    feature: str
    contribution: float                   # positive = increases consumption


class ExplainResponse(BaseModel):
    building_id: str
    explanation_text: str
    feature_contributions: list[FeatureContribution]


# ──────────────────────────────────────────────
# /whatif  request & response
# ──────────────────────────────────────────────

class WhatIfChanges(BaseModel):
    temperature_offset: float = 0.0      # °C delta from current
    occupancy_multiplier: float = 1.0    # 1.0 = no change


class WhatIfRequest(BaseModel):
    building_id: str
    changes: WhatIfChanges


class WhatIfResponse(BaseModel):
    building_id: str
    baseline_forecast: list[ForecastPoint]
    modified_forecast: list[ForecastPoint]
    delta_summary: str


# ──────────────────────────────────────────────
# /predict/batch  request & response
# ──────────────────────────────────────────────

class BatchPredictRequest(BaseModel):
    building_ids: List[str]
    horizon: int = 24
    what_if_modifiers: Optional[WhatIfModifiers] = None


class BatchPredictResponse(BaseModel):
    results: List[PredictResponse]
