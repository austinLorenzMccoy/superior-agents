#!/usr/bin/env python3
"""
GigNova: Payment Agent
Modular implementation for blockchain payments
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from gignova.models.base import AgentType, AgentConfig
from gignova.agents.base import BaseAgent
from gignova.utils.service_factory import service_factory
from gignova.utils.analytics import analytics_logger

# Configure logging
logger = logging.getLogger(__name__)


class PaymentAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.PAYMENT, config)
        
    async def create_escrow(self, job_data: Dict) -> Dict[str, Any]:
        """Create escrow contract for job using blockchain manager"""
        try:
            # Log escrow creation attempt to analytics
            await analytics_logger.log_event(
                event_type="escrow_creation_started",
                event_data={
                    "job_id": job_data['job_id'],
                    "client_address": job_data['client'],
                    "freelancer_address": job_data['freelancer'],
                    "amount": job_data['amount'],
                    "agent_id": self.agent_id
                }
            )
            
            # Get blockchain manager from service factory
            blockchain_manager = service_factory.get_blockchain_manager()
            
            # Create escrow via blockchain manager
            result = await blockchain_manager.create_escrow(
                client_id=job_data['client'],
                freelancer_id=job_data['freelancer'],
                amount=job_data['amount'],
                deadline=job_data.get('deadline', 30 * 24 * 60 * 60)  # Default to 30 days in seconds
            )
            
            # Log result to analytics
            if result.get("success"):
                await analytics_logger.log_event(
                    event_type="escrow_creation_completed",
                    event_data={
                        "job_id": job_data['job_id'],
                        "agent_id": self.agent_id,
                        "contract_address": result.get("contract_address"),
                        "escrow_id": result.get("escrow_id"),
                        "success": True
                    }
                )
            
            # Store outcome for learning
            await self.learn_from_outcome({
                "type": "escrow_creation",
                "job_id": job_data['job_id'],
                "success": result.get("success", False),
                "contract_address": result.get("contract_address"),
                "escrow_id": result.get("escrow_id")
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Escrow creation failed: {e}")
            
            # Log error to analytics
            await analytics_logger.log_event(
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
        """Release payment if QA passed using blockchain manager"""
        try:
            # Log payment release attempt to analytics
            await analytics_logger.log_event(
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
                await analytics_logger.log_event(
                    event_type="payment_release_skipped",
                    event_data={
                        "job_id": job_id,
                        "reason": "QA failed",
                        "agent_id": self.agent_id
                    }
                )
                
                return result
            
            # Get blockchain manager from service factory
            blockchain_manager = service_factory.get_blockchain_manager()
            
            # Release payment via blockchain manager
            result = await blockchain_manager.release_payment(
                escrow_id=contract_address or escrow_id
            )
            
            if result.get("success"):
                # Log successful payment release
                await analytics_logger.log_event(
                    event_type="payment_release_completed",
                    event_data={
                        "job_id": job_id,
                        "contract_address": contract_address,
                        "escrow_id": escrow_id,
                        "transaction_hash": result.get("transaction_hash"),
                        "agent_id": self.agent_id
                    }
                )
                
                # Store outcome for learning
                await self.learn_from_outcome({
                    "type": "payment_release",
                    "job_id": job_id,
                    "success": True,
                    "transaction_hash": result.get("transaction_hash")
                })
                
                return {
                    "success": True,
                    "message": "Payment released successfully",
                    "transaction_hash": result.get("transaction_hash")
                }
            else:
                # Log failed payment release
                await analytics_logger.log_event(
                    event_type="payment_release_failed",
                    event_data={
                        "job_id": job_id,
                        "contract_address": contract_address,
                        "escrow_id": escrow_id,
                        "error": result.get('error', 'Unknown error'),
                        "agent_id": self.agent_id
                    }
                )
                
                return {
                    "success": False,
                    "message": f"Payment release failed: {result.get('error', 'Unknown error')}",
                    "transaction_hash": None
                }
                
        except Exception as e:
            logger.error(f"Payment release failed: {e}")
            
            # Log error to analytics
            await analytics_logger.log_event(
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
        
        try:
            # Get payment-specific metrics from analytics logger
            # Get successful payment releases
            completed_events = await analytics_logger.get_events(
                event_type="payment_release_completed",
                limit=100,
                time_range_days=30  # Last 30 days
            )
            
            # Get failed payment releases
            failed_events = await analytics_logger.get_events(
                event_type="payment_release_failed",
                limit=100,
                time_range_days=30  # Last 30 days
            )
            
            # Get error events
            error_events = await analytics_logger.get_events(
                event_type="payment_release_error",
                limit=100,
                time_range_days=30  # Last 30 days
            )
            
            if not completed_events and not failed_events and not error_events:
                return {
                    **metrics,
                    "evolved": False,
                    "reason": "No payment data available for evolution"
                }
            
            # Calculate metrics
            total_attempts = len(completed_events) + len(failed_events) + len(error_events)
            success_rate = len(completed_events) / total_attempts if total_attempts > 0 else 0
            failed_transactions = len(failed_events) + len(error_events)
            
            # Extract gas costs if available
            gas_costs = []
            for event in completed_events:
                data = event.get("data", {})
                if "gas_cost" in data:
                    gas_costs.append(data["gas_cost"])
            
            avg_gas_cost = sum(gas_costs) / len(gas_costs) if gas_costs else 0.0
            
            # Log metrics
            logger.info(f"Payment agent metrics - Success rate: {success_rate:.2f}, Avg gas: {avg_gas_cost:.2f}, Failed tx: {failed_transactions}")
            
            # For now, payment agent doesn't evolve parameters automatically
            # This could be extended to optimize gas strategies, retry mechanisms, etc.
            
            # Log evolution metrics to analytics
            await analytics_logger.log_event(
                event_type="agent_evolution_metrics",
                event_data={
                    "agent_type": self.agent_type.value,
                    "agent_id": self.agent_id,
                    "success_rate": success_rate,
                    "avg_gas_cost": avg_gas_cost,
                    "failed_transactions": failed_transactions,
                    "evolved": False,
                    "reason": "No evolution parameters defined for payment agent"
                }
            )
            
            return {
                **metrics,
                "evolved": False,
                "reason": "No evolution parameters defined for payment agent",
                "success_rate": success_rate,
                "avg_gas_cost": avg_gas_cost,
                "failed_transactions": failed_transactions
            }
            
        except Exception as e:
            logger.error(f"Payment agent evolution failed: {e}")
            return {
                **metrics,
                "evolved": False,
                "error": str(e)
            }
