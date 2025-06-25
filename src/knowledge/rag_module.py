"""
Retrieval-Augmented Generation (RAG) Module
Implements enhanced RAG pattern inspired by Fin.ai's architecture
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio
from abc import ABC, abstractmethod
# import numpy as np  # Not needed for MVP
from datetime import datetime
from src.utils.logging import knowledge_logger as logger


@dataclass
class Document:
    """Represents a document in the knowledge base"""
    id: str
    content: str
    title: str
    source: str
    metadata: Dict[str, any]
    embedding: Optional[List[float]] = None  # Changed from np.ndarray for MVP
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class RetrievalResult:
    """Result from document retrieval"""
    documents: List[Document]
    scores: List[float]
    query: str
    refined_query: str


@dataclass
class GenerationResult:
    """Result from response generation"""
    response: str
    confidence: float
    sources: List[str]
    validation_passed: bool
    metadata: Dict[str, any]


class QueryRefiner:
    """
    Query refinement stage - optimizes customer queries for better retrieval
    Inspired by Fin.ai's query refinement approach
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
    async def refine_query(self, 
                          original_query: str, 
                          context: Optional[Dict] = None) -> str:
        """
        Refine user query to improve retrieval accuracy
        
        Args:
            original_query: Raw user input
            context: Conversation context
            
        Returns:
            Refined query optimized for retrieval
        """
        # Remove noise and clarify intent
        refined = original_query.lower().strip()
        
        # Expand abbreviations and acronyms
        abbreviations = {
            "vm": "virtual machine",
            "db": "database",
            "api": "application programming interface",
            "vpn": "virtual private network",
            "ssl": "secure socket layer",
            "dns": "domain name system"
        }
        
        for abbr, full in abbreviations.items():
            refined = refined.replace(f" {abbr} ", f" {full} ")
        
        # Add context if available
        if context and "previous_intent" in context:
            refined = f"{context['previous_intent']} {refined}"
        
        # In production, use LLM for sophisticated query expansion
        # if self.llm_client:
        #     refined = await self.llm_client.refine_query(refined)
        
        return refined


class SemanticRetriever:
    """
    Retrieves relevant documents using semantic search
    """
    
    def __init__(self, vector_store=None, embedding_model=None):
        # Initialize vector store - disabled for MVP
        if vector_store is None:
            # For MVP, we'll use a simple in-memory store
            self.vector_store = None  # Will use simple keyword search instead
            self.use_pinecone = False
            logger.info("Vector store disabled for MVP - using simple search")
        else:
            self.vector_store = vector_store
            self.use_pinecone = False
        
        self.embedding_model = embedding_model
        
    async def retrieve(self, 
                      query: str, 
                      top_k: int = 5,
                      filters: Optional[Dict] = None) -> RetrievalResult:
        """
        Retrieve relevant documents for the query
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Optional metadata filters
            
        Returns:
            RetrievalResult with documents and scores
        """
        # Use vector store for retrieval
        if self.vector_store:
            # Search using vector store
            search_results = self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_dict=filters
            )
            
            # Convert to Document objects
            relevant_docs = []
            scores = []
            
            for result in search_results:
                doc = Document(
                    id=result['id'],
                    content=result['content'],
                    title=result.get('metadata', {}).get('title', 'Untitled'),
                    source=result.get('metadata', {}).get('source', 'knowledge_base'),
                    metadata=result.get('metadata', {})
                )
                relevant_docs.append(doc)
                scores.append(result.get('score', 0.0))
        else:
            # Fallback mock implementation if no vector store
            mock_documents = [
                Document(
                    id="doc1",
                    content="To reset your password, click on 'Forgot Password' on the login page.",
                    title="Password Reset Guide",
                    source="knowledge_base",
                    metadata={"category": "authentication", "last_updated": "2024-01-15"}
                ),
                Document(
                    id="doc2",
                    content="Our IT support services include 24/7 monitoring, incident response, and system maintenance.",
                    title="IT Support Services Overview",
                    source="service_catalog",
                    metadata={"category": "services", "last_updated": "2024-01-10"}
                )
            ]
            
            # Simple keyword matching for mock
            scores = []
            relevant_docs = []
            
            for doc in mock_documents:
                score = self._calculate_relevance(query, doc.content)
                if score > 0:
                    scores.append(score)
                    relevant_docs.append(doc)
            
            # Sort by score
            if relevant_docs:
                # Sort without numpy for MVP
                sorted_pairs = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
                sorted_indices = [i for i, _ in sorted_pairs]
                relevant_docs = [relevant_docs[i] for i in sorted_indices]
                scores = [scores[i] for i in sorted_indices]
        
        return RetrievalResult(
            documents=relevant_docs,
            scores=scores,
            query=query,
            refined_query=query
        )
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Simple relevance calculation for mock implementation"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
            
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)


