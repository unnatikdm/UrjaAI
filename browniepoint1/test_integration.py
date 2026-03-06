import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from energy_optimizer import EnergyOptimizer

def test_weather_api():
    """Test weather API integration"""
    print("Testing Weather API...")
    
    try:
        optimizer = EnergyOptimizer()
        weather_data = optimizer.get_weather_forecast(48)
        
        if weather_data:
            print(f"✓ Weather data retrieved successfully")
            print(f"  - Temperature points: {len(weather_data.get('temperature', []))}")
            print(f"  - Current temp: {weather_data.get('temperature', [20])[0]:.1f}°C")
            print(f"  - Forecast hours: {len(weather_data.get('timestamps', []))}")
            return True
        else:
            print("✗ No weather data received")
            return False
            
    except Exception as e:
        print(f"✗ Weather API test failed: {e}")
        return False

def test_carbon_tracker():
    """Test carbon tracking functionality"""
    print("\nTesting Carbon Tracker...")
    
    try:
        optimizer = EnergyOptimizer()
        
        # Test with sample energy savings
        test_savings = [50, 150, 500, 1000]  # kWh
        
        for savings in test_savings:
            impact = optimizer.get_carbon_impact(savings)
            if impact:
                print(f"✓ {savings} kWh savings:")
                print(f"  - CO2 saved: {impact.get('co2_saved_kg', 0):.2f} kg")
                print(f"  - Trees equivalent: {impact.get('trees_equivalent', 0):.2f}")
                print(f"  - Car km avoided: {impact.get('car_km_avoided', 0):.2f}")
                print(f"  - Badge: {impact.get('badge_earned', {}).get('name', 'None')}")
            else:
                print(f"✗ Failed to calculate impact for {savings} kWh")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Carbon tracker test failed: {e}")
        return False

def test_weather_alerts():
    """Test weather alerts generation"""
    print("\nTesting Weather Alerts...")
    
    try:
        optimizer = EnergyOptimizer()
        alerts = optimizer.get_weather_alerts()
        
        print(f"✓ Weather alerts retrieved: {len(alerts)} alerts")
        
        for alert in alerts:
            print(f"  - {alert.get('type', 'Unknown')}: {alert.get('severity', 'Unknown')} severity")
            print(f"    {alert.get('message', 'No message')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Weather alerts test failed: {e}")
        return False

def test_energy_predictions():
    """Test energy consumption predictions"""
    print("\nTesting Energy Predictions...")
    
    try:
        optimizer = EnergyOptimizer()
        weather_data = optimizer.get_weather_forecast(48)
        
        if not weather_data:
            print("✗ No weather data available for predictions")
            return False
        
        buildings = ['A', 'B', 'C']
        
        for building_id in buildings:
            predictions = optimizer.predict_energy_consumption(building_id, weather_data)
            
            if predictions:
                print(f"✓ Building {building_id}: {len(predictions)} predictions")
                print(f"  - Average load: {sum(predictions)/len(predictions):.2f} kWh")
                print(f"  - Peak load: {max(predictions):.2f} kWh")
                print(f"  - Min load: {min(predictions):.2f} kWh")
            else:
                print(f"✗ Failed to generate predictions for building {building_id}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Energy predictions test failed: {e}")
        return False

def test_optimization_recommendations():
    """Test optimization recommendations"""
    print("\nTesting Optimization Recommendations...")
    
    try:
        optimizer = EnergyOptimizer()
        weather_data = optimizer.get_weather_forecast(48)
        
        if not weather_data:
            print("✗ No weather data available for recommendations")
            return False
        
        buildings = ['A', 'B', 'C']
        total_recommendations = 0
        
        for building_id in buildings:
            recommendations = optimizer.generate_optimization_recommendations(building_id, weather_data)
            total_recommendations += len(recommendations)
            
            print(f"✓ Building {building_id}: {len(recommendations)} recommendations")
            
            # Show top 3 recommendations
            for i, rec in enumerate(recommendations[:3]):
                print(f"  {i+1}. {rec.get('type', 'Unknown')} - {rec.get('priority', 'Unknown')} priority")
                print(f"     Savings: {rec.get('energy_savings_kwh', 0):.2f} kWh")
                print(f"     Action: {rec.get('action', 'No action')}")
        
        print(f"✓ Total recommendations generated: {total_recommendations}")
        return True
        
    except Exception as e:
        print(f"✗ Optimization recommendations test failed: {e}")
        return False

