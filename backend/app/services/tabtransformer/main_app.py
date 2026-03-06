from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
import os
import logging
from datetime import datetime
import uuid
import asyncio
from sqlalchemy import text

# Import all services
from tabtransformer_model import TabTransformerModel
from shap_service import SHAPExplainer
from gamification_api import (
    TrackActionRequest, TrackActionResponse, UserProgressResponse,
    LeaderboardResponse, BadgeCheckResponse, PointsSummaryResponse,
    add_gamification_routes, track_user_action, get_user_progress,
    get_leaderboard, check_user_badges, get_points_summary,
    get_available_badges, create_user, get_user_stats
)
from gamification_service import GamificationService
from database_models import DatabaseManager, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TabTransformer ML Platform",
    description="Complete ML platform with TabTransformer, SHAP explanations, and gamification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global instances
model = None
shap_explainer = None

# Request/Response models
class ComprehensivePredictionRequest(BaseModel):
    """Comprehensive prediction request with all features"""
    features: Dict[str, Any] = Field(..., description="Feature values for prediction")
    explain: bool = Field(default=False, description="Generate SHAP explanation")
    user_id: Optional[str] = Field(default=None, description="User ID for gamification")
    top_k_features: int = Field(default=10, description="Number of top features to show in explanation")

class ComprehensivePredictionResponse(BaseModel):
    """Comprehensive prediction response"""
    request_id: str
    prediction: int
    prediction_class: str
    probability: float
    confidence: str
    processing_time_ms: float
    explanation: Optional[Dict[str, Any]] = None
    gamification: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    shap_explainer_ready: bool
    database_connected: bool
    redis_connected: bool
    timestamp: str
    version: str

