import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class WeatherAPI:
    """Open-Meteo weather API integration for live weather data"""
    
    def __init__(self, latitude: float = 19.0176, longitude: float = 72.8562):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.latitude = latitude
        self.longitude = longitude
        self.cache = {}
        self.cache_duration = 6  # hours
        self.logger = logging.getLogger(__name__)
    
    def fetch_weather_forecast(self, forecast_days: int = 3) -> Dict:
        """Fetch hourly weather forecast from Open-Meteo API"""
        
        # Check cache first
        cache_key = f"weather_{datetime.now().strftime('%Y%m%d_%H')}"
        if cache_key in self.cache:
            self.logger.info("Using cached weather data")
            return self.cache[cache_key]
        
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": "temperature_2m,relativehumidity_2m,cloudcover,precipitation,windspeed_10m,weathercode",
            "forecast_days": forecast_days,
            "timezone": "auto",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Cache the data
            self.cache[cache_key] = weather_data
            
            self.logger.info(f"Successfully fetched weather data for {forecast_days} days")
            return weather_data
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch weather data: {e}")
            # Return cached data if available, or raise exception
            if self.cache:
                return list(self.cache.values())[-1]
            raise
    
    def get_weather_alerts(self, weather_data: Dict) -> List[Dict]:
        """Generate weather alerts based on forecast data"""
        
        alerts = []
        hourly_data = weather_data.get("hourly", {})
        
        if not hourly_data:
            return alerts
        
        temperatures = hourly_data.get("temperature_2m", [])
        precipitation = hourly_data.get("precipitation", [])
        weather_codes = hourly_data.get("weathercode", [])
        wind_speeds = hourly_data.get("windspeed_10m", [])
        timestamps = hourly_data.get("time", [])
        
        # Heatwave detection
        high_temps = [temp for temp in temperatures if temp > 35]
        if len(high_temps) >= 24:  # 3+ consecutive days (24+ hours)
            max_temp = max(high_temps)
            peak_idx = temperatures.index(max_temp)
            alerts.append({
                "type": "heatwave",
                "severity": "high",
                "message": f"Extreme heat predicted ({max_temp}°C) – optimize pre-cooling schedules",
                "peak_time": timestamps[peak_idx] if peak_idx < len(timestamps) else None
            })
        
        # Cold snap detection
        low_temps = [temp for temp in temperatures if temp < -5]
        if low_temps:
            min_temp = min(low_temps)
            peak_idx = temperatures.index(min_temp)
            alerts.append({
                "type": "cold_snap",
                "severity": "high", 
                "message": f"Freezing temperatures ({min_temp}°C) – increase heating efficiency",
                "peak_time": timestamps[peak_idx] if peak_idx < len(timestamps) else None
            })
        
        # Heavy rain detection
        heavy_rain = [prec for prec in precipitation if prec > 10]
        if heavy_rain:
            max_prec = max(heavy_rain)
            peak_idx = precipitation.index(max_prec)
            alerts.append({
                "type": "heavy_rain",
                "severity": "medium",
                "message": f"Heavy rain expected ({max_prec} mm/h) – prepare for potential outages",
                "peak_time": timestamps[peak_idx] if peak_idx < len(timestamps) else None
            })
        
        # Thunderstorm detection
        thunderstorm_codes = [95, 96, 99]
        storm_indices = [i for i, code in enumerate(weather_codes) if code in thunderstorm_codes]
        if storm_indices:
            alerts.append({
                "type": "thunderstorm",
                "severity": "medium",
                "message": "Thunderstorms forecast – backup power systems ready",
                "peak_time": timestamps[storm_indices[0]] if storm_indices[0] < len(timestamps) else None
            })
        
        # High wind detection
        high_winds = [wind for wind in wind_speeds if wind > 50]
        if high_winds:
            max_wind = max(high_winds)
            peak_idx = wind_speeds.index(max_wind)
            alerts.append({
                "type": "high_wind",
                "severity": "low",
                "message": f"High winds ({max_wind} km/h) – check building envelope integrity",
                "peak_time": timestamps[peak_idx] if peak_idx < len(timestamps) else None
            })
        
        return alerts
    
    def get_current_weather(self) -> Dict:
        """Get current weather conditions"""
        weather_data = self.fetch_weather_forecast(1)
        hourly_data = weather_data.get("hourly", {})
        
        if not hourly_data:
            return {}
        
        # Get the first hour (current conditions)
        current = {}
        for key, values in hourly_data.items():
            if values and len(values) > 0:
                current[key] = values[0]
        
        return current