class ResponseGenerator:
    """
    Generates responses using LLM with retrieved context
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
    async def generate(self, 
                      query: str,
                      retrieved_docs: List[Document],
                      conversation_context: Optional[Dict] = None) -> str:
        """
        Generate response using LLM with retrieved context
        
        Args:
            query: User query
            retrieved_docs: Retrieved relevant documents
            conversation_context: Previous conversation context
            
        Returns:
            Generated response
        """
        # Construct prompt with retrieved context
        context_str = "\n\n".join([
            f"Source: {doc.source}\n{doc.content}" 
            for doc in retrieved_docs
        ])
        
        prompt = f"""Based on the following context, answer the user's question.
        
Context:
{context_str}

User Question: {query}

Provide a helpful, accurate response based only on the given context. 
If the context doesn't contain enough information, say so."""

        # In production, use actual LLM
        # if self.llm_client:
        #     response = await self.llm_client.generate(prompt)
        
        # Mock implementation
        if retrieved_docs:
            response = f"Based on our documentation: {retrieved_docs[0].content}"
        else:
            response = "I couldn't find specific information about that. Would you like me to connect you with a human agent?"
        
        return response


class ResponseValidator:
    """
    Validates generated responses for accuracy and safety
    Inspired by Fin.ai's validation approach
    """
    
    def __init__(self):
        self.safety_checks = [
            self._check_no_hallucination,
            self._check_no_sensitive_info,
            self._check_appropriate_confidence,
            self._check_no_harmful_content
        ]
    
    async def validate(self, 
                      response: str,
                      source_docs: List[Document],
                      query: str) -> Tuple[bool, Dict[str, any]]:
        """
        Validate generated response
        
        Args:
            response: Generated response
            source_docs: Source documents used
            query: Original user query
            
        Returns:
            Tuple of (is_valid, validation_metadata)
        """
        validation_results = {
            "checks_passed": [],
            "checks_failed": [],
            "confidence": 0.0,
            "warnings": []
        }
        
        # Run all safety checks
        for check in self.safety_checks:
            passed, metadata = await check(response, source_docs, query)
            if passed:
                validation_results["checks_passed"].append(check.__name__)
            else:
                validation_results["checks_failed"].append({
                    "check": check.__name__,
                    "reason": metadata.get("reason", "Unknown")
                })
        
        # Calculate overall validation result
        is_valid = len(validation_results["checks_failed"]) == 0
        validation_results["confidence"] = len(validation_results["checks_passed"]) / len(self.safety_checks)
        
        return is_valid, validation_results
    
    async def _check_no_hallucination(self, response: str, source_docs: List[Document], query: str) -> Tuple[bool, Dict]:
        """Check that response is grounded in source documents"""
        # Simple implementation - check if response content appears in sources
        if not source_docs:
            return True, {"reason": "No source documents to verify against"}
        
        # In production, use more sophisticated grounding checks
        source_content = " ".join([doc.content for doc in source_docs])
        
        # Very basic check - ensure key phrases from response appear in sources
        response_words = set(response.lower().split())
        source_words = set(source_content.lower().split())
        
        overlap_ratio = len(response_words.intersection(source_words)) / len(response_words)
        
        if overlap_ratio < 0.3:  # Threshold for hallucination detection
            return False, {"reason": "Response contains information not found in sources"}
        
        return True, {"overlap_ratio": overlap_ratio}
    
    async def _check_no_sensitive_info(self, response: str, source_docs: List[Document], query: str) -> Tuple[bool, Dict]:
        """Check that response doesn't contain sensitive information"""
        sensitive_patterns = [
            "password", "api_key", "secret", "token",
            "credit_card", "ssn", "social_security"
        ]
        
        response_lower = response.lower()
        for pattern in sensitive_patterns:
            if pattern in response_lower:
                return False, {"reason": f"Response contains sensitive information: {pattern}"}
        
        return True, {}
    
    async def _check_appropriate_confidence(self, response: str, source_docs: List[Document], query: str) -> Tuple[bool, Dict]:
        """Check that response has appropriate confidence level"""
        # Check if response admits uncertainty when appropriate
        uncertainty_phrases = [
            "i don't have enough information",
            "i couldn't find",
            "would you like me to connect you with",
            "i'm not sure"
        ]
        
        has_uncertainty = any(phrase in response.lower() for phrase in uncertainty_phrases)
        has_sources = len(source_docs) > 0
        
        # If no sources but response is confident, that's bad
        if not has_sources and not has_uncertainty:
            return False, {"reason": "Response is too confident without supporting sources"}
        
        return True, {"has_uncertainty": has_uncertainty, "has_sources": has_sources}
    
    async def _check_no_harmful_content(self, response: str, source_docs: List[Document], query: str) -> Tuple[bool, Dict]:
        """Check that response doesn't contain harmful content"""
        # Basic check for harmful patterns
        harmful_patterns = [
            "hack", "exploit", "vulnerability", "breach",
            "ddos", "injection", "malware"
        ]
        
        response_lower = response.lower()
        
        # Allow these terms if they're in an educational/defensive context
        for pattern in harmful_patterns:
            if pattern in response_lower:
                # Check context - if it's about protection/defense, it's okay
                defensive_context = any(term in response_lower for term in ["protect", "prevent", "secure", "defend"])
                if not defensive_context:
                    return False, {"reason": f"Response contains potentially harmful content: {pattern}"}
        
        return True, {}