class SystemInfoResponse(BaseModel):
    """System information response"""
    model_info: Dict[str, Any]
    features: Dict[str, Any]
    badges_count: int
    system_stats: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    global model, shap_explainer
    
    try:
        logger.info("Starting TabTransformer ML Platform...")
        
        # Initialize model
        model = TabTransformerModel()
        model_path = os.path.join('models', 'tabtransformer_v1')
        
        if os.path.exists(model_path):
            model.load_model(model_path)
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.info("No existing model found. Training new model...")
            train_dataset, val_dataset, test_dataset = model.prepare_data()
            model.build_model()
            model.train_model(train_dataset, val_dataset)
            model.save_model()
            logger.info("New model trained and saved")
        
        # Initialize SHAP explainer
        try:
            shap_explainer = SHAPExplainer(model.model, model.pipeline)
            shap_explainer.initialize_explainer()
            logger.info("SHAP explainer initialized")
        except Exception as e:
            logger.warning(f"SHAP explainer initialization failed: {e}")
            shap_explainer = None
        
        # Test database connection
        try:
            db = DatabaseManager()
            session = db.get_session()
            session.execute(text("SELECT 1"))
            db.close_session(session)
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
        
        # Test Redis connection
        try:
            import redis
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        # Add gamification routes
        add_gamification_routes(app)
        
        logger.info("TabTransformer ML Platform started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize platform: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    # Check components
    model_loaded = model is not None and model.model is not None
    shap_ready = shap_explainer is not None
    db_connected = False
    redis_connected = False
    
    # Test database
    try:
        db = DatabaseManager()
        session = db.get_session()
        session.execute(text("SELECT 1"))
        db.close_session(session)
        db_connected = True
    except:
        pass
    
    # Test Redis
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        redis_connected = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        shap_explainer_ready=shap_ready,
        database_connected=db_connected,
        redis_connected=redis_connected,
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """Get comprehensive system information"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Model information
    model_info = {
        "model_type": "TabTransformer",
        "parameters": model.model.count_params(),
        "config": model.config,
        "target": model.pipeline.target_column
    }
    
    # Feature information
    features = {
        "categorical": model.pipeline.categorical_features,
        "numerical": model.pipeline.numerical_features,
        "total_features": len(model.pipeline.categorical_features) + len(model.pipeline.numerical_features)
    }
    
    # Badge information
    try:
        db = DatabaseManager()
        session = db.get_session()
        from database_models import Badge
        badges_count = session.query(Badge).filter(Badge.is_active == True).count()
        db.close_session(session)
    except:
        badges_count = 0
    
    # System stats
    system_stats = {
        "shap_ready": shap_explainer is not None,
        "database_ready": True,  # Assume true if we can query badges
        "model_path": os.path.join('models', 'tabtransformer_v1')
    }
    
    return SystemInfoResponse(
        model_info=model_info,
        features=features,
        badges_count=badges_count,
        system_stats=system_stats
    )

@app.post("/api/v1/predict/comprehensive", response_model=ComprehensivePredictionResponse)
async def comprehensive_predict(request: ComprehensivePredictionRequest, background_tasks: BackgroundTasks):
    """Comprehensive prediction with explanation and gamification"""
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
        prediction_class = "Has Insurance" if class_label == 1 else "No Insurance"
        
        # Generate explanation if requested
        explanation = None
        if request.explain and shap_explainer:
            try:
                explanation = shap_explainer.explain_instance(
                    request.features, 
                    top_k=request.top_k_features
                )
            except Exception as e:
                logger.warning(f"SHAP explanation failed: {e}")
                explanation = {"error": "Explanation generation failed"}
        
        # Track gamification if user_id provided
        gamification_result = None
        if request.user_id:
            try:
                from database_models import DatabaseManager
                db = DatabaseManager()
                gamification_service = GamificationService(db)
                
                action_data = {
                    "request_id": request_id,
                    "probability": probability,
                    "confidence": confidence,
                    "explanation_requested": request.explain
                }
                
                gamification_result = gamification_service.track_action(
                    user_id=request.user_id,
                    action_type="prediction",
                    action_data=action_data
                )
                
                # Track explanation as separate action
                if request.explain:
                    gamification_service.track_action(
                        user_id=request.user_id,
                        action_type="explanation",
                        action_data={"request_id": request_id}
                    )
                
                db.close_session(db)
                
            except Exception as e:
                logger.warning(f"Gamification tracking failed: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ComprehensivePredictionResponse(
            request_id=request_id,
            prediction=class_label,
            prediction_class=prediction_class,
            probability=probability,
            confidence=confidence,
            processing_time_ms=processing_time,
            explanation=explanation,
            gamification=gamification_result
        )
        
    except Exception as e:
        logger.error(f"Comprehensive prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/explain/waterfall")
async def generate_waterfall_explanation(
    features: Dict[str, Any],
    top_k: int = 10,
    user_id: Optional[str] = None
):
    """Generate detailed SHAP waterfall explanation"""
    if shap_explainer is None:
        raise HTTPException(status_code=503, detail="SHAP explainer not available")
    
    try:
        explanation = shap_explainer.explain_instance(features, top_k)
        
        # Track gamification if user_id provided
        if user_id:
            try:
                from database_models import DatabaseManager
                db = DatabaseManager()
                gamification_service = GamificationService(db)
                
                gamification_service.track_action(
                    user_id=user_id,
                    action_type="explanation",
                    action_data={"explanation_type": "waterfall", "top_k": top_k}
                )
                
                db.close_session(db)
            except Exception as e:
                logger.warning(f"Gamification tracking failed: {e}")
        
        return explanation
        
    except Exception as e:
        logger.error(f"Waterfall explanation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")

@app.post("/api/v1/explain/batch")
async def generate_batch_explanations(
    instances: List[Dict[str, Any]],
    top_k: int = 10,
    user_id: Optional[str] = None
):
    """Generate SHAP explanations for multiple instances"""
    if shap_explainer is None:
        raise HTTPException(status_code=503, detail="SHAP explainer not available")
    
    if len(instances) > 20:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 20 instances for explanations")
    
    try:
        explanations = shap_explainer.explain_batch(instances, top_k)
        
        # Track gamification if user_id provided
        if user_id:
            try:
                from database_models import DatabaseManager
                db = DatabaseManager()
                gamification_service = GamificationService(db)
                
                gamification_service.track_action(
                    user_id=user_id,
                    action_type="explanation",
                    action_data={"explanation_type": "batch", "batch_size": len(instances)}
                )
                
                db.close_session(db)
            except Exception as e:
                logger.warning(f"Gamification tracking failed: {e}")
        
        return {
            "request_id": str(uuid.uuid4()),
            "explanations": explanations,
            "total_processed": len(instances)
        }
        
    except Exception as e:
        logger.error(f"Batch explanation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch explanation failed: {str(e)}")

@app.get("/api/v1/features/summary")
async def get_feature_summary():
    """Get feature importance summary"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Generate sample instances for feature summary
        sample_data, _ = model.pipeline.prepare_data()
        sample_instances = sample_data.head(10).to_dict('records')
        
        if shap_explainer:
            summary = shap_explainer.get_feature_summary(sample_instances)
        else:
            # Basic feature summary without SHAP
            summary = {
                "categorical_features": model.pipeline.categorical_features,
                "numerical_features": model.pipeline.numerical_features,
                "feature_vocabularies": model.pipeline.feature_vocab,
                "message": "SHAP explainer not available - showing basic feature info"
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"Feature summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feature summary failed: {str(e)}")

# Legacy prediction endpoints for backward compatibility
@app.post("/api/v1/predict")
async def legacy_predict(request: dict, background_tasks: BackgroundTasks):
    """Legacy prediction endpoint"""
    # Convert to new format
    comprehensive_request = ComprehensivePredictionRequest(
        features=request.get("features", {}),
        explain=request.get("explain", False),
        user_id=request.get("user_id"),
        top_k_features=request.get("top_k_features", 10)
    )
    
    result = await comprehensive_predict(comprehensive_request, background_tasks)
    
    # Convert to legacy format
    legacy_response = {
        "request_id": result.request_id,
        "prediction": result.prediction,
        "prediction_class": result.prediction_class,
        "probability": result.probability,
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms
    }
    
    if result.explanation:
        legacy_response["explanation"] = result.explanation
    
    return legacy_response

@app.post("/api/v1/predict/batch")
async def legacy_batch_predict(request: dict, background_tasks: BackgroundTasks):
    """Legacy batch prediction endpoint"""
    instances = request.get("instances", [])
    user_id = request.get("user_id")
    
    if model is None or model.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = datetime.now()
    request_id = str(uuid.uuid4())
    
    try:
        # Make batch predictions
        predictions = model.predict_batch(instances)
        
        # Format predictions
        formatted_predictions = []
        for i, (class_label, probability) in enumerate(predictions):
            confidence = "high" if probability > 0.8 else "medium" if probability > 0.6 else "low"
            prediction_class = "Has Insurance" if class_label == 1 else "No Insurance"
            
            formatted_predictions.append({
                "instance_id": i,
                "prediction": class_label,
                "prediction_class": prediction_class,
                "probability": probability,
                "confidence": confidence
            })
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Track gamification if user_id provided
        if user_id:
            background_tasks.add_task(
                track_user_action,
                TrackActionRequest(
                    user_id=user_id,
                    action_type="batch_prediction",
                    action_data={
                        "request_id": request_id,
                        "batch_size": len(instances),
                        "avg_probability": sum(p[1] for p in predictions) / len(predictions)
                    }
                )
            )
        
        return {
            "request_id": request_id,
            "predictions": formatted_predictions,
            "total_processed": len(instances),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
