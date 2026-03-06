from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.services.weather_api import WeatherAPI
from app.services.carbon_tracker import CarbonTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/browniepoint1", tags=["browniepoint1"])

# Initialize singletons
weather_api = WeatherAPI()
carbon_tracker = CarbonTracker()

@router.get("/health", tags=["browniepoint1-health"])
def browniepoint1_health():
    """Check health of browniepoint1 service natively."""
    return {"status": "ok", "service": "Carbon Tracker Native Service"}


@router.get("/weather", tags=["weather"])
def get_weather_forecast(
    location: Optional[str] = Query("19.0176,72.8562"),
    hours: Optional[int] = Query(48)
):
    """Get weather forecast."""
    try:
        if location and ',' in location:
            lat, lon = map(float, location.split(','))
            weather_api.latitude = lat
            weather_api.longitude = lon
            
        forecast_days = max(1, hours // 24 + 1)
        weather_data = weather_api.fetch_weather_forecast(forecast_days)
        
        hourly_data = weather_data.get('hourly', {})
        return {
            'timestamps': hourly_data.get('time', [])[:hours],
            'temperature': hourly_data.get('temperature_2m', [])[:hours],
            'humidity': hourly_data.get('relativehumidity_2m', [])[:hours],
            'cloudcover': hourly_data.get('cloudcover', [])[:hours],
            'precipitation': hourly_data.get('precipitation', [])[:hours],
            'windspeed': hourly_data.get('windspeed_10m', [])[:hours],
            'weathercode': hourly_data.get('weathercode', [])[:hours]
        }
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to process weather request")


@router.get("/weather-alerts", tags=["alerts"])
def get_weather_alerts():
    """Get weather alerts."""
    try:
        weather_data = weather_api.fetch_weather_forecast(3)
        alerts = weather_api.get_weather_alerts(weather_data)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        return {"alerts": []}


@router.post("/carbon-impact", tags=["carbon"])
def calculate_carbon_impact(request: Dict[str, Any]):
    """Calculate carbon impact metrics for energy savings."""
    try:
        energy_saved_kwh = request.get("energy_saved_kwh")
        if energy_saved_kwh is None:
            raise HTTPException(status_code=400, detail="energy_saved_kwh is required")

        timestamp_obj = None
        if request.get("timestamp"):
            try:
                timestamp_obj = datetime.fromisoformat(request["timestamp"].replace('Z', '+00:00'))
            except ValueError:
                pass
                
        impact = carbon_tracker.calculate_carbon_impact(energy_saved_kwh, timestamp_obj)
        return impact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating carbon impact: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate carbon impact")


@router.get("/badges", tags=["gamification"])
def get_badges():
    """Get all available badges and progress."""
    try:
        badges = carbon_tracker.get_all_badges()
        
        # Format for browniepoint1 UI expects an array, not a dict with key format
        badge_list = []
        for key, badge in badges.items():
            badge_list.append({
                "name": badge["name"],
                "description": badge["description"],
                "icon": badge["icon"],
                "earned": carbon_tracker.cumulative_co2_saved >= badge["threshold"],
                "progress": min(100, int((carbon_tracker.cumulative_co2_saved / badge["threshold"]) * 100)) if badge["threshold"] > 0 else 100
            })
            
        return badge_list
    except Exception as e:
        logger.error(f"Error fetching badges: {e}")
        return []


@router.get("/carbon-forecast", tags=["carbon"])
def get_carbon_forecast(days: Optional[int] = Query(7)):
    """Get grid carbon intensity forecast."""
    try:
        # Generate timestamps for n days
        now = datetime.now()
        ts_objs = [now] # simplified for now
        intensities = carbon_tracker.get_grid_intensity_forecast(ts_objs)
        
        return {
            'grid_intensities': intensities,
        }
    except Exception as e:
        logger.error(f"Error fetching carbon forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch carbon forecast")
