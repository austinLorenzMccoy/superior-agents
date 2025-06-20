#!/usr/bin/env python3
"""
GigNova: Main System Orchestrator
Enhanced with MCP integration
"""

import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from gignova.models.base import AgentConfig, JobStatus, JobPost
from gignova.agents.matching import MatchingAgent
from gignova.agents.negotiation import NegotiationAgent
from gignova.agents.qa import QAAgent
from gignova.agents.payment import PaymentAgent
from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class GigNovaOrchestrator:
    def __init__(self):
        self.config = AgentConfig()
        self.matching_agent = MatchingAgent(self.config)
        self.negotiation_agent = NegotiationAgent(self.config)
        self.qa_agent = QAAgent(self.config)
        self.payment_agent = PaymentAgent(self.config)
        
        # In-memory storage (replace with proper DB in production)
        self.jobs = {}
        self.freelancers = {}
        self.contracts = {}
        
        logger.info("GigNova Orchestrator initialized with MCP integration")
        
    async def process_job_posting(self, job_post: JobPost) -> Dict:
        """Complete job processing pipeline with MCP integration"""
        job_id = str(uuid.uuid4())
        
        try:
            # Log job posting to analytics
            await mcp_manager.analytics_log_event(
                event_type="job_posted",
                event_data={
                    "job_id": job_id,
                    "client_id": job_post.client_id,
                    "title": job_post.title,
                    "budget_range": [job_post.budget_min, job_post.budget_max]
                }
            )
            
            # Step 1: Store job and find matches
            self.jobs[job_id] = {
                "post": job_post,
                "status": JobStatus.POSTED,
                "created_at": datetime.now()
            }
            
            # Store job embedding via MCP vector server
            job_text = f"{job_post.title} {job_post.description} {' '.join(job_post.skills)}"
            await self.matching_agent.vector_manager.store_job_embedding(
                job_id, job_text, {"budget_range": [job_post.budget_min, job_post.budget_max]}
            )
            
            # Find matches via MCP vector search
            matches = await self.matching_agent.find_matches(job_post)
            
            if not matches:
                await mcp_manager.analytics_log_event(
                    event_type="job_no_matches",
                    event_data={"job_id": job_id}
                )
                
                return {
                    "job_id": job_id,
                    "status": "no_matches",
                    "message": "No suitable freelancers found"
                }
            
            # Step 2: Negotiate with best match
            best_match = matches[0]
            freelancer_data = self.freelancers.get(best_match["freelancer_id"], {})
            
            await mcp_manager.analytics_log_event(
                event_type="negotiation_started",
                event_data={
                    "job_id": job_id,
                    "freelancer_id": best_match["freelancer_id"],
                    "match_score": best_match["score"]
                }
            )
            
            negotiation_result = await self.negotiation_agent.negotiate(
                (job_post.budget_min, job_post.budget_max),
                freelancer_data.get('hourly_rate', job_post.budget_max)
            )
            
            if not negotiation_result['success']:
                await mcp_manager.analytics_log_event(
                    event_type="negotiation_failed",
                    event_data={
                        "job_id": job_id,
                        "freelancer_id": best_match["freelancer_id"]
                    }
                )
                
                return {
                    "job_id": job_id,
                    "status": "negotiation_failed",
                    "message": "Could not reach agreement on rate"
                }
            
            # Step 3: Create smart contract via MCP blockchain server
            contract_data = {
                "job_id": job_id,
                "client": job_post.client_id,
                "freelancer": best_match["freelancer_id"],
                "amount": negotiation_result['agreed_rate']
            }
            
            contract_result = await self.payment_agent.create_escrow(contract_data)
            
            if not contract_result.get("success"):
                await mcp_manager.analytics_log_event(
                    event_type="contract_creation_failed",
                    event_data={
                        "job_id": job_id,
                        "error": contract_result.get("error", "Unknown error")
                    }
                )
                
                return {
                    "job_id": job_id,
                    "status": "contract_failed",
                    "message": f"Failed to create contract: {contract_result.get('error', 'Unknown error')}"
                }
            
            # Update job status
            self.jobs[job_id].update({
                "status": JobStatus.ACTIVE,
                "freelancer_id": best_match["freelancer_id"],
                "agreed_rate": negotiation_result['agreed_rate'],
                "contract_address": contract_result.get("contract_address"),
                "escrow_id": contract_result.get("escrow_id"),
                "match_confidence": best_match["score"]
            })
            
            await mcp_manager.analytics_log_event(
                event_type="job_activated",
                event_data={
                    "job_id": job_id,
                    "freelancer_id": best_match["freelancer_id"],
                    "agreed_rate": negotiation_result['agreed_rate'],
                    "contract_address": contract_result.get("contract_address")
                }
            )
            
            return {
                "job_id": job_id,
                "status": "active",
                "freelancer_id": best_match["freelancer_id"],
                "agreed_rate": negotiation_result['agreed_rate'],
                "contract_address": contract_result.get("contract_address"),
                "escrow_id": contract_result.get("escrow_id"),
                "confidence_score": best_match["score"]
            }
            
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            
            await mcp_manager.analytics_log_event(
                event_type="job_processing_error",
                event_data={
                    "job_id": job_id,
                    "error": str(e)
                }
            )
            
            return {
                "job_id": job_id,
                "status": "error",
                "message": str(e)
            }
    
    async def submit_deliverable(self, job_id: str, deliverable_data: bytes) -> Dict:
        """Process deliverable submission with MCP integration"""
        try:
            if job_id not in self.jobs:
                raise ValueError("Job not found")
            
            job = self.jobs[job_id]
            
            await mcp_manager.analytics_log_event(
                event_type="deliverable_submitted",
                event_data={
                    "job_id": job_id,
                    "freelancer_id": job.get("freelancer_id"),
                    "file_size": len(deliverable_data)
                }
            )
            
            # Store deliverable via MCP storage server
            file_hash = await self.qa_agent.ipfs_manager.store_deliverable(deliverable_data)
            
            # Run QA validation via MCP
            job_requirements = f"{job['post'].title} {job['post'].description}"
            qa_result = await self.qa_agent.validate_deliverable(job_id, job_requirements, file_hash)
            
            # Update job status
            self.jobs[job_id].update({
                "status": JobStatus.IN_QA if not qa_result.passed else JobStatus.COMPLETED,
                "deliverable_hash": file_hash,
                "qa_result": qa_result
            })
            
            # If QA passed, release payment via MCP blockchain server
            if qa_result.passed:
                payment_result = await self.payment_agent.release_payment(
                    job_id, 
                    job.get("contract_address"), 
                    job.get("escrow_id"),
                    True
                )
                
                self.jobs[job_id]["payment_tx"] = payment_result.get("transaction_hash")
                
                # Record successful outcome for learning
                outcome = {
                    "job_id": job_id,
                    "successful": True,
                    "qa_score": qa_result.similarity_score,
                    "negotiation_rounds": job.get("negotiation_rounds", 0),
                    "timestamp": datetime.now().timestamp()
                }
                
                await self.matching_agent.learn_from_outcome(outcome)
                
                await mcp_manager.analytics_log_event(
                    event_type="job_completed",
                    event_data={
                        "job_id": job_id,
                        "qa_score": qa_result.similarity_score,
                        "payment_tx": payment_result.get("transaction_hash")
                    }
                )
            else:
                await mcp_manager.analytics_log_event(
                    event_type="qa_failed",
                    event_data={
                        "job_id": job_id,
                        "qa_score": qa_result.similarity_score,
                        "feedback": qa_result.feedback
                    }
                )
            
            return {
                "job_id": job_id,
                "qa_passed": qa_result.passed,
                "similarity_score": qa_result.similarity_score,
                "feedback": qa_result.feedback,
                "file_hash": file_hash,
                "payment_released": qa_result.passed,
                "transaction_hash": self.jobs[job_id].get("payment_tx") if qa_result.passed else None
            }
            
        except Exception as e:
            logger.error(f"Deliverable processing failed: {e}")
            
            await mcp_manager.analytics_log_event(
                event_type="deliverable_processing_error",
                event_data={
                    "job_id": job_id,
                    "error": str(e)
                }
            )
            
            return {
                "job_id": job_id,
                "error": str(e)
            }
    
    async def get_performance_metrics(self) -> Dict:
        """Get current system performance metrics with MCP analytics integration"""
        try:
            # Get basic metrics from local data
            total_jobs = len(self.jobs)
            
            if total_jobs == 0:
                return {
                    "total_jobs": 0,
                    "match_rate": 0,
                    "completion_rate": 0,
                    "avg_qa_score": 0,
                    "active_jobs": 0
                }
            
            completed_jobs = sum(1 for job in self.jobs.values() if job["status"] == JobStatus.COMPLETED)
            matched_jobs = sum(1 for job in self.jobs.values() if job["status"] != JobStatus.POSTED)
            active_jobs = sum(1 for job in self.jobs.values() if job["status"] in [JobStatus.ACTIVE, JobStatus.IN_QA])
            
            qa_scores = [job.get("qa_result").similarity_score 
                        for job in self.jobs.values() if job.get("qa_result")]
            
            # Get enhanced metrics from MCP analytics server
            analytics_metrics = await mcp_manager.analytics_get_metrics(
                metric_type="system_performance",
                time_range="30d",
                filters={}
            )
            
            # Combine local and MCP metrics
            basic_metrics = {
                "total_jobs": total_jobs,
                "match_rate": matched_jobs / total_jobs if total_jobs > 0 else 0,
                "completion_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
                "avg_qa_score": sum(qa_scores) / len(qa_scores) if qa_scores else 0,
                "active_jobs": active_jobs,
                "agent_config": asdict(self.config)
            }
            
            if analytics_metrics.get("success"):
                return {
                    **basic_metrics,
                    "mcp_metrics": analytics_metrics.get("data", {})
                }
            else:
                return basic_metrics
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def evolve_agents(self):
        """Weekly evolution process for all agents using MCP integration"""
        logger.info("Starting agent evolution process with MCP integration...")
        
        try:
            # Log evolution start to analytics
            await mcp_manager.analytics_log_event(
                event_type="agent_evolution_started",
                event_data={
                    "timestamp": datetime.now().timestamp()
                }
            )
            
            # Evolve each agent type
            matching_evolution = await self.matching_agent.evolve()
            negotiation_evolution = await self.negotiation_agent.evolve()
            qa_evolution = await self.qa_agent.evolve()
            payment_evolution = await self.payment_agent.evolve()
            
            # Collect evolution results
            evolution_results = {
                "matching": matching_evolution,
                "negotiation": negotiation_evolution,
                "qa": qa_evolution,
                "payment": payment_evolution
            }
            
            # Log evolution results to analytics
            await mcp_manager.analytics_log_event(
                event_type="agent_evolution_completed",
                event_data={
                    "results": evolution_results,
                    "timestamp": datetime.now().timestamp()
                }
            )
            
            logger.info(f"Evolution complete. Results: {evolution_results}")
            return evolution_results
            
        except Exception as e:
            logger.error(f"Agent evolution failed: {e}")
            
            await mcp_manager.analytics_log_event(
                event_type="agent_evolution_error",
                event_data={
                    "error": str(e),
                    "timestamp": datetime.now().timestamp()
                }
            )
            
            return {"error": str(e)}
    
    async def initialize_mcp_connections(self):
        """Initialize all MCP server connections"""
        try:
            # Check vector MCP server
            vector_status = await mcp_manager.vector_store_embedding(
                id="test_connection",
                vector=[0.1, 0.2, 0.3],
                metadata={"test": True}
            )
            
            # Check blockchain MCP server
            blockchain_status = await mcp_manager.blockchain_call_tool("get_status", {})
            
            # Check storage MCP server
            storage_status = await mcp_manager.storage_call_tool("get_status", {})
            
            # Check analytics MCP server
            analytics_status = await mcp_manager.analytics_log_event(
                event_type="system_startup",
                event_data={"timestamp": datetime.now().timestamp()}
            )
            
            logger.info("MCP connections initialized")
            
            return {
                "vector_mcp": vector_status.get("success", False),
                "blockchain_mcp": blockchain_status.get("success", False),
                "storage_mcp": storage_status.get("success", False),
                "analytics_mcp": analytics_status.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            return {"error": str(e)}
