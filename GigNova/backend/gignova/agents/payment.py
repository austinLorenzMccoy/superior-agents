#!/usr/bin/env python3
"""
GigNova: Payment Agent
Enhanced with MCP integration
"""

import logging
from typing import Dict, Any

from gignova.models.base import AgentType, AgentConfig
from gignova.agents.base import BaseAgent
from gignova.blockchain.manager_mcp import BlockchainManager
from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class PaymentAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.PAYMENT, config)
        self.blockchain_manager = BlockchainManager()
        
    async def create_escrow(self, job_data: Dict) -> Dict[str, Any]:
        """Create escrow contract for job using MCP blockchain server"""
        try:
            # Log escrow creation attempt to analytics
            await mcp_manager.analytics_log_event(
                event_type="escrow_creation_started",
                event_data={
                    "job_id": job_data['job_id'],
                    "client_address": job_data['client'],
                    "freelancer_address": job_data['freelancer'],
                    "amount": job_data['amount'],
                    "agent_id": self.agent_id
                }
            )
            
            # Create escrow via MCP blockchain server
            result = await self.blockchain_manager.create_escrow(
                client_address=job_data['client'],
                freelancer_address=job_data['freelancer'],
                amount=job_data['amount'],
                job_id=job_data['job_id']
            )
            
            # Store outcome for learning
            await self.learn_from_outcome({
                "type": "escrow_creation",
                "job_id": job_data['job_id'],
                "success": result.get("success", False),
                "contract_address": result.get("contract_address"),
                "escrow_id": result.get("escrow_id"),
                "timestamp": 0  # Should be current timestamp in production
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Escrow creation failed: {e}")
            
            # Log error to analytics
            await mcp_manager.analytics_log_event(
                event_type="escrow_creation_error",
                event_data={
                    "job_id": job_data.get('job_id', 'unknown'),
                    "agent_id": self.agent_id,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "contract_address": None,
                "escrow_id": None
            }
    
    async def release_payment(self, job_id: str, contract_address: str, escrow_id: str, qa_passed: bool) -> Dict[str, Any]:
        """Release payment if QA passed using MCP blockchain server"""
        try:
            # Log payment release attempt to analytics
            await mcp_manager.analytics_log_event(
                event_type="payment_release_started",
                event_data={
                    "job_id": job_id,
                    "contract_address": contract_address,
                    "escrow_id": escrow_id,
                    "qa_passed": qa_passed,
                    "agent_id": self.agent_id
                }
            )
            
            if not qa_passed:
                result = {
                    "success": False,
                    "message": "Payment held due to QA failure",
                    "transaction_hash": None
                }
                
                # Log decision to analytics
                await mcp_manager.analytics_log_event(
                    event_type="payment_release_skipped",
                    event_data={
                        "job_id": job_id,
                        "reason": "QA failed",
                        "agent_id": self.agent_id
                    }
                )
                
                return result
            
            # Release payment via MCP blockchain server
            result = await self.blockchain_manager.release_payment(
                contract_address=contract_address,
                escrow_id=escrow_id
            )
            
            if result.get("success"):
                # Store outcome for learning
                await self.learn_from_outcome({
                    "type": "payment_release",
                    "job_id": job_id,
                    "success": True,
                    "transaction_hash": result.get("transaction_hash"),
                    "timestamp": 0  # Should be current timestamp in production
                })
                
                return {
                    "success": True,
                    "message": "Payment released successfully",
                    "transaction_hash": result.get("transaction_hash")
                }
            else:
                return {
                    "success": False,
                    "message": f"Payment release failed: {result.get('error', 'Unknown error')}",
                    "transaction_hash": None
                }
                
        except Exception as e:
            logger.error(f"Payment release failed: {e}")
            
            # Log error to analytics
            await mcp_manager.analytics_log_event(
                event_type="payment_release_error",
                event_data={
                    "job_id": job_id,
                    "contract_address": contract_address,
                    "escrow_id": escrow_id,
                    "agent_id": self.agent_id,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "message": f"Payment release error: {str(e)}",
                "transaction_hash": None
            }
    
    async def evolve(self) -> Dict[str, Any]:
        """Evolve the payment agent based on historical performance"""
        # Get base evolution metrics
        metrics = await super().evolve()
        
        # Get payment-specific metrics from analytics MCP
        payment_metrics = await mcp_manager.analytics_get_metrics(
            metric_type="payment_performance",
            time_range="30d",  # Last 30 days
            filters={
                "agent_id": self.agent_id
            }
        )
        
        if not payment_metrics.get("success"):
            return {
                **metrics,
                "evolved": False,
                "reason": "Failed to retrieve payment metrics"
            }
        
        # Extract metrics for evolution
        success_rate = payment_metrics.get("data", {}).get("success_rate", 0.0)
        avg_gas_cost = payment_metrics.get("data", {}).get("average_gas_cost", 0.0)
        failed_transactions = payment_metrics.get("data", {}).get("failed_transactions", 0)
        
        # Log metrics
        logger.info(f"Payment agent metrics - Success rate: {success_rate:.2f}, Avg gas: {avg_gas_cost:.2f}, Failed tx: {failed_transactions}")
        
        # For now, payment agent doesn't evolve parameters automatically
        # This could be extended to optimize gas strategies, retry mechanisms, etc.
        
        return {
            **metrics,
            "evolved": False,
            "reason": "No evolution parameters defined for payment agent"
        }
