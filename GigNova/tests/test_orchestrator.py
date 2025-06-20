#!/usr/bin/env python3
"""
GigNova: Tests for orchestrator
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from gignova.models.base import JobStatus, JobPost, JobMatch, QAResult
from gignova.orchestrator import GigNovaOrchestrator, mcp_manager


@pytest.fixture
def mock_agents():
    """Create mocked agents for testing"""
    mock_matching = MagicMock()
    mock_negotiation = MagicMock()
    mock_qa = MagicMock()
    mock_payment = MagicMock()
    
    return {
        'matching': mock_matching,
        'negotiation': mock_negotiation,
        'qa': mock_qa,
        'payment': mock_payment
    }


@patch('gignova.orchestrator.MatchingAgent')
@patch('gignova.orchestrator.NegotiationAgent')
@patch('gignova.orchestrator.QAAgent')
@patch('gignova.orchestrator.PaymentAgent')
def test_orchestrator_initialization(mock_payment, mock_qa, mock_negotiation, mock_matching):
    """Test orchestrator initialization"""
    orchestrator = GigNovaOrchestrator()
    
    assert orchestrator.matching_agent is not None
    assert orchestrator.negotiation_agent is not None
    assert orchestrator.qa_agent is not None
    assert orchestrator.payment_agent is not None
    assert orchestrator.jobs == {}
    assert orchestrator.freelancers == {}
    assert orchestrator.contracts == {}


@pytest.mark.asyncio
async def test_process_job_posting(sample_job_post):
    """Test job posting processing"""
    # Mock MCP manager
    mcp_manager.analytics_log_event = AsyncMock(return_value={"success": True})
    
    orchestrator = GigNovaOrchestrator()
    
    # Mock vector_manager.store_job_embedding to prevent "Numpy is not available" error
    orchestrator.matching_agent.vector_manager.store_job_embedding = AsyncMock(return_value={"success": True})
    
    # Mock agent methods
    orchestrator.matching_agent.find_matches = AsyncMock(return_value=[
        {
            "job_id": "job123",
            "freelancer_id": "freelancer123",
            "score": 0.85,
            "reasons": ["Skill match"]
        }
    ])
    
    orchestrator.negotiation_agent.negotiate = AsyncMock(return_value={
        "agreed_rate": 1500.0,
        "rounds": 2,
        "success": True
    })
    
    orchestrator.payment_agent.create_escrow = AsyncMock(return_value={
        "success": True,
        "contract_address": "0xcontract_123",
        "escrow_id": "escrow_123",
        "transaction_hash": "0xtx_hash_123"
    })
    
    # Add a test freelancer
    orchestrator.freelancers["freelancer123"] = {
        "hourly_rate": 60.0
    }
    
    # Process job
    result = await orchestrator.process_job_posting(sample_job_post)
    
    assert result["status"] == "active"
    assert result["freelancer_id"] == "freelancer123"
    assert result["agreed_rate"] == 1500.0
    assert result["contract_address"] == "0xcontract_123"
    assert result["escrow_id"] == "escrow_123"
    assert result["confidence_score"] == 0.85
    
    # Check job was stored
    job_id = result["job_id"]
    assert job_id in orchestrator.jobs
    assert orchestrator.jobs[job_id]["status"] == JobStatus.ACTIVE


@pytest.mark.asyncio
async def test_submit_deliverable():
    """Test deliverable submission"""
    # Mock MCP manager
    mcp_manager.analytics_log_event = AsyncMock(return_value={"success": True})
    
    orchestrator = GigNovaOrchestrator()
    
    # Setup test job
    job_post = JobPost(
        title="Test Job",
        description="Test description",
        skills=["python"],
        budget_min=1000.0,
        budget_max=2000.0,
        deadline_days=14,
        client_id="client123"
    )
    
    job_id = "job123"
    orchestrator.jobs[job_id] = {
        "post": job_post,
        "status": JobStatus.ACTIVE,
        "created_at": datetime.now(),
        "freelancer_id": "freelancer123"
    }
    
    # Mock agent methods
    orchestrator.qa_agent.ipfs_manager.store_deliverable = AsyncMock(return_value="ipfs_hash_123")
    
    orchestrator.qa_agent.validate_deliverable = AsyncMock(return_value=QAResult(
        job_id=job_id,
        deliverable_hash="ipfs_hash_123",
        similarity_score=0.92,
        passed=True,
        feedback="Excellent work"
    ))
    
    orchestrator.payment_agent.release_payment = AsyncMock(return_value={
        "success": True,
        "transaction_hash": "0xtx_hash_456",
        "message": "Payment released successfully"
    })
    
    # Submit deliverable
    result = await orchestrator.submit_deliverable(job_id, b"Test deliverable content")
    
    assert result["job_id"] == job_id
    assert result["qa_passed"] is True
    assert result["similarity_score"] == 0.92
    assert result["file_hash"] == "ipfs_hash_123"
    assert result["payment_released"] is True
    
    # Check job was updated
    assert orchestrator.jobs[job_id]["status"] == JobStatus.COMPLETED
    assert orchestrator.jobs[job_id]["deliverable_hash"] == "ipfs_hash_123"


@pytest.mark.asyncio
async def test_get_performance_metrics():
    """Test performance metrics calculation"""
    # Mock MCP manager
    mcp_manager.analytics_log_event = AsyncMock(return_value={"success": True})
    mcp_manager.analytics_get_metrics = AsyncMock(return_value={"success": True, "data": {"mcp_metric": 0.95}})
    
    orchestrator = GigNovaOrchestrator()
    
    # Setup test jobs
    job_post = JobPost(
        title="Test Job",
        description="Test description",
        skills=["python"],
        budget_min=1000.0,
        budget_max=2000.0,
        deadline_days=14,
        client_id="client123"
    )
    
    # Add jobs with different statuses
    orchestrator.jobs = {
        "job1": {
            "post": job_post,
            "status": JobStatus.POSTED,
            "created_at": datetime.now()
        },
        "job2": {
            "post": job_post,
            "status": JobStatus.ACTIVE,
            "created_at": datetime.now(),
            "freelancer_id": "freelancer1"
        },
        "job3": {
            "post": job_post,
            "status": JobStatus.COMPLETED,
            "created_at": datetime.now(),
            "freelancer_id": "freelancer2",
            "qa_result": QAResult(
                job_id="job3",
                deliverable_hash="ipfs_hash_123",
                similarity_score=0.92,
                passed=True,
                feedback="Good work"
            )
        }
    }
    
    # Get metrics
    metrics = await orchestrator.get_performance_metrics()
    
    assert metrics["total_jobs"] == 3
    assert metrics["match_rate"] == 2/3  # 2 out of 3 jobs matched
    assert metrics["completion_rate"] == 1/3  # 1 out of 3 jobs completed
    assert metrics["avg_qa_score"] == 0.92  # Only one job with QA
    assert metrics["active_jobs"] == 1  # One active job
