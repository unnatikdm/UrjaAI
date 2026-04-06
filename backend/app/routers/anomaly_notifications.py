"""
Actionable Anomaly Notifications API
Provides real-time anomaly alerts with resolution actions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


class AnomalyNotification(BaseModel):
    id: str
    type: str = "anomaly"
    severity: str  # 'high', 'medium', 'low'
    building: str
    room: Optional[str] = None
    message: str
    detected_at: str
    suggestion: str
    estimated_savings: Dict[str, float]
    resolved: bool = False


class AnomalyResolutionRequest(BaseModel):
    anomaly_id: str
    resolution: Dict[str, Any]


class AnomalyResolutionResponse(BaseModel):
    success: bool
    anomaly_id: str
    savings_kwh: float
    savings_inr: float
    resolution_message: str
    applied_at: str


# Simulated anomaly store (replace with DB in production)
_active_anomalies: List[Dict[str, Any]] = []
_resolved_anomalies: List[Dict[str, Any]] = []


def generate_demo_anomalies() -> List[Dict[str, Any]]:
    """Generate realistic demo anomalies for UX testing"""
    buildings = ['Hall A', 'Library', 'Admin Block', 'Engineering Block']
    rooms = ['Lecture Hall A', 'Reading Room', 'Conference Room', 'Lab 101']
    
    anomalies = [
        {
            "id": f"anomaly-{datetime.utcnow().timestamp()}-1",
            "type": "anomaly",
            "severity": "high",
            "building": random.choice(buildings),
            "room": random.choice(rooms),
            "message": "Energy consumption 45% above baseline for 2+ hours",
            "detected_at": (datetime.utcnow() - timedelta(minutes=random.randint(5, 30))).isoformat(),
            "suggestion": "Smart-dim lights to 60% and adjust HVAC setpoint by 1°C",
            "estimated_savings": {"kwh": round(random.uniform(3, 6), 1), "inr": random.randint(200, 400)},
            "resolved": False
        },
        {
            "id": f"anomaly-{datetime.utcnow().timestamp()}-2",
            "type": "anomaly",
            "severity": "medium",
            "building": random.choice(buildings),
            "room": None,
            "message": "HVAC cycling too frequently (inefficient operation)",
            "detected_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 3))).isoformat(),
            "suggestion": "Extend HVAC cycle time by 5 minutes",
            "estimated_savings": {"kwh": round(random.uniform(2, 4), 1), "inr": random.randint(100, 250)},
            "resolved": False
        }
    ]
    return anomalies


@router.get("/notifications")
async def get_anomaly_notifications():
    """
    Get current active anomaly notifications.
    
    Returns real-time alerts with:
    - Severity levels
    - Location details
    - Suggested resolution actions
    - Estimated savings for each fix
    """
    # In production, fetch from anomaly detection service
    # For demo, generate realistic anomalies
    global _active_anomalies
    
    if not _active_anomalies or random.random() > 0.7:
        _active_anomalies = generate_demo_anomalies()
    
    return {"notifications": _active_anomalies}


@router.post("/resolve", response_model=AnomalyResolutionResponse)
async def resolve_anomaly(request: AnomalyResolutionRequest):
    """
    Apply a resolution action to an anomaly.
    
    Simulates the action (e.g., smart-dimming lights, adjusting HVAC)
    and returns the immediate savings achieved.
    """
    global _active_anomalies, _resolved_anomalies
    
    # Find the anomaly
    anomaly = None
    for a in _active_anomalies:
        if a["id"] == request.anomaly_id:
            anomaly = a
            break
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found or already resolved")
    
    # Calculate actual savings (with some variance from estimate)
    estimated = anomaly["estimated_savings"]
    actual_savings_kwh = round(estimated["kwh"] * random.uniform(0.8, 1.2), 2)
    actual_savings_inr = int(estimated["inr"] * random.uniform(0.9, 1.1))
    
    # Move to resolved
    anomaly["resolved"] = True
    anomaly["resolved_at"] = datetime.utcnow().isoformat()
    anomaly["resolution"] = request.resolution
    anomaly["actual_savings"] = {"kwh": actual_savings_kwh, "inr": actual_savings_inr}
    
    _resolved_anomalies.append(anomaly)
    _active_anomalies = [a for a in _active_anomalies if a["id"] != request.anomaly_id]
    
    return AnomalyResolutionResponse(
        success=True,
        anomaly_id=request.anomaly_id,
        savings_kwh=actual_savings_kwh,
        savings_inr=actual_savings_inr,
        resolution_message=f"Applied: {request.resolution.get('action', 'Resolution action')}",
        applied_at=datetime.utcnow().isoformat()
    )


@router.get("/stats")
async def get_anomaly_stats():
    """Get statistics on anomalies detected and resolved"""
    return {
        "active_count": len(_active_anomalies),
        "resolved_count": len(_resolved_anomalies),
        "total_savings_kwh": sum(a.get("actual_savings", {}).get("kwh", 0) for a in _resolved_anomalies),
        "total_savings_inr": sum(a.get("actual_savings", {}).get("inr", 0) for a in _resolved_anomalies)
    }
