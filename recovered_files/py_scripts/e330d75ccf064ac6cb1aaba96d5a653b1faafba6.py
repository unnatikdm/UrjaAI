from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
import duckdb
import os
from datetime import timedelta
import holidays

app = FastAPI(title="UrjaAI Forecasting API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths to artifacts (relative to the project root)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "time_forecasting")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "urjaai.db")

# Global dict to store loaded models to avoid reloading
models = {}

def get_model_artifacts(sensor_id):
    try:
        model_xgb = joblib.load(os.path.join(MODEL_DIR, "ensemble_xgb.joblib"))
        model_lgb = joblib.load(os.path.join(MODEL_DIR, "ensemble_lgb.joblib"))
        scaler = joblib.load(os.path.join(MODEL_DIR, "ensemble_scaler.joblib"))
        features = joblib.load(os.path.join(MODEL_DIR, "ensemble_features.joblib"))
        return model_xgb, model_lgb, scaler, features
    except Exception as e:
        raise Exception(f"Failed to load ensemble artifacts: {e}")

@app.get("/")
def read_root():
    return {"message": "UrjaAI Forecasting API is running. Go to /dashboard for the UI."}

@app.get("/dashboard")
def get_dashboard():
    # Path to dashboard.html in the parent directory
    dash_path = os.path.join(os.path.dirname(__file__), "..", "dashboard.html")
    return FileResponse(dash_path)

@app.get("/forecast/{sensor_id}")
def get_forecast(sensor_id: str, horizon: int = 24):
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        query = f"""
            SELECT s.time, s.data, m.device, m.dimension_text
            FROM sensors_cleaned s
            JOIN metadata m ON s.source_file LIKE '%' || m.file
            WHERE m.object_id = '{sensor_id}'
            ORDER BY s.time DESC
            LIMIT 500
        """
        df_sensor = con.execute(query).df()
        
        # Load weather for join
        WEATHER_PATH = os.path.join(os.path.dirname(__file__), "..", "mumbai_weather_2025.csv")
        df_weather = pd.read_csv(WEATHER_PATH)
        df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
        
        con.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading error: {e}")

    if df_sensor.empty:
        raise HTTPException(status_code=404, detail="No data found for this sensor.")

    # Preprocessing
    df_sensor['time'] = pd.to_datetime(df_sensor['time'], utc=True)
    df_sensor['time_h'] = df_sensor['time'].dt.floor('h')
    df_merged = pd.merge(df_sensor, df_weather, left_on='time_h', right_on='date', how='left')
    df_merged = df_merged.sort_values('time').set_index('time')
    df_merged = df_merged[['data', 'temperature', 'humidity']].resample('h').mean().interpolate().ffill().bfill()

    # Load Ensemble Models
    try:
        model_xgb, model_lgb, scaler, features = get_model_artifacts(sensor_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Forecast
    last_time = df_merged.index[-1]
    hist_data = df_merged['data'].tolist()
    hist_temp = df_merged['temperature'].tolist()
    
    de_holidays = holidays.Germany()
    predictions = []

    for i in range(1, horizon + 1):
        future_time = last_time + timedelta(hours=i)
        
        # In a real API, you'd fetch real-time future weather forecasts here.
        # For now, we simulate by using the average or sticking to the last known temp.
        future_temp = hist_temp[-1] 
        
        feat_dict = {
            'hour': future_time.hour,
            'day_of_week': future_time.dayofweek,
            'is_weekend': 1 if future_time.dayofweek >= 5 else 0,
            'hour_sin': np.sin(2 * np.pi * future_time.hour / 24.0),
            'hour_cos': np.cos(2 * np.pi * future_time.hour / 24.0),
            'is_holiday': 1 if future_time.date() in de_holidays else 0,
            'temperature': future_temp,
            'humidity': 50.0, 
            'apparent_temp': future_temp,
            'precipitation': 0.0,
            'lag_1': hist_data[-1],
            'lag_2': hist_data[-2],
            'lag_24': hist_data[-24] if len(hist_data) >= 24 else hist_data[-1],
            'lag_168': hist_data[-168] if len(hist_data) >= 168 else hist_data[-1],
            'temp_lag_1': hist_temp[-1],
            'temp_lag_2': hist_temp[-2],
            'temp_lag_24': hist_temp[-24] if len(hist_temp) >= 24 else hist_temp[-1],
            'temp_lag_168': hist_temp[-168] if len(hist_temp) >= 168 else hist_temp[-1],
            'rolling_mean_24h': np.mean(hist_data[-24:])
        }
        
        X = pd.DataFrame([feat_dict])[features]
        X_scaled = scaler.transform(X)
        pred = (model_xgb.predict(X_scaled)[0] + model_lgb.predict(X_scaled)[0]) / 2
        
        predictions.append({"time": future_time.isoformat(), "value": float(pred)})
        hist_data.append(pred)
        hist_temp.append(future_temp)

    return {
        "sensor_id": sensor_id,
        "horizon": horizon,
        "forecast": predictions
    }

@app.post("/simulate-what-if")
async def simulate_what_if(
    sensor_id: str,
    temp_delta: float = 0.0,
    efficiency_factor: float = 1.0,
    horizon: int = 24
):
    """
    Simulation Engine: Predict outcome if temperature changes or building efficiency improves.
    """
    # Reuse logic from get_forecast but apply modifications
    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        query = f"SELECT s.time, s.data FROM sensors_cleaned s JOIN metadata m ON s.source_file LIKE '%' || m.file WHERE m.object_id = '{sensor_id}' ORDER BY s.time DESC LIMIT 200"
        df_sensor = con.execute(query).df()
        
        WEATHER_PATH = os.path.join(os.path.dirname(__file__), "..", "mumbai_weather_2025.csv")
        df_weather = pd.read_csv(WEATHER_PATH)
        df_weather['date'] = pd.to_datetime(df_weather['date'], utc=True)
        con.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df_sensor.empty:
        raise HTTPException(status_code=404, detail="Sensor not found")

    df_sensor['time'] = pd.to_datetime(df_sensor['time'], utc=True)
    df_sensor['time_h'] = df_sensor['time'].dt.floor('h')
    df_merged = pd.merge(df_sensor, df_weather, left_on='time_h', right_on='date', how='left')
    df_merged = df_merged.sort_values('time').set_index('time')
    df_merged = df_merged[['data', 'temperature', 'humidity']].resample('h').mean().interpolate().ffill().bfill()
    
    # Apply Temperature Delta
    df_merged['temperature'] = df_merged['temperature'] + temp_delta

    model_xgb, model_lgb, scaler, features = get_model_artifacts(sensor_id)
    
    last_time = df_merged.index[-1]
    hist_data = df_merged['data'].tolist()
    hist_temp = df_merged['temperature'].tolist()
    de_holidays = holidays.Germany()
    predictions = []

    for i in range(1, horizon + 1):
        future_time = last_time + timedelta(hours=i)
        f_temp = hist_temp[-1] + temp_delta # Simple temp persistence for simulation
        
        feat_dict = {
            'hour': future_time.hour, 'day_of_week': future_time.dayofweek,
            'is_weekend': 1 if future_time.dayofweek >= 5 else 0,
            'hour_sin': np.sin(2 * np.pi * future_time.hour / 24.0),
            'hour_cos': np.cos(2 * np.pi * future_time.hour / 24.0),
            'is_holiday': 1 if future_time.date() in de_holidays else 0,
            'temperature': f_temp, 'humidity': 50.0, 'apparent_temp': f_temp, 'precipitation': 0.0,
            'lag_1': hist_data[-1], 'lag_2': hist_data[-2],
            'lag_24': hist_data[-24] if len(hist_data) >= 24 else hist_data[-1],
            'lag_168': hist_data[-168] if len(hist_data) >= 168 else hist_data[-1],
            'temp_lag_1': hist_temp[-1], 'temp_lag_2': hist_temp[-2],
            'temp_lag_24': hist_temp[-24] if len(hist_temp) >= 24 else hist_temp[-1],
            'temp_lag_168': hist_temp[-168] if len(hist_temp) >= 168 else hist_temp[-1],
            'rolling_mean_24h': np.mean(hist_data[-24:])
        }
        
        X = pd.DataFrame([feat_dict])[features]
        X_scaled = scaler.transform(X)
        pred = (model_xgb.predict(X_scaled)[0] + model_lgb.predict(X_scaled)[0]) / 2
        
        # Apply Efficiency Factor (Building Retrofit Simulation)
        impact = float(pred) * efficiency_factor
        predictions.append({"time": future_time.isoformat(), "original_value": float(pred), "simulated_value": impact})
        hist_data.append(impact)
        hist_temp.append(f_temp)

    return {
        "sensor_id": sensor_id,
        "scenarios": {
            "temperature_adjustment": f"{temp_delta:+}°C",
            "efficiency_improvement": f"{(1-efficiency_factor)*100:.0f}%"
        },
        "forecast": predictions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
