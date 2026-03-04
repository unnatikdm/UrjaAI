from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from .services import ml

app = FastAPI(title="UrjaAI Partner Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class PredictRequest(BaseModel):
    building_id: str
    horizon: Optional[int] = 24
    include_confidence: Optional[bool] = True

class WhatIfRequest(BaseModel):
    building_id: str
    temperature_offset: Optional[float] = 0.0
    occupancy_multiplier: Optional[float] = 1.0
    horizon: Optional[int] = 24

class ExplainRequest(BaseModel):
    building_id: str
    target_timestamp: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "online", "message": "UrjaAI Partner Integration API is live."}

@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        points = ml.run_forecast(req.building_id, horizon=req.horizon)
        return {
            "building_id": req.building_id,
            "forecast": [p.to_dict() for p in points]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain")
async def explain(req: ExplainRequest):
    try:
        text, contributions = ml.get_explanation(req.building_id)
        return {
            "building_id": req.building_id,
            "explanation_text": text,
            "feature_contributions": [c.to_dict() for c in contributions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatif")
async def whatif(req: WhatIfRequest):
    try:
        points = ml.run_forecast(
            req.building_id, 
            horizon=req.horizon,
            temperature_offset=req.temperature_offset,
            occupancy_multiplier=req.occupancy_multiplier
        )
        return {
            "building_id": req.building_id,
            "scenario": {
                "temp_delta": req.temperature_offset,
                "occ_mult": req.occupancy_multiplier
            },
            "forecast": [p.to_dict() for p in points]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations")
async def recommendations(building_id: str, horizon: int = 24):
    # For now, return a placeholder based on our rule-based logic
    return {
        "building_id": building_id,
        "recommendations": [
            {
                "action": "Pre-cool building HVAC at 03:00 AM",
                "savings_kwh": 15.4,
                "savings_cost": 3.08,
                "reason": "Anticipated afternoon heatwave which increases peak cooling cost."
            }
        ]
    }
