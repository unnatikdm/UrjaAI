"""
Model API with SHAP Explanations
Serves XGBoost model predictions and SHAP explanations for real data integration
"""

import os
import pickle
import pandas as pd
import numpy as np
import shap
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import joblib

# Initialize FastAPI app
app = FastAPI(
    title="Energy Model API",
    description="XGBoost model with SHAP explanations for energy predictions",
    version="1.0.0"
)

# Global model storage
model = None
shap_explainer = None
feature_columns = None
model_metadata = {}

# Data models
class PredictionRequest(BaseModel):
    building_id: str
    timestamp: str
    features: Dict[str, float]
    horizon_hours: int = 24

class PredictionResponse(BaseModel):
    prediction_id: str
    building_id: str
    timestamp: str
    predicted_energy_kwh: float
    confidence: float
    features_used: Dict[str, float]
    model_version: str
    created_at: str

class SHAPRequest(BaseModel):
    prediction_id: Optional[str] = None
    building_id: str
    timestamp: str
    features: Dict[str, float]

class SHAPResponse(BaseModel):
    prediction_id: str
    building_id: str
    timestamp: str
    shap_values: Dict[str, float]
    base_value: float
    feature_importance: List[Dict[str, Any]]
    explanation: str
    model_version: str

class WhatIfRequest(BaseModel):
    building_id: str
    timestamp: str
    original_features: Dict[str, float]
    modified_features: Dict[str, float]
    action_description: str

class WhatIfResponse(BaseModel):
    building_id: str
    timestamp: str
    action_description: str
    original_prediction: float
    modified_prediction: float
    difference: float
    percentage_change: float
    impact_analysis: str

def load_model():
    """Load the trained XGBoost model and initialize SHAP explainer"""
    global model, shap_explainer, feature_columns, model_metadata
    
    # Look for model files in various locations
    model_paths = [
        "../browniepoint2/models/xgboost_model.pkl",
        "../browniepoint2/tabtransformer_model.pkl",
        "models/xgboost_model.pkl",
        "models/tabtransformer_model.pkl"
    ]
    
    model_file = None
    for path in model_paths:
        if os.path.exists(path):
            model_file = path
            break
    
    if not model_file:
        print("Warning: No model file found. Creating mock model for demonstration.")
        create_mock_model()
        return
    
    try:
        # Load the model
        if model_file.endswith('.pkl'):
            model = joblib.load(model_file)
        else:
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
        
        # Initialize SHAP explainer
        shap_explainer = shap.TreeExplainer(model)
        
        # Load feature columns if available
        feature_file = model_file.replace('.pkl', '_features.json').replace('.joblib', '_features.json')
        if os.path.exists(feature_file):
            with open(feature_file, 'r') as f:
                feature_columns = json.load(f)
        else:
            # Default feature set for energy prediction
            feature_columns = [
                'temperature', 'humidity', 'occupancy', 'hour_of_day', 'day_of_week',
                'month', 'is_weekend', 'lag_1h', 'lag_24h', 'rolling_mean_24h'
            ]
        
        # Set model metadata
        model_metadata = {
            'model_type': 'XGBoost',
            'model_file': model_file,
            'feature_count': len(feature_columns),
            'model_version': 'v1.0',
            'training_date': datetime.now().isoformat(),
            'description': 'Energy consumption prediction model'
        }
        
        print(f"✅ Model loaded: {model_file}")
        print(f"✅ Features: {len(feature_columns)}")
        print(f"✅ SHAP explainer initialized")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Creating mock model for demonstration...")
        create_mock_model()

