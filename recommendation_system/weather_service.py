"""
Weather Service Integration with Open-Meteo API
Provides real historical and forecast weather data for energy recommendations
"""

import os
import aiohttp
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class WeatherService:
    """Integration with Open-Meteo weather API"""
    
    def __init__(self, api_base_url: str = "https://archive-api.open-meteo.com/v1"):
        self.api_base_url = api_base_url
        self.forecast_base_url = "https://api.open-meteo.com/v1"
        self.session = None
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
        
        # Default coordinates (can be overridden per building)
        self.default_coords = {
            'latitude': 52.5200,  # Berlin coordinates
            'longitude': 13.4050
        }
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for requests"""
        param_str = json.dumps(params, sort_keys=True)
        return f"{endpoint}:{param_str}"
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached data is still valid"""
        return (datetime.now().timestamp() - timestamp) < self.cache_duration
    
    async def get_historical_weather(
        self, 
        start_date: str, 
        end_date: str,
        latitude: float = None,
        longitude: float = None,
        building_id: str = None
    ) -> Dict[str, Any]:
        """Get historical weather data from Open-Meteo archive"""
        
        # Use provided coordinates or defaults
        lat = latitude or self.default_coords['latitude']
        lon = longitude or self.default_coords['longitude']
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'hourly': [
                'temperature_2m',
                'relativehumidity_2m',
                'windspeed_10m',
                'weathercode',
                'apparent_temperature',
                'precipitation'
            ],
            'timezone': 'auto'
        }
        
        cache_key = self._get_cache_key('archive', params)
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.logger.info(f"Using cached historical weather data for {start_date} to {end_date}")
                return cached_data
        
        # Fetch from API
        session = await self._get_session()
        url = f"{self.api_base_url}/archive"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process and cache the data
                    processed_data = self._process_historical_data(data, building_id)
                    self.cache[cache_key] = (processed_data, datetime.now().timestamp())
                    
                    self.logger.info(f"Fetched historical weather data: {len(processed_data.get('hourly', {}).get('time', []))} records")
                    return processed_data
                else:
                    self.logger.error(f"Weather API error: {response.status}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch historical weather: {e}")
            return {}
    
    async def get_weather_forecast(
        self,
        hours: int = 48,
        latitude: float = None,
        longitude: float = None,
        building_id: str = None
    ) -> Dict[str, Any]:
        """Get weather forecast from Open-Meteo"""
        
        lat = latitude or self.default_coords['latitude']
        lon = longitude or self.default_coords['longitude']
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': [
                'temperature_2m',
                'relativehumidity_2m',
                'windspeed_10m',
                'weathercode',
                'apparent_temperature',
                'precipitation'
            ],
            'forecast_hours': hours,
            'timezone': 'auto'
        }
        
        cache_key = self._get_cache_key('forecast', params)
        
        # Check cache (shorter duration for forecasts)
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.logger.info(f"Using cached forecast data")
                return cached_data
        
        # Fetch from API
        session = await self._get_session()
        url = f"{self.forecast_base_url}/forecast"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process and cache the data
                    processed_data = self._process_forecast_data(data, building_id)
                    self.cache[cache_key] = (processed_data, datetime.now().timestamp())
                    
                    self.logger.info(f"Fetched weather forecast: {len(processed_data.get('hourly', {}).get('time', []))} hours")
                    return processed_data
                else:
                    self.logger.error(f"Weather forecast API error: {response.status}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch weather forecast: {e}")
            return {}
    
    def _process_historical_data(self, data: Dict[str, Any], building_id: str = None) -> Dict[str, Any]:
        """Process historical weather data into structured format"""
        
        if 'hourly' not in data:
            return {}
        
        hourly = data['hourly']
        processed = {
            'building_id': building_id,
            'data_type': 'historical',
            'source': 'open-meteo',
            'extraction_date': datetime.now().isoformat(),
            'hourly': {
                'time': hourly.get('time', []),
                'temperature_2m': hourly.get('temperature_2m', []),
                'relativehumidity_2m': hourly.get('relativehumidity_2m', []),
                'windspeed_10m': hourly.get('windspeed_10m', []),
                'weathercode': hourly.get('weathercode', []),
                'apparent_temperature': hourly.get('apparent_temperature', []),
                'precipitation': hourly.get('precipitation', [])
            }
        }
        
        # Add derived metrics
        if processed['hourly']['time'] and processed['hourly']['temperature_2m']:
            processed['derived'] = self._calculate_derived_metrics(processed['hourly'])
        
        return processed
    
    def _process_forecast_data(self, data: Dict[str, Any], building_id: str = None) -> Dict[str, Any]:
        """Process forecast weather data into structured format"""
        
        if 'hourly' not in data:
            return {}
        
        hourly = data['hourly']
        processed = {
            'building_id': building_id,
            'data_type': 'forecast',
            'source': 'open-meteo',
            'extraction_date': datetime.now().isoformat(),
            'hourly': {
                'time': hourly.get('time', []),
                'temperature_2m': hourly.get('temperature_2m', []),
                'relativehumidity_2m': hourly.get('relativehumidity_2m', []),
                'windspeed_10m': hourly.get('windspeed_10m', []),
                'weathercode': hourly.get('weathercode', []),
                'apparent_temperature': hourly.get('apparent_temperature', []),
                'precipitation': hourly.get('precipitation', [])
            }
        }
        
        # Add derived metrics
        if processed['hourly']['time'] and processed['hourly']['temperature_2m']:
            processed['derived'] = self._calculate_derived_metrics(processed['hourly'])
        
        return processed
    
    def _calculate_derived_metrics(self, hourly_data: Dict[str, List]) -> Dict[str, Any]:
        """Calculate derived weather metrics"""
        
        temperatures = hourly_data.get('temperature_2m', [])
        humidity = hourly_data.get('relativehumidity_2m', [])
        weather_codes = hourly_data.get('weathercode', [])
        
        if not temperatures:
            return {}
        
        # Temperature statistics
        temp_stats = {
            'max_temp': max(temperatures),
            'min_temp': min(temperatures),
            'avg_temp': sum(temperatures) / len(temperatures)
        }
        
        # Heat wave detection (consecutive hours > 30°C)
        heat_wave_hours = 0
        consecutive_heat = 0
        for temp in temperatures:
            if temp > 30:
                consecutive_heat += 1
                heat_wave_hours = max(heat_wave_hours, consecutive_heat)
            else:
                consecutive_heat = 0
        
        # Cold snap detection (consecutive hours < 5°C)
        cold_snap_hours = 0
        consecutive_cold = 0
        for temp in temperatures:
            if temp < 5:
                consecutive_cold += 1
                cold_snap_hours = max(cold_snap_hours, consecutive_cold)
            else:
                consecutive_cold = 0
        
        # Weather conditions analysis
        if weather_codes:
            # WMO weather codes: 0=Clear, 1-3=Cloudy, 45,48=Fog, 51-67=Rain, 71-77=Snow, 80-82=Showers, 95-99=Thunderstorm
            clear_hours = sum(1 for code in weather_codes if code == 0)
            cloudy_hours = sum(1 for code in weather_codes if 1 <= code <= 3)
            precipitation_hours = sum(1 for code in weather_codes if 51 <= code <= 67 or 80 <= code <= 82)
            
            weather_conditions = {
                'clear_hours': clear_hours,
                'cloudy_hours': cloudy_hours,
                'precipitation_hours': precipitation_hours,
                'total_hours': len(weather_codes)
            }
        else:
            weather_conditions = {}
        
        # Comfort index (simplified)
        if humidity and temperatures:
            avg_humidity = sum(humidity) / len(humidity)
            comfort_hours = sum(1 for temp, hum in zip(temperatures, humidity) 
                             if 18 <= temp <= 26 and 30 <= hum <= 60)
        else:
            avg_humidity = 0
            comfort_hours = 0
        
        return {
            'temperature_stats': temp_stats,
            'heat_wave_hours': heat_wave_hours,
            'cold_snap_hours': cold_snap_hours,
            'weather_conditions': weather_conditions,
            'avg_humidity': avg_humidity,
            'comfort_hours': comfort_hours,
            'total_hours': len(temperatures)
        }
    
    async def get_weather_patterns(
        self, 
        start_date: str, 
        end_date: str,
        building_id: str = None
    ) -> List[Dict[str, Any]]:
        """Analyze weather patterns for knowledge base"""
        
        weather_data = await self.get_historical_weather(
            start_date, end_date, building_id=building_id
        )
        
        if not weather_data or 'derived' not in weather_data:
            return []
        
        derived = weather_data['derived']
        patterns = []
        
        # Heat wave pattern
        if derived.get('heat_wave_hours', 0) >= 6:  # 6+ consecutive hours
            patterns.append({
                'type': 'weather_pattern',
                'condition': 'heatwave',
                'impact': f"Heatwave detected with {derived['heat_wave_hours']} consecutive hours above 30°C. This typically increases cooling load by 25-35% compared to normal conditions.",
                'temperature_range': f"{derived['temperature_stats']['min_temp']:.1f}-{derived['temperature_stats']['max_temp']:.1f}°C",
                'avg_temperature': derived['temperature_stats']['avg_temp'],
                'building_id': building_id,
                'date_range': f"{start_date} to {end_date}",
                'source': 'open-meteo',
                'confidence': 0.9
            })
        
        # Cold snap pattern
        if derived.get('cold_snap_hours', 0) >= 6:  # 6+ consecutive hours
            patterns.append({
                'type': 'weather_pattern',
                'condition': 'cold_snap',
                'impact': f"Cold snap detected with {derived['cold_snap_hours']} consecutive hours below 5°C. This typically increases heating load by 20-30% compared to normal conditions.",
                'temperature_range': f"{derived['temperature_stats']['min_temp']:.1f}-{derived['temperature_stats']['max_temp']:.1f}°C",
                'avg_temperature': derived['temperature_stats']['avg_temp'],
                'building_id': building_id,
                'date_range': f"{start_date} to {end_date}",
                'source': 'open-meteo',
                'confidence': 0.9
            })
        
        # High humidity pattern
        if derived.get('avg_humidity', 0) > 70:
            patterns.append({
                'type': 'weather_pattern',
                'condition': 'high_humidity',
                'impact': f"High humidity conditions (avg {derived['avg_humidity']:.1f}%) increase perceived temperature and HVAC load by 10-15%.",
                'humidity_range': f"High (>70%)",
                'avg_humidity': derived['avg_humidity'],
                'building_id': building_id,
                'date_range': f"{start_date} to {end_date}",
                'source': 'open-meteo',
                'confidence': 0.8
            })
        
        # Comfortable conditions pattern
        comfort_ratio = derived.get('comfort_hours', 0) / derived.get('total_hours', 1)
        if comfort_ratio > 0.7:
            patterns.append({
                'type': 'weather_pattern',
                'condition': 'comfortable',
                'impact': f"Comfortable weather conditions ({comfort_ratio:.1%} of time in comfort range) typically result in optimal HVAC efficiency.",
                'comfort_hours': derived['comfort_hours'],
                'total_hours': derived['total_hours'],
                'comfort_ratio': comfort_ratio,
                'building_id': building_id,
                'date_range': f"{start_date} to {end_date}",
                'source': 'open-meteo',
                'confidence': 0.8
            })
        
        return patterns
    
    async def cache_historical_data(
        self, 
        start_date: str, 
        end_date: str,
        building_id: str = None
    ) -> bool:
        """Pre-cache historical weather data for offline use"""
        
        try:
            weather_data = await self.get_historical_weather(
                start_date, end_date, building_id=building_id
            )
            
            if weather_data:
                # Save to local cache file
                cache_dir = Path("weather_cache")
                cache_dir.mkdir(exist_ok=True)
                
                cache_file = cache_dir / f"weather_{building_id or 'default'}_{start_date}_{end_date}.json"
                
                with open(cache_file, 'w') as f:
                    json.dump(weather_data, f, indent=2)
                
                self.logger.info(f"Weather data cached to {cache_file}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache weather data: {e}")
        
        return False
    
    def load_cached_data(
        self, 
        start_date: str, 
        end_date: str,
        building_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """Load cached weather data from file"""
        
        cache_dir = Path("weather_cache")
        cache_file = cache_dir / f"weather_{building_id or 'default'}_{start_date}_{end_date}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded cached weather data from {cache_file}")
                return data
            except Exception as e:
                self.logger.error(f"Failed to load cached data: {e}")
        
        return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

