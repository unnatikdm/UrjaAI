from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.services.bosch_transfer import BoschAnomalyTransfer

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])

# Singleton service injection
anomaly_service = None

def get_anomaly_service():
    global anomaly_service
    if anomaly_service is None:
        try:
             anomaly_service = BoschAnomalyTransfer()
        except Exception as e:
             print(f"Failed to load Anomaly Transfer: {e}")
             return None
    return anomaly_service

# Pydantic Schemas
class AnomalyDetectionRequest(BaseModel):
    building_id: str
    building_type: str = Field(..., description="E.g., Lecture Hall, Library, Dormitory")
    timestamp: datetime
    actual_consumption: float = Field(..., description="Actual energy measured in kWh")

class AnomalyDetectionResponse(BaseModel):
    is_anomaly: bool
    anomaly_type: str = Field(..., description="A (High), B (Low/Meter Issue), C (Schedule Mismatch)")
    severity: str = Field(..., description="low, medium, high")
    expected: float
    deviation: float
    deviation_percent: float
    threshold_used: float
    explanation: str
    shap_values: List[str]
    similar_past: Optional[List[dict]] = []

@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    request: AnomalyDetectionRequest,
    service: BoschAnomalyTransfer = Depends(get_anomaly_service)
):
    """
    Analyzes a real-time energy ping for anomalies using the Schedule-Aware transferred I-BLEND intelligent models.
    """
    if service is None:
         raise HTTPException(status_code=503, detail="Anomaly models not initialized. Ensure XGBoost models are present.")
         
    try:
        # Evaluate anomaly
        result = service.detect_anomaly(
             building_id=request.building_id,
             building_type=request.building_type,
             timestamp=request.timestamp.isoformat(),
             actual_consumption=request.actual_consumption
        )
        
        # Integration hook: RAG search for similar anomalies (Phase 4.3)
        # TODO: Add Vector DB hook here when RAG module is ready
        result["similar_past"] = []
        
        return AnomalyDetectionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
