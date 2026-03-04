"""
train_ensemble.py — Train XGBoost + LightGBM ensemble from parquet sensor data.

Run from the backend/ directory:
    python train_ensemble.py

Saves 4 joblib files to backend/app/models/:
    ensemble_xgb.joblib, ensemble_lgb.joblib,
    ensemble_scaler.joblib, ensemble_features.joblib
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib
import holidays

BACKEND_DIR     = Path(__file__).parent
PARQUET_DIR     = BACKEND_DIR.parent / "recovered_files" / "parquet_files"
WEATHER_CSV     = BACKEND_DIR / "mumbai_weather_2025.csv"
MODELS_DIR      = BACKEND_DIR / "app" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# How many parquet files to aggregate (more = better model, slower training)
MAX_FILES = 100


def load_sensor_data() -> pd.DataFrame:
    """Read MAX_FILES parquet files and concat into a single hourly DataFrame."""
    files = sorted(PARQUET_DIR.glob("*.parquet"))
    files = files[:MAX_FILES]
    print(f"Loading {len(files)} parquet sensor files from {PARQUET_DIR}...")

    frames = []
    for f in files:
        df = pd.read_parquet(f)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["time"] = pd.to_datetime(combined["time"], utc=True)
    combined = combined.sort_values("time").reset_index(drop=True)

    # Resample to hourly mean (watts → kWh per hour = watts / 1000)
    combined = combined.set_index("time")
    hourly = combined["data"].resample("h").mean().dropna()
    hourly = hourly / 1000.0  # W → kWh
    hourly = hourly.to_frame(name="data")

    print(f"Hourly rows: {len(hourly)}, range: {hourly.index.min()} to {hourly.index.max()}")
    return hourly


def load_weather(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Load or generate Mumbai weather aligned to the given datetime index."""
    if WEATHER_CSV.exists():
        print("Loading Mumbai weather CSV...")
        df = pd.read_csv(WEATHER_CSV)
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.set_index("date")
    else:
        print("Generating synthetic Mumbai weather...")
        sys.path.insert(0, str(BACKEND_DIR))
        from app.services.data import get_weather_data
        df = get_weather_data()
        df = df.set_index("date")

    # Reindex to match sensor timestamps
    df = df.reindex(index, method="nearest", tolerance=pd.Timedelta("1h"))
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    print("Engineering features...")

    # Time features
    df["hour"]        = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["is_weekend"]  = df["day_of_week"].isin([5, 6]).astype(int)
    df["hour_sin"]    = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"]    = np.cos(2 * np.pi * df["hour"] / 24.0)

    # India - Maharashtra holidays
    in_holidays = holidays.India(state="MH")
    df["is_holiday"] = [1 if d in in_holidays else 0 for d in df.index.date]

    # Lag features
    for lag in [1, 2, 24, 168]:
        df[f"lag_{lag}"] = df["data"].shift(lag)
        if "temperature" in df.columns:
            df[f"temp_lag_{lag}"] = df["temperature"].shift(lag)

    # Rolling mean
    df["rolling_mean_24h"] = df["data"].shift(1).rolling(24).mean()

    return df.dropna()


def train():
    # 1. Load & merge
    hourly    = load_sensor_data()
    weather   = load_weather(hourly.index)
    df        = hourly.join(weather, how="left")

    # Fill any missing weather with column means
    for col in ["temperature", "humidity", "apparent_temp", "precipitation"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mean())
        else:
            df[col] = 28.0 if col in ("temperature", "apparent_temp") else (60.0 if col == "humidity" else 0.0)

    # 2. Feature engineering
    df = engineer_features(df)

    n         = len(df)
    print(f"Dataset after feature engineering: {n} rows")
    if n < 200:
        print("⚠  Not enough data to train (need > 200 hourly rows). Exiting.")
        sys.exit(1)

    train_end = int(n * 0.8)
    val_end   = int(n * 0.9)

    target    = "data"
    feat_cols = [c for c in df.columns if c != target]

    X_tr, y_tr = df.iloc[:train_end][feat_cols],  df.iloc[:train_end][target]
    X_va, y_va = df.iloc[train_end:val_end][feat_cols], df.iloc[train_end:val_end][target]
    X_te, y_te = df.iloc[val_end:][feat_cols],    df.iloc[val_end:][target]

    scaler   = StandardScaler()
    X_tr_s   = scaler.fit_transform(X_tr)
    X_va_s   = scaler.transform(X_va)
    X_te_s   = scaler.transform(X_te)

    # 3. Train XGBoost
    print("Training XGBoost...")
    model_xgb = xgb.XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8,
        early_stopping_rounds=30, n_jobs=-1, verbosity=0,
    )
    model_xgb.fit(X_tr_s, y_tr, eval_set=[(X_va_s, y_va)], verbose=False)

    # 4. Train LightGBM
    print("Training LightGBM...")
    model_lgb = lgb.LGBMRegressor(
        n_estimators=500, learning_rate=0.05, num_leaves=63,
        subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
    )
    model_lgb.fit(
        X_tr_s, y_tr,
        eval_set=[(X_va_s, y_va)],
        callbacks=[lgb.early_stopping(30), lgb.log_evaluation(period=0)],
    )

    # 5. Evaluate ensemble
    ensemble = (model_xgb.predict(X_te_s) + model_lgb.predict(X_te_s)) / 2
    rmse = np.sqrt(mean_squared_error(y_te, ensemble))
    mae  = mean_absolute_error(y_te, ensemble)
    print(f"\nEnsemble Test  RMSE: {rmse:.4f} kWh   MAE: {mae:.4f} kWh")

    # 6. Save artifacts
    print(f"\nSaving models to {MODELS_DIR}/...")
    joblib.dump(model_xgb, MODELS_DIR / "ensemble_xgb.joblib")
    joblib.dump(model_lgb,  MODELS_DIR / "ensemble_lgb.joblib")
    joblib.dump(scaler,     MODELS_DIR / "ensemble_scaler.joblib")
    joblib.dump(feat_cols,  MODELS_DIR / "ensemble_features.joblib")
    print("✅ Training complete! Models saved.")
    print("   The API will now use real ML predictions on next request.")


if __name__ == "__main__":
    train()
