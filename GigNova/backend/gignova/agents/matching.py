#!/usr/bin/env python3
"""
GigNova: Matching Agent
"""

import uuid
import logging
from typing import Dict, List, Any

from gignova.models.base import AgentType, AgentConfig, JobPost, JobMatch
from gignova.agents.base import BaseAgent
from gignova.utils.service_factory import service_factory
from gignova.utils.analytics import analytics_logger

# Configure logging
logger = logging.getLogger(__name__)


class MatchingAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.MATCHING, config)
        
    async def find_matches(self, job_post: JobPost) -> List[JobMatch]:
        """Find matching freelancers for a job"""
        job_text = f"{job_post.title} {job_post.description} {' '.join(job_post.skills)}"
        
        try:
            # Log the matching attempt
            await analytics_logger.log_event(
                event_type="matching_attempt",
                event_data={
                    "job_title": job_post.title,
                    "skills_required": job_post.skills
                }
            )
            
            # Get vector manager from service factory
            vector_manager = service_factory.get_vector_manager()
            
            # Generate embedding for the job text and perform similarity search
            job_embedding = await vector_manager.generate_embedding(job_text)
            search_results = await vector_manager.similarity_search(
                query=job_embedding,
                top_k=10
            )
            
            if "error" in search_results:
                logger.error(f"Vector search error: {search_results['error']}")
                return []
                
            matches = search_results.get("results", [])
            
            # Process and filter matches
            job_matches = []
            for match in matches:
                # Extract freelancer ID from metadata
                metadata = match.get("metadata", {})
                freelancer_id = metadata.get("freelancer_id")
                if not freelancer_id:
                    continue
                    
                # Check if score meets threshold
                score = match.get("score", 0)
                if score >= self.config.confidence_threshold:
                    job_matches.append(JobMatch(
                        job_id=str(uuid.uuid4()),
                        freelancer_id=freelancer_id,
                        confidence_score=score,
                        match_reasons=[f"Skill match: {score:.2f}"]
                    ))
            
            # Log match results
            await analytics_logger.log_event(
                event_type="matching_results",
                event_data={
                    "job_title": job_post.title,
                    "matches_found": len(job_matches),
                    "confidence_threshold": self.config.confidence_threshold
                }
            )
            
            return job_matches
            
        except Exception as e:
            logger.error(f"Error in finding matches: {str(e)}")
            await analytics_logger.log_event(
                event_type="matching_error",
                event_data={"error": str(e)}
            )
            return []
    
    async def evolve_threshold(self, recent_outcomes: List[Dict]):
        """Adjust confidence threshold based on recent outcomes"""
        if not recent_outcomes:
            return
            
        success_rate = sum(1 for outcome in recent_outcomes if outcome.get('successful', False)) / len(recent_outcomes)
        old_threshold = self.config.confidence_threshold
        
        if success_rate < 0.6:  # Too many failures
            self.config.confidence_threshold = min(0.95, self.config.confidence_threshold + 0.05)
        elif success_rate > 0.8:  # Too conservative
            self.config.confidence_threshold = max(0.5, self.config.confidence_threshold - 0.02)
        
        # Log the evolution event
        await analytics_logger.log_event(
            event_type="agent_evolution",
            event_data={
                "agent_type": self.agent_type,
                "success_rate": success_rate,
                "old_threshold": old_threshold,
                "new_threshold": self.config.confidence_threshold,
                "outcomes_count": len(recent_outcomes)
            }
        )
        
        logger.info(
            f"Evolved matching threshold: {old_threshold:.2f} -> {self.config.confidence_threshold:.2f} "
            f"(success rate: {success_rate:.2f})"
        )
            
        # Keep within bounds
        self.config.confidence_threshold = max(0.5, min(0.95, self.config.confidence_threshold))
        
        logger.info(f"Matching agent threshold adjusted to: {self.config.confidence_threshold}")
