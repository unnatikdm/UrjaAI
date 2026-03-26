from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.auth import get_current_user
from app.models.user import User
from app.services.rag.rag_browniepoint1_integration import rag_browniepoint1_service
from app.services.enhanced_recommendations import (
    enhanced_recommendation_engine,
    EnergyPricingService,
    PhysicalModelCalculator,
    BenchmarkService
)

router = APIRouter(prefix="/rag", tags=["RAG"])

# Feedback storage (in production, use database)
recommendation_feedback = []

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

class EnhancedChatRequest(BaseModel):
    recommendation: Dict[str, Any]
    message: str
    chat_history: Optional[List[Dict[str, str]]] = []
    building_id: Optional[str] = None
    use_dynamic_calculations: bool = True

class EnhancedChatResponse(BaseModel):
    response: str
    sources: List[str]
    relevant_docs_count: int
    calculation_result: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    recommendation_id: str
    building_id: str
    was_helpful: bool
    feedback_text: Optional[str] = None
    actual_savings_kwh: Optional[float] = None
    rating: Optional[int] = None  # 1-5

class WhatIfRequest(BaseModel):
    building_id: str
    current_setpoint: float
    proposed_setpoint: float
    outdoor_temp: float
    occupancy_count: int
    duration_hours: float = 3.0
    current_rate: Optional[float] = None

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

