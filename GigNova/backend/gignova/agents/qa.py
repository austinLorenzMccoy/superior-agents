#!/usr/bin/env python3
"""
GigNova: QA Agent
Modular implementation for quality assurance
"""

import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional

from gignova.models.base import AgentType, AgentConfig, QAResult
from gignova.agents.base import BaseAgent
from gignova.utils.service_factory import service_factory
from gignova.utils.analytics import analytics_logger

# Configure logging
logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.QA, config)
        
    async def validate_deliverable(self, job_id: str, requirements: str, deliverable_id: str) -> QAResult:
        """Validate deliverable against job requirements using storage manager"""
        try:
            # Log validation attempt to analytics
            await analytics_logger.log_event(
                event_type="qa_validation_started",
                event_data={
                    "job_id": job_id,
                    "deliverable_id": deliverable_id,
                    "agent_id": self.agent_id
                }
            )
            
            # Get storage manager from service factory
            storage_manager = service_factory.get_storage_manager()
            
            # Retrieve deliverable from storage
            result = await storage_manager.retrieve_file(deliverable_id)
            deliverable_data = result.get('data') if result.get('success') else None
            
            # For text deliverables, compare embeddings
            if deliverable_data:
                # Handle both bytes and dict responses from storage manager
                if isinstance(deliverable_data, bytes):
                    deliverable_text = deliverable_data.decode('utf-8', errors='ignore')
                elif isinstance(deliverable_data, dict) and 'content' in deliverable_data:
                    # If it's a dict with content field, use that
                    deliverable_text = str(deliverable_data['content'])
                elif isinstance(deliverable_data, dict):
                    # Otherwise stringify the whole dict
                    deliverable_text = str(deliverable_data)
                else:
                    # Fallback for other types
                    deliverable_text = str(deliverable_data)
                
                # Calculate similarity using vector embeddings
                from gignova.database.vector_manager import vector_manager
                import numpy as np
                
                # Generate embeddings for requirements and deliverable
                req_embedding = await vector_manager.generate_embedding(requirements)
                del_embedding = await vector_manager.generate_embedding(deliverable_text)
                
                similarity = np.dot(req_embedding, del_embedding) / (
                    np.linalg.norm(req_embedding) * np.linalg.norm(del_embedding)
                )
                
                passed = similarity >= self.config.qa_similarity_threshold
                
                # Create result
                result = QAResult(
                    job_id=job_id,
                    deliverable_id=deliverable_id,
                    similarity_score=float(similarity),
                    passed=passed,
                    feedback=f"Similarity score: {similarity:.2f}. {'Approved' if passed else 'Needs revision'}."
                )
                
                # Log validation result to analytics
                await analytics_logger.log_event(
                    event_type="qa_validation_completed",
                    event_data={
                        "job_id": job_id,
                        "deliverable_id": deliverable_id,
                        "agent_id": self.agent_id,
                        "similarity_score": float(similarity),
                        "passed": passed
                    }
                )
                
                # Store outcome for learning
                await self.learn_from_outcome({
                    "type": "qa_validation",
                    "job_id": job_id,
                    "deliverable_id": deliverable_id,
                    "similarity_score": float(similarity),
                    "passed": passed,
                    "timestamp": 0  # Should be current timestamp in production
                })
                
                return result
            else:
                result = QAResult(
                    job_id=job_id,
                    deliverable_id=deliverable_id,
                    similarity_score=0.0,
                    passed=False,
                    feedback="Could not retrieve deliverable for validation."
                )
                
                # Log error to analytics
                await analytics_logger.log_event(
                    event_type="qa_validation_error",
                    event_data={
                        "job_id": job_id,
                        "deliverable_id": deliverable_id,
                        "agent_id": self.agent_id,
                        "error": "Could not retrieve deliverable for validation"
                    }
                )
                
                return result
                
        except Exception as e:
            logger.error(f"QA validation failed: {e}")
            
            # Log error to analytics
            await analytics_logger.log_event(
                event_type="qa_validation_error",
                event_data={
                    "job_id": job_id,
                    "deliverable_id": deliverable_id,
                    "agent_id": self.agent_id,
                    "error": str(e)
                }
            )
            
            return QAResult(
                job_id=job_id,
                deliverable_id=deliverable_id,
                similarity_score=0.0,
                passed=False,
                feedback=f"Validation failed: {str(e)}"
            )
            
    async def evolve(self) -> Dict[str, Any]:
        """Evolve the QA agent based on historical performance"""
        # Get base evolution metrics
        metrics = await super().evolve()
        
        # Get recent QA validation events
        qa_events = await analytics_logger.get_events(
            event_type="qa_validation_completed",
            limit=100,
            time_range_days=30  # Last 30 days
        )
        
        if not qa_events:
            return {
                **metrics,
                "evolved": False,
                "reason": "No QA validation data available for evolution"
            }
            
        # Calculate QA metrics from events
        qa_metrics = {
            "average_similarity": 0.0,
            "false_positives": 0,
            "false_negatives": 0,
            "total_validations": len(qa_events)
        }
        
        # Process events to calculate metrics
        similarity_scores = []
        for event in qa_events:
            data = event.get("data", {})
            similarity = data.get("similarity_score", 0.0)
            similarity_scores.append(similarity)
            
            # Check for false positives/negatives if feedback data available
            if "human_feedback" in data:
                human_approved = data.get("human_feedback", {}).get("approved", False)
                agent_approved = data.get("passed", False)
                
                if agent_approved and not human_approved:
                    qa_metrics["false_positives"] += 1
                elif not agent_approved and human_approved:
                    qa_metrics["false_negatives"] += 1
        
        # Calculate average similarity
        if similarity_scores:
            qa_metrics["average_similarity"] = sum(similarity_scores) / len(similarity_scores)
        
        # Extract metrics for evolution
        avg_similarity = qa_metrics.get("average_similarity", 0.0)
        false_positives = qa_metrics.get("false_positives", 0)
        false_negatives = qa_metrics.get("false_negatives", 0)
        
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
            await analytics_logger.log_event(
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
