import json
import numpy as np
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Try to import FAISS and SentenceTransformers, fallback to simple similarity if not available
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_RAG_LIBS = True
except ImportError:
    HAS_RAG_LIBS = False

class RAGService:
    """Service for Retrieval-Augmented Generation for Energy Recommendations"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.logger = logging.getLogger(__name__)
        if knowledge_base_path is None:
            # backend/app/services/rag/rag_service.py -> backend/data/rag/knowledge_base.json
            current_file_path = Path(__file__).resolve()
            base_dir = current_file_path.parents[3] 
            self.knowledge_base_path = base_dir / "data" / "rag" / "knowledge_base.json"
        else:
            self.knowledge_base_path = Path(knowledge_base_path)
            
        self.documents = []
        self.embeddings = None
        self.index = None
        self.embedding_model = None
        self.initialized = False
        
    def initialize(self):
        """Initialize RAG components"""
        if self.initialized:
            return
            
        self._load_knowledge_base()
        
        if HAS_RAG_LIBS:
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                self._build_vector_index()
                self.initialized = True
                self.logger.info("RAG Service initialized with FAISS and SentenceTransformers")
            except Exception as e:
                self.logger.error(f"Failed to initialize RAG libraries: {e}")
                self.initialized = False
        else:
            self.logger.warning("RAG libraries (faiss, sentence-transformers) not found. Using simple keyword matching.")
            self.initialized = True # Mark as initialized for keyword matching
            
    def _load_knowledge_base(self):
        """Load documents from JSON knowledge base"""
        try:
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, 'r') as f:
                    self.documents = json.load(f)
                self.logger.info(f"Loaded {len(self.documents)} documents from {self.knowledge_base_path}")
            else:
                self.logger.warning(f"Knowledge base file not found at {self.knowledge_base_path}")
                self.documents = []
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            self.documents = []
            
    def _build_vector_index(self):
        """Build FAISS index for vector search"""
        if not self.documents or not self.embedding_model:
            return
            
        try:
            doc_texts = [self._doc_to_text(doc) for doc in self.documents]
            self.embeddings = self.embedding_model.encode(doc_texts, convert_to_numpy=True)
            
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)
            self.logger.info(f"Built FAISS index with {len(self.documents)} documents")
        except Exception as e:
            self.logger.error(f"Error building vector index: {e}")
            self.index = None
            
    def _doc_to_text(self, doc: Dict[str, Any]) -> str:
        """Convert document dict to searchable text string"""
        parts = [f"Type: {doc.get('type', '')}"]
        if 'condition' in doc: parts.append(f"Condition: {doc['condition']}")
        if 'impact' in doc: parts.append(f"Impact: {doc['impact']}")
        if 'action' in doc: parts.append(f"Action: {doc['action']}")
        if 'building_id' in doc: parts.append(f"Building: {doc['building_id']}")
        return " | ".join(parts)
        
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if not self.documents:
            return []
            
        if HAS_RAG_LIBS and self.index is not None:
            try:
                query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
                distances, indices = self.index.search(query_embedding, top_k)
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.documents):
                        results.append(self.documents[idx])
                return results
            except Exception as e:
                self.logger.error(f"Vector search failed: {e}")
                
        # Fallback to simple keyword search
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in self.documents:
            doc_text = self._doc_to_text(doc).lower()
            score = sum(1 for word in query_words if word in doc_text)
            if score > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]

    def enrich_recommendation(self, rec: Dict[str, Any], building_id: str) -> Dict[str, Any]:
        """Enrich a single recommendation with RAG context"""
        query = f"{rec.get('action', '')} {building_id}"
        relevant_docs = self.search(query)
        
        enriched_reason = rec.get('reason', '')
        context_highlights = []
        
        for doc in relevant_docs:
            if doc.get('type') == 'weather_pattern':
                context_highlights.append(f"Weather Context: {doc.get('impact')}")
            elif doc.get('type') == 'recommendation_pattern':
                context_highlights.append(f"Historical Success: {doc.get('outcome', {}).get('success_rate', 0)*100:.0f}% success in similar scenarios.")
        
        if context_highlights:
            # Append RAG insights to the original reason
            enriched_reason += "\n\nDeep Insights:\n" + "\n".join(context_highlights)
            
        return {
            **rec,
            "reason": enriched_reason,
            "is_enriched": True,
            "sources": [doc.get('type') for doc in relevant_docs]
        }

rag_service = RAGService()
