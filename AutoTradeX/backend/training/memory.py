"""
Vector Memory System for AutoTradeX
Stores and retrieves trading experiences using Qdrant vector database
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.utils.config import get_config_value

logger = logging.getLogger(__name__)

class QdrantMemory:
    """Vector memory system using Qdrant"""
    
    def __init__(self):
        """Initialize the Qdrant memory system"""
        self.url = get_config_value("qdrant.url")
        self.api_key = get_config_value("qdrant.api_key")
        self.collection_name = get_config_value("qdrant.collection_name", "autotradex_memory")
        self.vector_size = 1536  # Default for embedding models
        
        logger.debug(f"Initializing QdrantMemory with URL: {self.url}")
        
        try:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key
            )
            self._ensure_collection_exists()
            logger.info(f"Connected to Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
    
    def _ensure_collection_exists(self) -> None:
        """Ensure the collection exists, create if it doesn't"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                
                # Create payload index for filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="market_regime",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="outcome_type",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timestamp",
                    field_schema=models.PayloadSchemaType.DATETIME
                )
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (simplified version)"""
        # In a real implementation, this would use a proper embedding model
        # For now, we'll use a simple deterministic hash-based approach
        import hashlib
        
        # Create a deterministic but unique vector based on the text
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to a normalized vector of the right dimension
        np.random.seed(int.from_bytes(hash_bytes[:4], byteorder='big'))
        vector = np.random.normal(0, 1, self.vector_size)
        return (vector / np.linalg.norm(vector)).tolist()
    
    def record(self, strategy_id: str, outcome: float, market_conditions: Dict[str, Any], 
               lessons: List[str]) -> bool:
        """Record a trade outcome and its context"""
        if not self.client:
            logger.error("Cannot record memory: Qdrant client not initialized")
            return False
        
        try:
            # Create memory entry
            memory_text = (
                f"Strategy {strategy_id} resulted in {outcome:.2f}x return under "
                f"{market_conditions.get('market_regime', 'UNKNOWN')} regime. "
                f"Lessons: {', '.join(lessons)}"
            )
            
            # Determine outcome type
            if outcome > 1.05:
                outcome_type = "PROFIT"
            elif outcome < 0.95:
                outcome_type = "LOSS"
            else:
                outcome_type = "NEUTRAL"
            
            # Generate embedding
            vector = self._generate_embedding(memory_text)
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=str(int(datetime.now().timestamp() * 1000)),
                        vector=vector,
                        payload={
                            "strategy_id": strategy_id,
                            "outcome": outcome,
                            "outcome_type": outcome_type,
                            "market_regime": market_conditions.get("market_regime", "UNKNOWN"),
                            "market_conditions": market_conditions,
                            "lessons": lessons,
                            "memory_text": memory_text,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                ]
            )
            
            logger.info(f"Recorded memory for strategy {strategy_id} with outcome {outcome:.2f}x")
            return True
            
        except Exception as e:
            logger.error(f"Error recording memory: {e}")
            return False
    
    def retrieve_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories similar to the query"""
        if not self.client:
            logger.error("Cannot retrieve memories: Qdrant client not initialized")
            return []
        
        try:
            # Generate query embedding
            query_vector = self._generate_embedding(query)
            
            # Search for similar memories
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            # Format results
            memories = []
            for result in results:
                payload = result.payload
                memories.append({
                    "strategy_id": payload.get("strategy_id"),
                    "outcome": payload.get("outcome"),
                    "market_regime": payload.get("market_regime"),
                    "memory_text": payload.get("memory_text"),
                    "similarity": result.score
                })
            
            logger.debug(f"Retrieved {len(memories)} similar memories")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving similar memories: {e}")
            return []
    
    def retrieve_by_regime(self, market_regime: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories for a specific market regime"""
        if not self.client:
            logger.error("Cannot retrieve memories: Qdrant client not initialized")
            return []
        
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="market_regime",
                            match=models.MatchValue(value=market_regime)
                        )
                    ]
                ),
                limit=limit
            )
            
            memories = []
            for point in results[0]:
                payload = point.payload
                memories.append({
                    "strategy_id": payload.get("strategy_id"),
                    "outcome": payload.get("outcome"),
                    "market_regime": payload.get("market_regime"),
                    "memory_text": payload.get("memory_text")
                })
            
            logger.info(f"Retrieved {len(memories)} memories for regime {market_regime}")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories by regime: {e}")
            return []
    
    def get_regime_performance(self, market_regime: str) -> Dict[str, Any]:
        """Get performance statistics for a specific market regime"""
        memories = self.retrieve_by_regime(market_regime, limit=100)
        
        if not memories:
            return {
                "regime": market_regime,
                "count": 0,
                "avg_outcome": 0,
                "win_rate": 0,
                "best_strategy": None
            }
        
        # Calculate statistics
        outcomes = [m.get("outcome", 1.0) for m in memories]
        win_count = sum(1 for o in outcomes if o > 1.05)
        
        # Find best strategy
        strategy_performance = {}
        for memory in memories:
            strategy_id = memory.get("strategy_id")
            outcome = memory.get("outcome", 1.0)
            
            if strategy_id not in strategy_performance:
                strategy_performance[strategy_id] = []
            
            strategy_performance[strategy_id].append(outcome)
        
        best_strategy = None
        best_avg = 0
        
        for strategy_id, outcomes in strategy_performance.items():
            avg = sum(outcomes) / len(outcomes)
            if avg > best_avg and len(outcomes) >= 3:
                best_avg = avg
                best_strategy = strategy_id
        
        return {
            "regime": market_regime,
            "count": len(memories),
            "avg_outcome": sum(outcomes) / len(outcomes),
            "win_rate": win_count / len(memories),
            "best_strategy": best_strategy
        }
    
    def clear_all_memories(self) -> bool:
        """Clear all memories (use with caution)"""
        if not self.client:
            return False
        
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection_exists()
            logger.warning("All memories have been cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False
