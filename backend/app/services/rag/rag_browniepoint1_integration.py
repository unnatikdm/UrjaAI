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
        Enhanced chat with dynamic context understanding and natural responses.
        Understands user intent and provides contextual, flowing answers.
        """
        if chat_history is None:
            chat_history = []
        
        # Analyze conversation context
        conversation_context = self._analyze_conversation_context(chat_history, user_message)
        
        # Extract user intent with deeper understanding
        intent = self._extract_user_intent(user_message, conversation_context)
        
        # Search knowledge base with context-aware query
        search_query = self._build_contextual_search_query(recommendation, user_message, intent)
        relevant_docs = self.search_knowledge_base(search_query, top_k=3)
        
        # Build knowledge context without duplication
        knowledge_context = self._build_unique_knowledge_context(relevant_docs)
        sources = list(set([doc.get('type', '') for doc in relevant_docs if doc.get('type')]))
        
        # Generate contextual, natural response
        response = self._generate_contextual_response(
            user_message=user_message,
            intent=intent,
            recommendation=recommendation,
            knowledge_context=knowledge_context,
            conversation_context=conversation_context,
            chat_history=chat_history
        )
        
        return {
            'response': response,
            'sources': sources,
            'relevant_docs_count': len(relevant_docs),
            'detected_intent': intent.get('primary', 'general')
        }
    
    def _analyze_conversation_context(self, chat_history: List[Dict[str, str]], current_message: str) -> Dict[str, Any]:
        """Analyze the conversation flow and previous topics"""
        context = {
            'previous_topics': [],
            'last_question_type': None,
            'conversation_depth': len(chat_history) // 2,
            'is_follow_up': False,
            'referenced_values': []
        }
        
        if not chat_history:
            return context
        
        # Extract topics from previous exchanges
        for msg in chat_history[-4:]:  # Look at last 4 messages
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                if any(word in content for word in ['temperature', 'temp']):
                    context['previous_topics'].append('temperature')
                elif any(word in content for word in ['save', 'cost', 'money']):
                    context['previous_topics'].append('savings')
                elif any(word in content for word in ['occupancy', 'people']):
                    context['previous_topics'].append('occupancy')
                elif any(word in content for word in ['weather', 'rain', 'hot']):
                    context['previous_topics'].append('weather')
        
        # Check if current message is a follow-up
        current_lower = current_message.lower()
        context['is_follow_up'] = (
            len(current_message.split()) <= 6 and
            (any(word in current_lower for word in ['what about', 'and', 'how about', 'also']) or
             context['previous_topics'])
        )
        
        # Extract referenced numbers/values
        import re
        numbers = re.findall(r'(\d+\.?\d*)', current_message)
        context['referenced_values'] = [float(n) for n in numbers if float(n) < 1000]
        
        return context
    
    def _extract_user_intent(self, user_message: str, context: Dict) -> Dict[str, Any]:
        """Extract detailed user intent from the message"""
        msg_lower = user_message.lower()
        
        intent = {
            'primary': 'general',
            'sub_intent': None,
            'entities': {},
            'sentiment': 'neutral',
            'urgency': 'normal'
        }
        
        # Detect question type with context awareness
        if any(word in msg_lower for word in ['why', 'reason', 'how come', 'what makes']):
            intent['primary'] = 'explanation'
        
        elif any(phrase in msg_lower for phrase in ['what if', 'what happens', 'suppose', 'if i']):
            intent['primary'] = 'what_if'
            # Detect what-if sub-type
            if any(word in msg_lower for word in ['temperature', 'temp', 'degree', '°c', 'setpoint']):
                intent['sub_intent'] = 'temperature_change'
            elif any(word in msg_lower for word in ['occupancy', 'people', 'crowd', 'staff']):
                intent['sub_intent'] = 'occupancy_change'
                # Detect direction
                if any(word in msg_lower for word in ['decrease', 'less', 'fewer', 'down', 'reduce']):
                    intent['entities']['direction'] = 'decrease'
                elif any(word in msg_lower for word in ['increase', 'more', 'higher', 'up']):
                    intent['entities']['direction'] = 'increase'
            elif any(word in msg_lower for word in ['time', 'when', 'hour', 'schedule']):
                intent['sub_intent'] = 'timing_change'
        
        elif any(word in msg_lower for word in ['how much', 'save', 'cost', 'money', 'price', 'dollar', '$', 'rs', 'inr', '₹']):
            intent['primary'] = 'savings_inquiry'
            # Detect time frame
            if any(word in msg_lower for word in ['annual', 'year', 'yearly']):
                intent['sub_intent'] = 'annual'
            elif any(word in msg_lower for word in ['month', 'monthly']):
                intent['sub_intent'] = 'monthly'
            elif any(word in msg_lower for word in ['daily', 'day', 'per day']):
                intent['sub_intent'] = 'daily'
        
        elif any(word in msg_lower for word in ['co2', 'carbon', 'environment', 'green', 'trees', 'pollution']):
            intent['primary'] = 'environmental_impact'
        
        elif any(word in msg_lower for word in ['how', 'implement', 'do this', 'apply', 'setup', 'configure']):
            intent['primary'] = 'implementation'
        
        elif any(word in msg_lower for word in ['when', 'time', 'best time', 'optimal']):
            intent['primary'] = 'timing'
        
        elif any(word in msg_lower for word in ['weather', 'temperature', 'temp', 'hot', 'cold', 'rain']):
            intent['primary'] = 'weather_inquiry'
        
        # Detect sentiment
        if any(word in msg_lower for word in ['great', 'good', 'awesome', 'excellent', 'thanks']):
            intent['sentiment'] = 'positive'
        elif any(word in msg_lower for word in ['bad', 'terrible', 'useless', 'problem']):
            intent['sentiment'] = 'negative'
        
        # Detect urgency
        if any(word in msg_lower for word in ['urgent', 'asap', 'immediately', 'quick']):
            intent['urgency'] = 'high'
        
        # Extract numerical entities
        import re
        numbers = re.findall(r'(\d+\.?\d*)', user_message)
        if numbers:
            intent['entities']['numbers'] = [float(n) for n in numbers]
        
        return intent
    
    def _build_contextual_search_query(self, recommendation: Dict, user_message: str, intent: Dict) -> str:
        """Build a context-aware search query"""
        query_parts = [recommendation.get('action', '')]
        
        # Add intent-based terms
        if intent['primary'] == 'what_if':
            if intent['sub_intent']:
                query_parts.append(intent['sub_intent'])
        elif intent['primary'] == 'savings_inquiry':
            query_parts.append('savings cost money')
        elif intent['primary'] == 'environmental_impact':
            query_parts.append('CO2 carbon environment')
        elif intent['primary'] == 'implementation':
            query_parts.append('implement how to steps')
        
        query_parts.append(user_message)
        
        return ' '.join(query_parts)
    
    def _build_unique_knowledge_context(self, docs: List[Dict]) -> str:
        """Build knowledge context without duplication"""
        seen_content = set()
        context_parts = []
        
        for doc in docs:
            doc_type = doc.get('type', '')
            
            if doc_type == 'weather_pattern':
                condition = doc.get('condition', '')
                impact = doc.get('impact', '')
                content_key = f"weather_{condition}_{impact}"
                if content_key not in seen_content and (condition or impact):
                    seen_content.add(content_key)
                    context_parts.append(f"Weather condition: {condition}. Impact: {impact}")
            
            elif doc_type == 'recommendation_pattern':
                outcome = doc.get('outcome', {})
                success_rate = outcome.get('success_rate', 0) if outcome else 0
                avg_savings = outcome.get('avg_savings_kwh', 0) if outcome else 0
                content_key = f"rec_{success_rate}_{avg_savings}"
                if content_key not in seen_content and (success_rate or avg_savings):
                    seen_content.add(content_key)
                    context_parts.append(f"Historical: {success_rate*100:.0f}% success, avg {avg_savings} kWh savings")
            
            elif doc_type == 'shap_explanation':
                explanation = doc.get('explanation', '')
                feature = doc.get('feature', '')
                content_key = f"shap_{feature}_{explanation[:50]}"
                if content_key not in seen_content and explanation:
                    seen_content.add(content_key)
                    context_parts.append(f"AI analysis: {explanation}")
        
        return ' | '.join(context_parts)
    
    def _generate_contextual_response(
        self,
        user_message: str,
        intent: Dict,
        recommendation: Dict,
        knowledge_context: str,
        conversation_context: Dict,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """Generate a contextual, natural response based on intent and conversation"""
        
        # Handle follow-up questions specially
        if conversation_context['is_follow_up'] and conversation_context['previous_topics']:
            return self._handle_follow_up_response(
                user_message, intent, recommendation, conversation_context, chat_history
            )
        
        # Route to appropriate response generator based on intent
        if intent['primary'] == 'what_if':
            return self._generate_what_if_response(intent, recommendation, conversation_context)
        
        elif intent['primary'] == 'savings_inquiry':
            return self._generate_savings_response(intent, recommendation)
        
        elif intent['primary'] == 'explanation':
            return self._generate_explanation_response(recommendation, knowledge_context)
        
        elif intent['primary'] == 'environmental_impact':
            return self._generate_environmental_response(recommendation)
        
        elif intent['primary'] == 'implementation':
            return self._generate_implementation_response(recommendation)
        
        elif intent['primary'] == 'timing':
            return self._generate_timing_response(recommendation)
        
        elif intent['primary'] == 'weather_inquiry':
            return self._generate_weather_response(recommendation, knowledge_context)
        
        else:
            return self._generate_general_response(recommendation, chat_history)
    
    def _handle_follow_up_response(
        self,
        user_message: str,
        intent: Dict,
        recommendation: Dict,
        context: Dict,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """Handle follow-up questions naturally"""
        last_topic = context['previous_topics'][-1] if context['previous_topics'] else 'general'
        values = context['referenced_values']
        
        if last_topic == 'temperature' and values:
            return self._generate_temperature_follow_up(values[0], intent, recommendation)
        
        elif last_topic == 'occupancy':
            direction = intent.get('entities', {}).get('direction', 'increase')
            return self._generate_occupancy_follow_up(direction, recommendation)
        
        elif last_topic == 'savings':
            return self._generate_savings_follow_up(intent, recommendation)
        
        return self._generate_general_response(recommendation, chat_history)
    
    def _generate_what_if_response(self, intent: Dict, rec: Dict, context: Dict) -> str:
        """Generate natural what-if scenario response"""
        action = rec.get('action', 'this recommendation')
        
        if intent['sub_intent'] == 'temperature_change':
            numbers = intent.get('entities', {}).get('numbers', [])
            if numbers:
                change = numbers[0]
                direction = intent.get('entities', {}).get('direction', 'increase')
                
                # Calculate impact (simplified)
                energy_per_degree = 2.5  # kWh per degree change
                if direction == 'increase':
                    energy_impact = change * energy_per_degree
                    cost_impact = energy_impact * 8
                    
                    return f"If you increase the temperature by {change}°C, you'd actually use **more energy** - about {energy_impact:.1f} kWh extra. This would cost you approximately ₹{cost_impact:.0f} more.\n\nInstead of raising the temperature, consider using fans or improving insulation to maintain comfort without increasing your energy bill."
                else:
                    energy_saved = change * energy_per_degree
                    cost_saved = energy_saved * 8
                    
                    return f"Decreasing the temperature by {change}°C could save you around {energy_saved:.1f} kWh, which translates to about ₹{cost_saved:.0f} per application.\n\nHowever, make sure this doesn't compromise occupant comfort. You might want to try this during off-peak hours first to test the impact."
        
        elif intent['sub_intent'] == 'occupancy_change':
            direction = intent.get('entities', {}).get('direction', 'increase')
            
            if direction == 'decrease':
                return f"With fewer people in the building, you'd actually have **lower internal heat gains** - each person generates about 100W of heat.\n\nThis means your HVAC system won't have to work as hard to maintain comfort. Your savings potential remains similar, but the baseline energy consumption decreases, so your total bill would be lower.\n\nThis is actually a great time to be more aggressive with your energy-saving strategies since there's less heat to manage."
            else:
                return f"More occupancy means more internal heat (about 100W per person) and higher ventilation requirements. Your HVAC system will need to work 8-12% harder.\n\nThe good news? Your recommended savings amount stays the same, so you're still saving the same amount of energy - it's just from a higher baseline. Consider using occupancy-based zoning to only condition the occupied areas."
        
        elif intent['sub_intent'] == 'timing_change':
            numbers = intent.get('entities', {}).get('numbers', [])
            if numbers:
                hour = numbers[0]
                is_peak = 16 <= hour <= 20
                if is_peak:
                    return f"Starting **{action}** at {hour:02.0f}:00 would put it right in the **peak demand window (16:00 - 20:00)**. Electricity rates are highest then (up to ₹12/kWh), so your cost savings would be roughly 30-40% lower than if you did it during off-peak hours.\n\nIt's much more efficient to stick to the recommended schedule or move it even earlier to pre-cool the building."
                else:
                    return f"Starting at {hour:02.0f}:00 is outside the peak window, so you'll still get good savings. However, {hour:02.0f}:00 is often the hottest part of the day, meaning your HVAC system has to work harder. \n\nStarting it at the recommended time is usually 5-10% more efficient because you're staying ahead of the afternoon heat spike."

        return f"Let me help you explore what happens if conditions change for **{action}**. What specific scenario are you thinking about?"
    
    def _generate_savings_response(self, intent: Dict, rec: Dict) -> str:
        """Generate natural savings response with proper calculations"""
        savings_kwh = rec.get('savings_kwh', 0)
        savings_cost = rec.get('savings_cost_inr', 0)
        action = rec.get('action', 'this recommendation')
        
        # Determine time frame
        timeframe = intent.get('sub_intent', 'general')
        
        if timeframe == 'annual':
            annual_kwh = savings_kwh * 261  # Weekdays per year
            annual_cost = savings_cost * 261
            co2_saved = annual_kwh * 0.85
            
            return f"Over a full year of consistent use (about 261 weekdays), **{action}** could save you approximately:\n\n• **{annual_kwh:.0f} kWh** of electricity\n• **₹{annual_cost:.0f}** in energy costs\n• **{co2_saved:.0f} kg** of CO₂ emissions\n\nThat's equivalent to the carbon absorption of about {(co2_saved/22):.1f} trees over a year, or not driving a car for {(co2_saved/0.12):.0f} kilometers."
        
        elif timeframe == 'monthly':
            monthly_kwh = savings_kwh * 20  # ~20 weekdays
            monthly_cost = savings_cost * 20
            
            return f"Applied consistently over a month (about 20 weekdays), you'd save approximately:\n\n• **{monthly_kwh:.0f} kWh**\n• **₹{monthly_cost:.0f}**\n\nPlus, if this reduces your peak demand by even 0.5 kW, you'd save an additional ₹100 in demand charges, bringing your total monthly savings to around ₹{monthly_cost + 100:.0f}."
        
        else:
            return f"For **{action}**, each time you apply this recommendation:\n\n• You save **{savings_kwh} kWh** of electricity\n• Which saves you **₹{savings_cost:.0f}** at current rates\n• And prevents **{savings_kwh * 0.85:.1f} kg** of CO₂ emissions\n\nTo maximize these savings:\n1. **Automate it** - Set up your BMS to apply this automatically\n2. **Be consistent** - Daily application compounds the savings\n3. **Track it** - Compare your actual usage to see the real impact\n\nWant to know the annual projection or see what happens under different conditions?"
    
    def _generate_explanation_response(self, rec: Dict, kb: str) -> str:
        """Generate natural explanation response"""
        action = rec.get('action', 'this action')
        reason = rec.get('reason', '')
        
        if 'precool' in action.lower() or 'pre-cool' in action.lower():
            return f"**Why pre-cooling works:**\n\nThink of your building like a thermal battery. At night (10 PM - 6 AM), electricity is cheaper (₹4-6/kWh vs ₹10-12/kWh during peak), and outdoor temperatures are lower.\n\nBy pre-cooling during these off-peak hours, you're 'charging' the building's thermal mass with coolness. During the day, this stored coolness helps resist heat gain, delaying when your HVAC needs to kick in - and avoiding those expensive peak hours (4-8 PM).\n\nIt's like filling up your car with cheap fuel at night so you don't have to buy expensive fuel during rush hour."
        
        elif 'shift' in action.lower() or 'load' in action.lower():
            return f"**The economics of load shifting:**\n\nElectricity rates vary dramatically throughout the day. Peak hours (4-8 PM) cost ₹10-12/kWh, while off-peak (10 PM - 6 AM) is only ₹4-6/kWh.\n\nThis recommendation identifies non-critical loads - things like water heaters, EV chargers, and dishwashers - that can run during cheaper hours without affecting operations.\n\nBy simply changing WHEN these devices run (not IF they run), you save up to 50% on the energy they consume. No comfort loss, no operational changes - just smarter timing."
        
        else:
            return f"**Why this helps:** {reason}\n\nThis recommendation addresses a specific inefficiency in your building's energy profile. {kb[:150] if kb else ''}"
    
    def _generate_environmental_response(self, rec: Dict) -> str:
        """Generate environmental impact response"""
        savings_kwh = rec.get('savings_kwh', 0)
        co2_per_kwh = 0.85
        trees_per_year = 22
        
        co2_saved = savings_kwh * co2_per_kwh
        trees_equivalent = co2_saved / trees_per_year
        car_km = co2_saved / 0.12
        
        annual_co2 = co2_saved * 365
        annual_trees = annual_co2 / trees_per_year
        
        return f"**Your environmental impact from this action:**\n\nEach time you apply this recommendation, you prevent **{co2_saved:.1f} kg** of CO₂ from entering the atmosphere. That's roughly the same as:\n\n• Planting **{trees_equivalent:.2f}** trees\n• Not driving a car for **{car_km:.0f} kilometers**\n• Charging **{(savings_kwh * 1000 / 15):.0f}** smartphones\n\n**Over a full year** of daily use:\n• **{annual_co2:.0f} kg** CO₂ saved\n• Equivalent to **{annual_trees:.1f}** trees worth of carbon absorption\n• Like taking a car off the road for **{(annual_co2 / 0.12 / 1000):.0f}** kilometers\n\nSmall actions, when repeated, create significant environmental impact."
    
    def _generate_implementation_response(self, rec: Dict) -> str:
        """Generate implementation guidance response"""
        action = rec.get('action', 'this action')
        
        if 'precool' in action.lower():
            return f"**How to implement pre-cooling in your BMS:**\n\n**Option 1: Automated (Recommended)**\n1. Access your BMS → Scheduling → HVAC → Setpoint Control\n2. Create a daily schedule: 10:00 PM - 6:00 AM, setpoint 22-23°C\n3. Set 6:00 AM - 10:00 PM, setpoint 25-26°C\n4. Enable auto-revert\n\n**Option 2: Manual**\n• At 10 PM: Lower setpoint to 22°C\n• At 6 AM: Raise setpoint to 25°C\n• Repeat daily during hot weather\n\n**Setup time:** ~15 minutes\n**Payback:** Immediate\n\nAfter a week, check your energy dashboard to see the actual savings compared to similar days before implementation."
        
        elif 'shift' in action.lower():
            return f"""**How to shift your loads:**