class EnhancedRAG:
    """
    Main RAG orchestrator implementing Fin.ai-inspired pipeline
    """
    
    def __init__(self, 
                 query_refiner: Optional[QueryRefiner] = None,
                 retriever: Optional[SemanticRetriever] = None,
                 generator: Optional[ResponseGenerator] = None,
                 validator: Optional[ResponseValidator] = None):
        self.query_refiner = query_refiner or QueryRefiner()
        self.retriever = retriever or SemanticRetriever()
        self.generator = generator or ResponseGenerator()
        self.validator = validator or ResponseValidator()
    
    async def process(self, 
                     query: str,
                     context: Optional[Dict] = None,
                     safety_mode: bool = True) -> GenerationResult:
        """
        Process query through complete RAG pipeline
        
        Args:
            query: User query
            context: Conversation context
            safety_mode: Whether to enforce validation
            
        Returns:
            GenerationResult with response and metadata
        """
        # Stage 1: Query Refinement
        refined_query = await self.query_refiner.refine_query(query, context)
        
        # Stage 2: Document Retrieval
        retrieval_result = await self.retriever.retrieve(refined_query)
        
        # Stage 3: Response Generation
        response = await self.generator.generate(
            query=refined_query,
            retrieved_docs=retrieval_result.documents,
            conversation_context=context
        )
        
        # Stage 4: Validation
        validation_passed = True
        validation_metadata = {}
        
        if safety_mode:
            validation_passed, validation_metadata = await self.validator.validate(
                response=response,
                source_docs=retrieval_result.documents,
                query=query
            )
        
        # If validation fails, generate safe fallback response
        if not validation_passed:
            response = "I apologize, but I don't have enough verified information to answer that question accurately. Would you like me to connect you with a human agent who can help?"
        
        # Compile final result
        return GenerationResult(
            response=response,
            confidence=validation_metadata.get("confidence", 1.0),
            sources=[doc.id for doc in retrieval_result.documents],
            validation_passed=validation_passed,
            metadata={
                "refined_query": refined_query,
                "retrieval_scores": retrieval_result.scores,
                "validation_details": validation_metadata,
                "document_count": len(retrieval_result.documents)
            }
        )