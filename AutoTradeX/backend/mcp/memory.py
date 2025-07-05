"""
Vector Memory Module for Model Context Protocol
Implements memory storage and retrieval using ChromaDB
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import logging

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from .protocol import MCPMessage, MessageRole, MessageType

# Set up logging
logger = logging.getLogger(__name__)


class VectorMemory:
    """
    Vector Memory for Model Context Protocol
    Stores and retrieves memories using vector embeddings
    """
    def __init__(
        self,
        storage_type: str = "chroma",
        collection_name: str = "autotradex_memories",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Any] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None
    ):
        """Initialize vector memory"""
        self.storage_type = storage_type.lower()
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.path.join(os.getcwd(), "vector_db")
        self.embedding_function = embedding_function
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        
        # Initialize storage
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize vector storage"""
        if self.storage_type == "chroma":
            self._initialize_chroma()
        elif self.storage_type == "qdrant":
            self._initialize_qdrant()
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _initialize_chroma(self) -> None:
        """Initialize ChromaDB storage"""
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Install it with 'pip install chromadb'")
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
        except Exception:
            logger.info(f"Creating new ChromaDB collection: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
    
    def _initialize_qdrant(self) -> None:
        """Initialize Qdrant storage"""
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client is not installed. Install it with 'pip install qdrant-client'")
        
        # Initialize Qdrant client
        if self.qdrant_url:
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
        else:
            # Local storage
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = QdrantClient(path=self.persist_directory)
        
        # Check if collection exists, create if not
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating new Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # Default for OpenAI embeddings
                        distance=models.Distance.COSINE
                    )
                )
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise
    
    def store_memory(
        self,
        text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        id: Optional[str] = None
    ) -> str:
        """Store a memory in vector storage"""
        memory_id = id or str(uuid.uuid4())
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.utcnow().isoformat()
        
        if self.storage_type == "chroma":
            self._store_in_chroma(memory_id, text, metadata, embedding)
        elif self.storage_type == "qdrant":
            self._store_in_qdrant(memory_id, text, metadata, embedding)
        
        return memory_id
    
    def _store_in_chroma(
        self,
        id: str,
        text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> None:
        """Store memory in ChromaDB"""
        # Convert metadata to string values for ChromaDB
        string_metadata = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                          for k, v in metadata.items()}
        
        # Add document to collection
        self.collection.add(
            ids=[id],
            documents=[text],
            metadatas=[string_metadata],
            embeddings=[embedding] if embedding else None
        )
    
    def _store_in_qdrant(
        self,
        id: str,
        text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> None:
        """Store memory in Qdrant"""
        if not embedding and not self.embedding_function:
            raise ValueError("Embedding or embedding_function must be provided for Qdrant storage")
        
        # Get embedding if not provided
        if not embedding and self.embedding_function:
            embedding = self.embedding_function(text)
        
        # Add document to collection
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=id,
                    vector=embedding,
                    payload={"text": text, **metadata}
                )
            ]
        )
    
    def retrieve_similar(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve similar memories based on query"""
        if self.storage_type == "chroma":
            return self._retrieve_from_chroma(query, n_results, filter, embedding)
        elif self.storage_type == "qdrant":
            return self._retrieve_from_qdrant(query, n_results, filter, embedding)
        return []
    
    def _retrieve_from_chroma(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from ChromaDB"""
        # Query collection
        results = self.collection.query(
            query_texts=[query] if not embedding else None,
            query_embeddings=[embedding] if embedding else None,
            n_results=n_results,
            where=filter
        )
        
        # Format results
        memories = []
        if results and "ids" in results and results["ids"]:
            for i, id in enumerate(results["ids"][0]):
                memories.append({
                    "id": id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results.get("distances", [[]])[0][i] if "distances" in results else None
                })
        
        return memories
    
    def _retrieve_from_qdrant(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from Qdrant"""
        if not embedding and not self.embedding_function:
            raise ValueError("Embedding or embedding_function must be provided for Qdrant retrieval")
        
        # Get embedding if not provided
        if not embedding and self.embedding_function:
            embedding = self.embedding_function(query)
        
        # Convert filter to Qdrant format if provided
        qdrant_filter = None
        if filter:
            filter_conditions = []
            for key, value in filter.items():
                filter_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            qdrant_filter = models.Filter(
                must=filter_conditions
            )
        
        # Query collection
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=n_results,
            query_filter=qdrant_filter
        )
        
        # Format results
        memories = []
        for result in results:
            payload = result.payload or {}
            text = payload.pop("text", "")
            memories.append({
                "id": result.id,
                "text": text,
                "metadata": payload,
                "distance": result.score
            })
        
        return memories
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID"""
        if self.storage_type == "chroma":
            return self._get_from_chroma(memory_id)
        elif self.storage_type == "qdrant":
            return self._get_from_qdrant(memory_id)
        return None
    
    def _get_from_chroma(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from ChromaDB"""
        try:
            result = self.collection.get(ids=[memory_id])
            if result and result["ids"] and len(result["ids"]) > 0:
                return {
                    "id": result["ids"][0],
                    "text": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
        except Exception as e:
            logger.error(f"Error retrieving memory from ChromaDB: {e}")
        return None
    
    def _get_from_qdrant(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from Qdrant"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id]
            )
            if result and len(result) > 0:
                payload = result[0].payload or {}
                text = payload.pop("text", "")
                return {
                    "id": result[0].id,
                    "text": text,
                    "metadata": payload
                }
        except Exception as e:
            logger.error(f"Error retrieving memory from Qdrant: {e}")
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        try:
            if self.storage_type == "chroma":
                self.collection.delete(ids=[memory_id])
            elif self.storage_type == "qdrant":
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=[memory_id])
                )
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    def update_memory(
        self,
        memory_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Update a memory"""
        # Get existing memory
        existing = self.get_memory(memory_id)
        if not existing:
            return False
        
        # Update with new values or keep existing
        updated_text = text if text is not None else existing.get("text", "")
        updated_metadata = {**existing.get("metadata", {}), **(metadata or {})}
        
        # Delete and re-add with updated values
        self.delete_memory(memory_id)
        self.store_memory(
            text=updated_text,
            metadata=updated_metadata,
            embedding=embedding,
            id=memory_id
        )
        return True
    
    def record_trade_outcome(
        self,
        strategy_id: str,
        outcome: float,
        market_conditions: Dict[str, Any],
        lessons: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a trade outcome in memory"""
        # Create memory text
        text = f"Strategy {strategy_id} achieved {outcome:.2f}x ROI under market conditions: {json.dumps(market_conditions)}. Lessons learned: {'; '.join(lessons)}"
        
        # Create metadata
        memory_metadata = {
            "type": "trade_outcome",
            "strategy_id": strategy_id,
            "outcome": outcome,
            "market_conditions": market_conditions,
            "lessons": lessons,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add additional metadata
        if metadata:
            memory_metadata.update(metadata)
        
        # Store in vector memory
        return self.store_memory(text=text, metadata=memory_metadata)
    
    def get_similar_trades(
        self,
        market_conditions: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get similar trades based on market conditions"""
        # Create query text from market conditions
        query_text = f"Market conditions: {json.dumps(market_conditions)}"
        
        # Filter for trade outcomes only
        filter_dict = {"type": "trade_outcome"}
        
        # Retrieve similar memories
        return self.retrieve_similar(
            query=query_text,
            n_results=n_results,
            filter=filter_dict
        )
    
    def get_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Get performance metrics for a strategy"""
        # Filter for specific strategy
        filter_dict = {"type": "trade_outcome", "strategy_id": strategy_id}
        
        if self.storage_type == "chroma":
            results = self.collection.get(where=filter_dict)
        elif self.storage_type == "qdrant":
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="trade_outcome")
                        ),
                        models.FieldCondition(
                            key="strategy_id",
                            match=models.MatchValue(value=strategy_id)
                        )
                    ]
                ),
                limit=100
            )[0]
        else:
            return {"error": "Unsupported storage type"}
        
        # Process results
        outcomes = []
        if self.storage_type == "chroma" and results and "metadatas" in results:
            for metadata in results["metadatas"]:
                if "outcome" in metadata:
                    outcomes.append(float(metadata["outcome"]))
        elif self.storage_type == "qdrant":
            for point in results:
                if point.payload and "outcome" in point.payload:
                    outcomes.append(float(point.payload["outcome"]))
        
        # Calculate metrics
        if outcomes:
            return {
                "strategy_id": strategy_id,
                "trade_count": len(outcomes),
                "avg_outcome": sum(outcomes) / len(outcomes),
                "max_outcome": max(outcomes),
                "min_outcome": min(outcomes),
                "total_roi": sum([o - 1 for o in outcomes])
            }
        else:
            return {
                "strategy_id": strategy_id,
                "trade_count": 0,
                "avg_outcome": 0,
                "max_outcome": 0,
                "min_outcome": 0,
                "total_roi": 0
            }
