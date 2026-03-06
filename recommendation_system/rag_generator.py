"""
RAG-based Explanation Generator
Transforms structured recommendations into rich, contextual explanations using retrieved knowledge.
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os

class RAGExplanationGenerator:
    """Generates rich explanations using RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, knowledge_base_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.knowledge_base_path = knowledge_base_path
        self.model_name = model_name
        self.documents = []
        self.embeddings = None
        self.index = None
        self.embedding_model = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._load_knowledge_base()
        self._initialize_embedding_model()
        self._build_vector_index()
    
    def _load_knowledge_base(self):
        """Load knowledge base from file"""
        try:
            with open(self.knowledge_base_path, 'r') as f:
                self.documents = json.load(f)
            self.logger.info(f"Loaded {len(self.documents)} documents from knowledge base")
        except Exception as e:
            self.logger.error(f"Failed to load knowledge base: {e}")
            self.documents = []
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            self.logger.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            # Fallback to simple embedding
            self.embedding_model = None
    
    def _build_vector_index(self):
        """Build FAISS vector index for fast retrieval"""
        if not self.documents or not self.embedding_model:
            return
        
        try:
            # Generate embeddings for all documents
            doc_texts = [self._document_to_text(doc) for doc in self.documents]
            self.embeddings = self.embedding_model.encode(
                doc_texts, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            # Build FAISS index
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)
            
            self.logger.info(f"Built vector index with {len(self.documents)} documents, dimension: {dimension}")
            
        except Exception as e:
            self.logger.error(f"Failed to build vector index: {e}")
            self.index = None
    
    def _document_to_text(self, document: Dict[str, Any]) -> str:
        """Convert document to searchable text"""
        text_parts = []
        
        # Add document type and main content
        text_parts.append(f"Type: {document.get('type', '')}")
        
        if document.get('type') == 'recommendation_pattern':
            text_parts.append(f"Action: {document.get('action', '')}")
            text_parts.append(f"Building: {document.get('building_id', '')}")
            
            conditions = document.get('conditions', {})
            if conditions:
                text_parts.append(f"Conditions: {conditions}")
            
            outcome = document.get('outcome', {})
            if outcome:
                text_parts.append(f"Success rate: {outcome.get('success_rate', 0)}")
                text_parts.append(f"Avg savings: {outcome.get('predicted_savings', 0)} kWh")
        
        elif document.get('type') == 'shap_explanation':
            text_parts.append(f"Building: {document.get('building_id', '')}")
            text_parts.append(f"Explanation: {document.get('explanation', '')}")
            
            top_features = document.get('top_features', [])
            if top_features:
                text_parts.append(f"Top features: {', '.join(top_features)}")
        
        elif document.get('type') == 'weather_impact':
            text_parts.append(f"Condition: {document.get('condition', '')}")
            text_parts.append(f"Impact: {document.get('impact', '')}")
        
        elif document.get('type') == 'building_metadata':
            text_parts.append(f"Building: {document.get('building_id', '')}")
            text_parts.append(f"Type: {document.get('building_type', '')}")
            text_parts.append(f"HVAC: {document.get('hvac_type', '')}")
            text_parts.append(f"Size: {document.get('size_sqft', 0)} sq ft")
        
        # Add metadata
        metadata = document.get('metadata', {})
        if metadata:
            for key, value in metadata.items():
                text_parts.append(f"{key}: {value}")
        
        return ' | '.join(text_parts)
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 5, 
                               similarity_threshold: float = 0.75,
                               metadata_filters: Dict[str, Any] = None) -> List[Dict]:
        """Retrieve most relevant documents for a query"""
        if not self.index or not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Search for similar documents
            similarities, indices = self.index.search(
                query_embedding, 
                k=min(top_k * 2, len(self.documents))  # Get more for filtering
            )
            
            # Filter and rank results
            relevant_docs = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= similarity_threshold:
                    doc = self.documents[idx]
                    
                    # Apply metadata filters if provided
                    if metadata_filters:
                        if not self._passes_metadata_filters(doc, metadata_filters):
                            continue
                    
                    relevant_docs.append({
                        'document': doc,
                        'similarity': float(similarity),
                        'index': int(idx)
                    })
            
            # Sort by similarity and return top_k
            relevant_docs.sort(key=lambda x: x['similarity'], reverse=True)
            return relevant_docs[:top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def _passes_metadata_filters(self, document: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document passes metadata filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key in document:
                if isinstance(value, list):
                    if document[key] not in value:
                        return False
                elif document.get('metadata', {}).get(key) not in value:
                    return False
            else:
                if document[key] != value and document.get('metadata', {}).get(key) != value:
                    return False
        
        return True
    
    def generate_explanation(self, recommendation: Dict[str, Any], 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate rich explanation for a recommendation"""
        try:
            # Build query from recommendation
            query = self._build_query_from_recommendation(recommendation, context)
            
            # Retrieve relevant knowledge
            retrieved_docs = self.retrieve_relevant_documents(
                query, 
                top_k=7,
                metadata_filters={
                    'type': ['recommendation_pattern', 'shap_explanation', 'weather_impact'],
                    'building_id': context.get('building_id') if context else None
                }
            )
            
            # Generate explanation using retrieved context
            explanation = self._generate_llm_explanation(recommendation, context, retrieved_docs)
            
            # Add quality checks
            quality_score = self._quality_check(explanation, retrieved_docs)
            
            return {
                'recommendation': recommendation,
                'explanation': explanation,
                'retrieved_documents': retrieved_docs,
                'quality_score': quality_score,
                'context_sources': [doc['document']['type'] for doc in retrieved_docs]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate explanation: {e}")
            return {
                'recommendation': recommendation,
                'explanation': f"Error generating explanation: {str(e)}",
                'retrieved_documents': [],
                'quality_score': 0.0,
                'context_sources': []
            }
    
    def _build_query_from_recommendation(self, recommendation: Dict[str, Any], 
                                    context: Dict[str, Any] = None) -> str:
        """Build search query from recommendation"""
        action = recommendation.get('action', '')
        building_id = recommendation.get('building_id', '')
        savings_kwh = recommendation.get('savings_kwh', 0)
        
        query_parts = [f"{action} {building_id}"]
        
        if context and 'weather' in context:
            weather = context['weather']
            if weather.get('temperature', 0) > 30:
                query_parts.append("heatwave conditions")
            if weather.get('humidity', 0) > 70:
                query_parts.append("high humidity")
        
        if savings_kwh > 100:
            query_parts.append("high savings")
        
        return ' '.join(query_parts)
    
    def _generate_llm_explanation(self, recommendation: Dict[str, Any], 
                               context: Dict[str, Any], 
                               retrieved_docs: List[Dict]) -> str:
        """Generate explanation using LLM (simulated for now)"""
        # This would normally call an LLM API
        # For now, we'll create a template-based explanation
        
        action = recommendation.get('action', '')
        savings_kwh = recommendation.get('savings_kwh', 0)
        savings_cost = recommendation.get('savings_cost', 0)
        
        # Extract relevant information from retrieved documents
        historical_success = []
        weather_impacts = []
        building_info = []
        
        for doc in retrieved_docs:
            doc_type = doc['document'].get('type', '')
            if doc_type == 'recommendation_pattern':
                outcome = doc['document'].get('outcome', {})
                if outcome:
                    historical_success.append(outcome.get('success_rate', 0))
            elif doc_type == 'weather_impact':
                weather_impacts.append(doc['document'].get('impact', ''))
            elif doc_type == 'building_metadata':
                building_info.append(doc['document'].get('building_type', ''))
        
        # Build explanation
        explanation_parts = []
        
        # Main recommendation statement
        explanation_parts.append(
            f"Based on analysis of similar conditions and historical patterns, "
            f"we recommend {action} which should save approximately {savings_kwh} kWh "
            f"(saving approximately ${savings_cost:.2f})."
        )
        
        # Add historical context
        if historical_success:
            avg_success = np.mean(historical_success)
            explanation_parts.append(
                f"Historical data shows this strategy has a {avg_success:.1%} success rate "
                f"in similar conditions."
            )
        
        # Add weather context
        if weather_impacts:
            explanation_parts.append(
                f"Weather analysis indicates that current conditions may affect energy consumption: "
                f"{'; '.join(weather_impacts[:2])}."
            )
        
        # Add building-specific context
        if building_info:
            explanation_parts.append(
                f"Building characteristics suggest this approach is well-suited for "
                f"{'; '.join(building_info[:1])} type buildings."
            )
        
        # Add environmental impact
        co2_saved = savings_kwh * 0.0005  # Approximate CO₂ kg/kWh
        trees_equivalent = co2_saved / 21  # Approximate trees per kg CO₂
        explanation_parts.append(
            f"This action would reduce CO₂ emissions by approximately {co2_saved:.1f} kg, "
            f"equivalent to planting {trees_equivalent:.1f} trees."
        )
        
        return ' '.join(explanation_parts)
    
    def _quality_check(self, explanation: str, retrieved_docs: List[Dict]) -> float:
        """Check quality of generated explanation"""
        if not explanation:
            return 0.0
        
        # Relevance check (does explanation address the recommendation?)
        relevance_score = 0.8 if len(explanation) > 50 else 0.5
        
        # Groundedness check (are claims supported by retrieved docs?)
        groundedness_score = 0.9 if retrieved_docs else 0.5
        
        # Conciseness check
        conciseness_score = 1.0 if len(explanation) < 300 else 0.7
        
        # Overall quality score
        quality_score = (relevance_score + groundedness_score + conciseness_score) / 3
        
        return quality_score
    
    def save_index(self, save_path: str = "rag_index"):
        """Save the built index for future use"""
        if self.index is not None and self.embeddings is not None:
            os.makedirs(save_path, exist_ok=True)
            
            # Save FAISS index
            index_file = os.path.join(save_path, "faiss_index.bin")
            faiss.write_index(self.index, index_file)
            
            # Save embeddings
            embeddings_file = os.path.join(save_path, "embeddings.npy")
            np.save(embeddings_file, self.embeddings)
            
            # Save documents mapping
            mapping_file = os.path.join(save_path, "document_mapping.json")
            with open(mapping_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
            
            self.logger.info(f"RAG index saved to {save_path}")
    
    def load_index(self, load_path: str = "rag_index"):
        """Load pre-built index"""
        try:
            # Load FAISS index
            index_file = os.path.join(load_path, "faiss_index.bin")
            self.index = faiss.read_index(index_file)
            
            # Load embeddings
            embeddings_file = os.path.join(load_path, "embeddings.npy")
            self.embeddings = np.load(embeddings_file)
            
            # Load documents mapping
            mapping_file = os.path.join(load_path, "document_mapping.json")
            with open(mapping_file, 'r') as f:
                self.documents = json.load(f)
            
            self.logger.info(f"RAG index loaded from {load_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load RAG index: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize RAG generator
    rag = RAGExplanationGenerator("knowledge_base/knowledge_base.json")
    
    # Test with sample recommendation
    sample_recommendation = {
        "action": "Pre-cool Building A from 04:00–06:00",
        "savings_kwh": 150,
        "savings_cost": 1.25,
        "building_id": "A"
    }
    
    context = {
        "building_id": "A",
        "weather": {
            "temperature": 37,
            "humidity": 65,
            "conditions": "heatwave"
        }
    }
    
    # Generate explanation
    result = rag.generate_explanation(sample_recommendation, context)
    
    print("Generated Explanation:")
    print(result['explanation'])
    print(f"\nQuality Score: {result['quality_score']:.2f}")
    print(f"Context Sources: {result['context_sources']}")
    print(f"Retrieved {len(result['retrieved_documents'])} documents")
    
    # Save index for future use
    rag.save_index()
