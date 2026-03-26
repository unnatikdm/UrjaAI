from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from app.services.weather_api import WeatherAPI
from app.services.carbon_tracker import CarbonTracker
from app.services.energy_optimizer import EnergyOptimizer

router = APIRouter(prefix="", tags=["Sustainability"])

logger = logging.getLogger(__name__)

# Initialize singletons for the router session
weather_api = WeatherAPI()
carbon_tracker = CarbonTracker()
energy_optimizer = EnergyOptimizer(weather_api=weather_api, carbon_tracker=carbon_tracker)

class CarbonImpactRequest(BaseModel):
    energy_saved_kwh: float
    timestamp: Optional[str] = None

class CarbonForecastRequest(BaseModel):
    timestamps: List[str]

@router.get("/weather")
def get_weather_forecast(location: str = Query("19.0176,72.8562"), hours: int = Query(48, ge=1)):
    """Get weather forecast for specified location and hours"""
    try:
        # Parse coordinates
        if ',' in location:
            lat, lon = map(float, location.split(','))
            weather_api.latitude = lat
            weather_api.longitude = lon
            
        forecast_days = max(1, hours // 24 + 1)
        weather_data = weather_api.fetch_weather_forecast(forecast_days)
        
        hourly_data = weather_data.get('hourly', {})
        response_data = {
            'timestamps': hourly_data.get('time', [])[:hours],
            'temperature': hourly_data.get('temperature_2m', [])[:hours],
            'humidity': hourly_data.get('relativehumidity_2m', [])[:hours],
            'cloudcover': hourly_data.get('cloudcover', [])[:hours],
            'precipitation': hourly_data.get('precipitation', [])[:hours],
            'windspeed': hourly_data.get('windspeed_10m', [])[:hours],
            'weathercode': hourly_data.get('weathercode', [])[:hours]
        }
        
        return response_data
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/carbon-impact")
def calculate_carbon_impact(request: CarbonImpactRequest):
    """Calculate carbon impact metrics for energy savings"""
    try:
        timestamp_obj = None
        if request.timestamp:
            try:
                timestamp_obj = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass
                
        impact = carbon_tracker.calculate_carbon_impact(request.energy_saved_kwh, timestamp_obj)
        return impact
    except Exception as e:
        logger.error(f"Error in carbon-impact endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather-alerts")
def get_weather_alerts():
    """Get weather alerts based on forecast data"""
    try:
        weather_data = weather_api.fetch_weather_forecast(3)
        alerts = weather_api.get_weather_alerts(weather_data)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error in weather-alerts endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/badges")
def get_badges():
    """Get all badges and current progress"""
    try:
        badges = carbon_tracker.get_all_badges()
        return badges
    except Exception as e:
        logger.error(f"Error in badges endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/carbon-forecast")
def get_carbon_forecast(request: CarbonForecastRequest):
    """Get carbon intensity forecast for multiple timestamps"""
    try:
        ts_objs = []
        for ts_str in request.timestamps:
            try:
                ts_objs.append(datetime.fromisoformat(ts_str.replace('Z', '+00:00')))
            except ValueError:
                ts_objs.append(datetime.now())
                
        intensities = carbon_tracker.get_grid_intensity_forecast(ts_objs)
        
        return {
            'timestamps': request.timestamps,
            'grid_intensities': intensities,
            'region': carbon_tracker.region
        }
    except Exception as e:
        logger.error(f"Error in carbon-forecast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_stats():
    """Get cumulative statistics"""
    try:
        return {
            'cumulative_co2_saved': carbon_tracker.cumulative_co2_saved,
            'current_badge': carbon_tracker.get_current_badge(),
            'region': carbon_tracker.region,
            'base_grid_intensity': carbon_tracker.grid_intensities.get(carbon_tracker.region, 0.242)
        }
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize")
def get_optimization_dashboard(buildings: str = Query("A,B,C")):
    """Get optimization dashboard data for given building IDs"""
    try:
        b_list = [b.strip() for b in buildings.split(',')]
        return energy_optimizer.get_comprehensive_dashboard_data(b_list)
    except Exception as e:
        logger.error(f"Error in optimize endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
