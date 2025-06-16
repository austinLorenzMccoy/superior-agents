#!/usr/bin/env python3
"""
GigNova: Payment Agent
"""

import logging
from typing import Dict

from gignova.models.base import AgentType, AgentConfig
from gignova.agents.base import BaseAgent
from gignova.blockchain.manager import BlockchainManager

# Configure logging
logger = logging.getLogger(__name__)


class PaymentAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.PAYMENT, config)
        self.blockchain_manager = BlockchainManager()
        
    def create_escrow(self, job_data: Dict) -> str:
        """Create escrow contract for job"""
        return self.blockchain_manager.create_escrow(
            job_data['job_id'],
            job_data['client'],
            job_data['freelancer'],
            job_data['amount'],
            job_data.get('ipfs_hash', '')
        )
    
    def release_payment(self, job_id: str, qa_passed: bool) -> Dict:
        """Release payment if QA passed"""
        if qa_passed:
            tx_hash = self.blockchain_manager.release_payment(job_id)
            return {
                "success": True,
                "tx_hash": tx_hash,
                "message": "Payment released successfully"
            }
        else:
            return {
                "success": False,
                "tx_hash": None,
                "message": "Payment held due to QA failure"
            }
