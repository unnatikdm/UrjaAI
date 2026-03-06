# Carbon Footprint Tracker + Live Weather Integration

A comprehensive energy intelligence system that integrates live weather forecasting with carbon footprint tracking for campus energy optimization.

## Features

### 🌤️ Live Weather Integration
- **Open-Meteo API** integration with no API key required
- Real-time weather data for Budapest campus (47.4979°N, 19.0402°E)
- 48-hour forecasts with hourly granularity
- Weather alerts for extreme conditions (heatwaves, storms, etc.)

### 🌱 Carbon Footprint Tracking
- Regional grid intensity calculations (Hungary: 0.242 kg CO₂/kWh)
- Time-of-day adjustments for solar generation
- Relatable metrics: trees planted, car km avoided, smartphone charges
- Gamification badges for cumulative savings

### ⚡ Energy Optimization
- Building-specific energy consumption predictions
- Weather-aware optimization recommendations
- Pre-cooling strategies for hot days
- Load shifting for evening peak hours
- Solar generation optimization

### 📊 API Endpoints
- `/weather` - Weather forecast data
- `/carbon-impact` - Carbon impact calculations
- `/weather-alerts` - Weather-based alerts
- `/badges` - Gamification progress
- `/carbon-forecast` - Grid intensity forecasts

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start API Server
```bash
python api_server.py
```
Server runs on `http://localhost:5000`

### 3. Run Integration Tests
```bash
python test_integration.py
```

### 4. Generate Sample Dashboard
```bash
python energy_optimizer.py
```

## API Usage Examples

### Get Weather Forecast
```bash
curl "http://localhost:5000/weather?hours=48"
```

### Calculate Carbon Impact
```bash
curl -X POST "http://localhost:5000/carbon-impact" \
  -H "Content-Type: application/json" \
  -d '{"energy_saved_kwh": 150}'
```

### Get Weather Alerts
```bash
curl "http://localhost:5000/weather-alerts"
```

## Key Parameters

### Weather API Configuration
- **Provider**: Open-Meteo (free, no API key)
- **Location**: Budapest campus (47.4979°N, 19.0402°E)
- **Update Frequency**: Every 6 hours
- **Parameters**: Temperature, humidity, cloud cover, precipitation, wind speed, weather codes

### Carbon Tracking Parameters
- **Base Grid Intensity (Hungary)**: 0.242 kg CO₂/kWh
- **Solar Hours Factor (9-16)**: 0.85 (15% reduction)
- **Evening Peak Factor (16-21)**: 1.10 (10% increase)
- **Night Factor (0-6)**: 1.05 (5% increase)

### Alert Thresholds
- **Heatwave**: Temperature > 35°C for 3+ consecutive days
- **Cold Snap**: Temperature < -5°C
- **Heavy Rain**: Precipitation > 10 mm/h
- **Thunderstorm**: Weather code 95-99
- **High Wind**: Wind speed > 50 km/h

## Badge System

| Badge | Threshold | Icon |
|-------|-----------|------|
| Seedling | 10 kg CO₂ saved | 🌱 |
| Sapling | 50 kg CO₂ saved | 🌿 |
| Tree | 200 kg CO₂ saved | 🌳 |
| Forest | 500 kg CO₂ saved | 🌲 |
| Carbon Hero | 1000+ kg CO₂ saved | 🏆 |

## File Structure

```
browniepoint1/
├── weather_api.py          # Open-Meteo weather integration
├── carbon_tracker.py       # Carbon footprint calculations
├── api_server.py          # Flask API endpoints
├── energy_optimizer.py     # Energy optimization engine
├── test_integration.py     # Integration test suite
├── requirements.txt        # Python dependencies
└── README.md             # This file
```

## Integration with Bosch Dataset

The system is designed to integrate with your existing Bosch campus energy dataset:

1. **Historical Data**: Use for training XGBoost models
2. **Live Weather**: Replace historical weather with real-time forecasts
3. **Carbon Metrics**: Add environmental impact to energy savings
4. **Optimization**: Generate weather-aware recommendations

## Expected Outcomes

### Judges Will See:
- **Live weather dashboard** with real-time updates
- **Weather alerts** for proactive energy management  
- **Carbon impact metrics** showing environmental benefits
- **Relatable comparisons** (trees planted, cars off road)
- **Gamification elements** with achievement badges

### Research Validation:
- Open-Meteo used in production energy systems
- European Environment Agency carbon intensity data
- IPCC standard conversion factors
- Building science weather-HVAC coupling

## Troubleshooting

### Common Issues:
1. **API Server Not Running**: Start with `python api_server.py`
2. **Weather API Timeout**: Check internet connection
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Port Conflicts**: Change port in `api_server.py` line 118

### Debug Mode:
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Notes

- **Weather Cache**: 6-hour cache to reduce API calls
- **Batch Processing**: Process multiple buildings efficiently
- **Memory Usage**: Lightweight design for hackathon deployment
- **Response Time**: <2 seconds for typical requests

## Future Enhancements

- Machine learning integration with XGBoost models
- Real-time Bosch dataset streaming
- Mobile app notifications for weather alerts
- Multi-campus support
- Advanced gamification with leaderboards

---

**Implementation Time**: 1-2 hours  
**Brownie Points**: High impact sustainability + real-time features  
**Tech Stack**: Python, Flask, Open-Meteo API, European Environment Agency data
