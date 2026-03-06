"""
RAG-Browniepoint1 Integration Service (Standalone)
Integrates recommendation_system RAG pipeline concepts with browniepoint1 EnergyOptimizer model
for deep energy recommendations with contextual insights.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import os
from pathlib import Path
import re

# Try to import FAISS and SentenceTransformers
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_RAG_LIBS = True
except ImportError:
    HAS_RAG_LIBS = False

logger = logging.getLogger(__name__)

class EnergyOptimizerStandalone:
    """Standalone implementation of EnergyOptimizer logic from browniepoint1"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api/browniepoint1"):
        self.api_base_url = api_base_url
        
        # Building-specific parameters
        self.building_params = {
            'A': {'base_load': 100, 'hvac_efficiency': 0.85, 'solar_capacity': 50},
            'B': {'base_load': 150, 'hvac_efficiency': 0.80, 'solar_capacity': 30},
            'C': {'base_load': 120, 'hvac_efficiency': 0.88, 'solar_capacity': 40}
        }
    
    def get_weather_forecast(self, hours: int = 48) -> Dict:
        """Get weather forecast data (simplified)"""
        now = datetime.now()
        timestamps = [(now + timedelta(hours=i)).isoformat() for i in range(hours)]
        
        temperatures = []
        for i in range(hours):
            hour = (now.hour + i) % 24
            base_temp = 27.5 + 7.5 * np.sin((hour - 6) * np.pi / 12)
            temperatures.append(round(base_temp, 1))
        
        return {
            'timestamps': timestamps,
            'temperature': temperatures,
            'humidity': [50 + int(20 * np.sin(i * np.pi / 12)) for i in range(hours)],
            'cloudcover': [30 + int(40 * np.random.random()) for _ in range(hours)]
        }
    
    def predict_energy_consumption(self, building_id: str, weather_data: Dict) -> List[float]:
        """Predict energy consumption based on weather forecast"""
        if building_id not in self.building_params:
            raise ValueError(f"Unknown building: {building_id}")
        
        params = self.building_params[building_id]
        temperatures = weather_data.get('temperature', [])
        humidity = weather_data.get('humidity', [])
        cloudcover = weather_data.get('cloudcover', [])
        
        if not temperatures:
            return []
        
        predictions = []
        for i, temp in enumerate(temperatures):
            base_load = params['base_load']
            
            if temp > 25:
                hvac_load = (temp - 25) * 5 * (1 / params['hvac_efficiency'])
            elif temp < 18:
                hvac_load = (18 - temp) * 3 * (1 / params['hvac_efficiency'])
            else:
                hvac_load = 0
            
            humidity_factor = 1.0
            if i < len(humidity):
                humidity_factor = 1 + (humidity[i] - 50) * 0.002
            
            solar_generation = 0
            if i < len(cloudcover):
                solar_factor = max(0, (100 - cloudcover[i]) / 100)
                hour = i % 24
                if 6 <= hour <= 18:
                    solar_generation = params['solar_capacity'] * solar_factor * \
                                     np.sin((hour - 6) * np.pi / 12)
            
            total_consumption = max(0, (base_load + hvac_load) * humidity_factor - solar_generation)
            predictions.append(round(total_consumption, 2))
        
        return predictions
    
    def generate_optimization_recommendations(self, building_id: str, weather_data: Dict) -> List[Dict]:
        """Generate energy optimization recommendations"""
        recommendations = []
        predictions = self.predict_energy_consumption(building_id, weather_data)
        temperatures = weather_data.get('temperature', [])
        timestamps = weather_data.get('timestamps', [])
        
        if not predictions or not temperatures:
            return recommendations
        
        for i in range(min(48, len(predictions))):
            timestamp = timestamps[i] if i < len(timestamps) else f"Hour {i+1}"
            temp = temperatures[i] if i < len(temperatures) else 20
            predicted_load = predictions[i]
            
            if temp > 30 and i < 24:
                night_temp = temperatures[i+12] if i+12 < len(temperatures) else 20
                if night_temp < 25:
                    savings = predicted_load * 0.15
                    recommendations.append({
                        'type': 'precooling',
                        'building_id': building_id,
                        'timestamp': timestamp,
                        'temperature': temp,
                        'predicted_load': predicted_load,
                        'action': f'Pre-cool building tonight (night temp: {night_temp:.1f}°C)',
                        'energy_savings_kwh': round(savings, 2),
                        'priority': 'high' if temp > 35 else 'medium'
                    })
            
            if 16 <= (i % 24) <= 20:
                savings = predicted_load * 0.10
                recommendations.append({
                    'type': 'load_shifting',
                    'building_id': building_id,
                    'timestamp': timestamp,
                    'temperature': temp,
                    'predicted_load': predicted_load,
                    'action': 'Shift non-critical loads to off-peak hours',
                    'energy_savings_kwh': round(savings, 2),
                    'priority': 'medium'
                })
            
            if 10 <= (i % 24) <= 14:
                cloudcover = weather_data.get('cloudcover', [])
                clouds = cloudcover[i] if i < len(cloudcover) else 0
                if clouds < 30:
                    savings = predicted_load * 0.08
                    recommendations.append({
                        'type': 'solar_optimization',
                        'building_id': building_id,
                        'timestamp': timestamp,
                        'temperature': temp,
                        'predicted_load': predicted_load,
                        'action': 'Maximize solar energy usage during peak generation',
                        'energy_savings_kwh': round(savings, 2),
                        'priority': 'low'
                    })
        
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        return recommendations[:10]


