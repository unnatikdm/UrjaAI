from flask import Flask, request, jsonify
from datetime import datetime
import logging
from weather_api import WeatherAPI
from carbon_tracker import CarbonTracker

app = Flask(__name__)

# Initialize components
weather_api = WeatherAPI()
carbon_tracker = CarbonTracker()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/weather', methods=['GET'])
def get_weather_forecast():
    """Get weather forecast for specified location and hours"""
    
    try:
        # Parse query parameters
        location = request.args.get('location', '19.0176,72.8562')  # Default: Mumbai Vadala
        hours = int(request.args.get('hours', 48))
        
        # Parse coordinates
        if ',' in location:
            lat, lon = map(float, location.split(','))
            weather_api.latitude = lat
            weather_api.longitude = lon
        
        # Fetch weather data
        forecast_days = max(1, hours // 24 + 1)
        weather_data = weather_api.fetch_weather_forecast(forecast_days)
        
        # Extract hourly data for requested hours
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
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/carbon-impact', methods=['POST'])
def calculate_carbon_impact():
    """Calculate carbon impact metrics for energy savings"""
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'energy_saved_kwh' not in data:
            return jsonify({'error': 'energy_saved_kwh is required'}), 400
        
        energy_saved_kwh = float(data['energy_saved_kwh'])
        
        # Parse timestamp if provided
        timestamp = None
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        # Calculate carbon impact
        impact = carbon_tracker.calculate_carbon_impact(energy_saved_kwh, timestamp)
        
        return jsonify(impact)
        
    except Exception as e:
        logger.error(f"Error in carbon-impact endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather-alerts', methods=['GET'])
def get_weather_alerts():
    """Get weather alerts based on forecast data"""
    
    try:
        # Get weather data
        weather_data = weather_api.fetch_weather_forecast(3)
        
        # Generate alerts
        alerts = weather_api.get_weather_alerts(weather_data)
        
        return jsonify({'alerts': alerts})
        
    except Exception as e:
        logger.error(f"Error in weather-alerts endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/badges', methods=['GET'])
def get_badges():
    """Get all badges and current progress"""
    
    try:
        badges = carbon_tracker.get_all_badges()
        return jsonify(badges)
        
    except Exception as e:
        logger.error(f"Error in badges endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/carbon-forecast', methods=['POST'])
def get_carbon_forecast():
    """Get carbon intensity forecast for multiple timestamps"""
    
    try:
        data = request.get_json()
        
        if not data or 'timestamps' not in data:
            return jsonify({'error': 'timestamps array is required'}), 400
        
        timestamps = []
        for ts_str in data['timestamps']:
            timestamps.append(datetime.fromisoformat(ts_str.replace('Z', '+00:00')))
        
        intensities = carbon_tracker.get_grid_intensity_forecast(timestamps)
        
        return jsonify({
            'timestamps': data['timestamps'],
            'grid_intensities': intensities,
            'region': carbon_tracker.region
        })
        
    except Exception as e:
        logger.error(f"Error in carbon-forecast endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'weather_api': 'active',
            'carbon_tracker': 'active'
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get cumulative statistics"""
    
    try:
        return jsonify({
            'cumulative_co2_saved': carbon_tracker.cumulative_co2_saved,
            'current_badge': carbon_tracker.get_current_badge(),
            'region': carbon_tracker.region,
            'base_grid_intensity': carbon_tracker.grid_intensities.get(carbon_tracker.region, 0.242)
        })
        
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
