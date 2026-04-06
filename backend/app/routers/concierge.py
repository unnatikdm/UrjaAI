"""
Urja Concierge - Floating AI Assistant API
Provides conversational RAG-powered queries about campus energy data
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

router = APIRouter(prefix="/concierge", tags=["concierge"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ConciergeChatRequest(BaseModel):
    message: str
    chat_history: List[ChatMessage] = []


class ConciergeChatResponse(BaseModel):
    response: str
    suggested_action: Optional[Dict[str, Any]] = None
    sources: List[str] = []
    timestamp: str


class ActionablePrompt(BaseModel):
    type: str  # 'alert', 'suggestion', 'info'
    text: str
    action: str
    priority: int = 1


# Mock campus data for intelligent responses
CAMPUS_DATA = {
    "library": {
        "co2_saved_today": 42.5,
        "co2_saved_weekly": 298,
        "efficiency": 94,
        "status": "optimal",
        "top_action": "Continue current AC schedule"
    },
    "admin_block": {
        "status": "critical",
        "hvac_above_baseline": 23,
        "issues": ["HVAC running 23% above baseline", "Peak occupancy during lunch"],
        "suggested_action": "Pre-cool during off-peak hours",
        "potential_savings": {"kwh": 12.5, "inr": 850}
    },
    "hall_a": {
        "current_occupancy": 35,
        "optimal_occupancy": 82,
        "classes_count": 3,
        "suggested_consolidation": 2,
        "potential_savings": {"kwh": 18, "inr": 1200}
    },
    "campus": {
        "weekly_efficiency_change": 12,
        "total_savings_kwh": 450,
        "total_savings_inr": 33750,
        "co2_saved_kg": 298,
        "trees_equivalent": 14.9,
        "weather_impact_tomorrow": 8
    }
}


def generate_contextual_response(message: str, history: List[ChatMessage]) -> ConciergeChatResponse:
    """Generate a contextual response based on the query"""
    lower_msg = message.lower()
    
    # CO2 / Carbon queries
    if any(word in lower_msg for word in ['co2', 'carbon', 'saved', 'environment']):
        data = CAMPUS_DATA["library"]
        return ConciergeChatResponse(
            response=f"🌱 **Carbon Impact Update**\n\n"
                    f"Library has saved **{data['co2_saved_today']} kg CO₂** today "
                    f"(equivalent to planting **{data['co2_saved_today'] / 20:.1f} trees**)!\n\n"
                    f"📊 Weekly total: {data['co2_saved_weekly']} kg CO₂ saved\n"
                    f"📈 {data['efficiency']}% efficiency rating - {data['status'].title()}",
            suggested_action=None,
            sources=["Carbon Tracking Engine", "IoT Sensors"],
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Critical status / Admin block queries
    if any(word in lower_msg for word in ['critical', 'admin', 'status', 'alert', 'problem']):
        data = CAMPUS_DATA["admin_block"]
        return ConciergeChatResponse(
            response=f"🔴 **Admin Block Status Alert**\n\n"
                    f"Currently at **{data['status'].upper()}** due to:\n"
                    f"• HVAC running {data['hvac_above_baseline']}% above baseline\n"
                    f"• {data['issues'][1]}\n"
                    f"• Outdoor temp 4°C above normal\n\n"
                    f"💡 **Suggested Action**: {data['suggested_action']} "
                    f"(saves ~₹{data['potential_savings']['inr']}/day)",
            suggested_action={"label": "Apply Pre-cooling Plan", "type": "action"},
            sources=["Anomaly Detection System", "HVAC Sensors", "Weather API"],
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Summary / Week queries
    if any(word in lower_msg for word in ['summary', 'week', 'overview', '30-second', 'digest']):
        data = CAMPUS_DATA["campus"]
        return ConciergeChatResponse(
            response=f"📊 **30-Second Weekly Summary**\n\n"
                    f"✅ Campus was **{data['weekly_efficiency_change']}% more efficient** than last week\n"
                    f"🎯 Library AC optimization: Biggest win (+₹3,200 savings)\n"
                    f"⚠️ Admin Block: Needs attention (Critical status)\n"
                    f"🌡️ Weather factor: Hot spell increased demand {data['weather_impact_tomorrow']}%\n\n"
                    f"**Bottom line**: You're on track for a 15% monthly savings goal!",
            suggested_action=None,
            sources=["Weekly Analytics Engine"],
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Class consolidation / Hall A queries
    if any(word in lower_msg for word in ['consolidation', 'hall a', 'schedule', 'optimize classes']):
        data = CAMPUS_DATA["hall_a"]
        return ConciergeChatResponse(
            response=f"🎯 **Class Consolidation Plan for Hall A**\n\n"
                    f"I've analyzed occupancy patterns:\n\n"
                    f"📍 **Current**: {data['classes_count']} classes, {data['current_occupancy']}% avg occupancy\n"
                    f"📍 **Proposed**: {data['suggested_consolidation']} classes, {data['optimal_occupancy']}% occupancy\n\n"
                    f"**Savings**: ~₹{data['potential_savings']['inr']}/day\n"
                    f"**Comfort**: Maintained (better thermal mass)\n\n"
                    f"Shall I generate the full schedule optimization?",
            suggested_action={"label": "Generate Full Plan", "type": "action"},
            sources=["Occupancy Analytics", "Scheduling Engine"],
            timestamp=datetime.utcnow().isoformat()
        )
    
    # General query fallback
    data = CAMPUS_DATA["campus"]
    return ConciergeChatResponse(
        response=f"I understand you're asking about: \"{message}\".\n\n"
                f"💡 **Quick Stats**:\n"
                f"• Campus efficiency: 87% (up {data['weekly_efficiency_change']}% from last week)\n"
                f"• Top performer: Library Block\n"
                f"• Needs attention: Admin Block (Critical)\n"
                f"• Weather impact: +{data['weather_impact_tomorrow']}% demand expected tomorrow\n\n"
                f"Ask me about specific buildings, carbon savings, or action plans!",
        suggested_action=None,
        sources=["Energy Analytics Engine"],
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/chat", response_model=ConciergeChatResponse)
async def concierge_chat(request: ConciergeChatRequest):
    """
    Chat with Urja Concierge AI assistant.
    
    Accepts natural language queries about:
    - Carbon/CO2 impact by building
    - Anomaly status and critical alerts
    - Weekly summaries and trends
    - Class consolidation recommendations
    - General campus energy insights
    """
    try:
        response = generate_contextual_response(request.message, request.chat_history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concierge error: {str(e)}")


@router.get("/prompts", response_model=Dict[str, List[ActionablePrompt]])
async def get_actionable_prompts():
    """
    Get current actionable prompts based on real-time campus conditions.
    
    Returns context-aware suggestions like:
    - High consumption alerts
    - Optimization opportunities
    - Weather-based recommendations
    """
    prompts = [
        ActionablePrompt(
            type="alert",
            text="🔴 High consumption detected in Hall A. Suggest a Class Consolidation plan?",
            action="consolidate_hall_a",
            priority=1
        ),
        ActionablePrompt(
            type="suggestion",
            text="💡 Library AC could be optimized. View recommendation?",
            action="optimize_library",
            priority=2
        ),
        ActionablePrompt(
            type="info",
            text="🌤️ Hot weather tomorrow. Pre-cool buildings tonight?",
            action="precool_campus",
            priority=3
        )
    ]
    
    # Randomly vary prompts for dynamic UX
    if random.random() > 0.5:
        prompts.append(ActionablePrompt(
            type="alert",
            text="⚡ Admin Block HVAC trending high. Investigate?",
            action="check_admin_hvac",
            priority=1
        ))
    
    return {"prompts": [p.dict() for p in prompts]}