def test_dashboard_integration():
    """Test comprehensive dashboard integration"""
    print("\nTesting Dashboard Integration...")
    
    try:
        optimizer = EnergyOptimizer()
        buildings = ['A', 'B', 'C']
        
        dashboard = optimizer.get_comprehensive_dashboard_data(buildings)
        
        if dashboard:
            print("✓ Dashboard data generated successfully")
            print(f"  - Buildings processed: {len(dashboard.get('buildings', {}))}")
            print(f"  - Weather alerts: {len(dashboard.get('weather_alerts', []))}")
            print(f"  - Total energy savings: {dashboard.get('total_savings', {}).get('energy_kwh', 0):.2f} kWh")
            print(f"  - Total CO2 savings: {dashboard.get('total_savings', {}).get('co2_kg', 0):.2f} kg")
            
            # Show sample building data
            sample_building = list(dashboard.get('buildings', {}).keys())[0]
            building_data = dashboard['buildings'][sample_building]
            print(f"  - Sample building ({sample_building}):")
            print(f"    - Recommendations: {len(building_data.get('recommendations', []))}")
            print(f"    - Potential savings: {building_data.get('potential_savings', {}).get('energy_kwh', 0):.2f} kWh")
            
            return True
        else:
            print("✗ No dashboard data generated")
            return False
            
    except Exception as e:
        print(f"✗ Dashboard integration test failed: {e}")
        return False

def generate_sample_dashboard():
    """Generate a sample dashboard for demonstration"""
    print("\nGenerating Sample Dashboard...")
    
    try:
        optimizer = EnergyOptimizer()
        buildings = ['A', 'B', 'C']
        
        dashboard = optimizer.get_comprehensive_dashboard_data(buildings)
        
        # Save dashboard to JSON file
        with open('sample_dashboard.json', 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)
        
        print("✓ Sample dashboard saved to 'sample_dashboard.json'")
        
        # Print summary
        print("\n=== DASHBOARD SUMMARY ===")
        print(f"Generated: {dashboard.get('timestamp')}")
        print(f"Buildings: {list(dashboard.get('buildings', {}).keys())}")
        print(f"Weather Alerts: {len(dashboard.get('weather_alerts', []))}")
        
        total_energy = dashboard.get('total_savings', {}).get('energy_kwh', 0)
        total_co2 = dashboard.get('total_savings', {}).get('co2_kg', 0)
        
        print(f"Total Potential Savings:")
        print(f"  - Energy: {total_energy:.2f} kWh")
        print(f"  - CO2: {total_co2:.2f} kg")
        print(f"  - Trees equivalent: {total_co2/20:.2f} trees")
        print(f"  - Car km avoided: {total_co2*4:.2f} km")
        
        return True
        
    except Exception as e:
        print(f"✗ Sample dashboard generation failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("=" * 50)
    print("BROWNIE POINTS INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Weather API", test_weather_api),
        ("Carbon Tracker", test_carbon_tracker),
        ("Weather Alerts", test_weather_alerts),
        ("Energy Predictions", test_energy_predictions),
        ("Optimization Recommendations", test_optimization_recommendations),
        ("Dashboard Integration", test_dashboard_integration),
        ("Sample Dashboard Generation", generate_sample_dashboard)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your brownie points implementation is ready!")
    else:
        print("⚠️  Some tests failed. Check the API server and dependencies.")

if __name__ == "__main__":
    run_all_tests()