**Identify shiftable loads:**
• Water heaters
• EV chargers
• Dishwashers
• Pool pumps
• Battery storage systems

**For each device:**
1. Check if it has a delay-start feature
2. Set it to start after 10 PM
3. For EVs: Charge overnight instead of right after work
4. For water heaters: Heat water at night, insulated tank keeps it hot

**Smart plugs** can automate this for devices without built-in timers.

**Expected result:** 30-50% cost reduction on shifted loads."""
        
        else:
            return f"**Implementation steps for {action}:**\n\n1. **Review** the recommendation details and verify it applies to your setup\n2. **Plan** when to implement - start during low-occupancy periods for testing\n3. **Execute** - Make the change incrementally if possible\n4. **Monitor** - Track energy use for 1-2 weeks\n5. **Adjust** - Fine-tune based on actual results and feedback\n\nNeed specific BMS instructions? Let me know your system type (Siemens, Honeywell, Johnson Controls, etc.)."
    
    def _generate_timing_response(self, rec: Dict) -> str:
        """Generate timing guidance response"""
        action = rec.get('action', 'this action')
        
        if 'precool' in action.lower():
            return f"**Optimal timing for pre-cooling:**\n\n**Best window:** 10:00 PM - 6:00 AM (Off-peak)\n\n**Why this time?**\n• Cheapest electricity rates: ₹4-6/kWh\n• Cooler outdoor temperatures make cooling more efficient\n• Building typically unoccupied - no comfort complaints\n• Less strain on the electrical grid\n\n**Avoid:** 4:00 PM - 8:00 PM (Peak rates: ₹10-12/kWh)\n\n**Duration:** 4-6 hours of pre-cooling is typically sufficient to charge the building's thermal mass.\n\nDuring a heatwave (>35°C), consider starting 2-3 hours earlier than usual."
        
        else:
            return f"**Best timing for {action}:**\n\n**Off-peak hours (10 PM - 6 AM):** Lowest rates, minimal grid stress\n**Standard hours (6 AM - 4 PM, 8 PM - 10 PM):** Moderate rates\n**Peak hours (4 PM - 8 PM):** Highest rates - avoid if possible\n\nYour specific recommendation is optimized for the current conditions. Shifting it to peak hours would reduce savings by 30-40%, while moving to off-peak could increase savings by 20-25%."
    
    def _generate_weather_response(self, rec: Dict, kb: str) -> str:
        """Generate weather-aware response"""
        return f"**Weather impact on this recommendation:**\n\n🌤️ **Sunny/Clear Days (Best conditions)**\n• Pre-cooling is highly effective\n• Solar generation peaks 10 AM - 2 PM\n• Maximum savings potential\n\n☁️ **Cloudy/Rainy Days**\n• Solar generation drops 40-70%\n• Higher humidity increases HVAC load\n• Recommendation becomes MORE valuable (higher baseline consumption)\n\n🔥 **Hot Days (>35°C)**\n• HVAC stress increases 15-25%\n• Start pre-cooling 2-3 hours earlier\n• Target 23-24°C instead of 22°C\n\n❄️ **Cold Days (<20°C)**\n• Pre-cooling less relevant\n• Consider pre-heating during off-peak instead\n\n{kb if kb else 'Current weather conditions suggest this is a good time to apply this recommendation.'}"
    
    def _generate_general_response(self, rec: Dict, chat_history: List[Dict[str, str]]) -> str:
        """Generate natural general response"""
        action = rec.get('action', 'this action')
        savings_kwh = rec.get('savings_kwh', 0)
        savings_cost = rec.get('savings_cost_inr', 0)
        
        # Check conversation depth for contextual opening
        depth = len(chat_history) // 2
        
        if depth == 0:
            opening = f"I can help you understand **{action}** better."
        elif depth == 1:
            opening = f"Continuing our discussion about {action}:"
        else:
            opening = "Building on what we've covered:"
        
        return f"{opening}\n\nThis recommendation saves **{savings_kwh} kWh** (₹{savings_cost:.0f}) per application by optimizing when and how your building uses energy.\n\n**What would you like to know?**\n• How much you could save annually\n• Why this specific timing is recommended\n• What happens if conditions change\n• How to implement it in your BMS\n• The environmental impact"
    
    def _generate_temperature_follow_up(self, temp_change: float, intent: Dict, rec: Dict) -> str:
        """Handle temperature-related follow-up"""
        action = rec.get('action', '')
        
        if 'decrease' in str(intent).lower() or temp_change < 0:
            return f"With a {abs(temp_change)}°C decrease, you're looking at roughly {(abs(temp_change) * 2.5):.1f} kWh more saved per session. That translates to about ₹{(abs(temp_change) * 2.5 * 8):.0f} additional savings.\n\nJust keep an eye on comfort levels - if people start wearing sweaters indoors, you might have gone too far!"
        else:
            return f"An increase of {temp_change}°C would add about {(temp_change * 2.5):.1f} kWh to your consumption, costing roughly ₹{(temp_change * 2.5 * 8):.0f} extra.\n\nInstead of raising the temperature, try using ceiling fans or improving your building's insulation."
    
    def _generate_occupancy_follow_up(self, direction: str, rec: Dict) -> str:
        """Handle occupancy-related follow-up"""
        if direction == 'decrease':
            return f"With fewer people, your internal heat load drops. Each person removed saves about 100W of heat that your HVAC doesn't have to remove.\n\nThis actually makes your energy-saving strategies more effective - there's less 'background' heat to overcome. Your percentage savings might even improve!"
        else:
            return f"More people means more heat to manage. Each additional person adds roughly 100W of body heat plus equipment use.\n\nYour HVAC will work harder, but your actual savings amount stays constant. The key is that you're saving the same amount from a higher baseline, so your percentage efficiency improves."
    
    def _generate_savings_follow_up(self, intent: Dict, rec: Dict) -> str:
        """Handle savings-related follow-up"""
        savings_kwh = rec.get('savings_kwh', 0)
        
        timeframe = intent.get('sub_intent', 'general')
        if timeframe == 'annual':
            return f"Annually, you're looking at approximately {savings_kwh * 261:.0f} kWh and ₹{savings_kwh * 8 * 261:.0f} in savings if applied consistently. That's like getting a free month of electricity!"
        else:
            return f"Monthly, with about 20 weekdays, you'd save roughly {savings_kwh * 20:.1f} kWh and ₹{savings_kwh * 8 * 20:.0f}. Not bad for a simple scheduling change!"
    
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
