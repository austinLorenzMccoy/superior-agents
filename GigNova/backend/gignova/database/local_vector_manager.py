#!/usr/bin/env python3
"""
Local Vector Database Manager for GigNova
Simple file-based implementation for development and testing
"""

import os
import json
import logging
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalVectorManager:
    """
    Simple file-based vector database manager for development and testing
    Uses JSON files to store embeddings and metadata
    """
    
    def __init__(self, persist_directory: str = "~/.gignova/vectors"):
        """
        Initialize the local vector database manager
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        # Expand user directory if needed
        self.persist_directory = os.path.expanduser(persist_directory)
        
        # Create directory structure if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Path to embeddings file
        self.embeddings_file = os.path.join(self.persist_directory, "embeddings.json")
        
        # Initialize embeddings storage
        self.embeddings = self._load_embeddings()
        
        logger.info(f"Local Vector Manager initialized at {self.persist_directory}")
    
    def _load_embeddings(self) -> Dict[str, Any]:
        """
        Load embeddings from file
        
        Returns:
            Dict: Embeddings data
        """
        try:
            with open(self.embeddings_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty dict if file is empty or doesn't exist
            return {}
    
    def _save_embeddings(self) -> None:
        """
        Save embeddings to file
        """
        with open(self.embeddings_file, 'w') as f:
            json.dump(self.embeddings, f, indent=2)
    
    async def connect(self) -> bool:
        """
        Connect to the vector database (no-op for local implementation)
        
        Returns:
            bool: True if connected successfully
        """
        logger.info("Local vector database connection established")
        return True
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a simple embedding for a text string
        This is a very basic implementation that uses SHA-256 hash
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List[float]: A list of floats representing the embedding
        """
        # Create a deterministic but simple embedding based on hash
        # This is NOT a proper embedding but works for testing
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Convert hash bytes to a list of 32 floats
        embedding = []
        for i in range(32):
            # Convert each byte to a float between -1 and 1
            embedding.append((hash_bytes[i] / 128.0) - 1.0)
        
        # Normalize the embedding to unit length
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [float(x / norm) for x in embedding]
        
        return embedding
    
    async def store_embedding(self, embedding_id: str, embedding: List[float], metadata: Dict = None) -> Dict[str, Any]:
        """
        Store an embedding in the local vector database
        
        Args:
            embedding_id: ID for the embedding
            embedding: List of floats representing the embedding
            metadata: Optional metadata to store with the embedding
            
        Returns:
            Dict with success status and embedding ID
        """
        try:
            # Create entry with metadata
            metadata = metadata or {}
            
            # Store the embedding with metadata
            self.embeddings[embedding_id] = {
                "embedding": embedding,
                "metadata": metadata
            }
            
            # Save to file
            self._save_embeddings()
            
            logger.info(f"Stored embedding with ID: {embedding_id}")
            return {"success": True, "id": embedding_id}
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_embedding(self, embedding_id: str) -> Dict[str, Any]:
        """
        Get an embedding by ID
        
        Args:
            embedding_id: ID of the embedding to retrieve
            
        Returns:
            Dict with embedding and metadata
        """
        try:
            if embedding_id in self.embeddings:
                return {
                    "success": True,
                    "embedding": self.embeddings[embedding_id]["embedding"],
                    "metadata": self.embeddings[embedding_id]["metadata"]
                }
            else:
                return {"success": False, "error": f"Embedding {embedding_id} not found"}
        except Exception as e:
            logger.error(f"Error retrieving embedding: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def similarity_search(self, query: Union[str, List[float]], top_k: int = 5) -> Dict[str, Any]:
        """
        Search for similar embeddings
        
        Args:
            query: Query text or embedding
            top_k: Number of results to return
            
        Returns:
            Dict with search results
        """
        try:
            # Generate embedding if query is a string
            query_embedding = query
            if isinstance(query, str):
                query_embedding = await self.generate_embedding(query)
            
            # Convert query embedding to numpy array
            query_vector = np.array(query_embedding)
            
            # Calculate similarity for all embeddings
            results = []
            for embedding_id, data in self.embeddings.items():
                embedding_vector = np.array(data["embedding"])
                
                # Calculate cosine similarity
                similarity = np.dot(query_vector, embedding_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(embedding_vector)
                )
                
                results.append({
                    "id": embedding_id,
                    "score": float(similarity),
                    "metadata": data["metadata"]
                })
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top_k results
            return {
                "success": True,
                "results": results[:top_k]
            }
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete_embedding(self, embedding_id: str) -> Dict[str, Any]:
        """
        Delete an embedding by ID
        
        Args:
            embedding_id: ID of the embedding to delete
            
        Returns:
            Dict with success status
        """
        try:
            if embedding_id in self.embeddings:
                del self.embeddings[embedding_id]
                self._save_embeddings()
                return {"success": True}
            else:
                return {"success": False, "error": f"Embedding {embedding_id} not found"}
        except Exception as e:
            logger.error(f"Error deleting embedding: {str(e)}")
            return {"success": False, "error": str(e)}

# Create a singleton instance
local_vector_manager = LocalVectorManager()
