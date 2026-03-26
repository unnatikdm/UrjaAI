import pandas as pd
import numpy as np
import json
from datetime import datetime

# Configuration
PEAK_PERCENTILE = 0.85  # Threshold to define a "peak"
PEAK_RATE = 0.20        # $/kWh
OFF_PEAK_RATE = 0.10    # $/kWh
SHIFT_FRACTION = 0.20   # How much of the peak load we can shift (e.g. 20%)

def generate_recommendations(forecast_csv):
    """
    Analyzes forecast and generates load-shifting recommendations.
    """
    df = pd.read_csv(forecast_csv)
    df['forecast_time'] = pd.to_datetime(df['forecast_time'])
    
    # Calculate threshold
    threshold = df['predicted_kw'].quantile(PEAK_PERCENTILE)
    peaks = df[df['predicted_kw'] > threshold].copy()
    
    recommendations = []
    
    for idx, row in peaks.iterrows():
        peak_val = row['predicted_kw']
        time_str = row['forecast_time'].strftime('%H:00')
        date_str = row['forecast_time'].strftime('%Y-%m-%d')
        
        # Calculate potential savings
        # Shift 20% to an off-peak period (e.g. 3 AM)
        shift_amount = peak_val * SHIFT_FRACTION
        peak_cost = shift_amount * PEAK_RATE
        off_peak_cost = shift_amount * OFF_PEAK_RATE
        savings = peak_cost - off_peak_cost
        
        rec = {
            "id": f"REC_{idx}",
            "type": "Peak Shifting",
            "impact": "High",
            "description": f"Anticipated peak of {peak_val:.2f} kW at {time_str} ({date_str}). Suggest shifting {shift_amount:.2f} kW (20%) of non-critical load (HVAC pre-cooling/Charging) to off-peak hours (02:00-05:00).",
            "justification": f"This peak is {((peak_val - threshold)/threshold)*100:.1f}% higher than your operational average. Temperature at this hour is forecasted at {row['temperature']:.1f}°C, which is a primary driver for increased HVAC demand.",
            "estimated_savings_usd": round(savings, 2),
            "suggested_time_window": "02:00 AM - 05:00 AM",
            "action": f"Automate HVAC pre-cooling at {date_str} 03:00"
        }
        recommendations.append(rec)
    
    return recommendations

if __name__ == "__main__":
    forecast_file = "../FINAL_ENSEMBLE_FORECAST.csv"
    try:
        recs = generate_recommendations(forecast_file)
        print(f"--- UrjaAI Optimization Recommendations ---")
        print(f"Total Recommendations: {len(recs)}\n")
        
        for r in recs[:5]: # Show first 5
            print(f"[{r['impact']}] {r['description']}")
            print(f"Est. Savings: ${r['estimated_savings_usd']}")
            print("-" * 50)
            
        with open("recommendations.json", "w") as f:
            json.dump(recs, f, indent=4)
        print(f"\nFull list saved to optimization/recommendations.json")
        
    except FileNotFoundError:
        print("Error: FINAL_ENSEMBLE_FORECAST.csv not found. Run run_final_forecast.py first.")
