#!/usr/bin/env python3
"""
GigNova: The Self-Evolving Talent Ecosystem
A blockchain-powered talent marketplace with autonomous AI agents
"""

import os
import json
import asyncio
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Core dependencies
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from pydantic import BaseModel, Field
import jwt
from passlib.context import CryptContext

# AI/ML dependencies
import openai
from sentence_transformers import SentenceTransformer
import torch
from transformers import pipeline

# Blockchain dependencies
from web3 import Web3
from eth_account import Account
import solcx

# Vector DB and Storage
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

# IPFS
import ipfshttpclient

# Environment and utilities
from dotenv import load_dotenv
import redis
import aioredis
from concurrent.futures import ThreadPoolExecutor
import schedule
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

class JobStatus(Enum):
    POSTED = "posted"
    MATCHED = "matched"
    NEGOTIATING = "negotiating"
    ACTIVE = "active"
    IN_QA = "in_qa"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

class AgentType(Enum):
    MATCHING = "matching"
    NEGOTIATION = "negotiation"
    QA = "qa"
    PAYMENT = "payment"

@dataclass
class AgentConfig:
    confidence_threshold: float = 0.85
    negotiation_rounds: int = 5
    qa_similarity_threshold: float = 0.7
    learning_rate: float = 0.01
    memory_window: int = 100

# =============================================================================
# DATA MODELS
# =============================================================================

class JobPost(BaseModel):
    title: str
    description: str
    skills: List[str]
    budget_min: float
    budget_max: float
    deadline: datetime
    client_id: str
    requirements: List[str] = []

class FreelancerProfile(BaseModel):
    user_id: str
    skills: List[str]
    hourly_rate: float
    portfolio: List[str] = []
    rating: float = 0.0
    completed_jobs: int = 0

class JobMatch(BaseModel):
    job_id: str
    freelancer_id: str
    confidence_score: float
    match_reasons: List[str]
    
class NegotiationRound(BaseModel):
    job_id: str
    client_offer: float
    freelancer_ask: float
    round_number: int
    timestamp: datetime

class QAResult(BaseModel):
    job_id: str
    deliverable_hash: str
    similarity_score: float
    passed: bool
    feedback: str

# =============================================================================
# SMART CONTRACTS (Solidity Templates)
# =============================================================================

ESCROW_CONTRACT = """
pragma solidity ^0.8.19;

contract GigNovaEscrow {
    struct Job {
        address client;
        address freelancer;
        uint256 amount;
        string ipfsHash;
        bool completed;
        bool disputed;
        uint256 deadline;
    }
    
    mapping(bytes32 => Job) public jobs;
    mapping(address => uint256) public balances;
    
    event JobCreated(bytes32 indexed jobId, address client, address freelancer, uint256 amount);
    event JobCompleted(bytes32 indexed jobId);
    event DisputeRaised(bytes32 indexed jobId);
    event PaymentReleased(bytes32 indexed jobId, uint256 amount);
    
    modifier onlyParties(bytes32 jobId) {
        require(
            msg.sender == jobs[jobId].client || msg.sender == jobs[jobId].freelancer,
            "Not authorized"
        );
        _;
    }
    
    function createJob(
        bytes32 jobId,
        address freelancer,
        uint256 deadline,
        string memory ipfsHash
    ) external payable {
        require(msg.value > 0, "Amount must be greater than 0");
        require(jobs[jobId].client == address(0), "Job already exists");
        
        jobs[jobId] = Job({
            client: msg.sender,
            freelancer: freelancer,
            amount: msg.value,
            ipfsHash: ipfsHash,
            completed: false,
            disputed: false,
            deadline: deadline
        });
        
        emit JobCreated(jobId, msg.sender, freelancer, msg.value);
    }
    
    function completeJob(bytes32 jobId) external onlyParties(jobId) {
        require(!jobs[jobId].completed, "Job already completed");
        require(!jobs[jobId].disputed, "Job is disputed");
        require(block.timestamp <= jobs[jobId].deadline || msg.sender == jobs[jobId].client, "Deadline passed");
        
        jobs[jobId].completed = true;
        
        // Release payment to freelancer
        payable(jobs[jobId].freelancer).transfer(jobs[jobId].amount);
        
        emit JobCompleted(jobId);
        emit PaymentReleased(jobId, jobs[jobId].amount);
    }
    
    function raiseDispute(bytes32 jobId) external onlyParties(jobId) {
        require(!jobs[jobId].completed, "Job already completed");
        
        jobs[jobId].disputed = true;
        emit DisputeRaised(jobId);
    }
}
"""

