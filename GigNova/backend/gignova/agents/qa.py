#!/usr/bin/env python3
"""
GigNova: QA Agent
Enhanced with MCP integration
"""

import uuid
import logging
import numpy as np
from typing import Dict, Any

from gignova.models.base import AgentType, AgentConfig, QAResult
from gignova.agents.base import BaseAgent
from gignova.ipfs.manager_mcp import IPFSManager
from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.QA, config)
        self.ipfs_manager = IPFSManager()
        
    async def validate_deliverable(self, job_id: str, job_requirements: str, deliverable_hash: str) -> QAResult:
        """Validate deliverable against job requirements using MCP storage"""
        try:
            # Log validation attempt to analytics
            await mcp_manager.analytics_log_event(
                event_type="qa_validation_started",
                event_data={
                    "job_id": job_id,
                    "deliverable_hash": deliverable_hash,
                    "agent_id": self.agent_id
                }
            )
            
            # Retrieve deliverable from MCP storage
            deliverable_data = await self.ipfs_manager.retrieve_deliverable(deliverable_hash)
            
            # For text deliverables, compare embeddings
            if deliverable_data:
                deliverable_text = deliverable_data.decode('utf-8', errors='ignore')
                
                # Calculate similarity using vector embeddings
                req_embedding = self.vector_manager.encoder.encode(job_requirements)
                del_embedding = self.vector_manager.encoder.encode(deliverable_text)
                
                similarity = np.dot(req_embedding, del_embedding) / (
                    np.linalg.norm(req_embedding) * np.linalg.norm(del_embedding)
                )
                
                passed = similarity >= self.config.qa_similarity_threshold
                
                # Create result
                result = QAResult(
                    job_id=job_id,
                    deliverable_hash=deliverable_hash,
                    similarity_score=float(similarity),
                    passed=passed,
                    feedback=f"Similarity score: {similarity:.2f}. {'Approved' if passed else 'Needs revision'}."
                )
                
                # Log validation result to analytics
                await mcp_manager.analytics_log_event(
                    event_type="qa_validation_completed",
                    event_data={
                        "job_id": job_id,
                        "deliverable_hash": deliverable_hash,
                        "agent_id": self.agent_id,
                        "similarity_score": float(similarity),
                        "passed": passed
                    }
                )
                
                # Store outcome for learning
                await self.learn_from_outcome({
                    "type": "qa_validation",
                    "job_id": job_id,
                    "deliverable_hash": deliverable_hash,
                    "similarity_score": float(similarity),
                    "passed": passed,
                    "timestamp": 0  # Should be current timestamp in production
                })
                
                return result
            else:
                result = QAResult(
                    job_id=job_id,
                    deliverable_hash=deliverable_hash,
                    similarity_score=0.0,
                    passed=False,
                    feedback="Could not retrieve deliverable for validation."
                )
                
                # Log error to analytics
                await mcp_manager.analytics_log_event(
                    event_type="qa_validation_error",
                    event_data={
                        "job_id": job_id,
                        "deliverable_hash": deliverable_hash,
                        "agent_id": self.agent_id,
                        "error": "Could not retrieve deliverable"
                    }
                )
                
                return result
                
        except Exception as e:
            logger.error(f"QA validation failed: {e}")
            
            # Log error to analytics
            await mcp_manager.analytics_log_event(
                event_type="qa_validation_error",
                event_data={
                    "job_id": job_id,
                    "deliverable_hash": deliverable_hash,
                    "agent_id": self.agent_id,
                    "error": str(e)
                }
            )
            
            return QAResult(
                job_id=job_id,
                deliverable_hash=deliverable_hash,
                similarity_score=0.0,
                passed=False,
                feedback=f"Validation error: {str(e)}"
            )
            
    async def evolve(self) -> Dict[str, Any]:
        """Evolve the QA agent based on historical performance"""
        # Get base evolution metrics
        metrics = await super().evolve()
        
        # Get QA-specific metrics from analytics MCP
        qa_metrics = await mcp_manager.analytics_get_metrics(
            metric_type="qa_performance",
            time_range="30d",  # Last 30 days
            filters={
                "agent_id": self.agent_id
            }
        )
        
        if not qa_metrics.get("success"):
            return {
                **metrics,
                "evolved": False,
                "reason": "Failed to retrieve QA metrics"
            }
        
        # Extract metrics for evolution
        avg_similarity = qa_metrics.get("data", {}).get("average_similarity", 0.0)
        false_positives = qa_metrics.get("data", {}).get("false_positives", 0)
        false_negatives = qa_metrics.get("data", {}).get("false_negatives", 0)
        
        # Adjust threshold based on false positives/negatives
        old_threshold = self.config.qa_similarity_threshold
        new_threshold = old_threshold
        
        if false_positives > false_negatives and false_positives > 5:
            # Too many false positives, increase threshold
            new_threshold = min(0.95, old_threshold + 0.05)
        elif false_negatives > false_positives and false_negatives > 5:
            # Too many false negatives, decrease threshold
            new_threshold = max(0.5, old_threshold - 0.05)
        
        # Update threshold if changed
        if new_threshold != old_threshold:
            self.config.qa_similarity_threshold = new_threshold
            logger.info(f"QA agent evolved: threshold adjusted from {old_threshold:.2f} to {new_threshold:.2f}")
            
            # Log evolution to analytics
            await mcp_manager.analytics_log_event(
                event_type="agent_evolution",
                event_data={
                    "agent_type": self.agent_type.value,
                    "agent_id": self.agent_id,
                    "parameter": "qa_similarity_threshold",
                    "old_value": old_threshold,
                    "new_value": new_threshold,
                    "reason": "Threshold adjusted based on false positive/negative rates"
                }
            )
            
            return {
                **metrics,
                "evolved": True,
                "parameter": "qa_similarity_threshold",
                "old_value": old_threshold,
                "new_value": new_threshold
            }
        
        return {
            **metrics,
            "evolved": False,
            "reason": "No evolution needed based on current metrics"
        }
