from fastapi import APIRouter, Depends, HTTPException
from app.services.rag.rag_service import rag_service, HAS_RAG_LIBS
from app.services.auth import get_current_user
from app.models.user import User
from app.routers.recommendations import _smart_recommendations
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/rag", tags=["RAG"])

class DeepRecommendationRequest(BaseModel):
    building_id: str
    temperature_offset: Optional[float] = 0.0
    occupancy_multiplier: Optional[float] = 1.0

class DeepRecommendation(BaseModel):
    action: str
    savings_kwh: float
    savings_cost_inr: float
    priority: str
    reason: str
    is_enriched: bool
    sources: List[str]

@router.on_event("startup")
async def startup_event():
    rag_service.initialize()

@router.post("/deep-recommendations", response_model=List[DeepRecommendation])
def get_deep_recommendations(req: DeepRecommendationRequest, _: User = Depends(get_current_user)):
    """
    Get recommendations enriched with RAG insights.
    """
    try:
        # 1. Get standard recommendations
        base_recs = _smart_recommendations(
            req.building_id,
            temperature_offset=req.temperature_offset if req.temperature_offset is not None else 0.0,
            occupancy_multiplier=req.occupancy_multiplier if req.occupancy_multiplier is not None else 1.0
        )
        
        # 2. Convert to dicts for enrichment
        enriched_recs = []
        for rec in base_recs:
            rec_dict = {
                "action": rec.action,
                "savings_kwh": rec.savings_kwh,
                "savings_cost_inr": rec.savings_cost_inr,
                "priority": rec.priority,
                "reason": rec.reason
            }
            
            # 3. Enrich with RAG
            try:
                enriched = rag_service.enrich_recommendation(rec_dict, req.building_id)
                enriched_recs.append(DeepRecommendation(**enriched))
            except Exception as e:
                # Fallback to base recommendation if enrichment fails
                print(f"RAG enrichment failed for {rec.action}: {e}")
                enriched_recs.append(DeepRecommendation(
                    **rec_dict,
                    is_enriched=False,
                    sources=[]
                ))
            
        return enriched_recs
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep analysis failed: {str(e)}")

@router.get("/status")
def get_rag_status():
    return {
        "initialized": rag_service.initialized,
        "document_count": len(rag_service.documents),
        "has_libs": HAS_RAG_LIBS if 'HAS_RAG_LIBS' in globals() else False
    }
