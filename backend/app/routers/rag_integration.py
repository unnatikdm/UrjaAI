from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.auth import get_current_user
from app.models.user import User
from app.services.rag.rag_browniepoint1_integration import rag_browniepoint1_service

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
    """Initialize RAG-Browniepoint1 integration on startup"""
    try:
        rag_browniepoint1_service.initialize()
    except Exception as e:
        print(f"[RAG Router] Error initializing RAG-Browniepoint1 integration: {e}")

@router.post("/deep-recommendations", response_model=List[DeepRecommendation])
def get_deep_recommendations(req: DeepRecommendationRequest, _: User = Depends(get_current_user)):
    """
    Get deep recommendations enriched with RAG insights using browniepoint1 EnergyOptimizer.
    
    This endpoint combines the browniepoint1 EnergyOptimizer model with the 
    recommendation_system RAG pipeline to provide contextual, intelligent 
    energy optimization recommendations.
    """
    try:
        # Generate deep recommendations with RAG enrichment
        recommendations = rag_browniepoint1_service.generate_deep_recommendations(
            building_id=req.building_id,
            temperature_offset=req.temperature_offset,
            occupancy_multiplier=req.occupancy_multiplier
        )
        
        # Convert to response model
        response_recs = []
        for rec in recommendations:
            response_recs.append(DeepRecommendation(
                action=rec['action'],
                savings_kwh=rec['savings_kwh'],
                savings_cost_inr=rec['savings_cost_inr'],
                priority=rec['priority'],
                reason=rec['reason'],
                is_enriched=rec.get('is_enriched', False),
                sources=rec.get('sources', [])
            ))
        
        return response_recs
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep analysis failed: {str(e)}")

@router.get("/status")
def get_rag_status():
    """Get status of RAG-Browniepoint1 integration service"""
    return rag_browniepoint1_service.get_system_status()

class ChatRequest(BaseModel):
    recommendation: Dict[str, Any]
    message: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    relevant_docs_count: int

@router.post("/chat", response_model=ChatResponse)
def chat_about_recommendation(req: ChatRequest, _: User = Depends(get_current_user)):
    """
    Chat with the AI about a specific recommendation.
    
    Ask questions like:
    - "What if I increase temperature by 3°C?"
    - "How much will this save me?"
    - "Why is this recommended for night time?"
    - "What happens if weather changes?"
    
    The AI uses the RAG pipeline to provide contextual answers based on
    the knowledge base, weather patterns, and historical data.
    """
    try:
        result = rag_browniepoint1_service.chat_about_recommendation(
            recommendation=req.recommendation,
            user_message=req.message,
            chat_history=req.chat_history or []
        )
        return ChatResponse(**result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@router.get("/knowledge-base/documents")
def get_knowledge_base_documents(_: User = Depends(get_current_user)):
    """Get all documents from the knowledge base"""
    try:
        documents = getattr(rag_browniepoint1_service, 'documents', [])
        return {
            "document_count": len(documents),
            "documents": documents[:10]  # Return first 10 for preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")