class RAGBrowniepoint1Integration:
    """Integration service combining EnergyOptimizer with RAG enrichment"""
    
    def __init__(self):
        self.energy_optimizer = None
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.knowledge_base_path = None
        self.initialized = False
    
    def initialize(self):
        """Initialize EnergyOptimizer and RAG components"""
        if self.initialized:
            return
        
        logger.info("Initializing RAG-Browniepoint1 Integration...")
        
        try:
            self.energy_optimizer = EnergyOptimizerStandalone()
            logger.info("EnergyOptimizer initialized (standalone)")
        except Exception as e:
            logger.error(f"Failed to initialize EnergyOptimizer: {e}")
            self.energy_optimizer = None
        
        self._initialize_rag_components()
        self.initialized = True
        logger.info("RAG-Browniepoint1 Integration initialized successfully")
    
    def _initialize_rag_components(self):
        """Initialize RAG components"""
        possible_paths = [
            Path(__file__).resolve().parents[4] / "recommendation_system" / "knowledge_base" / "documents.json",
            Path(__file__).resolve().parents[3] / "data" / "rag" / "knowledge_base.json",
            Path(__file__).resolve().parents[4] / "UrjaAI" / "backend" / "data" / "rag" / "knowledge_base.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                self.knowledge_base_path = path
                logger.info(f"Found knowledge base at: {path}")
                break
        
        if self.knowledge_base_path:
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Failed to load knowledge base: {e}")
                self.documents = []
        
        if HAS_RAG_LIBS and self.documents:
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                self._build_vector_index()
            except Exception as e:
                logger.error(f"Failed to build RAG vector index: {e}")
                self.embedding_model = None
                self.index = None
        else:
            logger.warning("RAG libraries not available or no documents, using keyword matching")
    
    def _build_vector_index(self):
        """Build FAISS index"""
        if not self.documents or not HAS_RAG_LIBS:
            return
        
        try:
            doc_texts = [self._doc_to_text(doc) for doc in self.documents]
            embeddings = self.embedding_model.encode(doc_texts, convert_to_numpy=True)
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            logger.info(f"Built FAISS index with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error building vector index: {e}")
            self.index = None
    
    def _doc_to_text(self, doc: Dict[str, Any]) -> str:
        """Convert document to searchable text"""
        parts = []
        if 'type' in doc:
            parts.append(f"Type: {doc['type']}")
        if 'condition' in doc:
            parts.append(f"Condition: {doc['condition']}")
        if 'impact' in doc:
            parts.append(f"Impact: {doc['impact']}")
        if 'action' in doc:
            parts.append(f"Action: {doc['action']}")
        if 'building_id' in doc:
            parts.append(f"Building: {doc['building_id']}")
        return " | ".join(parts)
    
    def search_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        if not self.documents:
            return []
        
        if HAS_RAG_LIBS and self.index and self.embedding_model:
            try:
                query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
                distances, indices = self.index.search(query_embedding, top_k)
                results = []
                for idx in indices[0]:
                    if idx < len(self.documents):
                        results.append(self.documents[idx])
                return results
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in self.documents:
            doc_text = self._doc_to_text(doc).lower()
            score = sum(1 for word in query_words if word in doc_text)
            if score > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]
    
    def generate_deep_recommendations(
        self, 
        building_id: str, 
        temperature_offset: float = 0.0,
        occupancy_multiplier: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Generate deep recommendations with RAG enrichment"""
        recommendations = []
        
        if self.energy_optimizer:
            try:
                weather_data = self.energy_optimizer.get_weather_forecast(48)
                
                if temperature_offset != 0:
                    weather_data['temperature'] = [
                        t + temperature_offset for t in weather_data['temperature']
                    ]
                
                base_recs = self.energy_optimizer.generate_optimization_recommendations(
                    building_id, weather_data
                )
                
                for rec in base_recs[:5]:
                    cost_savings = rec.get('energy_savings_kwh', 0) * 8
                    recommendations.append({
                        'action': rec.get('action', 'Optimize energy usage'),
                        'savings_kwh': round(rec.get('energy_savings_kwh', 0), 2),
                        'savings_cost_inr': round(cost_savings, 2),
                        'priority': rec.get('priority', 'medium'),
                        'reason': f"Type: {rec.get('type', 'optimization')}",
                        'building_id': building_id,
                        'timestamp': datetime.now().isoformat(),
                        'is_enriched': False,
                        'sources': []
                    })
            except Exception as e:
                logger.error(f"EnergyOptimizer failed: {e}")
        
        if not recommendations:
            recommendations = self._generate_default_recommendations(building_id)
        
        enriched = []
        for rec in recommendations:
            enriched.append(self._enrich_with_rag(rec, building_id))
        
        return enriched
    
    def _generate_default_recommendations(self, building_id: str) -> List[Dict[str, Any]]:
        """Generate default recommendations"""
        return [
            {
                'action': 'Pre-cool building during off-peak hours',
                'savings_kwh': 15.5,
                'savings_cost_inr': 124.0,
                'priority': 'high',
                'reason': 'Night temperatures are lower, reducing HVAC load during peak hours.',
                'building_id': building_id,
                'timestamp': datetime.now().isoformat(),
                'is_enriched': False,
                'sources': []
            },
            {
                'action': 'Shift non-critical loads to off-peak hours',
                'savings_kwh': 8.2,
                'savings_cost_inr': 65.6,
                'priority': 'medium',
                'reason': 'Evening peak hours have higher electricity rates.',
                'building_id': building_id,
                'timestamp': datetime.now().isoformat(),
                'is_enriched': False,
                'sources': []
            },
            {
                'action': 'Maximize solar energy usage during peak generation',
                'savings_kwh': 5.8,
                'savings_cost_inr': 46.4,
                'priority': 'low',
                'reason': 'Clear skies expected during peak solar hours (10:00-14:00).',
                'building_id': building_id,
                'timestamp': datetime.now().isoformat(),
                'is_enriched': False,
                'sources': []
            }
        ]
    
    def _enrich_with_rag(self, recommendation: Dict[str, Any], building_id: str) -> Dict[str, Any]:
        """Enrich recommendation with RAG insights"""
        query = f"{recommendation['action']} {building_id} {recommendation['reason']}"
        relevant_docs = self.search_knowledge_base(query, top_k=3)
        
        if not relevant_docs:
            return recommendation
        
        enriched_reason = recommendation['reason']
        sources = []
        
        for doc in relevant_docs:
            doc_type = doc.get('type', '')
            
            if doc_type == 'weather_pattern':
                impact = doc.get('impact', '')
                if impact:
                    enriched_reason += f"\n\n📊 Weather Context: {impact}"
                    sources.append('weather_pattern')
            
            elif doc_type == 'recommendation_pattern':
                outcome = doc.get('outcome', {})
                if outcome:
                    success_rate = outcome.get('success_rate', 0)
                    if success_rate and isinstance(success_rate, (int, float)):
                        enriched_reason += f"\n\n📈 Historical Data: {success_rate*100:.0f}% success rate in similar scenarios."
                        sources.append('historical_pattern')
            
            elif doc_type == 'shap_explanation':
                explanation = doc.get('explanation', '')
                if explanation:
                    enriched_reason += f"\n\n🤖 AI Analysis: {explanation}"
                    sources.append('ai_explanation')
        
        enriched = recommendation.copy()
        enriched['reason'] = enriched_reason
        enriched['is_enriched'] = len(sources) > 0
        enriched['sources'] = list(set(sources))
        
        return enriched
    
    def chat_about_recommendation(
        self, 
        recommendation: Dict[str, Any],
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Chat about a specific recommendation using RAG.
        Provides direct answers to user questions.
        """
        if chat_history is None:
            chat_history = []
        
        # Search knowledge base for relevant info based on user question
        search_query = f"{recommendation['action']} {user_message}"
        relevant_docs = self.search_knowledge_base(search_query, top_k=3)
        
        # Build knowledge context
        knowledge_context = ""
        sources = []
        
        for doc in relevant_docs:
            doc_type = doc.get('type', '')
            
            if doc_type == 'weather_pattern':
                condition = doc.get('condition', '')
                impact = doc.get('impact', '')
                if condition or impact:
                    knowledge_context += f"Weather: {condition}. Impact: {impact}. "
                    sources.append('weather_pattern')
            
            elif doc_type == 'recommendation_pattern':
                outcome = doc.get('outcome', {})
                success_rate = outcome.get('success_rate', 0) if outcome else 0
                avg_savings = outcome.get('avg_savings_kwh', 0) if outcome else 0
                if success_rate or avg_savings:
                    knowledge_context += f"Historical success: {success_rate*100:.0f}%, avg savings {avg_savings} kWh. "
                    sources.append('historical_pattern')
        
        # Generate direct answer
        response = self._generate_direct_answer(
            user_message=user_message,
            recommendation=recommendation,
            knowledge_context=knowledge_context,
            chat_history=chat_history
        )
        
        return {
            'response': response,
            'sources': list(set(sources)),
            'relevant_docs_count': len(relevant_docs)
        }
    
    def _generate_direct_answer(
        self,
        user_message: str,
        recommendation: Dict[str, Any],
        knowledge_context: str,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """Generate a direct, contextual answer to the user's question"""
        
        msg_lower = user_message.lower()
        action = recommendation.get('action', 'this recommendation')
        savings_kwh = recommendation.get('savings_kwh', 0)
        savings_cost = recommendation.get('savings_cost_inr', 0)
        priority = recommendation.get('priority', 'medium')
        
        # Check for "why" questions
        if any(word in msg_lower for word in ['why', 'reason', 'how come', 'what makes']):
            return self._answer_why_question(action, recommendation, knowledge_context)
        
        # Check for "how much" / savings questions
        if any(phrase in msg_lower for phrase in ['how much', 'save', 'cost', 'money', 'price', 'savings']):
            return self._answer_savings_question(action, savings_kwh, savings_cost, knowledge_context)
        
        # Check for "what if" / scenario questions
        if any(phrase in msg_lower for phrase in ['what if', 'what happens', 'if i', 'suppose', 'change', 'increase', 'decrease']):
            return self._answer_what_if_question(action, user_message, recommendation, knowledge_context)
        
        # Check for weather/temperature questions
        if any(word in msg_lower for word in ['weather', 'temperature', 'temp', 'hot', 'cold', 'rain', 'sunny']):
            return self._answer_weather_question(action, recommendation, knowledge_context)
        
        # Check for "when" / timing questions
        if any(word in msg_lower for word in ['when', 'time', 'hour', 'night', 'day', 'evening', 'morning', 'peak']):
            return self._answer_timing_question(action, recommendation, knowledge_context)
        
        # Check for "how" / implementation questions
        if any(word in msg_lower for word in ['how', 'implement', 'do this', 'apply', 'setup']):
            return self._answer_how_question(action, recommendation, knowledge_context)
        
        # Default: Direct answer about the recommendation
        return self._answer_general_question(action, recommendation, knowledge_context)
    
    def _answer_why_question(self, action: str, rec: Dict, kb: str) -> str:
        """Answer why this recommendation is given"""
        reason = rec.get('reason', '')
        savings = rec.get('savings_kwh', 0)
        
        response = f"**Why: {action}**\n\n"
        
        if 'precool' in action.lower() or 'pre-cool' in action.lower():
            response += "This uses **thermal mass** to your advantage.\n\n"
            response += "**The Science:**\n"
            response += f"• Buildings store heat in walls/floors (thermal mass)\n"
            response += f"• Pre-cooling at night (₹4-6/kWh) charges this mass with coolness\n"
            response += f"• During day, building resists heating, delaying HVAC startup\n"
            response += f"• You avoid peak rates (₹10-12/kWh during 4-8 PM)\n\n"
            response += f"**Benefit:** {savings} kWh shifted from peak to off-peak"
        
        elif 'shift' in action.lower():
            response += "This leverages **time-of-use pricing**.\n\n"
            response += "**The Economics:**\n"
            response += f"• Electricity varies 3x daily\n"
            response += f"• Peak (4-8 PM): ₹10-12/kWh\n"
            response += f"• Off-peak (10 PM-6 AM): ₹4-6/kWh\n"
            response += f"• Shifting non-critical loads saves 50% per kWh\n\n"
            response += f"**Benefit:** {savings} kWh at cheaper rates"
        
        elif 'solar' in action.lower():
            response += "This maximizes **free solar energy**.\n\n"
            response += "**The Opportunity:**\n"
            response += f"• Solar peaks 10 AM - 2 PM\n"
            response += f"• Every kWh used then is essentially free\n"
            response += f"• Run high-consumption devices during solar peak\n\n"
            response += f"**Benefit:** {savings} kWh of solar offset"
        
        else:
            response += f"**Why this matters:**\n"
            response += f"• Addresses specific energy consumption pattern\n"
            response += f"• Expected savings: {savings} kWh\n"
            if reason:
                response += f"• {reason[:150]}\n"
        
        return response
    
    def _answer_savings_question(self, action: str, savings_kwh: float, savings_cost: float, kb: str) -> str:
        """Answer how much this saves"""
        response = f"**💰 Savings: {action}**\n\n"
        
        if savings_kwh > 0:
            response += f"**Per Use:**\n"
            response += f"• {savings_kwh} kWh saved\n"
            response += f"• ₹{savings_cost:.0f} saved\n"
            response += f"• Rate: ₹{savings_cost/savings_kwh:.1f}/kWh\n\n"
            
            annual_kwh = savings_kwh * 365
            annual_cost = annual_kwh * 8
            response += f"**Annual (daily use):**\n"
            response += f"• {annual_kwh:,.0f} kWh/year\n"
            response += f"• ₹{annual_cost:,.0f}/year\n"
            response += f"• CO₂: ~{annual_kwh * 0.85:.0f} kg less\n\n"
        
        response += f"**Comparison:**\n"
        response += f"• Powers {int(savings_kwh/0.3)} LEDs for 24h\n"
        response += f"• Charges {(savings_kwh * 1000 / 15):.0f} phones\n\n"
        
        response += f"**Maximize by:**\n"
        response += f"1. Apply consistently\n"
        response += f"2. Automate if possible\n"
        response += f"3. Track actual savings"
        
        return response
    
    def _answer_what_if_question(self, action: str, user_msg: str, rec: Dict, kb: str) -> str:
        """Answer what-if scenario questions"""
        response = f"**🔄 What-If: {action}**\n\n"
        
        temp_match = re.search(r'(\d+)', user_msg)
        temp_val = int(temp_match.group(1)) if temp_match else None
        
        if any(word in user_msg.lower() for word in ['temperature', 'temp', 'degree', '°c']):
            if temp_val:
                energy_delta = temp_val * 2.5
                cost_delta = energy_delta * 8
                
                if any(word in user_msg.lower() for word in ['increase', 'raise', 'higher']):
                    response += f"**If +{temp_val}°C:**\n\n"
                    response += f"⚠️ **Impact:**\n"
                    response += f"• +{energy_delta:.1f} kWh\n"
                    response += f"• +₹{cost_delta:.0f}\n"
                    response += f"• {(temp_val*15):.0f}% less effective\n\n"
                    response += f"💡 Try fans/insulation instead"
                else:
                    response += f"**If -{temp_val}°C:**\n\n"
                    response += f"✅ **Impact:**\n"
                    response += f"• {energy_delta:.1f} kWh more saved\n"
                    response += f"• ₹{cost_delta:.0f} more saved\n"
                    response += f"• Total: ₹{cost_delta + rec.get('savings_cost_inr', 0):.0f}\n\n"
                    response += f"⚠️ Check occupant comfort"
            else:
                response += "Need a temperature value. Try: 'What if +3°C?'"
        
        elif any(word in user_msg.lower() for word in ['people', 'occupancy']):
            response += "**If 20% more people:**\n\n"
            response += f"• +8-12% HVAC load\n"
            response += f"• Each person = 100W heat\n"
            response += f"• Your savings same, but higher baseline\n\n"
            response += f"💡 Use occupancy-based zoning"
        
        elif any(word in user_msg.lower() for word in ['time', 'peak']):
            response += "**Rate Impact:**\n\n"
            response += f"• Peak (4-8 PM): ₹10-12/kWh\n"
            response += f"• Off-peak: ₹4-6/kWh\n\n"
            response += f"• Move TO peak: -30-40% savings\n"
            response += f"• Move TO off-peak: +20-25% savings\n\n"
            response += f"✅ Current timing is optimal"
        
        else:
            response += "Ask about:\n"
            response += "• Temperature changes\n"
            response += "• Occupancy changes\n"  
            response += "• Timing changes"
        
        return response
    
    def _answer_weather_question(self, action: str, rec: Dict, kb: str) -> str:
        """Answer weather-related questions"""
        response = f"**🌤️ Weather: {action}**\n\n"
        
        response += f"**☀️ Sunny:**\n"
        response += f"• Max solar 10 AM - 2 PM\n"
        response += f"• Pre-cooling offsets heat\n"
        response += f"• Best savings potential\n\n"
        
        response += f"**☁️ Cloudy:**\n"
        response += f"• Solar -40-70%\n"
        response += f"• Higher humidity load\n"
        response += f"• Strategy MORE valuable\n\n"
        
        response += f"**🔥 Hot (>35°C):**\n"
        response += f"• HVAC +15-25% stress\n"
        response += f"• Pre-cooling CRITICAL\n"
        response += f"• Start 2-3h earlier\n\n"
        
        response += f"**❄️ Cold (<20°C):**\n"
        response += f"• Pre-cooling less relevant\n"
        response += f"• Consider pre-heating instead\n"
        response += f"• Maximize solar gain"
        
        return response
    
    def _answer_timing_question(self, action: str, rec: Dict, kb: str) -> str:
        """Answer when/timing questions"""
        response = f"**⏰ Best Time: {action}**\n\n"
        
        if 'precool' in action.lower():
            response += f"**10 PM - 6 AM (Off-Peak)**\n\n"
            response += f"**Why:**\n"
            response += f"• Cheapest rates: ₹4-6/kWh\n"
            response += f"• Cooler outside temps\n"
            response += f"• No occupant complaints\n"
            response += f"• 4-6h duration ideal\n\n"
            response += f"**Avoid:** 4-8 PM (₹10-12/kWh)"
        
        elif 'shift' in action.lower():
            response += f"**After 10 PM**\n\n"
            response += f"**Shift these:**\n"
            response += f"• Water heaters\n"
            response += f"• EV charging\n"
            response += f"• Dishwashers\n"
            response += f"• Battery charging\n\n"
            response += f"**Savings:** 50% per kWh"
        
        elif 'solar' in action.lower():
            response += f"**10 AM - 2 PM**\n\n"
            response += f"**Why:**\n"
            response += f"• Max solar output\n"
            response += f"• Free energy\n"
            response += f"• Run AC/pumps then"
        
        else:
            response += f"**Optimal:** Off-peak (10 PM - 6 AM)\n\n"
            response += f"**Avoid:** Peak (4-8 PM)"
        
        return response
    
    def _answer_how_question(self, action: str, rec: Dict, kb: str) -> str:
        """Answer how to implement questions"""
        response = f"**🔧 How To: {action}**\n\n"
        
        if 'precool' in action.lower():
            response += f"**Steps:**\n\n"
            response += f"1. Set 22-23°C at 10 PM\n"
            response += f"2. Cool overnight\n"
            response += f"3. Raise to 25-26°C at 6 AM\n"
            response += f"4. Let thermal mass work\n"
            response += f"5. Adjust ±1°C as needed\n\n"
            response += f"**Tools:** Smart thermostat schedule"
        
        elif 'shift' in action.lower():
            response += f"**Steps:**\n\n"
            response += f"1. Find shiftable loads\n"
            response += f"2. Set timers for 10 PM+\n"
            response += f"3. EV: Charge overnight\n"
            response += f"4. Water heater: Heat at night\n\n"
            response += f"**Tools:** Smart plugs, delay-start"
        
        else:
            response += f"**Steps:**\n\n"
            response += f"1. Review details\n"
            response += f"2. Assess current setup\n"
            response += f"3. Make one change\n"
            response += f"4. Monitor 1-2 weeks\n"
            response += f"5. Fine-tune results"
        
        return response
    
    def _answer_general_question(self, action: str, rec: Dict, kb: str) -> str:
        """Answer general questions"""
        response = f"**📋 {action}**\n\n"
        
        response += f"**Summary:**\n"
        response += f"Saves {rec.get('savings_kwh', 0)} kWh (₹{rec.get('savings_cost_inr', 0):.0f})\n\n"
        
        response += f"**Benefits:**\n"
        response += f"• Lower electricity costs\n"
        response += f"• Reduced CO₂\n"
        response += f"• Maintains comfort\n"
        response += f"• No investment needed\n\n"
        
        response += f"**Ask me:**\n"
        response += f"• 'Why?'\n"
        response += f"• 'How much?'\n"
        response += f"• 'What if?'\n"
        response += f"• 'When?'\n"
        response += f"• 'How?'"
        
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'initialized': self.initialized,
            'has_energy_optimizer': self.energy_optimizer is not None,
            'has_rag_libs': HAS_RAG_LIBS,
            'knowledge_base_loaded': self.knowledge_base_path is not None,
            'document_count': len(self.documents),
            'vector_index_built': self.index is not None
        }


# Global instance
rag_browniepoint1_service = RAGBrowniepoint1Integration()
