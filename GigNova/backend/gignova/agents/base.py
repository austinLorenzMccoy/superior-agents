#!/usr/bin/env python3
"""
GigNova: Base Agent
"""

import uuid
import logging
from typing import Dict, List

from gignova.models.base import AgentType, AgentConfig
from gignova.database.vector_manager import VectorManager

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(self, agent_type: AgentType, config: AgentConfig):
        self.agent_type = agent_type
        self.config = config
        self.vector_manager = VectorManager()
        self.memory = []
        
    def learn_from_outcome(self, outcome: Dict):
        """Update agent behavior based on outcome"""
        self.memory.append(outcome)
        self.vector_manager.store_outcome(
            f"{self.agent_type.value}_{uuid.uuid4()}",
            outcome
        )
        
    def get_relevant_experience(self, context: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant past experiences"""
        return self.vector_manager.find_matches(context, limit)