def create_mock_model():
    """Create a mock model for demonstration when real model is not available"""
    global model, shap_explainer, feature_columns, model_metadata
    
    # Create a simple mock model
    class MockModel:
        def predict(self, X):
            # Simple linear combination with some noise
            if isinstance(X, pd.DataFrame):
                X_array = X.values
            else:
                X_array = X
            
            # Mock energy prediction based on features
            base_consumption = 50
            temp_effect = X_array[:, 0] * 2 if X_array.shape[1] > 0 else 0
            occupancy_effect = X_array[:, 2] * 15 if X_array.shape[1] > 2 else 0
            noise = np.random.normal(0, 5, X_array.shape[0])
            
            return base_consumption + temp_effect + occupancy_effect + noise
        
        def predict_proba(self, X):
            # Not used for regression, but implement for compatibility
            predictions = self.predict(X)
            # Convert to binary probabilities (high/low consumption)
            probs = np.zeros((len(predictions), 2))
            probs[:, 0] = 1 / (1 + np.exp(-(predictions - 50) / 10))  # Low consumption
            probs[:, 1] = 1 - probs[:, 0]  # High consumption
            return probs
    
    model = MockModel()
    
    # Mock SHAP explainer
    class MockSHAPExplainer:
        def shap_values(self, X):
            if isinstance(X, pd.DataFrame):
                X_array = X.values
            else:
                X_array = X
            
            # Mock SHAP values (feature contributions)
            n_samples, n_features = X_array.shape
            shap_vals = np.random.normal(0, 5, (n_samples, n_features))
            
            # Make temperature and occupancy have higher impact
            if n_features > 0:
                shap_vals[:, 0] = X_array[:, 0] * 2  # Temperature effect
            if n_features > 2:
                shap_vals[:, 2] = X_array[:, 2] * 10  # Occupancy effect
            
            return shap_vals
        
        def expected_value(self):
            return 50.0  # Base energy consumption
    
    shap_explainer = MockSHAPExplainer()
    
    feature_columns = [
        'temperature', 'humidity', 'occupancy', 'hour_of_day', 'day_of_week',
        'month', 'is_weekend', 'lag_1h', 'lag_24h', 'rolling_mean_24h'
    ]
    
    model_metadata = {
        'model_type': 'MockXGBoost',
        'model_file': 'mock_model',
        'feature_count': len(feature_columns),
        'model_version': 'mock_v1.0',
        'training_date': datetime.now().isoformat(),
        'description': 'Mock energy consumption prediction model for demonstration'
    }
    
    print("✅ Mock model created for demonstration")

def prepare_features(features: Dict[str, float]) -> pd.DataFrame:
    """Prepare features for model prediction"""
    
    # Create feature vector with all required columns
    feature_vector = {}
    
    for col in feature_columns:
        if col in features:
            feature_vector[col] = features[col]
        else:
            # Add default values for missing features
            if col == 'hour_of_day':
                feature_vector[col] = datetime.now().hour
            elif col == 'day_of_week':
                feature_vector[col] = datetime.now().weekday()
            elif col == 'month':
                feature_vector[col] = datetime.now().month
            elif col == 'is_weekend':
                feature_vector[col] = 1 if datetime.now().weekday() >= 5 else 0
            elif col.startswith('lag_') or col.startswith('rolling_'):
                feature_vector[col] = features.get('energy_kwh', 50)  # Use current energy as lag
            else:
                feature_vector[col] = 0.0  # Default for other features
    
    return pd.DataFrame([feature_vector])

def generate_prediction_id() -> str:
    """Generate unique prediction ID"""
    import uuid
    return f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# Load model on startup
@app.on_event("startup")
async def startup_event():
    load_model()
    print("Energy Model API initialized")

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Energy Model API",
        "model_metadata": model_metadata,
        "features": feature_columns
    }

