#!/usr/bin/env python3
"""
GigNova: QA Agent
"""

import uuid
import logging
import numpy as np
from typing import Dict

from gignova.models.base import AgentType, AgentConfig, QAResult
from gignova.agents.base import BaseAgent
from gignova.ipfs.manager import IPFSManager

# Configure logging
logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.QA, config)
        self.ipfs_manager = IPFSManager()
        
    def validate_deliverable(self, job_requirements: str, deliverable_hash: str) -> QAResult:
        """Validate deliverable against job requirements"""
        try:
            # Retrieve deliverable from local storage
            deliverable_data = self.ipfs_manager.retrieve_deliverable(deliverable_hash)
            
            # For text deliverables, compare embeddings
            if deliverable_data:
                deliverable_text = deliverable_data.decode('utf-8', errors='ignore')
                
                # Calculate similarity
                req_embedding = self.vector_manager.encoder.encode(job_requirements)
                del_embedding = self.vector_manager.encoder.encode(deliverable_text)
                
                similarity = np.dot(req_embedding, del_embedding) / (
                    np.linalg.norm(req_embedding) * np.linalg.norm(del_embedding)
                )
                
                passed = similarity >= self.config.qa_similarity_threshold
                
                return QAResult(
                    job_id=str(uuid.uuid4()),
                    deliverable_hash=deliverable_hash,
                    similarity_score=float(similarity),
                    passed=passed,
                    feedback=f"Similarity score: {similarity:.2f}. {'Approved' if passed else 'Needs revision'}."
                )
            else:
                return QAResult(
                    job_id=str(uuid.uuid4()),
                    deliverable_hash=deliverable_hash,
                    similarity_score=0.0,
                    passed=False,
                    feedback="Could not retrieve deliverable for validation."
                )
                
        except Exception as e:
            logger.error(f"QA validation failed: {e}")
            return QAResult(
                job_id=str(uuid.uuid4()),
                deliverable_hash=deliverable_hash,
                similarity_score=0.0,
                passed=False,
                feedback=f"Validation error: {str(e)}"
            )