# =============================================================================
# BLOCKCHAIN INTERFACE
# =============================================================================

class BlockchainManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI')))
        self.account = Account.from_key(os.getenv('WALLET_PRIVATE_KEY'))
        self.contract = None
        self._deploy_contract()
    
    def _deploy_contract(self):
        """Deploy the escrow contract"""
        try:
            # Compile contract
            solcx.install_solc('0.8.19')
            solcx.set_solc_version('0.8.19')
            
            compiled_sol = solcx.compile_source(ESCROW_CONTRACT)
            contract_interface = compiled_sol['<stdin>:GigNovaEscrow']
            
            # Deploy contract
            contract = self.w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            transaction = contract.constructor().build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.contract = self.w3.eth.contract(
                address=tx_receipt.contractAddress,
                abi=contract_interface['abi']
            )
            
            logger.info(f"Contract deployed at: {tx_receipt.contractAddress}")
            
        except Exception as e:
            logger.error(f"Contract deployment failed: {e}")
            # Use mock contract for development
            self.contract = MockContract()
    
    def create_escrow(self, job_id: str, client: str, freelancer: str, amount: float, ipfs_hash: str) -> str:
        """Create escrow for a job"""
        try:
            job_id_bytes = self.w3.keccak(text=job_id)
            deadline = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            transaction = self.contract.functions.createJob(
                job_id_bytes,
                freelancer,
                deadline,
                ipfs_hash
            ).build_transaction({
                'from': self.account.address,
                'value': self.w3.to_wei(amount, 'ether'),
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Escrow creation failed: {e}")
            return f"mock_tx_{job_id}"
    
    def release_payment(self, job_id: str) -> str:
        """Release payment from escrow"""
        try:
            job_id_bytes = self.w3.keccak(text=job_id)
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            transaction = self.contract.functions.completeJob(job_id_bytes).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Payment release failed: {e}")
            return f"mock_payment_{job_id}"

class MockContract:
    """Mock contract for development"""
    def functions(self):
        return self
    
    def createJob(self, *args):
        return self
        
    def completeJob(self, *args):
        return self
        
    def build_transaction(self, *args):
        return {"to": "0x0", "data": "0x0"}

# =============================================================================
# VECTOR DATABASE MANAGER
# =============================================================================

class VectorManager:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv('QDRANT_URL', 'http://localhost:6333'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "gignova_embeddings"
        self._setup_collection()
    
    def _setup_collection(self):
        """Initialize Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Collection setup failed: {e}")
    
    def store_job_embedding(self, job_id: str, job_text: str, metadata: Dict):
        """Store job posting embedding"""
        try:
            embedding = self.encoder.encode(job_text).tolist()
            
            point = PointStruct(
                id=job_id,
                vector=embedding,
                payload={
                    "type": "job",
                    "text": job_text,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
        except Exception as e:
            logger.error(f"Job embedding storage failed: {e}")
    
    def store_freelancer_embedding(self, freelancer_id: str, profile_text: str, metadata: Dict):
        """Store freelancer profile embedding"""
        try:
            embedding = self.encoder.encode(profile_text).tolist()
            
            point = PointStruct(
                id=freelancer_id,
                vector=embedding,
                payload={
                    "type": "freelancer",
                    "text": profile_text,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
        except Exception as e:
            logger.error(f"Freelancer embedding storage failed: {e}")
    
    def find_matches(self, job_text: str, limit: int = 10) -> List[Dict]:
        """Find matching freelancers for a job"""
        try:
            query_embedding = self.encoder.encode(job_text).tolist()
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="freelancer"))]
                ),
                limit=limit,
                with_payload=True
            )
            
            matches = []
            for result in results:
                matches.append({
                    "freelancer_id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            return matches
            
        except Exception as e:
            logger.error(f"Match finding failed: {e}")
            return []
    
    def store_outcome(self, interaction_id: str, outcome_data: Dict):
        """Store interaction outcome for learning"""
        try:
            outcome_text = json.dumps(outcome_data)
            embedding = self.encoder.encode(outcome_text).tolist()
            
            point = PointStruct(
                id=f"outcome_{interaction_id}",
                vector=embedding,
                payload={
                    "type": "outcome",
                    "timestamp": time.time(),
                    **outcome_data
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
        except Exception as e:
            logger.error(f"Outcome storage failed: {e}")

# =============================================================================
# IPFS MANAGER
# =============================================================================

class IPFSManager:
    def __init__(self):
        try:
            self.client = ipfshttpclient.connect(os.getenv('IPFS_API_URL', '/ip4/127.0.0.1/tcp/5001'))
        except Exception as e:
            logger.error(f"IPFS connection failed: {e}")
            self.client = None
    
    def store_deliverable(self, data: bytes) -> str:
        """Store deliverable on IPFS"""
        try:
            if self.client:
                result = self.client.add_bytes(data)
                return result
            else:
                # Mock hash for development
                return hashlib.sha256(data).hexdigest()
        except Exception as e:
            logger.error(f"IPFS storage failed: {e}")
            return hashlib.sha256(data).hexdigest()
    
    def retrieve_deliverable(self, ipfs_hash: str) -> bytes:
        """Retrieve deliverable from IPFS"""
        try:
            if self.client:
                return self.client.cat(ipfs_hash)
            else:
                return b"mock_deliverable_data"
        except Exception as e:
            logger.error(f"IPFS retrieval failed: {e}")
            return b""

# =============================================================================
# AI AGENTS
# =============================================================================

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

class MatchingAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.MATCHING, config)
        
    def find_matches(self, job_post: JobPost) -> List[JobMatch]:
        """Find matching freelancers for a job"""
        job_text = f"{job_post.title} {job_post.description} {' '.join(job_post.skills)}"
        
        # Get matches from vector DB
        matches = self.vector_manager.find_matches(job_text, limit=10)
        
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

class NegotiationAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.NEGOTIATION, config)
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
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
        """Generate negotiation message using LLM"""
        try:
            prompt = f"""
            You are a professional negotiation agent. Generate a polite but firm negotiation message.
            Context: {json.dumps(context)}
            Keep it professional and brief.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            return "Thank you for your proposal. Let's find a mutually beneficial rate."

class QAAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(AgentType.QA, config)
        self.ipfs_manager = IPFSManager()
        
    def validate_deliverable(self, job_requirements: str, deliverable_hash: str) -> QAResult:
        """Validate deliverable against job requirements"""
        try:
            # Retrieve deliverable from IPFS
            deliverable_data = self.ipfs_manager.retrieve_deliverable(deliverable_hash)
            
            # For text deliverables, compare embeddings
            if deliverable_data:
                deliverable_text = deliverable_data.decode('utf-8', errors='ignore')
                
                # Calculate similarity
                req_embedding = self.vector_manager.encoder.encode(job_requirements)
                del_embedding = self.vector_manager.encoder.encode(deliverable_text)
                
                similarity = np.dot(req_embedding, del_embedding) / (
                    np.linalg.norm(req_embedding) * np.linalg.norm(del_embedding)
                )
                
                passed = similarity >= self.config.qa_similarity_threshold
                
                return QAResult(
                    job_id=str(uuid.uuid4()),
                    deliverable_hash=deliverable_hash,
                    similarity_score=float(similarity),
                    passed=passed,
                    feedback=f"Similarity score: {similarity:.2f}. {'Approved' if passed else 'Needs revision'}."
                )
            else:
                return QAResult(
                    job_id=str(uuid.uuid4()),
                    deliverable_hash=deliverable_hash,
                    similarity_score=0.0,
                    passed=False,
                    feedback="Could not retrieve deliverable for validation."
                )
                
        except Exception as e:
            logger.error(f"QA validation failed: {e}")
            return QAResult(
                job_id=str(uuid.uuid4()),
                deliverable_hash=deliverable_hash,
                similarity_score=0.0,
                passed=False,
                feedback=f"Validation error: {str(e)}"
            )

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

# =============================================================================
# ORCHESTRATOR - MAIN SYSTEM CONTROLLER
# =============================================================================

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
                "ipfs_hash": ""
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
            
            # Store deliverable on IPFS
            ipfs_hash = self.qa_agent.ipfs_manager.store_deliverable(deliverable_data)
            
            # Run QA validation
            job_requirements = f"{job['post'].title} {job['post'].description}"
            qa_result = self.qa_agent.validate_deliverable(job_requirements, ipfs_hash)
            
            # Update job status
            self.jobs[job_id].update({
                "status": JobStatus.IN_QA if not qa_result.passed else JobStatus.COMPLETED,
                "deliverable_hash": ipfs_hash,
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
                "ipfs_hash": ipfs_hash,
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

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(title="GigNova API", description="Self-Evolving Talent Ecosystem", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Global orchestrator instance
orchestrator = GigNovaOrchestrator()

# Authentication dependency
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, os.getenv('JWT_SECRET', 'secret'), algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "GigNova API is running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get system performance metrics"""
    return orchestrator.get_performance_metrics()

@app.post("/jobs")
async def create_job(job_post: JobPost, user_id: str = Depends(verify_token)):
    """Create a new job posting"""
    job_post.client_id = user_id
    result = await orchestrator.process_job_posting(job_post)
    return result

@app.get("/jobs/{job_id}")
async def get_job(job_id: str, user_id: str = Depends(verify_token)):
    """Get job details"""
    if job_id not in orchestrator.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = orchestrator.jobs[job_id]
    
    # Check if user has access to this job
    if job["post"].client_id != user_id and job.get("freelancer_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": job_id,
        "status": job["status"].value,
        "post": job["post"],
        "freelancer_id": job.get("freelancer_id"),
        "agreed_rate": job.get("agreed_rate"),
        "contract_tx": job.get("contract_tx"),
        "deliverable_hash": job.get("deliverable_hash"),
        "qa_result": job.get("qa_result")
    }

@app.post("/jobs/{job_id}/deliverable")
async def submit_deliverable(
    job_id: str, 
    deliverable: bytes,
    user_id: str = Depends(verify_token)
):
    """Submit deliverable for a job"""
    if job_id not in orchestrator.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = orchestrator.jobs[job_id]
    
    # Check if user is the assigned freelancer
    if job.get("freelancer_id") != user_id:
        raise HTTPException(status_code=403, detail="Only assigned freelancer can submit deliverable")
    
    result = await orchestrator.submit_deliverable(job_id, deliverable)
    return result

@app.post("/freelancers/register")
async def register_freelancer(profile: FreelancerProfile, user_id: str = Depends(verify_token)):
    """Register freelancer profile"""
    profile.user_id = user_id
    
    # Store freelancer profile
    orchestrator.freelancers[user_id] = profile
    
    # Store freelancer embedding
    profile_text = f"{' '.join(profile.skills)} Rate: ${profile.hourly_rate}/hr Rating: {profile.rating}"
    orchestrator.matching_agent.vector_manager.store_freelancer_embedding(
        user_id, 
        profile_text, 
        {
            "skills": profile.skills,
            "hourly_rate": profile.hourly_rate,
            "rating": profile.rating
        }
    )
    
    return {"message": "Freelancer registered successfully", "user_id": user_id}

@app.get("/freelancers/{freelancer_id}")
async def get_freelancer(freelancer_id: str):
    """Get freelancer profile"""
    if freelancer_id not in orchestrator.freelancers:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    
    return orchestrator.freelancers[freelancer_id]

@app.post("/auth/login")
async def login(credentials: dict):
    """Mock login endpoint - returns JWT token"""
    # In production, verify credentials against database
    user_id = credentials.get("user_id", "demo_user")
    
    token_data = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=24)}
    token = jwt.encode(token_data, os.getenv('JWT_SECRET', 'secret'), algorithm='HS256')
    
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}

@app.post("/evolve")
async def trigger_evolution(user_id: str = Depends(verify_token)):
    """Manually trigger agent evolution (for testing)"""
    orchestrator.evolve_agents()
    return {"message": "Agent evolution completed", "metrics": orchestrator.get_performance_metrics()}

@app.get("/jobs")
async def list_jobs(user_id: str = Depends(verify_token)):
    """List all jobs for the user"""
    user_jobs = []
    
    for job_id, job_data in orchestrator.jobs.items():
        if (job_data["post"].client_id == user_id or 
            job_data.get("freelancer_id") == user_id):
            user_jobs.append({
                "job_id": job_id,
                "title": job_data["post"].title,
                "status": job_data["status"].value,
                "budget_max": job_data["post"].budget_max,
                "created_at": job_data["created_at"].isoformat(),
                "freelancer_id": job_data.get("freelancer_id"),
                "agreed_rate": job_data.get("agreed_rate")
            })
    
    return {"jobs": user_jobs}

@app.get("/dashboard")
async def dashboard(user_id: str = Depends(verify_token)):
    """Get dashboard data for user"""
    user_jobs = [job for job in orchestrator.jobs.values() 
                 if job["post"].client_id == user_id or job.get("freelancer_id") == user_id]
    
    client_jobs = [job for job in user_jobs if job["post"].client_id == user_id]
    freelancer_jobs = [job for job in user_jobs if job.get("freelancer_id") == user_id]
    
    return {
        "user_id": user_id,
        "total_jobs": len(user_jobs),
        "as_client": {
            "posted": len([j for j in client_jobs if j["status"] == JobStatus.POSTED]),
            "active": len([j for j in client_jobs if j["status"] == JobStatus.ACTIVE]),
            "completed": len([j for j in client_jobs if j["status"] == JobStatus.COMPLETED])
        },
        "as_freelancer": {
            "active": len([j for j in freelancer_jobs if j["status"] == JobStatus.ACTIVE]),
            "completed": len([j for j in freelancer_jobs if j["status"] == JobStatus.COMPLETED]),
            "total_earned": sum(j.get("agreed_rate", 0) for j in freelancer_jobs 
                              if j["status"] == JobStatus.COMPLETED)
        },
        "system_metrics": orchestrator.get_performance_metrics()
    }

# =============================================================================
# BACKGROUND TASKS & SCHEDULING
# =============================================================================

def run_weekly_evolution():
    """Background task for weekly agent evolution"""
    orchestrator.evolve_agents()

def start_background_scheduler():
    """Start background task scheduler"""
    def scheduler_loop():
        schedule.every().sunday.at("02:00").do(run_weekly_evolution)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    logger.info("Background scheduler started")

# =============================================================================
# STARTUP EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting GigNova API...")
    
    # Start background scheduler
    start_background_scheduler()
    
    # Initialize demo data
    await initialize_demo_data()
    
    logger.info("GigNova API started successfully!")

async def initialize_demo_data():
    """Initialize demo freelancers and jobs for testing"""
    try:
        # Demo freelancers
        demo_freelancers = [
            FreelancerProfile(
                user_id="freelancer_1",
                skills=["Python", "Machine Learning", "AI"],
                hourly_rate=75.0,
                portfolio=["AI chatbot", "ML model optimization"],
                rating=4.8,
                completed_jobs=23
            ),
            FreelancerProfile(
                user_id="freelancer_2",
                skills=["React", "Node.js", "Full Stack"],
                hourly_rate=65.0,
                portfolio=["E-commerce platform", "Real-time chat app"],
                rating=4.6,
                completed_jobs=31
            ),
            FreelancerProfile(
                user_id="freelancer_3",
                skills=["Solidity", "Blockchain", "Web3"],
                hourly_rate=90.0,
                portfolio=["DeFi protocol", "NFT marketplace"],
                rating=4.9,
                completed_jobs=18
            )
        ]
        
        for freelancer in demo_freelancers:
            orchestrator.freelancers[freelancer.user_id] = freelancer
            
            # Store embeddings
            profile_text = f"{' '.join(freelancer.skills)} Rate: ${freelancer.hourly_rate}/hr Rating: {freelancer.rating}"
            orchestrator.matching_agent.vector_manager.store_freelancer_embedding(
                freelancer.user_id,
                profile_text,
                {
                    "skills": freelancer.skills,
                    "hourly_rate": freelancer.hourly_rate,
                    "rating": freelancer.rating
                }
            )
        
        logger.info(f"Initialized {len(demo_freelancers)} demo freelancers")
        
    except Exception as e:
        logger.error(f"Demo data initialization failed: {e}")

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check vector DB connection
        vector_status = "connected"
        try:
            orchestrator.matching_agent.vector_manager.client.get_collections()
        except:
            vector_status = "disconnected"
        
        # Check blockchain connection
        blockchain_status = "connected"
        try:
            orchestrator.payment_agent.blockchain_manager.w3.is_connected()
        except:
            blockchain_status = "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "vector_db": vector_status,
                "blockchain": blockchain_status,
                "ipfs": "connected" if orchestrator.qa_agent.ipfs_manager.client else "disconnected"
            },
            "metrics": orchestrator.get_performance_metrics()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# TESTING ENDPOINTS
# =============================================================================

@app.post("/test/create-sample-job")
async def create_sample_job():
    """Create a sample job for testing"""
    sample_job = JobPost(
        title="AI Chatbot Development",
        description="Build an intelligent chatbot using GPT-4 for customer service automation",
        skills=["Python", "AI", "NLP", "API Integration"],
        budget_min=1000.0,
        budget_max=2500.0,
        deadline=datetime.now() + timedelta(days=14),
        client_id="demo_client",
        requirements=["Experience with OpenAI API", "Previous chatbot projects"]
    )
    
    result = await orchestrator.process_job_posting(sample_job)
    return result

@app.post("/test/submit-sample-deliverable/{job_id}")
async def submit_sample_deliverable(job_id: str):
    """Submit a sample deliverable for testing"""
    sample_deliverable = b"""
    # AI Chatbot Implementation
    
    This chatbot uses GPT-4 for natural language processing and includes:
    - Context-aware responses
    - API integration for customer data
    - Multi-language support
    - Analytics dashboard
    
    The implementation follows best practices for security and scalability.
    """
    
    result = await orchestrator.submit_deliverable(job_id, sample_deliverable)
    return result

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Set up environment
    if not os.path.exists('.env'):
        logger.warning("No .env file found. Using default configuration.")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )