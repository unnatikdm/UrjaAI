"""
ml.py — Real ML integration using XGBoost + LightGBM ensemble.

Implements run_forecast() and get_explanation() using trained models
saved to backend/app/models/ by train_ensemble.py.

If model files are not found, both functions fall back gracefully to
the synthetic stub so the API stays usable during development.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.schemas.predict import ForecastPoint, FeatureContribution, WhatIfModifiers

MODELS_PATH = Path(__file__).resolve().parents[2] / "app" / "models"

# ─────────────────────────────────────────────────────────────────────────────
# Stub fallback (used when .joblib files are not present yet)
# ─────────────────────────────────────────────────────────────────────────────
_DAILY_PATTERN = [
    42, 39, 37, 36, 36, 38,
    45, 58, 75, 92, 105, 112,
    108, 115, 118, 114, 108, 102,
    95, 85, 75, 65, 55, 48,
]
_FEATURE_STUBS: list[FeatureContribution] = [
    FeatureContribution(feature="temperature",    contribution=0.31),
    FeatureContribution(feature="hour_of_day",   contribution=0.24),
    FeatureContribution(feature="occupancy",      contribution=0.20),
    FeatureContribution(feature="day_of_week",   contribution=0.12),
    FeatureContribution(feature="humidity",       contribution=0.08),
    FeatureContribution(feature="solar_irradiance", contribution=-0.05),
]


def _models_available() -> bool:
    required = ["ensemble_xgb.joblib", "ensemble_lgb.joblib",
                "ensemble_scaler.joblib", "ensemble_features.joblib"]
    return all((MODELS_PATH / f).exists() for f in required)


def _load_models():
    import joblib
    model_xgb = joblib.load(MODELS_PATH / "ensemble_xgb.joblib")
    model_lgb  = joblib.load(MODELS_PATH / "ensemble_lgb.joblib")
    scaler     = joblib.load(MODELS_PATH / "ensemble_scaler.joblib")
    features   = joblib.load(MODELS_PATH / "ensemble_features.joblib")
    return model_xgb, model_lgb, scaler, features


def _stub_forecast(
    horizon: int,
    temperature_offset: float,
    occupancy_multiplier: float,
) -> list[ForecastPoint]:
    """Synthetic fallback when trained models are not present."""
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    temp_factor = 1.0 + temperature_offset * 0.015
    points: list[ForecastPoint] = []
    for h in range(horizon):
        ts   = now + timedelta(hours=h)
        base = _DAILY_PATTERN[ts.hour] * occupancy_multiplier * temp_factor
        points.append(ForecastPoint(
            timestamp=ts.isoformat() + "Z",
            consumption=round(base, 2),
            lower_bound=round(base * 0.92, 2),
            upper_bound=round(base * 1.08, 2),
        ))
    return points


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
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
    Uses XGBoost + LightGBM ensemble when models are available,
    otherwise falls back to the synthetic stub.
    """
    if not _models_available():
        return _stub_forecast(horizon, temperature_offset, occupancy_multiplier)

    import numpy as np
    import pandas as pd
    import holidays

    from app.services.data import get_building_history, get_weather_data

    model_xgb, model_lgb, scaler, features = _load_models()

    # 1. Load history (our data.py returns consumption_kwh column)
    df_history = get_building_history(building_id, days=7)
    df_history = df_history.rename(columns={"consumption_kwh": "data"})

    # 2. Load weather
    df_weather = get_weather_data()

    # 3. Merge & resample to hourly
    df_history["timestamp"] = pd.to_datetime(df_history["timestamp"], utc=True)
    df_history["time_h"]    = df_history["timestamp"].dt.floor("h")
    df_merged = pd.merge(df_history, df_weather, left_on="time_h", right_on="date", how="left")
    df_merged = df_merged.sort_values("timestamp").set_index("timestamp")

    needed = [c for c in ["data", "temperature", "humidity", "apparent_temp", "precipitation"] if c in df_merged.columns]
    df_merged = df_merged[needed].resample("h").mean().interpolate().ffill().bfill()

    # Fill missing weather columns with defaults if not in weather file
    for col, default in [("humidity", 60.0), ("apparent_temp", df_merged.get("temperature", pd.Series([25])).mean()), ("precipitation", 0.0)]:
        if col not in df_merged.columns:
            df_merged[col] = default

    # 4. Recursive forecast
    last_time  = df_merged.index[-1]
    hist_data  = df_merged["data"].tolist()
    hist_temp  = df_merged["temperature"].tolist() if "temperature" in df_merged.columns else [25.0] * len(hist_data)

    # Fix: use India/Maharashtra holidays (not Germany)
    in_holidays = holidays.India(state="MH")
    forecast_points: list[ForecastPoint] = []

    for i in range(1, horizon + 1):
        future_time = last_time + timedelta(hours=i)
        f_temp      = hist_temp[-1] + temperature_offset

        feat_dict = {
            "hour":             future_time.hour,
            "day_of_week":      future_time.dayofweek,
            "is_weekend":       1 if future_time.dayofweek >= 5 else 0,
            "hour_sin":         math.sin(2 * math.pi * future_time.hour / 24.0),
            "hour_cos":         math.cos(2 * math.pi * future_time.hour / 24.0),
            "is_holiday":       1 if future_time.date() in in_holidays else 0,
            "temperature":      f_temp,
            "humidity":         60.0,
            "apparent_temp":    f_temp,
            "precipitation":    0.0,
            "lag_1":            hist_data[-1],
            "lag_2":            hist_data[-2] if len(hist_data) >= 2 else hist_data[-1],
            "lag_24":           hist_data[-24] if len(hist_data) >= 24 else hist_data[-1],
            "lag_168":          hist_data[-168] if len(hist_data) >= 168 else hist_data[-1],
            "temp_lag_1":       hist_temp[-1],
            "temp_lag_2":       hist_temp[-2] if len(hist_temp) >= 2 else hist_temp[-1],
            "temp_lag_24":      hist_temp[-24] if len(hist_temp) >= 24 else hist_temp[-1],
            "temp_lag_168":     hist_temp[-168] if len(hist_temp) >= 168 else hist_temp[-1],
            "rolling_mean_24h": float(np.mean(hist_data[-24:])),
        }

        # Only keep features the scaler was trained on
        X        = pd.DataFrame([feat_dict])[[f for f in features if f in feat_dict]]
        X_scaled = scaler.transform(X)
        pred     = (model_xgb.predict(X_scaled)[0] + model_lgb.predict(X_scaled)[0]) / 2
        impact   = float(pred) * occupancy_multiplier

        forecast_points.append(ForecastPoint(
            timestamp=future_time.isoformat() + "Z",
            consumption=round(impact, 2),
            lower_bound=round(impact * 0.95, 2),
            upper_bound=round(impact * 1.05, 2),
        ))
        hist_data.append(impact)
        hist_temp.append(f_temp)

    return forecast_points


def get_explanation(building_id: str) -> tuple[str, list[FeatureContribution]]:
    """
    Return a plain-English explanation and SHAP-style feature contributions.
    Uses real SHAP values when models are available, stub otherwise.
    """
    if not _models_available():
        text = (
            f"The forecast for {building_id} is approximately 15% above the "
            "7-day average, primarily driven by high outdoor temperature and "
            "above-normal occupancy levels during peak hours (10:00–15:00). "
            "[Note: ML models not yet loaded — showing illustrative values.]"
        )
        return text, _FEATURE_STUBS

    import numpy as np
    import pandas as pd
    import shap
    from app.services.data import get_building_history, get_weather_data

    model_xgb, model_lgb, scaler, features = _load_models()

    try:
        df_history = get_building_history(building_id, days=1)
        df_history = df_history.rename(columns={"consumption_kwh": "data"})
        df_weather = get_weather_data()

        df_history["timestamp"] = pd.to_datetime(df_history["timestamp"], utc=True)
        df_history["time_h"]    = df_history["timestamp"].dt.floor("h")
        df_merged = pd.merge(df_history, df_weather, left_on="time_h", right_on="date", how="left")
        df_merged = df_merged.sort_values("timestamp").set_index("timestamp")

        # Build one representative feature row for the most recent hour
        hist_data = df_merged.get("data", pd.Series([75.0])).tolist()
        hist_temp = df_merged.get("temperature", pd.Series([28.0])).tolist()
        latest_ts = df_merged.index[-1]

        feat_dict = {
            "hour":             latest_ts.hour,
            "day_of_week":      latest_ts.dayofweek,
            "is_weekend":       1 if latest_ts.dayofweek >= 5 else 0,
            "hour_sin":         math.sin(2 * math.pi * latest_ts.hour / 24.0),
            "hour_cos":         math.cos(2 * math.pi * latest_ts.hour / 24.0),
            "is_holiday":       0,
            "temperature":      hist_temp[-1],
            "humidity":         60.0,
            "apparent_temp":    hist_temp[-1],
            "precipitation":    0.0,
            "lag_1":            hist_data[-1],
            "lag_2":            hist_data[-2] if len(hist_data) >= 2 else hist_data[-1],
            "lag_24":           hist_data[-24] if len(hist_data) >= 24 else hist_data[-1],
            "lag_168":          hist_data[-168] if len(hist_data) >= 168 else hist_data[-1],
            "temp_lag_1":       hist_temp[-1],
            "temp_lag_2":       hist_temp[-2] if len(hist_temp) >= 2 else hist_temp[-1],
            "temp_lag_24":      hist_temp[-24] if len(hist_temp) >= 24 else hist_temp[-1],
            "temp_lag_168":     hist_temp[-168] if len(hist_temp) >= 168 else hist_temp[-1],
            "rolling_mean_24h": float(np.mean(hist_data[-24:])),
        }

        X        = pd.DataFrame([feat_dict])[[f for f in features if f in feat_dict]]
        X_scaled = scaler.transform(X)

        explainer   = shap.TreeExplainer(model_xgb)
        shap_values = explainer.shap_values(X_scaled)
        shap_row    = shap_values[0]

        contributions = [
            FeatureContribution(feature=feat, contribution=round(float(val), 4))
            for feat, val in sorted(zip(features, shap_row), key=lambda x: abs(x[1]), reverse=True)
        ][:6]  # top-6 contributors

        text = (
            f"The forecast for {building_id} is primarily driven by "
            f"{contributions[0].feature} ({contributions[0].contribution:+.2f}) and "
            f"{contributions[1].feature} ({contributions[1].contribution:+.2f})."
        )
        return text, contributions

    except Exception as e:
        # Graceful degradation if SHAP fails
        return (
            f"The forecast for {building_id} is driven by historical patterns "
            f"and local weather conditions. (Explanation detail unavailable: {e})",
            _FEATURE_STUBS,
        )
