#!/usr/bin/env python3
"""
GigNova: Negotiation Agent
"""

import os
import json
import logging
from typing import Dict, Tuple

from gignova.models.base import AgentType, AgentConfig
from gignova.agents.base import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class NegotiationAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.NEGOTIATION, config)
        
    def negotiate(self, client_budget: Tuple[float, float], freelancer_rate: float) -> Dict:
        """Negotiate between client budget and freelancer rate"""
        client_min, client_max = client_budget
        
        if freelancer_rate <= client_max:
            # Easy agreement
            return {
                "agreed_rate": freelancer_rate,
                "rounds": 0,
                "success": True
            }
            
        # Start negotiation
        current_offer = client_max
        current_ask = freelancer_rate
        rounds = 0
        
        while abs(current_offer - current_ask) / current_ask > 0.15 and rounds < self.config.negotiation_rounds:
            # Calculate midpoint with slight bias toward client
            midpoint = (current_offer + current_ask) / 2
            new_offer = current_offer + (midpoint - current_offer) * 0.7
            new_ask = current_ask - (current_ask - midpoint) * 0.3
            
            current_offer = new_offer
            current_ask = new_ask
            rounds += 1
            
        if abs(current_offer - current_ask) / current_ask <= 0.15:
            agreed_rate = (current_offer + current_ask) / 2
            return {
                "agreed_rate": agreed_rate,
                "rounds": rounds,
                "success": True
            }
        else:
            return {
                "agreed_rate": None,
                "rounds": rounds,
                "success": False
            }
    
    def generate_negotiation_message(self, context: Dict) -> str:
        """Generate negotiation message using templates instead of LLM"""
        try:
            # Use template-based approach instead of LLM API calls
            if context.get('is_counter_offer', False):
                return f"Thank you for your proposal. Based on the project requirements and market rates, I'd like to suggest a rate of ${context.get('proposed_rate', 0):.2f}. This reflects the complexity and timeline of the project."
            elif context.get('is_acceptance', False):
                return f"Great! I'm pleased to accept the rate of ${context.get('agreed_rate', 0):.2f}. Looking forward to working together on this project."
            else:
                return f"I'm interested in this project and would like to propose a rate of ${context.get('proposed_rate', 0):.2f} based on my experience and the project requirements."
            
        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            return "Thank you for your proposal. Let's find a mutually beneficial rate."
