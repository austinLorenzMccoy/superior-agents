#!/usr/bin/env python3
"""
GigNova: Matching Agent
"""

import uuid
import logging
from typing import Dict, List

from gignova.models.base import AgentType, AgentConfig, JobPost, JobMatch
from gignova.agents.base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class MatchingAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.MATCHING, config)
        
    async def find_matches(self, job_post: JobPost) -> List[JobMatch]:
        """Find matching freelancers for a job"""
        job_text = f"{job_post.title} {job_post.description} {' '.join(job_post.skills)}"
        
        # Get matches from vector DB
        matches = await self.vector_manager.find_matches(job_text, limit=10)
        
        job_matches = []
        for match in matches:
            if match['score'] >= self.config.confidence_threshold:
                job_matches.append(JobMatch(
                    job_id=str(uuid.uuid4()),
                    freelancer_id=match['freelancer_id'],
                    confidence_score=match['score'],
                    match_reasons=[f"Skill match: {match['score']:.2f}"]
                ))
        
        return job_matches
    
    def evolve_threshold(self, recent_outcomes: List[Dict]):
        """Adjust confidence threshold based on recent outcomes"""
        if not recent_outcomes:
            return
            
        success_rate = sum(1 for outcome in recent_outcomes if outcome.get('successful', False)) / len(recent_outcomes)
        
        if success_rate < 0.6:  # Too many failures
            self.config.confidence_threshold += 0.05
        elif success_rate > 0.8:  # Too conservative
            self.config.confidence_threshold -= 0.02
            
        # Keep within bounds
        self.config.confidence_threshold = max(0.5, min(0.95, self.config.confidence_threshold))
        
        logger.info(f"Matching agent threshold adjusted to: {self.config.confidence_threshold}")
