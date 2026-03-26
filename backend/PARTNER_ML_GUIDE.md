# Partner ML Integration Guide

Everything in the backend is built and wired up. You only need to fill in **one file**:

```
backend/app/services/ml.py
```

---

## Your Two Functions

### 1. `run_forecast()`

Returns an hourly energy consumption forecast for a building.

**Signature:**
```python
def run_forecast(
    building_id: str,
    horizon: int = 24,
    modifiers = None,            # optional WhatIfModifiers object
    temperature_offset: float = 0.0,   # °C delta from current
    occupancy_multiplier: float = 1.0, # 1.0 = no change
) -> list[ForecastPoint]:
```

**You must return** a list of `ForecastPoint` objects (one per hour):
```python
ForecastPoint(
    timestamp="2026-03-03T08:00:00Z",  # ISO 8601 UTC
    consumption=105.2,   # predicted kWh
    lower_bound=96.8,    # confidence interval lower
    upper_bound=113.6,   # confidence interval upper
)
```

**Example implementation:**
```python
import joblib
from pathlib import Path

MODEL = joblib.load(Path(__file__).parent.parent / "models" / "forecast.pkl")

def run_forecast(building_id, horizon=24, modifiers=None,
                 temperature_offset=0.0, occupancy_multiplier=1.0):
    # 1. Build your feature matrix (hour, temperature, occupancy, etc.)
    # 2. Run inference: predictions = MODEL.predict(feature_matrix)
    # 3. Return list of ForecastPoint(...)
```

---

### 2. `get_explanation()`

Returns SHAP-style feature attributions explaining why the forecast is high/low.

**Signature:**
```python
def get_explanation(building_id: str) -> tuple[str, list[FeatureContribution]]:
```

**You must return** a tuple of:
1. A plain-English string explaining the forecast
2. A list of `FeatureContribution` objects

```python
FeatureContribution(
    feature="Temperature",    # feature name
    contribution=0.31,        # positive = increases consumption, negative = decreases
)
```

**Example implementation:**
```python
import shap

def get_explanation(building_id):
    shap_values = explainer(feature_matrix)
    contributions = [
        FeatureContribution(feature=name, contribution=float(val))
        for name, val in zip(feature_names, shap_values.values[0])
    ]
    text = "The forecast is X% above average due to..."
    return text, contributions
```

---

## Available Data

Use the existing data service to get historical sensor readings:

```python
from app.services.data import get_building_history, get_current_conditions

# pandas DataFrame: timestamp, building_id, consumption_kwh,
#                   temperature_c, occupancy, humidity_pct
df = get_building_history("main_library", days=7)

# Most recent reading as a dict
current = get_current_conditions("main_library")
```

---

## Where to Put Model Files

Drop trained model artifacts (`.pkl`, `.onnx`, `.h5`, etc.) into:

```
backend/app/models/
```

---

## Where to Put Real Sensor Data

If you have real CSV data, place files named `{building_id}.csv` in:

```
backend/data/
```

See `backend/data/README.md` for the required column format.
If no CSV is found, the system auto-generates synthetic data as a fallback.

---

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI (to test your endpoints): **http://localhost:8000/docs**
