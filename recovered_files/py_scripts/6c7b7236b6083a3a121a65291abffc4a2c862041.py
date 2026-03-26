import pandas as pd
import numpy as np
import joblib
import duckdb
from datetime import timedelta
import holidays
import os

# Configuration
SENSOR_ID = 'B201AH115.AM63_1'
DB_PATH = 'urjaai.db'
WEATHER_PATH = 'mumbai_weather_2025.csv'
MODEL_DIR = 'time_forecasting'

def run_final_ensemble_forecast():
    print(f"--- UrjaAI Final Ensemble Run ---")
    print(f"Target Sensor: {SENSOR_ID}")
    
    # 1. Load data from Cleaned DB
    con = duckdb.connect(DB_PATH, read_only=True)
    query = f"""
        SELECT s.time, s.data
        FROM sensors_cleaned s
        JOIN metadata m ON s.source_file LIKE '%' || m.file
        WHERE m.object_id = '{SENSOR_ID}'
        ORDER BY s.time DESC
        LIMIT 500
    """
    df_sensor = con.execute(query).df()
    con.close()
    
    # 2. Preprocess
    df_sensor['time'] = pd.to_datetime(df_sensor['time'], utc=True)
    df_sensor['time_h'] = df_sensor['time'].dt.floor('h')
    
    df_weather = pd.read_csv(WEATHER_PATH)
    df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
    
    df_merged = pd.merge(df_sensor, df_weather, left_on='time_h', right_on='date', how='left')
    df_merged = df_merged.sort_values('time').set_index('time')
    df_merged = df_merged[['data', 'temperature', 'humidity', 'apparent_temp', 'precipitation']].resample('h').mean().interpolate().ffill().bfill()
    
    # 3. Load Ensemble Models
    model_xgb = joblib.load(os.path.join(MODEL_DIR, "ensemble_xgb.joblib"))
    model_lgb = joblib.load(os.path.join(MODEL_DIR, "ensemble_lgb.joblib"))
    scaler = joblib.load(os.path.join(MODEL_DIR, "ensemble_scaler.joblib"))
    features = joblib.load(os.path.join(MODEL_DIR, "ensemble_features.joblib"))
    
    # 4. Generate 24h Recursive Forecast
    last_time = df_merged.index[-1]
    hist_data = df_merged['data'].tolist()
    hist_temp = df_merged['temperature'].tolist()
    hist_hum = df_merged['humidity'].tolist()
    hist_app = df_merged['apparent_temp'].tolist()
    hist_precip = df_merged['precipitation'].tolist()
    
    de_holidays = holidays.Germany() # Sensors are from RBHU (German context)
    forecast_results = []
    
    for i in range(1, 25):
        future_time = last_time + timedelta(hours=i)
        
        # Using persistency for future weather simulation
        f_temp = hist_temp[-1]
        f_hum = hist_hum[-1]
        f_app = hist_app[-1]
        f_precip = hist_precip[-1]
        
        feat_dict = {
            'hour': future_time.hour,
            'day_of_week': future_time.dayofweek,
            'is_weekend': 1 if future_time.dayofweek >= 5 else 0,
            'hour_sin': np.sin(2 * np.pi * future_time.hour / 24.0),
            'hour_cos': np.cos(2 * np.pi * future_time.hour / 24.0),
            'is_holiday': 1 if future_time.date() in de_holidays else 0,
            'temperature': f_temp,
            'humidity': f_hum,
            'apparent_temp': f_app,
            'precipitation': f_precip,
            'lag_1': hist_data[-1],
            'lag_2': hist_data[-2],
            'lag_24': hist_data[-24],
            'lag_168': hist_data[-168] if len(hist_data) >= 168 else hist_data[-1],
            'temp_lag_1': hist_temp[-1],
            'temp_lag_2': hist_temp[-2],
            'temp_lag_24': hist_temp[-24],
            'temp_lag_168': hist_temp[-168] if len(hist_temp) >= 168 else hist_temp[-1],
            'rolling_mean_24h': np.mean(hist_data[-24:])
        }
        
        X = pd.DataFrame([feat_dict])[features]
        X_scaled = scaler.transform(X)
        pred = (model_xgb.predict(X_scaled)[0] + model_lgb.predict(X_scaled)[0]) / 2
        
        forecast_results.append({
            "forecast_time": future_time,
            "predicted_kw": round(float(pred), 4),
            "temperature": f_temp
        })
        
        # Update history for next iteration
        hist_data.append(pred)
        hist_temp.append(f_temp)
        
    df_res = pd.DataFrame(forecast_results)
    print("\n--- Next 24 Hours Forecast ---")
    print(df_res.head(10))
    df_res.to_csv("FINAL_ENSEMBLE_FORECAST.csv", index=False)
    print(f"\nSuccess! Results saved to FINAL_ENSEMBLE_FORECAST.csv")

if __name__ == "__main__":
    run_final_ensemble_forecast()
