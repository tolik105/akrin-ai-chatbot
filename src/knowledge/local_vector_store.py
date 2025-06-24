"""
Local vector store implementation using ChromaDB
This can be used instead of Pinecone for development
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime

from src.utils.logging import knowledge_logger as logger


class LocalVectorStore:
    """
    Local vector store using ChromaDB as a Pinecone alternative
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        Initialize local vector store
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("akrin_knowledge_base")
            logger.info("Loaded existing ChromaDB collection")
        except:
            self.collection = self.client.create_collection(
                name="akrin_knowledge_base",
                metadata={"description": "AKRIN AI Chatbot Knowledge Base"}
            )
            logger.info("Created new ChromaDB collection")
    
    def add_documents(self, 
                     documents: List[Dict], 
                     batch_size: int = 100) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents with 'id', 'content', and 'metadata'
            batch_size: Batch size for processing
            
        Returns:
            List of document IDs
        """
        try:
            ids = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Prepare data for ChromaDB
                batch_ids = [doc['id'] for doc in batch]
                batch_texts = [doc['content'] for doc in batch]
                batch_metadatas = [doc.get('metadata', {}) for doc in batch]
                
                # Generate embeddings
                embeddings = self.embedding_model.encode(batch_texts).tolist()
                
                # Add to collection
                self.collection.add(
                    ids=batch_ids,
                    embeddings=embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                
                ids.extend(batch_ids)
                logger.info(f"Added batch of {len(batch)} documents to vector store")
            
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def search(self, 
              query: str, 
              top_k: int = 5,
              filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents
        
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
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def update_document(self, 
                       document_id: str, 
                       content: str, 
                       metadata: Optional[Dict] = None):
        """
        Update a document in the vector store
        
        Args:
            document_id: Document ID to update
            content: New content
            metadata: Optional new metadata
        """
        try:
            # Generate new embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Update in collection
            self.collection.update(
                ids=[document_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata] if metadata else None
            )
            
            logger.info(f"Updated document {document_id} in vector store")
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise
    
    def delete_document(self, document_id: str):
        """
        Delete a document from the vector store
        
        Args:
            document_id: Document ID to delete
        """
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from vector store")
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Get a specific document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document dict or None if not found
        """
        try:
            result = self.collection.get(ids=[document_id])
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    def list_documents(self, 
                      limit: int = 100, 
                      offset: int = 0) -> List[Dict]:
        """
        List all documents in the collection
        
        Args:
            limit: Maximum number of documents to return
            offset: Offset for pagination
            
        Returns:
            List of documents
        """
        try:
            # ChromaDB doesn't have direct pagination, so we get all and slice
            result = self.collection.get(limit=limit + offset)
            
            documents = []
            start_idx = offset
            end_idx = min(offset + limit, len(result['ids']))
            
            for i in range(start_idx, end_idx):
                documents.append({
                    'id': result['ids'][i],
                    'content': result['documents'][i],
                    'metadata': result['metadatas'][i]
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get vector store statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            count = self.collection.count()
            
            return {
                'total_documents': count,
                'embedding_model': 'all-MiniLM-L6-v2',
                'embedding_dimension': 384,
                'storage_path': self.persist_directory,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def clear_all(self):
        """
        Clear all documents from the collection
        WARNING: This will delete all data!
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection("akrin_knowledge_base")
            self.collection = self.client.create_collection(
                name="akrin_knowledge_base",
                metadata={"description": "AKRIN AI Chatbot Knowledge Base"}
            )
            logger.warning("Cleared all documents from vector store")
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> LocalVectorStore:
    """
    Get singleton instance of vector store
    
    Returns:
        LocalVectorStore instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LocalVectorStore()
    return _vector_store_instance