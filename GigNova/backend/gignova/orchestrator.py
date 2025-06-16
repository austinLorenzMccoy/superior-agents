#!/usr/bin/env python3
"""
GigNova: Main System Orchestrator
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import asdict

from gignova.models.base import AgentConfig, JobStatus, JobPost
from gignova.agents.matching import MatchingAgent
from gignova.agents.negotiation import NegotiationAgent
from gignova.agents.qa import QAAgent
from gignova.agents.payment import PaymentAgent

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
        
        # Evolution tracking
        self.performance_metrics = {
            "match_rate": [],
            "negotiation_success": [],
            "qa_pass_rate": [],
            "payment_disputes": []
        }
        
    async def process_job_posting(self, job_post: JobPost) -> Dict:
        """Complete job processing pipeline"""
        job_id = str(uuid.uuid4())
        
        try:
            # Step 1: Store job and find matches
            self.jobs[job_id] = {
                "post": job_post,
                "status": JobStatus.POSTED,
                "created_at": datetime.now()
            }
            
            # Store job embedding
            job_text = f"{job_post.title} {job_post.description} {' '.join(job_post.skills)}"
            self.matching_agent.vector_manager.store_job_embedding(
                job_id, job_text, {"budget_range": [job_post.budget_min, job_post.budget_max]}
            )
            
            # Find matches
            matches = self.matching_agent.find_matches(job_post)
            
            if not matches:
                return {
                    "job_id": job_id,
                    "status": "no_matches",
                    "message": "No suitable freelancers found"
                }
            
            # Step 2: Negotiate with best match
            best_match = matches[0]
            freelancer_data = self.freelancers.get(best_match.freelancer_id, {})
            
            negotiation_result = self.negotiation_agent.negotiate(
                (job_post.budget_min, job_post.budget_max),
                freelancer_data.get('hourly_rate', job_post.budget_max)
            )
            
            if not negotiation_result['success']:
                return {
                    "job_id": job_id,
                    "status": "negotiation_failed",
                    "message": "Could not reach agreement on rate"
                }
            
            # Step 3: Create smart contract
            contract_data = {
                "job_id": job_id,
                "client": job_post.client_id,
                "freelancer": best_match.freelancer_id,
                "amount": negotiation_result['agreed_rate'],
                "file_hash": ""
            }
            
            tx_hash = self.payment_agent.create_escrow(contract_data)
            
            # Update job status
            self.jobs[job_id].update({
                "status": JobStatus.ACTIVE,
                "freelancer_id": best_match.freelancer_id,
                "agreed_rate": negotiation_result['agreed_rate'],
                "contract_tx": tx_hash,
                "match_confidence": best_match.confidence_score
            })
            
            return {
                "job_id": job_id,
                "status": "active",
                "freelancer_id": best_match.freelancer_id,
                "agreed_rate": negotiation_result['agreed_rate'],
                "contract_tx": tx_hash,
                "confidence_score": best_match.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            return {
                "job_id": job_id,
                "status": "error",
                "message": str(e)
            }
    
    async def submit_deliverable(self, job_id: str, deliverable_data: bytes) -> Dict:
        """Process deliverable submission"""
        try:
            if job_id not in self.jobs:
                raise ValueError("Job not found")
            
            job = self.jobs[job_id]
            
            # Store deliverable in local storage
            file_hash = self.qa_agent.ipfs_manager.store_deliverable(deliverable_data)
            
            # Run QA validation
            job_requirements = f"{job['post'].title} {job['post'].description}"
            qa_result = self.qa_agent.validate_deliverable(job_requirements, file_hash)
            
            # Update job status
            self.jobs[job_id].update({
                "status": JobStatus.IN_QA if not qa_result.passed else JobStatus.COMPLETED,
                "deliverable_hash": file_hash,
                "qa_result": qa_result
            })
            
            # If QA passed, release payment
            if qa_result.passed:
                payment_result = self.payment_agent.release_payment(job_id, True)
                self.jobs[job_id]["payment_tx"] = payment_result.get("tx_hash")
                
                # Record successful outcome
                outcome = {
                    "job_id": job_id,
                    "successful": True,
                    "qa_score": qa_result.similarity_score,
                    "negotiation_rounds": 0  # TODO: track from negotiation
                }
                
                self.matching_agent.learn_from_outcome(outcome)
                
            return {
                "job_id": job_id,
                "qa_passed": qa_result.passed,
                "similarity_score": qa_result.similarity_score,
                "feedback": qa_result.feedback,
                "file_hash": file_hash,
                "payment_released": qa_result.passed
            }
            
        except Exception as e:
            logger.error(f"Deliverable processing failed: {e}")
            return {
                "job_id": job_id,
                "error": str(e)
            }
    
    def get_performance_metrics(self) -> Dict:
        """Get current system performance metrics"""
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
        
        qa_scores = [job.get("qa_result", {}).get("similarity_score", 0) 
                    for job in self.jobs.values() if job.get("qa_result")]
        
        return {
            "total_jobs": total_jobs,
            "match_rate": matched_jobs / total_jobs if total_jobs > 0 else 0,
            "completion_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
            "avg_qa_score": sum(qa_scores) / len(qa_scores) if qa_scores else 0,
            "active_jobs": active_jobs,
            "agent_config": asdict(self.config)
        }
    
    def evolve_agents(self):
        """Weekly evolution process for all agents"""
        logger.info("Starting agent evolution process...")
        
        # Get recent outcomes for learning
        recent_outcomes = []
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for job in self.jobs.values():
            if job.get("created_at", datetime.min) > cutoff_time:
                outcome = {
                    "successful": job["status"] == JobStatus.COMPLETED,
                    "qa_score": job.get("qa_result", {}).get("similarity_score", 0),
                    "match_confidence": job.get("match_confidence", 0)
                }
                recent_outcomes.append(outcome)
        
        # Evolve matching agent
        self.matching_agent.evolve_threshold(recent_outcomes)
        
        # Update performance tracking
        if recent_outcomes:
            success_rate = sum(1 for o in recent_outcomes if o["successful"]) / len(recent_outcomes)
            avg_qa_score = sum(o["qa_score"] for o in recent_outcomes) / len(recent_outcomes)
            
            self.performance_metrics["match_rate"].append(success_rate)
            self.performance_metrics["qa_pass_rate"].append(avg_qa_score)
        
            logger.info(f"Evolution complete. Recent success rate: {success_rate:.2%}")
        else:
            logger.info("Evolution complete. No recent outcomes to learn from.")
