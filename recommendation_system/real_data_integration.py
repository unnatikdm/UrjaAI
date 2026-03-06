"""
Real Data Integration Module
Connects the recommendation system to actual Bosch energy data sources
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd

class BoschAPIClient:
    """Client for Bosch Energy Management System API"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or os.getenv('BOSCH_API_URL', 'https://api.bosch-energy.com/v1')
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        return self.session
    
    async def get_recommendations(self, building_id: str, start_date: str = None, 
                            end_date: str = None) -> List[Dict]:
        """Get recommendations from Bosch system"""
        session = await self._get_session()
        
        params = {'building_id': building_id}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        url = f"{self.base_url}/recommendations"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('recommendations', [])
                else:
                    logging.error(f"Bosch API error: {response.status}")
                    return []
        except Exception as e:
            logging.error(f"Failed to fetch recommendations: {e}")
            return []
    
    async def get_recommendation_outcome(self, recommendation_id: str) -> Dict[str, Any]:
        """Get actual outcome for a recommendation"""
        session = await self._get_session()
        
        url = f"{self.base_url}/recommendations/{recommendation_id}/outcome"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Failed to get outcome: {response.status}")
                    return {}
        except Exception as e:
            logging.error(f"Failed to fetch outcome: {e}")
            return {}
    
    async def get_building_metadata(self, building_id: str) -> Dict[str, Any]:
        """Get building metadata from Bosch system"""
        session = await self._get_session()
        
        url = f"{self.base_url}/buildings/{building_id}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Failed to get building metadata: {response.status}")
                    return {}
        except Exception as e:
            logging.error(f"Failed to get building metadata: {e}")
            return {}
    
    async def submit_feedback(self, recommendation_id: str, feedback: Dict[str, Any]) -> bool:
        """Submit user feedback for a recommendation"""
        session = await self._get_session()
        
        url = f"{self.base_url}/recommendations/{recommendation_id}/feedback"
        
        try:
            async with session.post(url, json=feedback) as response:
                return response.status == 200
        except Exception as e:
            logging.error(f"Failed to submit feedback: {e}")
            return False

class WeatherAPIClient:
    """Client for Weather Service Integration"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or os.getenv('WEATHER_API_URL', 'https://api.weather-service.com/v1')
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        return self.session
    
    async def get_current_weather(self, location: Dict[str, float]) -> Dict[str, Any]:
        """Get current weather for a location"""
        session = await self._get_session()
        
        url = f"{self.base_url}/current"
        params = {
            'latitude': location.get('latitude'),
            'longitude': location.get('longitude'),
            'building_id': location.get('building_id')
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Weather API error: {response.status}")
                    return {}
        except Exception as e:
            logging.error(f"Failed to get weather: {e}")
            return {}
    
    async def get_forecast(self, location: Dict[str, float], hours: int = 24) -> Dict[str, Any]:
        """Get weather forecast"""
        session = await self._get_session()
        
        url = f"{self.base_url}/forecast"
        params = {
            'latitude': location.get('latitude'),
            'longitude': location.get('longitude'),
            'hours': hours,
            'building_id': location.get('building_id')
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Weather forecast error: {response.status}")
                    return {}
        except Exception as e:
            logging.error(f"Failed to get forecast: {e}")
            return {}

class ModelAPIClient:
    """Client for Model/SHAP explanations"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url or os.getenv('MODEL_API_URL', 'https://api.energy-models.com/v1')
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        return self.session
    
    async def get_shap_explanations(self, prediction_id: str) -> List[Dict[str, Any]]:
        """Get SHAP explanations for a prediction"""
        session = await self._get_session()
        
        url = f"{self.base_url}/predictions/{prediction_id}/shap"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('shap_explanations', [])
                else:
                    logging.error(f"Model API error: {response.status}")
                    return []
        except Exception as e:
            logging.error(f"Failed to get SHAP explanations: {e}")
            return []
    
    async def get_feature_importance(self, model_id: str) -> Dict[str, float]:
        """Get global feature importance from model"""
        session = await self._get_session()
        
        url = f"{self.base_url}/models/{model_id}/importance"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Model API error: {response.status}")
                    return {}
        except Exception as e:
            logging.error(f"Failed to get feature importance: {e}")
            return {}

