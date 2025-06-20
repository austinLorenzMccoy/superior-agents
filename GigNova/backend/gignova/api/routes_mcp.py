#!/usr/bin/env python3
"""
GigNova: API Routes with MCP Integration
"""

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext

from gignova.models.base import JobPost, FreelancerProfile, JobStatus
from gignova.orchestrator_mcp import GigNovaOrchestrator
from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create router
router = APIRouter(prefix="/api/v1")

# In-memory user store (replace with proper DB in production)
users = {}

# Initialize orchestrator
orchestrator = GigNovaOrchestrator()


# Authentication helpers
def create_token(user_id: str) -> str:
    """Create JWT token"""
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": user_id,
        "exp": expiration
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET", "dev_secret"), algorithm="HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "dev_secret"), algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint with MCP status"""
    # Check MCP connections
    mcp_status = await orchestrator.initialize_mcp_connections()
    
    return {
        "status": "healthy" if "error" not in mcp_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "mcp_status": mcp_status
    }


# Authentication endpoints
@router.post("/auth/register")
async def register(username: str = Body(...), password: str = Body(...), role: str = Body(...)):
    """Register a new user"""
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    user_id = str(uuid.uuid4())
    users[username] = {
        "id": user_id,
        "password": pwd_context.hash(password),
        "role": role
    }
    
    # Log user registration in analytics
    await mcp_manager.analytics_log_event(
        event_type="user_registered",
        event_data={
            "user_id": user_id,
            "role": role,
            "timestamp": datetime.now().timestamp()
        }
    )
    
    return {
        "user_id": user_id,
        "username": username,
        "role": role
    }


@router.post("/auth/login")
async def login(username: str = Body(...), password: str = Body(...)):
    """Login and get token"""
    if username not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = users[username]
    if not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_token(user["id"])
    
    # Log login event in analytics
    await mcp_manager.analytics_log_event(
        event_type="user_login",
        event_data={
            "user_id": user["id"],
            "role": user["role"],
            "timestamp": datetime.now().timestamp()
        }
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "role": user["role"]
    }


# Job endpoints
@router.post("/jobs")
async def create_job(job_post: JobPost, user_id: str = Depends(verify_token)):
    """Create a new job with MCP integration"""
    job_post.client_id = user_id
    result = await orchestrator.process_job_posting(job_post)
    return result


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, user_id: str = Depends(verify_token)):
    """Get job details"""
    if job_id not in orchestrator.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = orchestrator.jobs[job_id]
    
    # Check authorization
    if job["post"].client_id != user_id and job.get("freelancer_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")
        
    # Log job view event
    await mcp_manager.analytics_log_event(
        event_type="job_viewed",
        event_data={
            "job_id": job_id,
            "viewer_id": user_id,
            "timestamp": datetime.now().timestamp()
        }
    )
        
    return {
        "job_id": job_id,
        "status": job["status"].value,
        "post": job["post"],
        "freelancer_id": job.get("freelancer_id"),
        "created_at": job.get("created_at").isoformat(),
        "agreed_rate": job.get("agreed_rate"),
        "contract_address": job.get("contract_address"),
        "escrow_id": job.get("escrow_id"),
        "deliverable_hash": job.get("deliverable_hash"),
        "qa_result": job.get("qa_result")
    }


@router.post("/jobs/{job_id}/deliverable")
async def submit_deliverable(
    job_id: str, 
    deliverable: UploadFile = File(...), 
    user_id: str = Depends(verify_token)
):
    """Submit deliverable for a job with MCP integration"""
    if job_id not in orchestrator.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = orchestrator.jobs[job_id]
    
    # Check authorization
    if job.get("freelancer_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to submit deliverable")
        
    # Check job status
    if job["status"] != JobStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Job is not active, current status: {job['status'].value}")
        
    # Process deliverable
    deliverable_data = await deliverable.read()
    result = await orchestrator.submit_deliverable(job_id, deliverable_data)
    
    return result


# Freelancer endpoints
@router.post("/freelancers")
async def register_freelancer(profile: FreelancerProfile, user_id: str = Depends(verify_token)):
    """Register freelancer profile with MCP integration"""
    # Ensure user_id matches the one in the profile
    if profile.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    # Store in orchestrator
    orchestrator.freelancers[user_id] = profile.dict()
    
    # Store embedding via MCP vector server
    profile_text = f"{profile.name} {profile.bio} {' '.join(profile.skills)}, hourly rate: {profile.hourly_rate}"
    await orchestrator.matching_agent.vector_manager.store_freelancer_embedding(
        user_id, profile_text, profile.dict()
    )
    
    # Log freelancer registration in analytics
    await mcp_manager.analytics_log_event(
        event_type="freelancer_registered",
        event_data={
            "freelancer_id": user_id,
            "skills": profile.skills,
            "hourly_rate": profile.hourly_rate,
            "timestamp": datetime.now().timestamp()
        }
    )
    
    return {
        "freelancer_id": user_id,
        "status": "registered"
    }


@router.get("/freelancers/{freelancer_id}")
async def get_freelancer(freelancer_id: str, user_id: str = Depends(verify_token)):
    """Get freelancer profile"""
    if freelancer_id not in orchestrator.freelancers:
        raise HTTPException(status_code=404, detail="Freelancer not found")
        
    # Log freelancer profile view in analytics
    await mcp_manager.analytics_log_event(
        event_type="freelancer_profile_viewed",
        event_data={
            "freelancer_id": freelancer_id,
            "viewer_id": user_id,
            "timestamp": datetime.now().timestamp()
        }
    )
        
    return orchestrator.freelancers[freelancer_id]


# Job listing endpoints
@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None, 
    limit: int = 10, 
    user_id: str = Depends(verify_token)
):
    """List jobs"""
    results = []
    
    for job_id, job in orchestrator.jobs.items():
        # Filter by status if specified
        if status and job["status"].value != status:
            continue
            
        # Filter by user association
        if job["post"].client_id == user_id or job.get("freelancer_id") == user_id:
            results.append({
                "job_id": job_id,
                "title": job["post"].title,
                "status": job["status"].value,
                "created_at": job.get("created_at").isoformat(),
                "client_id": job["post"].client_id,
                "freelancer_id": job.get("freelancer_id"),
                "contract_address": job.get("contract_address")
            })
            
        if len(results) >= limit:
            break
    
    # Log job listing view in analytics
    await mcp_manager.analytics_log_event(
        event_type="job_list_viewed",
        event_data={
            "user_id": user_id,
            "filter_status": status,
            "result_count": len(results),
            "timestamp": datetime.now().timestamp()
        }
    )
            
    return results


# Dashboard endpoints
@router.get("/dashboard")
async def get_dashboard(user_id: str = Depends(verify_token)):
    """Get user dashboard data with MCP analytics integration"""
    # Get user's role
    user_role = None
    for user in users.values():
        if user["id"] == user_id:
            user_role = user["role"]
            break
            
    if not user_role:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get relevant metrics with MCP analytics
    metrics = await orchestrator.get_performance_metrics()
    
    # Get user's jobs
    user_jobs = []
    for job_id, job in orchestrator.jobs.items():
        if (user_role == "client" and job["post"].client_id == user_id) or \
           (user_role == "freelancer" and job.get("freelancer_id") == user_id):
            user_jobs.append({
                "job_id": job_id,
                "title": job["post"].title,
                "status": job["status"].value,
                "created_at": job.get("created_at").isoformat(),
                "contract_address": job.get("contract_address")
            })
    
    # Log dashboard view in analytics
    await mcp_manager.analytics_log_event(
        event_type="dashboard_viewed",
        event_data={
            "user_id": user_id,
            "role": user_role,
            "jobs_count": len(user_jobs),
            "timestamp": datetime.now().timestamp()
        }
    )
            
    return {
        "user_id": user_id,
        "role": user_role,
        "jobs": user_jobs,
        "metrics": metrics
    }


# Admin endpoints
@router.post("/admin/evolve")
async def trigger_evolution(user_id: str = Depends(verify_token)):
    """Trigger agent evolution with MCP integration"""
    # Check if admin (in production, use proper role check)
    is_admin = False
    for user in users.values():
        if user["id"] == user_id and user.get("role") == "admin":
            is_admin = True
            break
            
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    # Trigger evolution
    evolution_results = await orchestrator.evolve_agents()
    metrics = await orchestrator.get_performance_metrics()
    
    return {
        "status": "evolution_complete",
        "evolution_results": evolution_results,
        "metrics": metrics
    }


# MCP specific endpoints
@router.get("/mcp/status")
async def get_mcp_status(user_id: str = Depends(verify_token)):
    """Get MCP connection status"""
    return await orchestrator.initialize_mcp_connections()


@router.post("/mcp/refresh")
async def refresh_mcp_connections(user_id: str = Depends(verify_token)):
    """Refresh MCP connections"""
    return await orchestrator.initialize_mcp_connections()


# Testing endpoints
@router.post("/test/init")
async def initialize_test_data():
    """Initialize test data (development only)"""
    # Only allow in development
    if os.getenv("ENVIRONMENT", "dev") != "dev":
        raise HTTPException(status_code=403, detail="Only available in development")
        
    # Create test users
    if "testclient" not in users:
        users["testclient"] = {
            "id": "client-123",
            "password": pwd_context.hash("password"),
            "role": "client"
        }
        
    if "testfreelancer" not in users:
        users["testfreelancer"] = {
            "id": "freelancer-123",
            "password": pwd_context.hash("password"),
            "role": "freelancer"
        }
        
    # Create test freelancer profile
    profile = FreelancerProfile(
        user_id="freelancer-123",
        name="Test Freelancer",
        bio="Experienced developer with 5 years of experience",
        skills=["python", "javascript", "react", "fastapi"],
        hourly_rate=50.0,
        availability="full-time"
    )
    
    orchestrator.freelancers["freelancer-123"] = profile.dict()
    
    # Store embedding via MCP vector server
    profile_text = f"{profile.name} {profile.bio} {' '.join(profile.skills)}"
    await orchestrator.matching_agent.vector_manager.store_freelancer_embedding(
        "freelancer-123", profile_text, profile.dict()
    )
    
    # Log test data initialization in analytics
    await mcp_manager.analytics_log_event(
        event_type="test_data_initialized",
        event_data={
            "timestamp": datetime.now().timestamp()
        }
    )
    
    return {
        "status": "initialized",
        "test_client": "testclient",
        "test_freelancer": "testfreelancer",
        "password": "password"
    }
