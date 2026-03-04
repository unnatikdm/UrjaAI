import joblib
import pandas as pd
import numpy as np
import shap
import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time_forecasting.ensemble_training import load_and_merge, engineer_features

def explain_prediction(target_idx=0):
    print(f"--- UrjaAI Local Prediction Explainer ---")
    
    # 1. Setup
    df = load_and_merge()
    df = engineer_features(df)
    
    n = len(df)
    test_df = df.iloc[int(n*0.9):] # Last 10%
    
    features = joblib.load('time_forecasting/ensemble_features.joblib')
    scaler = joblib.load('time_forecasting/ensemble_scaler.joblib')
    model = joblib.load('time_forecasting/ensemble_xgb.joblib')
    
    # Select specific instance to explain
    X_target = test_df[features].iloc[target_idx:target_idx+1]
    X_target_scaled = scaler.transform(X_target)
    
    prediction = model.predict(X_target_scaled)[0]
    avg_power = test_df['data'].mean()
    
    # 2. SHAP Explanation
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_target_scaled)[0]
    expected_value = explainer.expected_value
    
    # 3. Create Text Summary
    impacts = []
    for i, feature_name in enumerate(features):
        impacts.append({
            "feature": feature_name,
            "value": X_target.iloc[0][feature_name],
            "shap_impact": shap_values[i]
        })
    
    # Sort by absolute impact
    impacts = sorted(impacts, key=lambda x: abs(x['shap_impact']), reverse=True)
    
    print(f"\nTime: {X_target.index[0]}")
    print(f"Predicted Power: {prediction:.2f} kW")
    print(f"Historical Average: {avg_power:.2f} kW")
    print(f"Deviation from Baseline: {((prediction - avg_power)/avg_power)*100:+.1f}%")
    
    print("\n--- Why this forecast? ---")
    top_pos = [i for i in impacts if i['shap_impact'] > 0.01][:3]
    top_neg = [i for i in impacts if i['shap_impact'] < -0.01][:3]
    
    if top_pos:
        print("Increasing Drivers:")
        for i in top_pos:
            direction = "High" if i['shap_impact'] > 0 else "Low"
            print(f"  • {i['feature']} ({i['value']:.1f}): +{i['shap_impact']:.3f} kW")
            
    if top_neg:
        print("Decreasing Drivers:")
        for i in top_neg:
            print(f"  • {i['feature']} ({i['value']:.1f}): {i['shap_impact']:.3f} kW")

if __name__ == "__main__":
    # Explain the latest prediction in the test set
    explain_prediction(target_idx=-1)
