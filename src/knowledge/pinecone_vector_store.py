"""
Pinecone vector store implementation for production use
"""

import pinecone
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime
import time

from src.core.config import settings
from src.utils.logging import knowledge_logger as logger


class PineconeVectorStore:
    """
    Production vector store using Pinecone
    """
    
    def __init__(self):
        """Initialize Pinecone vector store"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
            
            # Create or connect to index
            self.index_name = settings.pinecone_index_name
            
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric='cosine',
                    pod_type='p1.x1'  # Starter pod type
                )
                # Wait for index to be ready
                time.sleep(10)
            
            self.index = pinecone.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            raise
    
    def add_documents(self, 
                     documents: List[Dict], 
                     batch_size: int = 100) -> List[str]:
        """
        Add documents to Pinecone
        
        Args:
            documents: List of documents with 'id', 'content', and 'metadata'
            batch_size: Batch size for upsert operations
            
        Returns:
            List of document IDs
        """
        try:
            ids = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Prepare vectors for Pinecone
                vectors_to_upsert = []
                
                for doc in batch:
                    # Generate embedding
                    embedding = self.embedding_model.encode(doc['content']).tolist()
                    
                    # Prepare metadata
                    metadata = doc.get('metadata', {})
                    metadata['content'] = doc['content'][:1000]  # Store truncated content
                    metadata['timestamp'] = datetime.utcnow().isoformat()
                    
                    vectors_to_upsert.append({
                        'id': doc['id'],
                        'values': embedding,
                        'metadata': metadata
                    })
                    
                    ids.append(doc['id'])
                
                # Upsert to Pinecone
                self.index.upsert(vectors=vectors_to_upsert)
                logger.info(f"Added batch of {len(batch)} documents to Pinecone")
            
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to Pinecone: {str(e)}")
            raise
    
    def search(self, 
              query: str, 
              top_k: int = 5,
              filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents in Pinecone
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in Pinecone
            search_params = {
                'vector': query_embedding,
                'top_k': top_k,
                'include_metadata': True
            }
            
            if filter_dict:
                search_params['filter'] = filter_dict
            
            results = self.index.query(**search_params)
            
            # Format results
            formatted_results = []
            for match in results['matches']:
                formatted_results.append({
                    'id': match['id'],
                    'content': match['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in match['metadata'].items() if k != 'content'},
                    'score': match['score']
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Pinecone: {str(e)}")
            return []
    
    def update_document(self, 
                       document_id: str, 
                       content: str, 
                       metadata: Optional[Dict] = None):
        """
        Update a document in Pinecone
        
        Args:
            document_id: Document ID to update
            content: New content
            metadata: Optional new metadata
        """
        try:
            # Generate new embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata['content'] = content[:1000]
            metadata['updated_at'] = datetime.utcnow().isoformat()
            
            # Update in Pinecone
            self.index.upsert(vectors=[{
                'id': document_id,
                'values': embedding,
                'metadata': metadata
            }])
            
            logger.info(f"Updated document {document_id} in Pinecone")
            
        except Exception as e:
            logger.error(f"Error updating document in Pinecone: {str(e)}")
            raise
    
    def delete_document(self, document_id: str):
        """
        Delete a document from Pinecone
        
        Args:
            document_id: Document ID to delete
        """
        try:
            self.index.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from Pinecone")
            
        except Exception as e:
            logger.error(f"Error deleting document from Pinecone: {str(e)}")
            raise
    
    def delete_documents(self, document_ids: List[str]):
        """
        Delete multiple documents from Pinecone
        
        Args:
            document_ids: List of document IDs to delete
        """
        try:
            self.index.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from Pinecone")
            
        except Exception as e:
            logger.error(f"Error deleting documents from Pinecone: {str(e)}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Get Pinecone index statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = self.index.describe_index_stats()
            
            return {
                'total_vectors': stats['total_vector_count'],
                'dimension': stats['dimension'],
                'index_fullness': stats['index_fullness'],
                'namespaces': stats.get('namespaces', {}),
                'index_name': self.index_name,
                'environment': settings.pinecone_environment,
                'embedding_model': 'all-MiniLM-L6-v2',
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {str(e)}")
            return {}
    
    def clear_namespace(self, namespace: str = ""):
        """
        Clear all vectors in a namespace
        
        Args:
            namespace: Namespace to clear (empty string for default namespace)
        """
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.warning(f"Cleared all vectors in namespace: {namespace or 'default'}")
            
        except Exception as e:
            logger.error(f"Error clearing namespace: {str(e)}")
            raise
    
    def fetch_documents(self, document_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch specific documents by ID
        
        Args:
            document_ids: List of document IDs to fetch
            
        Returns:
            Dictionary mapping IDs to document data
        """
        try:
            result = self.index.fetch(ids=document_ids)
            
            documents = {}
            for doc_id, doc_data in result['vectors'].items():
                documents[doc_id] = {
                    'id': doc_id,
                    'content': doc_data['metadata'].get('content', ''),
                    'metadata': {k: v for k, v in doc_data['metadata'].items() if k != 'content'}
                }
            
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            return {}


# Singleton instance
_pinecone_store_instance = None


def get_pinecone_store() -> PineconeVectorStore:
    """
    Get singleton instance of Pinecone vector store
    
    Returns:
        PineconeVectorStore instance
    """
    global _pinecone_store_instance
    if _pinecone_store_instance is None:
        _pinecone_store_instance = PineconeVectorStore()
    return _pinecone_store_instance