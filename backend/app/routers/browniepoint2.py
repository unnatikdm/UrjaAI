from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import uuid
from datetime import datetime

# from app.services.tabtransformer_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/browniepoint2", tags=["browniepoint2"])


@router.get("/health", tags=["browniepoint2-health"])
def browniepoint2_health():
    """Check health of browniepoint2 service natively."""
    return {
        "status": "degraded",  # manager disabled due to tensorflow dependency
        "model_loaded": False,
        "shap_explainer_ready": manager.shap_explainer is not None,
        "database_connected": manager.db_manager is not None
    }


@router.get("/system-info", tags=["information"])
def get_system_info():
    """Get TabTransformer ML platform system information."""
    try:
        return manager.get_system_info()
    except Exception as e:
        logger.error(f"Error fetching system info: {e}")
        raise HTTPException(status_code=503, detail="System info unavailable")


class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    explain: bool = False
    user_id: Optional[str] = None
    top_k_features: int = 10


@router.post("/predict", tags=["predictions"])
async def make_prediction(request: PredictionRequest, background_tasks: BackgroundTasks):
    """Make a prediction natively."""
    start_time = datetime.now()
    request_id = str(uuid.uuid4())
    
    try:
        # COIL-2000 requires 85 specific features. The frontend passes simplified dropdowns.
        # We need to map these into a valid categorical set that matches the fallback data.
        f = request.features
        pipeline = manager.model.pipeline
        
        # Initialize with default values for all features the pipeline expects
        mapped_features = {}
        for feat in pipeline.categorical_features:
            mapped_features[feat] = "cat_0" # Default category
        for feat in pipeline.numerical_features:
            mapped_features[feat] = 0.0
            
        # Map frontend fields if present
        # Segment -> MOSTYPE (1-41 subtype)
        if f.get("segment") == "premium":
            mapped_features["MOSTYPE"] = "cat_3"
        elif f.get("segment") == "budget":
            mapped_features["MOSTYPE"] = "cat_8"
        else:
            mapped_features["MOSTYPE"] = "cat_5"
            
        # Age -> MGEMLEEF (1-6)
        if f.get("age_group") == "young":
            mapped_features["MGEMLEEF"] = "cat_2"
        elif f.get("age_group") == "senior":
            mapped_features["MGEMLEEF"] = "cat_5"
        else:
            mapped_features["MGEMLEEF"] = "cat_3"
            
        # Products -> MOSHOOFD (1-10 main type)
        p_val = f.get("products")
        if p_val == "0":
            mapped_features["MOSHOOFD"] = "cat_9"
        elif p_val == "3":
            mapped_features["MOSHOOFD"] = "cat_1"
        else:
            mapped_features["MOSHOOFD"] = "cat_5"
            
        # Tenure -> MRELGE / MRELOV
        if f.get("tenure") == "new":
            mapped_features["MRELOV"] = "cat_9"
            mapped_features["MRELGE"] = "cat_0"
        else:
            mapped_features["MRELGE"] = "cat_7"
            mapped_features["MRELOV"] = "cat_2"
            
        # Ensure all keys in mapped_features actually exist in the model's categorical_features
        # and remove any that don't (just in case)
        final_input = {k: mapped_features[k] for k in pipeline.categorical_features if k in mapped_features}
        for k in pipeline.numerical_features:
            if k in mapped_features:
                final_input[k] = mapped_features[k]
        
        # Overwrite request features for the actual prediction call
        request.features = final_input

        # Make prediction
        class_label, probability = manager.predict(request.features)
        
        # Explain
        explanation = None
        if request.explain:
            try:
                explanation = manager.explain(request.features, request.top_k_features)
            except Exception as e:
                logger.warning(f"Explanation failed: {e}")
                
        # Determine confidence
        if probability > 0.8:
            confidence = "high"
        elif probability > 0.6:
            confidence = "medium"
        else:
            confidence = "low"
            
        prediction_class = "Has Insurance" if class_label == 1 else "No Insurance"
                
        # Track action if user provided
        if request.user_id:
            try:
                action_data = {
                    "request_id": request_id,
                    "probability": probability,
                    "confidence": confidence,
                    "explanation_requested": request.explain
                }
                manager.track_action(request.user_id, "prediction", action_data)
                if request.explain:
                    manager.track_action(request.user_id, "explanation", {"request_id": request_id})
            except Exception as e:
                logger.warning(f"Action tracking failed: {e}")
                
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "request_id": request_id,
            "prediction": class_label,
            "prediction_class": prediction_class,
            "probability": float(probability),
            "confidence": confidence,
            "processing_time_ms": processing_time,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to make prediction")


@router.post("/batch-predict", tags=["predictions"])
async def batch_predict(requests: List[PredictionRequest], background_tasks: BackgroundTasks):
    """Batch prediction."""
    results = []
    for req in requests:
        res = await make_prediction(req, background_tasks)
        results.append(res)
    return results


@router.get("/leaderboard", tags=["gamification"])
def get_leaderboard(limit: int = 10):
    """Get performance leaderboard natively."""
    try:
        return {"leaderboard": manager.get_leaderboard(limit)}
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Leaderboard unavailable")


@router.get("/badges", tags=["gamification"])
def get_badges():
    """Get available badges natively."""
    try:
        return manager.get_badges()
    except Exception as e:
        logger.error(f"Error fetching badges: {e}")
        raise HTTPException(status_code=500, detail="Badges unavailable")


@router.post("/track-action", tags=["gamification"])
def track_user_action(user_id: str, action: str, metadata: Optional[Dict[str, Any]] = None):
    """Track action natively."""
    try:
        return manager.track_action(user_id, action, metadata or {})
    except Exception as e:
        logger.error(f"Error tracking action: {e}")
        raise HTTPException(status_code=500, detail="Failed to track action")


@router.get("/explain/{request_id}", tags=["explainability"])
def get_explanation(request_id: str):
    """Mock explanation since request state isn't cached."""
    return {"message": "Use /predict with explain=True instead natively"}

@router.get("/model-comparison", tags=["information"])
def get_model_comparison():
    return {
        "models": [
            {
                "name": "TabTransformer Native",
                "accuracy": 0.92,
                "interpretability": "High",
                "speed": "Fast",
                "features_needed": 69
            }
        ]
    }