@router.post("/chat", response_model=EnhancedChatResponse)
def chat_about_recommendation(req: EnhancedChatRequest, _: User = Depends(get_current_user)):
    """
    Enhanced chat with dynamic calculations and real-time context.
    
    Ask questions like:
    - "What if I increase temperature by 3°C?" → Gets real calculation
    - "How much will this save me?" → Includes benchmarks and annual projections
    - "Why is this recommended for night time?" → Weather context
    - "What's the carbon impact?" → CO2 calculations
    """
    try:
        # First get base response from RAG
        result = rag_browniepoint1_service.chat_about_recommendation(
            recommendation=req.recommendation,
            user_message=req.message,
            chat_history=req.chat_history or []
        )
        
        calculation_result = None
        
        # Add dynamic calculations if enabled
        if req.use_dynamic_calculations:
            msg_lower = req.message.lower()
            
            # Check for what-if temperature questions
            if any(phrase in msg_lower for phrase in ['what if', 'what happens', 'suppose']) and \
               any(word in msg_lower for word in ['temperature', 'temp', 'setpoint', 'degree', '°c']):
                
                # Extract numbers from message
                import re
                numbers = re.findall(r'(\d+\.?\d*)', req.message)
                
                if numbers:
                    temp_change = float(numbers[0])
                    direction = -1 if any(word in msg_lower for word in ['decrease', 'lower', 'reduce', 'down']) else 1
                    
                    # Use physical model
                    calculator = PhysicalModelCalculator()
                    outdoor_temp = 32  # Default or get from weather API
                    occupancy = 50     # Default or get from occupancy service
                    
                    impact = calculator.calculate_setpoint_impact(
                        current_setpoint=24,
                        new_setpoint=24 + (direction * temp_change),
                        outdoor_temp=outdoor_temp,
                        occupancy_count=occupancy,
                        duration_hours=3
                    )
                    
                    # Add pricing
                    pricing = EnergyPricingService()
                    cost_saved = impact['energy_saved_kwh'] * pricing.get_current_rate()
                    
                    calculation_result = {
                        'type': 'temperature_impact',
                        'impact': impact,
                        'cost_saved_inr': round(cost_saved, 2),
                        'note': f'Calculation based on {outdoor_temp}°C outdoor temp, {occupancy} people, 3-hour duration'
                    }
            
            # Check for carbon/CO2 questions
            if any(word in msg_lower for word in ['co2', 'carbon', 'environment', 'green']):
                savings_kwh = req.recommendation.get('savings_kwh', 0.5)
                benchmarks = BenchmarkService()
                
                calculation_result = {
                    'type': 'carbon_impact',
                    'co2_saved_kg': round(savings_kwh * 0.85, 2),
                    'trees_equivalent': round(savings_kwh * 0.85 / 22, 2),
                    'car_km_avoided': int(savings_kwh * 0.85 / 0.12),
                    'annual_projection': {
                        'co2_saved_kg': round(savings_kwh * 365 * 0.85, 1),
                        'trees_equivalent': round(savings_kwh * 365 * 0.85 / 22, 1)
                    }
                }
            
            # Check for savings/money questions with detailed breakdown
            if any(word in msg_lower for word in ['save', 'cost', 'money', 'price', 'rs', 'inr', '₹']):
                savings_kwh = req.recommendation.get('savings_kwh', 0)
                
                if savings_kwh > 0:
                    pricing = EnergyPricingService()
                    
                    # Calculate with different rates
                    peak_savings = savings_kwh * pricing.peak_rate
                    offpeak_savings = savings_kwh * pricing.off_peak_rate
                    
                    # Demand charge savings if applicable
                    demand_savings = pricing.calculate_demand_savings(0.5)  # Assume 0.5kW reduction
                    
                    calculation_result = {
                        'type': 'detailed_savings',
                        'per_action': {
                            'kwh': savings_kwh,
                            'peak_rate_savings': round(peak_savings, 2),
                            'offpeak_rate_savings': round(offpeak_savings, 2),
                            'avg_savings': round((peak_savings + offpeak_savings) / 2, 2)
                        },
                        'monthly': {
                            'energy_savings': round(peak_savings * 20, 2),  # ~20 days
                            'demand_savings': demand_savings['monthly_demand_savings'],
                            'total': round(peak_savings * 20 + demand_savings['monthly_demand_savings'], 2)
                        },
                        'annual': {
                            'energy_savings': round(peak_savings * 20 * 12, 2),
                            'demand_savings': demand_savings['annual_demand_savings'],
                            'total': round(peak_savings * 20 * 12 + demand_savings['annual_demand_savings'], 2)
                        }
                    }
        
        # Enhance response with calculation if available
        if calculation_result:
            enhanced_response = _enhance_response_with_calculation(result['response'], calculation_result)
            result['response'] = enhanced_response
            result['calculation_result'] = calculation_result
        
        return EnhancedChatResponse(**result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")


def _enhance_response_with_calculation(base_response: str, calc: Dict) -> str:
    """Add calculation details to response"""
    
    if calc['type'] == 'temperature_impact':
        impact = calc['impact']
        return f"""**Temperature Impact Calculation:**

{base_response}

📊 **Detailed Calculation:**
• Energy change: {impact['energy_saved_kwh']:+.3f} kWh
• Peak load reduction: {impact['peak_load_reduction_kw']:.3f} kW
• Cost impact: ₹{calc['cost_saved_inr']:.2f}
• Efficiency improvement: {impact['percentage_reduction']:.1f}%

_{calc['note']}_"""
    
    elif calc['type'] == 'carbon_impact':
        return f"""**Environmental Impact:**

{base_response}

🌱 **Carbon Footprint:**
• Per action: {calc['co2_saved_kg']} kg CO₂ ({calc['co2_saved_kg']*1000:.0f}g)
• Equivalent to: {calc['trees_equivalent']} trees planted
• Car travel avoided: {calc['car_km_avoided']} km

📈 **Annual Impact (daily use):**
• {calc['annual_projection']['co2_saved_kg']} kg CO₂ saved/year
• = {calc['annual_projection']['trees_equivalent']} trees worth of CO₂ absorption"""
    
    elif calc['type'] == 'detailed_savings':
        return f"""**Detailed Savings Breakdown:**

{base_response}

💰 **Per Action:**
• Energy: {calc['per_action']['kwh']} kWh
• Peak rate savings: ₹{calc['per_action']['peak_rate_savings']}
• Off-peak savings: ₹{calc['per_action']['offpeak_rate_savings']}

📅 **Monthly (~20 weekdays):**
• Energy: ₹{calc['monthly']['energy_savings']}
• Demand charges: ₹{calc['monthly']['demand_savings']}
• **Total: ₹{calc['monthly']['total']}**

📆 **Annual:**
• Energy: ₹{calc['annual']['energy_savings']}
• Demand: ₹{calc['annual']['demand_savings']}
• **Total: ₹{calc['annual']['total']}**"""
    
    return base_response

@router.post("/feedback", response_model=Dict[str, Any])
def submit_recommendation_feedback(req: FeedbackRequest, _: User = Depends(get_current_user)):
    """
    Submit feedback on a recommendation for continuous learning.
    
    This helps improve future recommendations by tracking:
    - Whether the recommendation was helpful
    - Actual vs predicted savings
    - User ratings and comments
    """
    try:
        feedback_entry = {
            'id': f"feedback_{len(recommendation_feedback)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'recommendation_id': req.recommendation_id,
            'building_id': req.building_id,
            'was_helpful': req.was_helpful,
            'feedback_text': req.feedback_text,
            'actual_savings_kwh': req.actual_savings_kwh,
            'rating': req.rating,
            'timestamp': datetime.now().isoformat(),
            'user_id': _.id if _ else None
        }
        
        recommendation_feedback.append(feedback_entry)
        
        # In production: store to database, trigger model retraining if needed
        # For now, just log and return success
        logger = logging.getLogger(__name__)
        logger.info(f"Feedback received: {feedback_entry['id']} - Helpful: {req.was_helpful}")
        
        return {
            'status': 'success',
            'feedback_id': feedback_entry['id'],
            'message': 'Thank you for your feedback! This helps improve future recommendations.',
            'total_feedback_count': len(recommendation_feedback)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/feedback/stats")
def get_feedback_stats(_: User = Depends(get_current_user)):
    """Get aggregate feedback statistics"""
    if not recommendation_feedback:
        return {
            'total_feedback': 0,
            'message': 'No feedback collected yet'
        }
    
    helpful_count = sum(1 for f in recommendation_feedback if f['was_helpful'])
    avg_rating = sum(f['rating'] for f in recommendation_feedback if f['rating']) / \
                 len([f for f in recommendation_feedback if f['rating']])
    
    return {
        'total_feedback': len(recommendation_feedback),
        'helpful_percentage': round(helpful_count / len(recommendation_feedback) * 100, 1),
        'average_rating': round(avg_rating, 1) if avg_rating else None,
        'recent_feedback': recommendation_feedback[-5:]  # Last 5 entries
    }


@router.post("/what-if", response_model=Dict[str, Any])
def calculate_what_if_scenario(req: WhatIfRequest, _: User = Depends(get_current_user)):
    """
    Calculate impact of a hypothetical scenario dynamically.
    
    This allows users to explore "what-if" situations with real calculations:
    - "What if I change temperature by 2°C?"
    - "What if occupancy is 30% higher?"
    """
    try:
        calculator = PhysicalModelCalculator()
        pricing = EnergyPricingService()
        
        # Calculate energy impact
        impact = calculator.calculate_setpoint_impact(
            current_setpoint=req.current_setpoint,
            new_setpoint=req.proposed_setpoint,
            outdoor_temp=req.outdoor_temp,
            occupancy_count=req.occupancy_count,
            duration_hours=req.duration_hours
        )
        
        # Calculate cost impact
        rate = req.current_rate or pricing.get_current_rate()
        cost_saved = impact['energy_saved_kwh'] * rate
        
        # Calculate demand savings
        demand_savings = pricing.calculate_demand_savings(impact['peak_load_reduction_kw'])
        
        # Environmental impact
        co2_saved_kg = impact['energy_saved_kwh'] * 0.85
        
        return {
            'scenario': {
                'building_id': req.building_id,
                'current_setpoint': req.current_setpoint,
                'proposed_setpoint': req.proposed_setpoint,
                'change': f"{impact['setpoint_change']:+.1f}°C",
                'outdoor_temp': req.outdoor_temp,
                'occupancy_count': req.occupancy_count,
                'duration_hours': req.duration_hours
            },
            'impact': {
                'energy_saved_kwh': impact['energy_saved_kwh'],
                'percentage_reduction': impact['percentage_reduction'],
                'peak_load_reduction_kw': impact['peak_load_reduction_kw'],
                'cost_saved_inr': round(cost_saved, 2),
                'co2_saved_kg': round(co2_saved_kg, 3),
                'trees_equivalent': round(co2_saved_kg / 22, 3)
            },
            'demand_savings': demand_savings,
            'annual_projection': {
                'energy_saved_kwh': round(impact['energy_saved_kwh'] * 261, 1),  # Weekdays per year
                'cost_saved_inr': round(cost_saved * 261, 2),
                'co2_saved_kg': round(co2_saved_kg * 261, 1),
                'total_demand_savings': demand_savings['annual_demand_savings']
            },
            'pricing_used': {
                'rate_inr_per_kwh': rate,
                'peak_rate': pricing.peak_rate,
                'off_peak_rate': pricing.off_peak_rate
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


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