# Example usage and testing
async def test_weather_service():
    """Test the weather service integration"""
    
    weather_service = WeatherService()
    
    try:
        # Test historical weather
        print("Testing historical weather...")
        historical = await weather_service.get_historical_weather(
            start_date="2025-07-01",
            end_date="2025-07-07",
            building_id="A"
        )
        
        if historical:
            print(f"✅ Historical weather: {len(historical.get('hourly', {}).get('time', []))} records")
        
        # Test forecast
        print("Testing weather forecast...")
        forecast = await weather_service.get_weather_forecast(
            hours=48,
            building_id="A"
        )
        
        if forecast:
            print(f"✅ Forecast: {len(forecast.get('hourly', {}).get('time', []))} hours")
        
        # Test weather patterns
        print("Testing weather patterns...")
        patterns = await weather_service.get_weather_patterns(
            start_date="2025-07-01",
            end_date="2025-07-07",
            building_id="A"
        )
        
        print(f"✅ Weather patterns: {len(patterns)} identified")
        for pattern in patterns:
            print(f"  - {pattern['condition']}: {pattern['impact']}")
        
        # Test caching
        print("Testing data caching...")
        cached = await weather_service.cache_historical_data(
            start_date="2025-07-01",
            end_date="2025-07-07",
            building_id="A"
        )
        
        if cached:
            print("✅ Data cached successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Weather service test failed: {e}")
        return False
    
    finally:
        await weather_service.close()

if __name__ == "__main__":
    asyncio.run(test_weather_service())
