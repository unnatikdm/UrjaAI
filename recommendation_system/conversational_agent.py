"""
Conversational AI Agent for Energy Recommendations
Enables bidirectional chat with intent understanding, tool routing, and dynamic responses.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
import re

class ConversationalAgent:
    """Multi-agent conversational system for energy recommendations"""
    
    def __init__(self, tool_registry: Dict[str, Callable]):
        self.tool_registry = tool_registry
        self.conversation_state = {}
        self.user_profiles = {}
        self.logger = logging.getLogger(__name__)
    
    async def process_message(self, user_id: str, message: str, 
                           conversation_id: str = None) -> Dict[str, Any]:
        """Process user message and generate response"""
        try:
            # Get or create conversation state
            if not conversation_id:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            state = self._get_conversation_state(conversation_id)
            
            # Parse intent and entities
            intent_result = self._parse_intent(message)
            
            # Update conversation state
            state['turns'].append({
                'role': 'user',
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'intent': intent_result['intent'],
                'entities': intent_result['entities']
            })
            
            # Generate response
            response = await self._generate_response(
                user_id, message, intent_result, state, conversation_id
            )
            
            # Update state with assistant response
            state['turns'].append({
                'role': 'assistant',
                'message': response['message'],
                'timestamp': datetime.now().isoformat(),
                'tool_calls': response.get('tool_calls', []),
                'context': response.get('context', {})
            })
            
            # Save conversation state
            self._save_conversation_state(conversation_id, state)
            
            return {
                'conversation_id': conversation_id,
                'user_message': message,
                'response': response,
                'intent': intent_result['intent'],
                'entities': intent_result['entities'],
                'turn_count': len(state['turns'])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            return {
                'error': str(e),
                'conversation_id': conversation_id,
                'user_message': message
            }
    
    def _parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse user intent and extract entities"""
        message_lower = message.lower()
        
        # Intent classification (simplified rule-based)
        intent_patterns = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'thanks': ['thank', 'thanks', 'great', 'awesome'],
            'request_recs': ['recommend', 'suggest', 'what should i do', 'recommendation'],
            'explain_rec': ['explain', 'why', 'how does', 'tell me about'],
            'what_if': ['what if', 'if i', 'suppose', 'imagine'],
            'building_info': ['building', 'hvac', 'size', 'square feet'],
            'weather_query': ['weather', 'temperature', 'rain', 'forecast'],
            'carbon_query': ['carbon', 'co2', 'trees', 'environmental'],
            'modify_rec': ['change', 'modify', 'adjust', 'different'],
            'compare_recs': ['compare', 'versus', 'better'],
            'accept_rec': ['yes', 'ok', 'do it', 'accept', 'sounds good'],
            'reject_rec': ['no', 'cancel', 'dont', 'reject', 'not good'],
            'clarify': ['what do you mean', 'clarify', 'explain more']
        }
        
        detected_intent = 'unknown'
        entities = {}
        
        # Check each intent pattern
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    detected_intent = intent
                    break
        
        # Extract entities based on intent
        if detected_intent != 'unknown':
            entities = self._extract_entities(message_lower, detected_intent)
        
        return {
            'intent': detected_intent,
            'entities': entities,
            'confidence': 0.8 if detected_intent != 'unknown' else 0.3
        }
    
    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract entities based on intent"""
        entities = {}
        
        if intent in ['request_recs', 'explain_rec', 'what_if', 'modify_rec']:
            # Extract building
            building_patterns = [
                r'building\s+([a-z])',
                r'building\s+([a-z]\d+)',
                r'lecture hall|library|dormitory'
            ]
            for pattern in building_patterns:
                match = re.search(pattern, message)
                if match:
                    entities['building'] = match.group(1) if match.groups() else match.group(0)
                    break
            
            # Extract time
            time_patterns = [
                r'(\d{1,2})\s*(am|pm)',
                r'(morning|afternoon|evening|night)',
                r'tomorrow|today|next week|next month'
            ]
            for pattern in time_patterns:
                match = re.search(pattern, message)
                if match:
                    entities['time'] = match.group(0) if match.groups() else match.group(0)
                    break
            
            # Extract action
            action_patterns = [
                r'pre-?cool|shift|adjust|raise|lower',
                r'setpoint|temperature|thermostat'
            ]
            for pattern in action_patterns:
                match = re.search(pattern, message)
                if match:
                    entities['action'] = match.group(0)
                    break
            
            # Extract metrics
            metric_patterns = [
                r'(\d+)\s*kwh',
                r'\$(\d+\.?\d*)',
                r'(\d+)\s*%|percent',
                r'co2|carbon|trees'
            ]
            for pattern in metric_patterns:
                match = re.search(pattern, message)
                if match:
                    metric_value = match.group(1) if match.groups() else match.group(0)
                    if 'kwh' in pattern:
                        entities['savings_kwh'] = float(metric_value)
                    elif '$' in pattern:
                        entities['cost'] = float(metric_value)
                    elif '%' in pattern:
                        entities['percentage'] = float(metric_value)
                    elif 'co2' in pattern:
                        entities['co2_kg'] = float(metric_value)
                    break
        
        elif intent == 'building_info':
            # Extract building-specific information
            if 'size' in message or 'square feet' in message:
                size_match = re.search(r'(\d+)\s*(?:sq\s*ft|square feet)', message)
                if size_match:
                    entities['size_sqft'] = int(size_match.group(1))
            
            if 'hvac' in message:
                hvac_types = ['vav', 'constant volume', 'fan coil', 'heat pump']
                for hvac_type in hvac_types:
                    if hvac_type in message:
                        entities['hvac_type'] = hvac_type
                        break
        
        return entities
    
    async def _generate_response(self, user_id: str, message: str, 
                            intent_result: Dict[str, Any], 
                            state: Dict[str, Any], 
                            conversation_id: str) -> Dict[str, Any]:
        """Generate contextual response using appropriate tools"""
        intent = intent_result['intent']
        entities = intent_result['entities']
        
        try:
            if intent == 'greeting':
                return {
                    'message': "Hello! I'm your energy assistant. I can help you with energy-saving recommendations, weather forecasts, and answer questions about your buildings. What would you like to know today?",
                    'tool_calls': [],
                    'context': {'greeting': True}
                }
            
            elif intent == 'thanks':
                return {
                    'message': "You're welcome! I'm glad I could help. Is there anything else you'd like to know about energy optimization?",
                    'tool_calls': [],
                    'context': {'acknowledgment': True}
                }
            
            elif intent == 'request_recs':
                return await self._handle_recommendation_request(user_id, entities, state)
            
            elif intent == 'explain_rec':
                return await self._handle_explanation_request(user_id, entities, state)
            
            elif intent == 'what_if':
                return await self._handle_whatif_request(user_id, entities, state)
            
            elif intent == 'building_info':
                return await self._handle_building_info_request(user_id, entities, state)
            
            elif intent == 'weather_query':
                return await self._handle_weather_request(user_id, entities, state)
            
            elif intent == 'carbon_query':
                return await self._handle_carbon_request(user_id, entities, state)
            
            elif intent == 'clarify':
                return await self._handle_clarification_request(user_id, entities, state)
            
            elif intent in ['accept_rec', 'reject_rec', 'modify_rec']:
                return await self._handle_feedback_request(user_id, intent, entities, state)
            
            else:
                return {
                    'message': "I'm not sure I understood that. Could you please rephrase your question? I can help with energy recommendations, building information, weather forecasts, and carbon impact calculations.",
                    'tool_calls': [],
                    'context': {'clarification_needed': True}
                }
        
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return {
                'message': f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                'tool_calls': [],
                'context': {'error': True}
            }
    
    async def _handle_recommendation_request(self, user_id: str, entities: Dict[str, Any], 
                                       state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request for recommendations"""
        building_id = entities.get('building', 'current')
        horizon = entities.get('time', 'today')
        
        # Call recommendations tool
        if 'get_recommendations' in self.tool_registry:
            recommendations = await self.tool_registry['get_recommendations'](
                building_id=building_id, 
                horizon=horizon,
                user_id=user_id
            )
        else:
            recommendations = []
        
        # Format response
        if recommendations:
            top_recs = recommendations[:3]  # Show top 3
            rec_text = []
            for i, rec in enumerate(top_recs, 1):
                action = rec.get('action', 'Unknown action')
                savings = rec.get('savings_kwh', 0)
                cost = rec.get('savings_cost', 0)
                rec_text.append(f"{i}. {action} (save {savings} kWh, ${cost:.2f})")
            
            return {
                'message': f"Here are my top recommendations for {building_id}:\n" + "\n".join(rec_text),
                'tool_calls': [{'tool': 'get_recommendations', 'params': {'building_id': building_id, 'horizon': horizon}}],
                'context': {'recommendations': recommendations}
            }
        else:
            return {
                'message': f"I don't have specific recommendations for {building_id} right now. Would you like me to check current conditions and suggest some actions?",
                'tool_calls': [],
                'context': {'no_recommendations': True}
            }
    
    async def _handle_explanation_request(self, user_id: str, entities: Dict[str, Any], 
                                     state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request for explanation"""
        # Find current focus from conversation
        current_focus = None
        for turn in reversed(state['turns']):
            if turn.get('role') == 'user' and turn.get('intent') == 'request_recs':
                # Look for the last assistant response with recommendations
                for later_turn in state['turns']:
                    if later_turn.get('role') == 'assistant' and 'recommendations' in later_turn.get('context', {}):
                        current_focus = later_turn['context']['recommendations'][0] if later_turn['context']['recommendations'] else None
                        break
        
        if not current_focus:
            return {
                'message': "I don't see a recent recommendation to explain. Could you tell me which recommendation you'd like me to explain?",
                'tool_calls': [],
                'context': {'no_recommendation_to_explain': True}
            }
        
        # Generate explanation
        if 'generate_explanation' in self.tool_registry:
            explanation = await self.tool_registry['generate_explanation'](
                recommendation=current_focus,
                user_id=user_id
            )
        else:
            explanation = {'explanation': "Explanation service not available"}
        
        return {
            'message': f"Here's an explanation for the recommendation:\n{explanation.get('explanation', 'No explanation available')}",
            'tool_calls': [{'tool': 'generate_explanation', 'params': {'recommendation': current_focus, 'user_id': user_id}}],
            'context': {'explanation': explanation}
        }
    
    async def _handle_whatif_request(self, user_id: str, entities: Dict[str, Any], 
                                 state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle what-if scenario requests"""
        # Extract what-if parameters
        action = entities.get('action', '')
        start_time = entities.get('time', '')
        building = entities.get('building', 'current')
        
        # Call what-if tool
        if 'tools_whatif' in self.tool_registry:
            scenario_result = await self.tool_registry['tools_whatif'](
                building_id=building,
                action=action,
                start_time=start_time,
                user_id=user_id
            )
        else:
            scenario_result = {'result': 'What-if analysis not available'}
        
        # Format response
        if scenario_result.get('success', False):
            return {
                'message': f"What-if analysis for {action} on {building}: {scenario_result.get('message', 'Analysis failed')}",
                'tool_calls': [{'tool': 'tools_whatif', 'params': entities}],
                'context': {'what_if_result': scenario_result}
            }
        else:
            return {
                'message': f"If you {action} at {start_time} instead, here's what would happen:\n{scenario_result.get('message', 'No analysis available')}",
                'tool_calls': [{'tool': 'tools_whatif', 'params': entities}],
                'context': {'what_if_result': scenario_result}
            }
    
    async def _handle_building_info_request(self, user_id: str, entities: Dict[str, Any], 
                                       state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle building information requests"""
        building = entities.get('building', 'current')
        
        if 'get_building_info' in self.tool_registry:
            building_info = await self.tool_registry['get_building_info'](
                building_id=building,
                user_id=user_id
            )
        else:
            building_info = {'error': 'Building info service not available'}
        
        # Format response
        if building_info.get('size_sqft'):
            size_text = f"{building_info['size_sqft']} square feet"
        else:
            size_text = "size not available"
        
        if building_info.get('hvac_type'):
            hvac_text = f"equipped with {building_info['hvac_type']} system"
        else:
            hvac_text = "HVAC system type not specified"
        
        return {
            'message': f"Building {building} information:\n• Size: {size_text}\n• HVAC: {hvac_text}\n• Type: {building_info.get('building_type', 'Unknown')}",
            'tool_calls': [{'tool': 'get_building_info', 'params': {'building_id': building}}],
            'context': {'building_info': building_info}
        }
    
    async def _handle_weather_request(self, user_id: str, entities: Dict[str, Any], 
                                 state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather queries"""
        if 'get_weather' in self.tool_registry:
            weather = await self.tool_registry['get_weather'](
                user_id=user_id
            )
        else:
            weather = {'error': 'Weather service not available'}
        
        # Format response
        if weather.get('temperature'):
            temp_text = f"{weather['temperature']}°C"
        else:
            temp_text = "temperature not available"
        
        if weather.get('conditions'):
            condition_text = weather['conditions']
        else:
            condition_text = "conditions not available"
        
        return {
            'message': f"Current weather: {temp_text}, {condition_text}",
            'tool_calls': [{'tool': 'get_weather', 'params': {'user_id': user_id}}],
            'context': {'weather': weather}
        }
    
    async def _handle_carbon_request(self, user_id: str, entities: Dict[str, Any], 
                                state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle carbon impact queries"""
        if 'calculate_carbon' in self.tool_registry:
            carbon_result = await self.tool_registry['calculate_carbon'](
                user_id=user_id
            )
        else:
            carbon_result = {'error': 'Carbon calculation service not available'}
        
        # Format response
        if carbon_result.get('co2_kg'):
            co2_text = f"{carbon_result['co2_kg']:.1f} kg of CO₂"
        else:
            co2_text = "CO₂ impact not available"
        
        if carbon_result.get('trees_equivalent'):
            trees_text = f"equivalent to planting {carbon_result['trees_equivalent']:.1f} trees"
        else:
            trees_text = "tree equivalent not available"
        
        return {
            'message': f"Environmental impact: {co2_text}, {trees_text}",
            'tool_calls': [{'tool': 'calculate_carbon', 'params': {'user_id': user_id}}],
            'context': {'carbon_impact': carbon_result}
        }
    
    async def _handle_clarification_request(self, user_id: str, entities: Dict[str, Any], 
                                     state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification requests"""
        return {
            'message': "I'd be happy to clarify! Could you tell me:\n• Which building are you asking about?\n• What specific action or recommendation?\n• What time period are you interested in?",
            'tool_calls': [],
            'context': {'clarification_requested': True}
        }
    
    async def _handle_feedback_request(self, user_id: str, intent: str, entities: Dict[str, Any], 
                                    state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user feedback on recommendations"""
        if intent == 'accept_rec':
            return {
                'message': "Great! I've noted your acceptance. The recommendation will be added to your action plan. Would you like me to set up monitoring for this action?",
                'tool_calls': [],
                'context': {'feedback': 'accepted'}
            }
        
        elif intent == 'reject_rec':
            return {
                'message': "I understand. Would you like me to suggest an alternative approach, or explain why this recommendation might not be suitable?",
                'tool_calls': [],
                'context': {'feedback': 'rejected'}
            }
        
        elif intent == 'modify_rec':
            return {
                'message': "I can help modify that recommendation. What specific changes would you like me to make? For example, different timing, different building, or different parameters?",
                'tool_calls': [],
                'context': {'feedback': 'modify_requested'}
            }
        
        else:
            return {
                'message': "I've noted your feedback. This helps me improve future recommendations.",
                'tool_calls': [],
                'context': {'feedback': 'noted'}
            }
    
    def _get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        """Get or create conversation state"""
        if conversation_id not in self.conversation_state:
            self.conversation_state[conversation_id] = {
                'conversation_id': conversation_id,
                'turns': [],
                'context': {},
                'created_at': datetime.now().isoformat()
            }
        
        return self.conversation_state[conversation_id]
    
    def _save_conversation_state(self, conversation_id: str, state: Dict[str, Any]):
        """Save conversation state"""
        self.conversation_state[conversation_id] = state
        # In a real implementation, this would save to a database
        self.logger.info(f"Saved conversation state for {conversation_id} with {len(state['turns'])} turns")
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history"""
        if conversation_id in self.conversation_state:
            return {
                'conversation_id': conversation_id,
                'turns': self.conversation_state[conversation_id]['turns'],
                'created_at': self.conversation_state[conversation_id]['created_at']
            }
        else:
            return {'error': 'Conversation not found'}
    
    def reset_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Reset conversation"""
        if conversation_id in self.conversation_state:
            del self.conversation_state[conversation_id]
            return {'message': 'Conversation reset successfully'}
        else:
            return {'error': 'Conversation not found'}

# Example tool implementations (these would connect to your existing APIs)
async def mock_get_recommendations(building_id: str, horizon: str, user_id: str) -> List[Dict]:
    """Mock recommendation tool"""
    await asyncio.sleep(0.1)  # Simulate API call
    return [
        {
            'action': f'Pre-cool {building_id} from 04:00-06:00',
            'savings_kwh': 150,
            'savings_cost': 1.25,
            'confidence': 0.92,
            'building_id': building_id
        },
        {
            'action': f'Adjust {building_id} setpoint by -2°C',
            'savings_kwh': 80,
            'savings_cost': 0.67,
            'confidence': 0.78,
            'building_id': building_id
        }
    ]

async def mock_generate_explanation(recommendation: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Mock explanation generation tool"""
    await asyncio.sleep(0.2)  # Simulate RAG processing
    return {
        'explanation': f"Based on historical patterns and current conditions, {recommendation.get('action', 'Unknown action')} is recommended because similar actions have achieved 92% success rate. Weather analysis shows this approach is optimal for current conditions.",
        'context_sources': ['historical_success', 'weather_analysis'],
        'quality_score': 0.85
    }

async def mock_tools_whatif(building_id: str, action: str, start_time: str, user_id: str) -> Dict[str, Any]:
    """Mock what-if analysis tool"""
    await asyncio.sleep(0.3)  # Simulate analysis
    return {
        'success': True,
        'message': f"If you {action} at {start_time}, predicted savings would change from 150 kWh to 140 kWh due to reduced thermal storage time.",
        'new_savings': 140,
        'original_savings': 150,
        'impact_analysis': 'Reduced effectiveness by 7% due to timing change'
    }

async def mock_get_building_info(building_id: str, user_id: str) -> Dict[str, Any]:
    """Mock building info tool"""
    await asyncio.sleep(0.1)  # Simulate database query
    buildings = {
        'A': {
            'building_type': 'lecture_hall',
            'size_sqft': 2500,
            'hvac_type': 'constant_volume',
            'construction_year': 1985
        },
        'B': {
            'building_type': 'library',
            'size_sqft': 1800,
            'hvac_type': 'vav',
            'construction_year': 1992
        }
    }
    
    if building_id in buildings:
        return buildings[building_id]
    else:
        return {'error': 'Building not found'}

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Register tools
    tools = {
        'get_recommendations': mock_get_recommendations,
        'generate_explanation': mock_generate_explanation,
        'tools_whatif': mock_tools_whatif,
        'get_building_info': mock_get_building_info,
        'get_weather': lambda user_id: {'temperature': 32, 'conditions': 'partly cloudy'},
        'calculate_carbon': lambda user_id: {'co2_kg': 45.2, 'trees_equivalent': 2.1}
    }
    
    # Create agent
    agent = ConversationalAgent(tools)
    
    # Test conversation
    async def test_conversation():
        # Test different intents
        test_messages = [
            ("Hello, I need help with energy recommendations", "greeting"),
            ("Tell me about Building A", "building_info"),
            ("What if I pre-cool at 5 AM instead?", "what_if"),
            ("Explain the pre-cooling recommendation", "explain_rec"),
            ("Yes, do that", "accept_rec")
        ]
        
        for message, expected_intent in test_messages:
            print(f"\nUser: {message}")
            result = await agent.process_message("test_user", message)
            print(f"Intent: {result['intent']} (expected: {expected_intent})")
            print(f"Response: {result['message']}")
            print("-" * 50)
    
    # Run test
    asyncio.run(test_conversation())
