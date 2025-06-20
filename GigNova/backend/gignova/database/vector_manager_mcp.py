#!/usr/bin/env python3
"""
GigNova: Vector Database Manager (MCP Implementation)
Replaces the in-memory vector database with MCP vector server integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class VectorManager:
    def __init__(self):
        """Initialize vector manager with MCP integration"""
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Initialized vector manager with MCP integration")
    
    async def store_job_embedding(self, job_id: str, job_text: str, metadata: Dict):
        """Store job posting embedding via MCP vector server"""
        try:
            # Generate embedding locally
            embedding = self.encoder.encode(job_text).tolist()
            
            # Store via MCP
            result = await mcp_manager.vector_store_embedding(
                id=f"job_{job_id}",
                vector=embedding,
                metadata={
                    "type": "job",
                    "text": job_text,
                    **metadata
                }
            )
            
            if result.get("success"):
                logger.info(f"Stored job embedding for job_id: {job_id} via MCP")
            else:
                logger.error(f"Failed to store job embedding: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Job embedding storage failed: {e}")
    
    async def store_freelancer_embedding(self, freelancer_id: str, profile_text: str, metadata: Dict):
        """Store freelancer profile embedding via MCP vector server"""
        try:
            # Generate embedding locally
            embedding = self.encoder.encode(profile_text).tolist()
            
            # Store via MCP
            result = await mcp_manager.vector_store_embedding(
                id=f"freelancer_{freelancer_id}",
                vector=embedding,
                metadata={
                    "type": "freelancer",
                    "text": profile_text,
                    **metadata
                }
            )
            
            if result.get("success"):
                logger.info(f"Stored freelancer embedding for freelancer_id: {freelancer_id} via MCP")
            else:
                logger.error(f"Failed to store freelancer embedding: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Freelancer embedding storage failed: {e}")
    
    async def find_matches(self, job_text: str, limit: int = 10) -> List[Dict]:
        """Find matching freelancers for a job via MCP vector server"""
        try:
            # Generate query embedding locally
            query_embedding = self.encoder.encode(job_text).tolist()
            
            # Search via MCP
            result = await mcp_manager.vector_similarity_search(
                query_vector=query_embedding,
                threshold=0.7,  # Configurable threshold
                limit=limit,
                filter_params={"type": "freelancer"}
            )
            
            if not result.get("success"):
                logger.error(f"MCP similarity search failed: {result.get('error')}")
                return []
            
            # Process and format results
            matches = []
            for item in result.get("results", []):
                matches.append({
                    "freelancer_id": item["id"].replace("freelancer_", ""),
                    "score": item["score"],
                    "payload": item["metadata"]
                })
            
            logger.info(f"Found {len(matches)} matching freelancers via MCP")
            return matches
            
        except Exception as e:
            logger.error(f"Match finding failed: {e}")
            return []
    
    async def store_outcome(self, interaction_id: str, outcome_data: Dict):
        """Store interaction outcome for learning via MCP vector server"""
        try:
            # Convert outcome to text for embedding
            outcome_text = json.dumps(outcome_data)
            
            # Generate embedding locally
            embedding = self.encoder.encode(outcome_text).tolist()
            
            # Store via MCP
            result = await mcp_manager.vector_store_embedding(
                id=f"outcome_{interaction_id}",
                vector=embedding,
                metadata={
                    "type": "outcome",
                    "data": outcome_data,
                    "timestamp": outcome_data.get("timestamp", 0)
                }
            )
            
            if result.get("success"):
                logger.info(f"Stored outcome for interaction_id: {interaction_id} via MCP")
            else:
                logger.error(f"Failed to store outcome: {result.get('error')}")
            
            # Also log to analytics MCP
            await mcp_manager.analytics_log_event(
                event_type="agent_outcome",
                event_data=outcome_data
            )
            
        except Exception as e:
            logger.error(f"Outcome storage failed: {e}")