@app.get("/model/info")
async def get_model_info():
    """Get model information and metadata"""
    return {
        "model_metadata": model_metadata,
        "feature_columns": feature_columns,
        "model_loaded": model is not None,
        "shap_explainer_loaded": shap_explainer is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_energy(request: PredictionRequest):
    """Predict energy consumption for given features"""
    
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Prepare features
        features_df = prepare_features(request.features)
        
        # Make prediction
        prediction = model.predict(features_df)[0]
        
        # Generate prediction ID
        prediction_id = generate_prediction_id()
        
        # Calculate confidence (simplified)
        confidence = 0.85  # Mock confidence score
        
        response = PredictionResponse(
            prediction_id=prediction_id,
            building_id=request.building_id,
            timestamp=request.timestamp,
            predicted_energy_kwh=float(prediction),
            confidence=confidence,
            features_used=request.features,
            model_version=model_metadata['model_version'],
            created_at=datetime.now().isoformat()
        )
        
        # Store prediction for later SHAP explanation
        # In a real system, you'd store this in a database
        print(f"Prediction created: {prediction_id} for {request.building_id}")
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/explain", response_model=SHAPResponse)
async def explain_prediction(request: SHAPRequest):
    """Generate SHAP explanation for prediction"""
    
    if model is None or shap_explainer is None:
        raise HTTPException(status_code=500, detail="Model or SHAP explainer not loaded")
    
    try:
        # Prepare features
        features_df = prepare_features(request.features)
        
        # Get SHAP values
        shap_values = shap_explainer.shap_values(features_df)[0]
        base_value = shap_explainer.expected_value
        
        # Create feature importance mapping
        feature_importance = []
        for i, (feature, value) in enumerate(zip(feature_columns, shap_values)):
            feature_importance.append({
                'feature': feature,
                'shap_value': float(value),
                'feature_value': float(request.features.get(feature, 0)),
                'impact': 'positive' if value > 0 else 'negative'
            })
        
        # Sort by absolute SHAP value
        feature_importance.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        
        # Create explanation text
        top_features = feature_importance[:5]
        explanation_parts = []
        
        for feat in top_features:
            if abs(feat['shap_value']) > 0.1:
                direction = "increases" if feat['impact'] == 'positive' else "decreases"
                explanation_parts.append(
                    f"{feat['feature']} ({feat['shap_value']:+.1f}) {direction} energy consumption"
                )
        
        explanation = "Main factors: " + ", ".join(explanation_parts) if explanation_parts else "No significant factors identified"
        
        # Generate prediction ID if not provided
        prediction_id = request.prediction_id or generate_prediction_id()
        
        response = SHAPResponse(
            prediction_id=prediction_id,
            building_id=request.building_id,
            timestamp=request.timestamp,
            shap_values={feat: float(val) for feat, val in zip(feature_columns, shap_values)},
            base_value=float(base_value),
            feature_importance=feature_importance,
            explanation=explanation,
            model_version=model_metadata['model_version']
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SHAP explanation error: {str(e)}")

@app.post("/whatif", response_model=WhatIfResponse)
async def what_if_analysis(request: WhatIfRequest):
    """Perform what-if analysis by comparing original and modified scenarios"""
    
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Prepare original features
        original_df = prepare_features(request.original_features)
        original_prediction = float(model.predict(original_df)[0])
        
        # Prepare modified features
        modified_df = prepare_features(request.modified_features)
        modified_prediction = float(model.predict(modified_df)[0])
        
        # Calculate differences
        difference = modified_prediction - original_prediction
        percentage_change = (difference / original_prediction) * 100 if original_prediction != 0 else 0
        
        # Generate impact analysis
        if abs(difference) < 1:
            impact = "minimal impact"
        elif difference > 0:
            impact = f"increases energy consumption by {difference:.1f} kWh ({percentage_change:.1f}%)"
        else:
            impact = f"reduces energy consumption by {abs(difference):.1f} kWh ({abs(percentage_change):.1f}%)"
        
        response = WhatIfResponse(
            building_id=request.building_id,
            timestamp=request.timestamp,
            action_description=request.action_description,
            original_prediction=original_prediction,
            modified_prediction=modified_prediction,
            difference=difference,
            percentage_change=percentage_change,
            impact_analysis=impact
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis error: {str(e)}")

@app.get("/features")
async def get_features():
    """Get list of available features"""
    return {
        "features": feature_columns,
        "feature_count": len(feature_columns),
        "description": {
            "temperature": "Current temperature in Celsius",
            "humidity": "Relative humidity percentage",
            "occupancy": "Building occupancy percentage",
            "hour_of_day": "Hour of day (0-23)",
            "day_of_week": "Day of week (0-6)",
            "month": "Month (1-12)",
            "is_weekend": "Binary indicator for weekend",
            "lag_1h": "Energy consumption 1 hour ago",
            "lag_24h": "Energy consumption 24 hours ago",
            "rolling_mean_24h": "24-hour rolling average energy consumption"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "shap_explainer_loaded": shap_explainer is not None,
        "feature_count": len(feature_columns) if feature_columns else 0,
        "model_version": model_metadata.get('model_version', 'unknown')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
