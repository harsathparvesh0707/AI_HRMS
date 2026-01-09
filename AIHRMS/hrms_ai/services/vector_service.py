"""
Vector Service - Handles vector search operations
"""
import logging
from typing import List, Dict, Any
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from ..config.settings import settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector operations"""
    
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model
            )
            self.vector_store = Chroma(
                persist_directory=settings.vector_persist_dir,
                embedding_function=self.embeddings
            )
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.error(f"Vector service initialization failed: {e}")
            raise
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            hits = []
            for doc, score in results:
                similarity = 1 - score
                
                hits.append({
                    "employee_id": doc.metadata.get("employee_id"),
                    "display_name": doc.metadata.get("display_name", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": float(similarity)
                })
            
            logger.info(f"Vector search found {len(hits)} results")
            return hits
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to vector store"""
        try:
            self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    async def clear_store(self) -> bool:
        """Clear all documents from vector store"""
        try:
            # Get all collection IDs and delete them
            collections = self.vector_store._client.list_collections()
            for collection in collections:
                self.vector_store._client.delete_collection(collection.name)
            
            # Reinitialize the vector store
            self.vector_store = Chroma(
                persist_directory=settings.vector_persist_dir,
                embedding_function=self.embeddings
            )
            logger.info("Vector store cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False