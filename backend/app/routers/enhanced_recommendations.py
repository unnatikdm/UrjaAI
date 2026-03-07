"""
Enhanced Recommendations Router
Exposes enriched recommendations with real-time context
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.enhanced_recommendations import enhanced_recommendation_engine

router = APIRouter(prefix="/enhanced", tags=["enhanced-recommendations"])


class EnhancedRecommendationResponse(BaseModel):
    id: str
    type: str
    action: str
    priority: str
    priority_score: int
    savings: Dict[str, Any]
    benchmarks: Optional[Dict[str, Any]] = None
    action_levels: Optional[List[Dict]] = None
    implementation: Optional[Dict] = None
    enhanced_text: str
    historical_validation: Optional[Dict] = None


@router.get("/recommendations/{building_id}")
async def get_enhanced_recommendations(
    building_id: str,
    include_benchmarks: bool = True,
    include_multiple_levels: bool = True
):
    """
    Get enriched recommendations with real-time context:
    - Live weather from Open-Meteo
    - Occupancy predictions
    - Dynamic energy pricing
    - Physical model savings calculations
    - Comparative benchmarks
    - Multiple action levels
    - Implementation guidance
    """
    try:
        recommendations = enhanced_recommendation_engine.generate_enhanced_recommendations(
            building_id=building_id,
            include_benchmarks=include_benchmarks,
            include_multiple_levels=include_multiple_levels
        )
        return {
            "building_id": building_id,
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing/context")
async def get_pricing_context():
    """Get current energy pricing context"""
    return enhanced_recommendation_engine.pricing_service.get_pricing_context()


@router.get("/weather/alerts")
async def get_weather_alerts():
    """Get current weather alerts"""
    try:
        weather_data = enhanced_recommendation_engine.weather_api.fetch_weather_forecast(2)
        alerts = enhanced_recommendation_engine.weather_api.get_weather_alerts(weather_data)
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "forecast_days": 2
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Weather service unavailable: {str(e)}")


@router.get("/occupancy/{building_id}")
async def get_occupancy(building_id: str):
    """Get real-time occupancy for a building"""
    return enhanced_recommendation_engine.occupancy_service.get_occupancy(building_id)


@router.post("/calculate/what-if")
async def calculate_what_if_scenario(
    building_id: str,
    current_setpoint: float,
    new_setpoint: float,
    outdoor_temp: float,
    occupancy_count: int,
    duration_hours: float = 3.0
):
    """
    Calculate impact of a hypothetical scenario
    """
    impact = enhanced_recommendation_engine.physical_model.calculate_setpoint_impact(
        current_setpoint,
        new_setpoint,
        outdoor_temp,
        occupancy_count,
        duration_hours
    )
    
    # Add pricing context
    pricing = enhanced_recommendation_engine.pricing_service.get_pricing_context()
    cost_saved = impact['energy_saved_kwh'] * pricing['peak_rate']
    
    return {
        "scenario": {
            "building_id": building_id,
            "current_setpoint": current_setpoint,
            "new_setpoint": new_setpoint,
            "outdoor_temp": outdoor_temp,
            "occupancy_count": occupancy_count,
            "duration_hours": duration_hours
        },
        "impact": impact,
        "cost_saved_inr": round(cost_saved, 2),
        "pricing_used": pricing['peak_rate']
    }


from datetime import datetime
