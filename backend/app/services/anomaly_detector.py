import os
import pandas as pd
import numpy as np
import pickle
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import root_mean_squared_error, r2_score

from app.services.iblend_data_pipeline import IBlendDataPipeline

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

class AnomalyDetectorTrainer:
    def __init__(self):
        self.pipeline = IBlendDataPipeline()
        self.model = None
        self.encoder_cache = {}
        self.thresholds = {}
        os.makedirs(MODELS_DIR, exist_ok=True)
        
    def prepare_data(self):
        """Loads and pre-processes I-BLEND engineered features"""
        df = self.pipeline.process_all_buildings()
        
        if df.empty:
            raise ValueError("I-BLEND pipeline returned empty dataframe.")
            
        print(f"Loaded {len(df)} records for training.")
        
        # Categorical Encoding
        for col in ['building_id', 'building_type', 'day_type', 'description']:
            le = LabelEncoder()
            df[f"{col}_encoded"] = le.fit_transform(df[col].astype(str))
            self.encoder_cache[col] = le
            
        # Select Features
        features = [
            'capacity', 'occupancy_rate', 'hour', 'day_of_week', 'month', 'is_weekend',
            'is_holiday', 'is_exam', 'is_break', 'building_type_encoded'
        ]
        
        # In a real scenario we use weather, lags:
        # lag_1h, lag_24h, rolling_mean_24h are great predictors
        if 'lag_1h' in df.columns: features.append('lag_1h')
        if 'lag_24h' in df.columns: features.append('lag_24h')
        if 'rolling_mean_24h' in df.columns: features.append('rolling_mean_24h')
            
        X = df[features]
        y = df['power_kw']
        
        return X, y, df

    def train_model(self):
        """Trains XGBoost Model to learn 'expected_energy' from schedule patterns"""
        print("Training Expected Energy Model...")
        X, y, df = self.prepare_data()
        
        # Train-Test Split (Chronological for time-series typically, using random for mock simplicity)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = xgb.XGBRegressor(
            n_estimators=100, 
            learning_rate=0.1, 
            max_depth=5, 
            random_state=42
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        preds = self.model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        print(f"Model Training Complete. RMSE: {rmse:.2f}, R2: {r2:.2f}")
        
        # Save Model and Encoders
        self.model.save_model(os.path.join(MODELS_DIR, "expected_energy_xgb.json"))
        with open(os.path.join(MODELS_DIR, "anomaly_encoders.pkl"), "wb") as f:
            pickle.dump(self.encoder_cache, f)
            
        # Move to threshold generation
        self.generate_thresholds(df)

    def generate_thresholds(self, df):
        """Calculates dynamic residual threshold constraints"""
        print("Generating Anomaly Thresholds...")
        X = df[[c for c in df.columns if "_encoded" in c or c in ['capacity', 'occupancy_rate', 'hour', 'day_of_week', 'month', 'is_weekend', 'is_holiday', 'is_exam', 'is_break', 'lag_1h', 'lag_24h', 'rolling_mean_24h']]]
        
        # Filter purely features
        features = self.model.feature_names_in_
        X_clean = X[features]
        
        # Get residuals
        df['expected_power'] = self.model.predict(X_clean)
        df['residual'] = df['power_kw'] - df['expected_power']
        
        # Create grouped contexts mapping building type to schedule block
        contexts = df.groupby(['building_type', 'day_type'])
        
        for name, group in contexts:
            b_type, day_t = name
            
            mean_res = group['residual'].mean()
            std_res = group['residual'].std()
            
            # Formulate strictness depending on context
            if day_t == "holiday":
                sigma_multiplier = 2.5
            elif "exam" in day_t.lower() and b_type == "lecture":
                sigma_multiplier = 3.5  # High variability during tests
            elif day_t == "break" and b_type == "dorm":
                sigma_multiplier = 2.0  # Consistently empty, strict flag
            else:
                sigma_multiplier = 3.0  # Default 3 sigma
                
            upper_thresh = mean_res + (sigma_multiplier * std_res)
            lower_thresh = mean_res - (sigma_multiplier * std_res)
            
            # String key for dictionary store
            key = f"{b_type}_{day_t}"
            self.thresholds[key] = {
                "mean_residual": float(mean_res),
                "std_residual": float(std_res),
                "sigma_multiplier": sigma_multiplier,
                "upper_threshold": float(upper_thresh),
                "lower_threshold": float(lower_thresh)
            }
            
        print(f"Generated {len(self.thresholds)} threshold profiles.")
        
        # Save thresholds
        import json
        with open(os.path.join(MODELS_DIR, "anomaly_thresholds.json"), "w") as f:
             json.dump(self.thresholds, f, indent=4)
             
if __name__ == "__main__":
    trainer = AnomalyDetectorTrainer()
    trainer.train_model()
