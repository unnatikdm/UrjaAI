import duckdb
import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib
import holidays
import os

# Configuration
SENSOR_ID = 'B201AH115.AM63_1'
DB_PATH = '..\\urjaai.db'
WEATHER_PATH = '..\\mumbai_weather_2025.csv'

def load_and_merge():
    print(f"Loading sensor data for {SENSOR_ID}...")
    con = duckdb.connect(DB_PATH, read_only=True)
    query = f"""
        SELECT s.time, s.data
        FROM sensors_cleaned s
        JOIN metadata m ON s.source_file LIKE '%' || m.file
        WHERE m.object_id = '{SENSOR_ID}'
        ORDER BY s.time
    """
    df_sensor = con.execute(query).df()
    con.close()
    
    # Ensure sensor time is datetime and UTC for joining
    df_sensor['time'] = pd.to_datetime(df_sensor['time'], utc=True)
    
    print("Loading Mumbai weather data...")
    df_weather = pd.read_csv(WEATHER_PATH)
    df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
    
    # Merge on time (using floor to hour for weather join if needed)
    df_sensor['time_h'] = df_sensor['time'].dt.floor('h')
    df_merged = pd.merge(df_sensor, df_weather, left_on='time_h', right_on='date', how='left')
    
    # Cleanup
    df_merged = df_merged.drop(columns=['time_h', 'date'])
    return df_merged

def engineer_features(df):
    print("Engineering features...")
    df = df.set_index('time')
    
    # Resample to hourly and fill gaps
    df = df.resample('h').mean()
    df = df.interpolate(method='time').ffill().bfill()
    
    # Time Features
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Cyclical Encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24.0)
    
    # Holidays
    de_holidays = holidays.Germany()
    df['is_holiday'] = [1 if d in de_holidays else 0 for d in df.index.date]
    
    # Lags (Lags of energy and weather)
    for lag in [1, 2, 24, 168]:
        df[f'lag_{lag}'] = df['data'].shift(lag)
        df[f'temp_lag_{lag}'] = df['temperature'].shift(lag)
    
    # Rolling Stats
    df['rolling_mean_24h'] = df['data'].shift(1).rolling(window=24).mean()
    
    return df.dropna()

def train_ensemble():
    df = load_and_merge()
    df = engineer_features(df)
    
    # Split
    n = len(df)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]
    
    target = 'data'
    features = [c for c in df.columns if c != target]
    
    X_train, y_train = train_df[features], train_df[target]
    X_val, y_val = val_df[features], val_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # 1. XGBoost
    print("Training XGBoost...")
    model_xgb = xgb.XGBRegressor(n_estimators=1000, learning_rate=0.05, early_stopping_rounds=50, n_jobs=-1)
    model_xgb.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
    
    # 2. LightGBM
    print("Training LightGBM...")
    model_lgb = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, n_jobs=-1)
    model_lgb.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], 
                  eval_metric='l2', callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)])
    
    # Ensemble Predictions (Simple Weighted Average for now)
    pred_xgb = model_xgb.predict(X_test_scaled)
    pred_lgb = model_lgb.predict(X_test_scaled)
    
    # Dynamic weighting based on Validation error could be better, but let's start with 50/50
    ensemble_preds = (pred_xgb + pred_lgb) / 2
    
    rmse = np.sqrt(mean_squared_error(y_test, ensemble_preds))
    print(f"\nEnsemble Test RMSE: {rmse:.4f}")
    
    # Save artifacts
    joblib.dump(model_xgb, 'ensemble_xgb.joblib')
    joblib.dump(model_lgb, 'ensemble_lgb.joblib')
    joblib.dump(scaler, 'ensemble_scaler.joblib')
    joblib.dump(features, 'ensemble_features.joblib')
    print("Ensemble models saved.")

if __name__ == "__main__":
    train_ensemble()
