from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
import os
import logging
from datetime import datetime
import uuid

# Import model components
from tabtransformer_model import TabTransformerModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TabTransformer Inference API",
    description="High-performance ML inference with TabTransformer models",
    version="1.0.0"
)

# Global model instance
model = None

class PredictionRequest(BaseModel):
    """Request schema for predictions"""
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    explain: bool = Field(default=False, description="Whether to generate SHAP explanation")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")

class PredictionResponse(BaseModel):
    """Response schema for predictions"""
    request_id: str = Field(..., description="Unique request identifier")
    prediction: int = Field(..., description="Predicted class label")
    prediction_class: str = Field(..., description="Human-readable prediction")
    probability: float = Field(..., description="Prediction probability")
    confidence: str = Field(..., description="Confidence level")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    explanation: Optional[Dict[str, Any]] = Field(default=None, description="SHAP explanation if requested")

class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions"""
    instances: List[Dict[str, Any]] = Field(..., description="List of feature instances")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    request_id: str = Field(..., description="Unique request identifier")
    predictions: List[Dict[str, Any]] = Field(..., description="List of predictions")
    total_processed: int = Field(..., description="Total number of instances processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model
    try:
        model = TabTransformerModel()
        
        # Try to load existing model
        model_path = os.path.join('models', 'tabtransformer_v1')
        if os.path.exists(model_path):
            model.load_model(model_path)
            logger.info(f"Model loaded from {model_path}")
        else:
            # Train new model if none exists
            logger.info("No existing model found. Training new model...")
            train_dataset, val_dataset, test_dataset = model.prepare_data()
            model.build_model()
            model.train_model(train_dataset, val_dataset)
            model.save_model()
            logger.info("New model trained and saved")
        
        logger.info("TabTransformer inference service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None and model.model is not None,
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/model/info")
async def get_model_info():
    """Get model information"""
    if model is None or model.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_type": "TabTransformer",
        "parameters": model.model.count_params(),
        "config": model.config,
        "features": {
            "categorical": model.pipeline.categorical_features,
            "numerical": model.pipeline.numerical_features
        },
        "target": model.pipeline.target_column
    }

@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, background_tasks: BackgroundTasks):
    """Make single prediction"""
    if model is None or model.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = datetime.now()
    request_id = str(uuid.uuid4())
    
    try:
        # Make prediction
        class_label, probability = model.predict(request.features)
        
        # Determine confidence level
        if probability > 0.8:
            confidence = "high"
        elif probability > 0.6:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Convert to human-readable class
        prediction_class = ">50K" if class_label == 1 else "<=50K"
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Prepare response
        response = PredictionResponse(
            request_id=request_id,
            prediction=class_label,
            prediction_class=prediction_class,
            probability=probability,
            confidence=confidence,
            processing_time_ms=processing_time
        )
        
        # Add explanation if requested (placeholder for now)
        if request.explain:
            response.explanation = {
                "message": "SHAP explanation will be implemented in the next phase",
                "request_id": request_id
            }
        
        # Track user activity if user_id provided
        if request.user_id:
            background_tasks.add_task(
                track_user_activity,
                request.user_id,
                "prediction",
                {
                    "request_id": request_id,
                    "probability": probability,
                    "confidence": confidence,
                    "explanation_requested": request.explain
                }
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest, background_tasks: BackgroundTasks):
    """Make batch predictions"""
    if model is None or model.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(request.instances) > 100:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 100 instances")
    
    start_time = datetime.now()
    request_id = str(uuid.uuid4())
    
    try:
        # Make batch predictions
        predictions = model.predict_batch(request.instances)
        
        # Format predictions
        formatted_predictions = []
        for i, (class_label, probability) in enumerate(predictions):
            confidence = "high" if probability > 0.8 else "medium" if probability > 0.6 else "low"
            prediction_class = ">50K" if class_label == 1 else "<=50K"
            
            formatted_predictions.append({
                "instance_id": i,
                "prediction": class_label,
                "prediction_class": prediction_class,
                "probability": probability,
                "confidence": confidence
            })
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Track user activity if user_id provided
        if request.user_id:
            background_tasks.add_task(
                track_user_activity,
                request.user_id,
                "batch_prediction",
                {
                    "request_id": request_id,
                    "batch_size": len(request.instances),
                    "avg_probability": sum(p[1] for p in predictions) / len(predictions)
                }
            )
        
        return BatchPredictionResponse(
            request_id=request_id,
            predictions=formatted_predictions,
            total_processed=len(request.instances),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/api/v1/features")
async def get_features():
    """Get available features and their types"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "categorical_features": model.pipeline.categorical_features,
        "numerical_features": model.pipeline.numerical_features,
        "feature_vocabularies": model.pipeline.feature_vocab,
        "target_column": model.pipeline.target_column
    }

async def track_user_activity(user_id: str, action_type: str, action_data: Dict[str, Any]):
    """Track user activity for gamification (placeholder)"""
    # This will be implemented in the gamification phase
    logger.info(f"User activity tracked - User: {user_id}, Action: {action_type}, Data: {action_data}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
