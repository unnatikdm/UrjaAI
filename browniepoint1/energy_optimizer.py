import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Tuple
import logging

class EnergyOptimizer:
    """Energy optimization system integrating weather forecasts and carbon tracking"""
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        
        # Building-specific parameters
        self.building_params = {
            'A': {'base_load': 100, 'hvac_efficiency': 0.85, 'solar_capacity': 50},
            'B': {'base_load': 150, 'hvac_efficiency': 0.80, 'solar_capacity': 30},
            'C': {'base_load': 120, 'hvac_efficiency': 0.88, 'solar_capacity': 40}
        }
    
    def get_weather_forecast(self, hours: int = 48) -> Dict:
        """Get weather forecast from API"""
        
        try:
            response = requests.get(f"{self.api_base_url}/weather?hours={hours}", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get weather forecast: {e}")
            return {}
    
    def get_carbon_impact(self, energy_saved_kwh: float, timestamp: str = None) -> Dict:
        """Calculate carbon impact from API"""
        
        try:
            payload = {'energy_saved_kwh': energy_saved_kwh}
            if timestamp:
                payload['timestamp'] = timestamp
            
            response = requests.post(f"{self.api_base_url}/carbon-impact", 
                                   json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to calculate carbon impact: {e}")
            return {}
    
    def get_weather_alerts(self) -> List[Dict]:
        """Get weather alerts from API"""
        
        try:
            response = requests.get(f"{self.api_base_url}/weather-alerts", timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('alerts', [])
        except requests.RequestException as e:
            self.logger.error(f"Failed to get weather alerts: {e}")
            return []
    
    def predict_energy_consumption(self, building_id: str, weather_data: Dict) -> List[float]:
        """Predict energy consumption based on weather forecast"""
        
        if building_id not in self.building_params:
            raise ValueError(f"Unknown building: {building_id}")
        
        params = self.building_params[building_id]
        temperatures = weather_data.get('temperature', [])
        humidity = weather_data.get('humidity', [])
        cloudcover = weather_data.get('cloudcover', [])
        
        if not temperatures:
            return []
        
        predictions = []
        
        for i, temp in enumerate(temperatures):
            # Base load
            base_load = params['base_load']
            
            # Temperature impact (HVAC load)
            if temp > 25:  # Cooling needed
                hvac_load = (temp - 25) * 5 * (1 / params['hvac_efficiency'])
            elif temp < 18:  # Heating needed
                hvac_load = (18 - temp) * 3 * (1 / params['hvac_efficiency'])
            else:
                hvac_load = 0
            
            # Humidity impact
            humidity_factor = 1.0
            if i < len(humidity):
                humidity_factor = 1 + (humidity[i] - 50) * 0.002
            
            # Solar generation (reduces consumption)
            solar_generation = 0
            if i < len(cloudcover):
                # Simple solar model: more sun = more generation
                solar_factor = max(0, (100 - cloudcover[i]) / 100)
                hour = i % 24
                if 6 <= hour <= 18:  # Daylight hours
                    solar_generation = params['solar_capacity'] * solar_factor * \
                                     np.sin((hour - 6) * np.pi / 12)
            
            # Total consumption
            total_consumption = max(0, (base_load + hvac_load) * humidity_factor - solar_generation)
            predictions.append(round(total_consumption, 2))
        
        return predictions
    
    def generate_optimization_recommendations(self, building_id: str, 
                                           weather_data: Dict) -> List[Dict]:
        """Generate energy optimization recommendations"""
        
        recommendations = []
        predictions = self.predict_energy_consumption(building_id, weather_data)
        temperatures = weather_data.get('temperature', [])
        timestamps = weather_data.get('timestamps', [])
        
        if not predictions or not temperatures:
            return recommendations
        
        # Analyze next 48 hours
        for i in range(min(48, len(predictions))):
            timestamp = timestamps[i] if i < len(timestamps) else f"Hour {i+1}"
            temp = temperatures[i] if i < len(temperatures) else 20
            predicted_load = predictions[i]
            
            # Pre-cooling recommendation for hot days
            if temp > 30 and i < 24:  # Hot day in next 24h
                night_temp = temperatures[i+12] if i+12 < len(temperatures) else 20
                if night_temp < 25:
                    savings = predicted_load * 0.15  # 15% savings potential
                    carbon_impact = self.get_carbon_impact(savings, timestamp)
                    
                    recommendations.append({
                        'type': 'precooling',
                        'building_id': building_id,
                        'timestamp': timestamp,
                        'temperature': temp,
                        'predicted_load': predicted_load,
                        'action': f'Pre-cool building tonight (night temp: {night_temp:.1f}°C)',
                        'energy_savings_kwh': round(savings, 2),
                        'carbon_impact': carbon_impact,
                        'priority': 'high' if temp > 35 else 'medium'
                    })
            
            # Load shifting recommendation
            if 16 <= (i % 24) <= 20:  # Evening peak
                savings = predicted_load * 0.10  # 10% savings potential
                carbon_impact = self.get_carbon_impact(savings, timestamp)
                
                recommendations.append({
                    'type': 'load_shifting',
                    'building_id': building_id,
                    'timestamp': timestamp,
                    'temperature': temp,
                    'predicted_load': predicted_load,
                    'action': 'Shift non-critical loads to off-peak hours',
                    'energy_savings_kwh': round(savings, 2),
                    'carbon_impact': carbon_impact,
                    'priority': 'medium'
                })
            
            # Solar optimization
            if 10 <= (i % 24) <= 14:  # Peak solar hours
                cloudcover = weather_data.get('cloudcover', [])
                clouds = cloudcover[i] if i < len(cloudcover) else 0
                
                if clouds < 30:  # Clear skies
                    savings = predicted_load * 0.08  # 8% savings potential
                    carbon_impact = self.get_carbon_impact(savings, timestamp)
                    
                    recommendations.append({
                        'type': 'solar_optimization',
                        'building_id': building_id,
                        'timestamp': timestamp,
                        'temperature': temp,
                        'predicted_load': predicted_load,
                        'action': 'Maximize solar energy usage during peak generation',
                        'energy_savings_kwh': round(savings, 2),
                        'carbon_impact': carbon_impact,
                        'priority': 'low'
                    })
        
        # Sort by priority and limit to top 10
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations[:10]
    
    def get_comprehensive_dashboard_data(self, building_ids: List[str]) -> Dict:
        """Get comprehensive dashboard data for multiple buildings"""
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'buildings': {},
            'weather_alerts': [],
            'total_savings': {'energy_kwh': 0, 'co2_kg': 0}
        }
        
        # Get weather data and alerts
        weather_data = self.get_weather_forecast(48)
        dashboard_data['weather_alerts'] = self.get_weather_alerts()
        
        # Process each building
        for building_id in building_ids:
            if building_id not in self.building_params:
                continue
            
            # Generate predictions and recommendations
            predictions = self.predict_energy_consumption(building_id, weather_data)
            recommendations = self.generate_optimization_recommendations(building_id, weather_data)
            
            # Calculate potential savings
            total_energy_savings = sum(rec['energy_savings_kwh'] for rec in recommendations)
            total_co2_savings = 0
            
            for rec in recommendations:
                if rec.get('carbon_impact'):
                    total_co2_savings += rec['carbon_impact'].get('co2_saved_kg', 0)
            
            # Update totals
            dashboard_data['total_savings']['energy_kwh'] += total_energy_savings
            dashboard_data['total_savings']['co2_kg'] += total_co2_savings
            
            # Building-specific data
            dashboard_data['buildings'][building_id] = {
                'predictions_48h': predictions[:48],
                'recommendations': recommendations,
                'potential_savings': {
                    'energy_kwh': round(total_energy_savings, 2),
                    'co2_kg': round(total_co2_savings, 2)
                },
                'current_weather': {
                    'temperature': weather_data.get('temperature', [20])[0] if weather_data.get('temperature') else 20,
                    'humidity': weather_data.get('humidity', [50])[0] if weather_data.get('humidity') else 50
                }
            }
        
        return dashboard_data

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    optimizer = EnergyOptimizer()
    
    # Test with sample buildings
    buildings = ['A', 'B', 'C']
    
    try:
        dashboard = optimizer.get_comprehensive_dashboard_data(buildings)
        print("Dashboard Data Generated Successfully")
        print(f"Total Energy Savings: {dashboard['total_savings']['energy_kwh']:.2f} kWh")
        print(f"Total CO2 Savings: {dashboard['total_savings']['co2_kg']:.2f} kg")
        print(f"Weather Alerts: {len(dashboard['weather_alerts'])}")
        
    except Exception as e:
        print(f"Error: {e}")
