#!/usr/bin/env python3
"""
GigNova: Vector Database Manager (Simple In-Memory Implementation)
"""

import os
import json
import time
import logging
import uuid
import random
from typing import Dict, List, Any

import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger(__name__)


class VectorManager:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # In-memory storage for embeddings
        self.db = {
            "jobs": {},
            "freelancers": {},
            "outcomes": {}
        }
        
        logger.info("Initialized in-memory vector database")
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        return dot_product / (norm_a * norm_b)
    
    def store_job_embedding(self, job_id: str, job_text: str, metadata: Dict):
        """Store job posting embedding"""
        try:
            embedding = self.encoder.encode(job_text).tolist()
            
            self.db["jobs"][job_id] = {
                "vector": embedding,
                "payload": {
                    "type": "job",
                    "text": job_text,
                    **metadata
                }
            }
            
            logger.info(f"Stored job embedding for job_id: {job_id}")
            
        except Exception as e:
            logger.error(f"Job embedding storage failed: {e}")
    
    def store_freelancer_embedding(self, freelancer_id: str, profile_text: str, metadata: Dict):
        """Store freelancer profile embedding"""
        try:
            embedding = self.encoder.encode(profile_text).tolist()
            
            self.db["freelancers"][freelancer_id] = {
                "vector": embedding,
                "payload": {
                    "type": "freelancer",
                    "text": profile_text,
                    **metadata
                }
            }
            
            logger.info(f"Stored freelancer embedding for freelancer_id: {freelancer_id}")
            
        except Exception as e:
            logger.error(f"Freelancer embedding storage failed: {e}")
    
    def find_matches(self, job_text: str, limit: int = 10) -> List[Dict]:
        """Find matching freelancers for a job"""
        try:
            query_embedding = self.encoder.encode(job_text).tolist()
            
            # Calculate similarity scores for all freelancers
            scored_freelancers = []
            for freelancer_id, data in self.db["freelancers"].items():
                score = self._cosine_similarity(query_embedding, data["vector"])
                scored_freelancers.append({
                    "freelancer_id": freelancer_id,
                    "score": score,
                    "payload": data["payload"]
                })
            
            # Sort by score (descending) and limit results
            matches = sorted(scored_freelancers, key=lambda x: x["score"], reverse=True)[:limit]
            
            logger.info(f"Found {len(matches)} matching freelancers")
            return matches
            
        except Exception as e:
            logger.error(f"Match finding failed: {e}")
            return []
    
    def store_outcome(self, interaction_id: str, outcome_data: Dict):
        """Store interaction outcome for learning"""
        try:
            outcome_text = json.dumps(outcome_data)
            embedding = self.encoder.encode(outcome_text).tolist()
            
            outcome_id = f"outcome_{interaction_id}"
            self.db["outcomes"][outcome_id] = {
                "vector": embedding,
                "payload": {
                    "type": "outcome",
                    "data": outcome_data,
                    "timestamp": time.time()
                }
            }
            
            logger.info(f"Stored outcome for interaction_id: {interaction_id}")
            
        except Exception as e:
            logger.error(f"Outcome storage failed: {e}")
