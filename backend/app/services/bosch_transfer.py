import os
import json
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from datetime import datetime

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

class BoschAnomalyTransfer:
    def __init__(self):
        self.model = xgb.XGBRegressor()
        self.model.load_model(os.path.join(MODELS_DIR, "expected_energy_xgb.json"))
        
        with open(os.path.join(MODELS_DIR, "anomaly_thresholds.json"), "r") as f:
            self.iblend_thresholds = json.load(f)
            
        with open(os.path.join(MODELS_DIR, "anomaly_encoders.pkl"), "rb") as f:
            self.encoders = pickle.load(f)
            
        # Explainer for SHAP generic to the XGBoost Model
        self.explainer = shap.TreeExplainer(self.model)

    def map_bosch_to_iblend_context(self, bosch_type, timestamp):
        """Maps a Bosch building and Hungarian timestamp to an I-BLEND engineered equivalent"""
        # Map Building Type
        b_type_mapping = {
            "Lecture Hall": "lecture",
            "Library": "library",
            "Dormitory": "dorm",
            "Office": "lecture",  # Office closely aligns with Academic lecture scheduling
        }
        
        target_b_type = b_type_mapping.get(bosch_type, "lecture")
        
        # Determine Budapest Academic Calendar (simplified mock logic for 2025)
        # E.g. Jan 1 = Holiday, Mar 15 = National Holiday, May = Exams
        ts = pd.to_datetime(timestamp) if isinstance(timestamp, str) else timestamp
        
        is_holiday = 0
        is_exam = 0
        is_break = 0
        day_type = "normal"
        
        if (ts.month == 1 and ts.day == 1) or (ts.month == 3 and ts.day == 15):
             is_holiday = 1
             day_type = "holiday"
        elif ts.month == 5 or ts.month == 12:  # Typical European exam months
             is_exam = 1
             day_type = "exam_period"
        elif ts.month == 7 or ts.month == 8:
             is_break = 1
             day_type = "break"
             
        # Mocking an occupancy rate assumption given it's Bosch (no sensors)
        expected_occ_rate = 0.8 if (9 <= ts.hour <= 17 and not is_weekend) else 0.1
        if is_break or is_holiday: expected_occ_rate *= 0.2
        
        return {
             "building_type_mapped": target_b_type,
             "day_type": day_type,
             "is_holiday": is_holiday,
             "is_exam": is_exam,
             "is_break": is_break,
             "expected_occupancy_rate": expected_occ_rate
        }

    def detect_anomaly(self, building_id, building_type, timestamp, actual_consumption):
        """Processes a live Bosch ping and evaluates anomaly status via I-BLEND constraints"""
        ts = pd.to_datetime(timestamp)
        context = self.map_bosch_to_iblend_context(building_type, ts)
        
        # Format payload for XGBoost Model using the cached label encoders
        try:
             b_encoded = self.encoders['building_type'].transform([context["building_type_mapped"]])[0]
        except:
             b_encoded = 0 # default fallback
             
        feature_dict = {
            'capacity': 1000, # Mock baseline
            'occupancy_rate': context["expected_occupancy_rate"],
            'hour': ts.hour,
            'day_of_week': ts.dayofweek,
            'month': ts.month,
            'is_weekend': 1 if ts.dayofweek >= 5 else 0,
            'is_holiday': context["is_holiday"],
            'is_exam': context["is_exam"],
            'is_break': context["is_break"],
            'building_type_encoded': b_encoded
        }
        
        df = pd.DataFrame([feature_dict])
        
        # Ensure exact column match with training (pads missing lags)
        expected_cols = self.model.feature_names_in_
        for c in expected_cols:
             if c not in df.columns:
                 df[c] = 0.0 # Pad naive missing rolling features
                 
        df = df[expected_cols]
        expected_energy = self.model.predict(df)[0]
        
        residual = actual_consumption - expected_energy
        
        # Load I-BLEND mapped threshold
        t_key = f'{context["building_type_mapped"]}_{context["day_type"]}'
        if t_key not in self.iblend_thresholds:
             t_key = f'{context["building_type_mapped"]}_normal' # fallback
             
        t_data = self.iblend_thresholds.get(t_key, {
             "mean_residual": 0.0, "std_residual": 10.0, "sigma_multiplier": 3.0,
             "upper_threshold": 30.0, "lower_threshold": -30.0
        })
        
        is_anomaly = False
        anomaly_type = "None"
        severity = "low"
        
        if residual > t_data["upper_threshold"]:
             is_anomaly = True
             anomaly_type = "A" # Type A (Energy Too High)
             severity = "high" if residual > (t_data["upper_threshold"] * 1.5) else "medium"
        elif residual < t_data["lower_threshold"] and actual_consumption < (0.1 * expected_energy):
             is_anomaly = True
             anomaly_type = "B" # Type B (Meter Issue/Comms)
             severity = "high"
        elif context["expected_occupancy_rate"] > 0.7 and actual_consumption < (0.3 * expected_energy):
             is_anomaly = True
             anomaly_type = "C" # Schedule mismatch (High expected occ, no energy = empty when assumed full)
             severity = "medium"

        response = {
             "is_anomaly": bool(is_anomaly),
             "anomaly_type": anomaly_type,
             "severity": severity,
             "expected": float(expected_energy),
             "deviation": float(residual),
             "deviation_percent": float((residual / expected_energy) * 100) if expected_energy > 0 else 0.0,
             "threshold_used": float(t_data["upper_threshold"]),
             "explanation": "",
             "shap_values": {}
        }
        
        # Only inject SHAP if anomaly to speed up processing
        if is_anomaly:
             shap_vals = self.explainer(df).values[0]
             # Zip feature names and their absolute sum impact
             impacts = sorted(zip(expected_cols, shap_vals), key=lambda x: abs(x[1]), reverse=True)
             
             top_features = []
             for f_name, val in impacts[:3]:
                  modifier = "+" if val >= 0 else ""
                  top_features.append(f"{f_name}: {modifier}{val:.1f}")
                  
             response["shap_values"] = top_features
             response["explanation"] = f"Energy {response['deviation_percent']:.1f}% above expected. Main factors: " + ", ".join(top_features)
             
        return response

if __name__ == "__main__":
     transfer = BoschAnomalyTransfer()
     # Mock Sunday test
     import pandas as pd
     flag = transfer.detect_anomaly("Bosch_A", "Lecture Hall", "2025-03-16T02:00:00", 85.3)
     print(json.dumps(flag, indent=2))
