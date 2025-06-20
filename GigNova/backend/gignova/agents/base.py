#!/usr/bin/env python3
"""
GigNova: Base Agent
Enhanced with MCP integration
"""

import uuid
import logging
import asyncio
from typing import Dict, List, Any

from gignova.models.base import AgentType, AgentConfig
from gignova.database.vector_manager_mcp import VectorManager
from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(self, agent_type: AgentType, config: AgentConfig):
        self.agent_type = agent_type
        self.config = config
        self.vector_manager = VectorManager()
        self.memory = []
        self.agent_id = str(uuid.uuid4())
        logger.info(f"Initialized {agent_type.value} agent with ID: {self.agent_id}")
        
    async def learn_from_outcome(self, outcome: Dict):
        """Update agent behavior based on outcome using MCP vector storage"""
        # Add agent metadata to outcome
        outcome.update({
            "agent_type": self.agent_type.value,
            "agent_id": self.agent_id,
            "timestamp": outcome.get("timestamp", 0)
        })
        
        # Store in memory
        self.memory.append(outcome)
        
        # Store in vector database via MCP
        interaction_id = f"{self.agent_type.value}_{uuid.uuid4()}"
        await self.vector_manager.store_outcome(interaction_id, outcome)
        
        # Log analytics event
        await mcp_manager.analytics_log_event(
            event_type="agent_learning",
            event_data={
                "agent_type": self.agent_type.value,
                "agent_id": self.agent_id,
                "interaction_id": interaction_id,
                "outcome_type": outcome.get("type", "unknown")
            }
        )
        
        return interaction_id
        
    async def get_relevant_experience(self, context: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant past experiences via MCP vector search"""
        return await self.vector_manager.find_matches(context, limit)
    
    async def evolve(self) -> Dict[str, Any]:
        """Base implementation of agent evolution"""
        # Get agent performance metrics from analytics MCP
        metrics = await mcp_manager.analytics_get_metrics(
            metric_type="agent_performance",
            time_range="7d",  # Last 7 days
            filters={
                "agent_type": self.agent_type.value,
                "agent_id": self.agent_id
            }
        )
        
        # Default implementation just logs the metrics
        logger.info(f"Evolution metrics for {self.agent_type.value}: {metrics}")
        
        # Subclasses should override this method with specific evolution logic
        return {
            "agent_type": self.agent_type.value,
            "agent_id": self.agent_id,
            "evolved": False,
            "reason": "Base implementation does not evolve"
        }