class RealDataIntegrator:
    """Integrates real data sources into the recommendation system"""
    
    def __init__(self):
        self.bosch_client = None
        self.weather_client = None
        self.model_client = None
        
        # Initialize clients if API keys are available
        bosch_api_key = os.getenv('BOSCH_API_KEY')
        weather_api_key = os.getenv('WEATHER_API_KEY')
        model_api_key = os.getenv('MODEL_API_KEY')
        
        if bosch_api_key:
            self.bosch_client = BoschAPIClient(bosch_api_key)
        
        if weather_api_key:
            self.weather_client = WeatherAPIClient(weather_api_key)
        
        if model_api_key:
            self.model_client = ModelAPIClient(model_api_key)
        
        self.logger = logging.getLogger(__name__)
    
    async def get_real_recommendations(self, building_id: str, days_back: int = 30) -> List[Dict]:
        """Get real recommendations with actual outcomes"""
        if not self.bosch_client:
            self.logger.warning("Bosch API client not initialized")
            return []
        
        end_date = datetime.now()
        start_date = (end_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        recommendations = await self.bosch_client.get_recommendations(
            building_id=building_id,
            start_date=start_date,
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Get actual outcomes for each recommendation
        enriched_recommendations = []
        for rec in recommendations:
            rec_id = rec.get('id', '')
            if rec_id:
                outcome = await self.bosch_client.get_recommendation_outcome(rec_id)
                
                enriched_rec = {
                    **rec,
                    'actual_outcome': outcome,
                    'real_data': True,
                    'data_source': 'bosch_api',
                    'extraction_date': datetime.now().isoformat()
                }
                
                # Calculate real success rate
                if outcome.get('success') is not None:
                    enriched_rec['real_success_rate'] = 1.0 if outcome['success'] else 0.0
                
                enriched_recommendations.append(enriched_rec)
        
        return enriched_recommendations
    
    async def get_real_weather_context(self, building_id: str, location: Dict[str, float]) -> Dict[str, Any]:
        """Get real weather context for explanations"""
        if not self.weather_client:
            self.logger.warning("Weather API client not initialized")
            return {}
        
        current_weather = await self.weather_client.get_current_weather(location)
        forecast = await self.weather_client.get_forecast(location, hours=48)
        
        return {
            'current': current_weather,
            'forecast': forecast,
            'real_data': True,
            'data_source': 'weather_api',
            'extraction_date': datetime.now().isoformat(),
            'building_id': building_id
        }
    
    async def get_real_shap_explanations(self, prediction_ids: List[str]) -> List[Dict]:
        """Get real SHAP explanations"""
        if not self.model_client:
            self.logger.warning("Model API client not initialized")
            return []
        
        all_explanations = []
        for pred_id in prediction_ids:
            explanations = await self.model_client.get_shap_explanations(pred_id)
            for exp in explanations:
                exp['real_data'] = True
                exp['data_source'] = 'model_api'
                exp['extraction_date'] = datetime.now().isoformat()
            all_explanations.extend(explanations)
        
        return all_explanations
    
    async def submit_real_feedback(self, recommendation_id: str, feedback: Dict[str, Any]) -> bool:
        """Submit feedback to real system"""
        if not self.bosch_client:
            self.logger.warning("Bosch API client not initialized")
            return False
        
        success = await self.bosch_client.submit_feedback(recommendation_id, feedback)
        if success:
            self.logger.info(f"Feedback submitted for recommendation {recommendation_id}")
        return success
    
    async def get_real_building_metadata(self, building_id: str) -> Dict[str, Any]:
        """Get real building metadata"""
        if not self.bosch_client:
            self.logger.warning("Bosch API client not initialized")
            return {}
        
        metadata = await self.bosch_client.get_building_metadata(building_id)
        if metadata:
            metadata['real_data'] = True
            metadata['data_source'] = 'bosch_api'
            metadata['extraction_date'] = datetime.now().isoformat()
        
        return metadata
    
    def is_real_data_available(self) -> bool:
        """Check if real data sources are configured"""
        return all([
            os.getenv('BOSCH_API_KEY'),
            os.getenv('WEATHER_API_KEY'),
            os.getenv('MODEL_API_KEY')
        ])

# Example usage and testing
async def test_real_data_integration():
    """Test real data integration"""
    integrator = RealDataIntegrator()
    
    if integrator.is_real_data_available():
        print("✅ Real data sources configured")
        
        # Test getting recommendations
        recs = await integrator.get_real_recommendations("building_A")
        print(f"Retrieved {len(recs)} real recommendations")
        
        # Test weather context
        location = {"latitude": 52.5200, "longitude": 13.4050, "building_id": "building_A"}
        weather = await integrator.get_real_weather_context("building_A", location)
        print(f"Weather context: {weather.get('current', {}).get('temperature', 'N/A')}°C")
        
        return True
    else:
        print("❌ Real data sources not configured")
        print("Please set environment variables:")
        print("- BOSCH_API_KEY")
        print("- WEATHER_API_KEY") 
        print("- MODEL_API_KEY")
        return False

if __name__ == "__main__":
    asyncio.run(test_real_data_integration())
