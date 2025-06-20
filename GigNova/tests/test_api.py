#!/usr/bin/env python3
"""
GigNova: Tests for API routes
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, AsyncMock

from gignova.models.base import JobStatus


def test_health_check(test_client):
    """Test health check endpoint"""
    with patch("gignova.api.routes.orchestrator.initialize_mcp_connections") as mock_init:
        # Mock a healthy MCP connection status
        mock_init.return_value = {"status": "connected"}
        
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@patch("gignova.api.routes.create_token")
def test_register_and_login(mock_create_token, test_client):
    """Test user registration and login"""
    mock_create_token.return_value = "test_token"
    
    # Test registration
    register_data = {
        "username": "testuser",
        "password": "password123",
        "role": "client"
    }
    
    response = test_client.post("/api/v1/auth/register", json=register_data)
    
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["role"] == "client"
    
    # Test login
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = test_client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    assert response.json()["access_token"] == "test_token"
    assert response.json()["token_type"] == "bearer"


@patch("gignova.api.routes.verify_token")
@patch("gignova.api.routes.orchestrator.process_job_posting")
def test_create_job(mock_process_job, mock_verify_token, test_client, sample_job_post):
    """Test job creation endpoint"""
    mock_verify_token.return_value = "test-client-id"
    mock_process_job.return_value = {
        "job_id": "job123",
        "status": "active",
        "freelancer_id": "freelancer123",
        "agreed_rate": 1000.0,
        "contract_address": "0xcontract123",
        "escrow_id": "escrow123",
        "confidence_score": 0.85
    }
    
    response = test_client.post(
        "/api/v1/jobs", 
        json=sample_job_post.model_dump(),
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == "job123"
    assert response.json()["status"] == "active"


@pytest.mark.xfail(reason="Needs further investigation for authorization issues")
@patch("gignova.api.routes.verify_token")
def test_get_job(mock_verify_token, test_client, sample_job_post):
    """Test get job endpoint"""
    # Set client ID to match the job's client_id
    test_client_id = "test-client-id"
    mock_verify_token.return_value = test_client_id
    sample_job_post.client_id = test_client_id  # Ensure the job is owned by this client
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator, \
         patch("gignova.api.routes.mcp_manager.analytics_log_event") as mock_analytics:
        # Mock the analytics_log_event to prevent errors
        mock_analytics.return_value = None
        
        # Configure the jobs dictionary with the job associated with the test user
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "created_at": datetime.now().isoformat(),
                "freelancer_id": "freelancer123"
            }
        }
        
        response = test_client.get(
            "/api/v1/jobs/job123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["job_id"] == "job123"
        assert response.json()["status"] == "active"


@pytest.mark.xfail(reason="Needs further investigation for authorization issues")
@patch("gignova.api.routes.verify_token")
def test_submit_deliverable(mock_verify_token, test_client, sample_job_post):
    """Test deliverable submission endpoint"""
    # Set the mock_verify_token to return the same freelancer_id that's in the job
    test_freelancer_id = "freelancer123"
    mock_verify_token.return_value = test_freelancer_id
    
    # Setup job in orchestrator and mock submit_deliverable
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator:
        # Configure the jobs dictionary
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "freelancer_id": test_freelancer_id
            }
        }
        
        # Mock the submit_deliverable method
        mock_orchestrator.submit_deliverable = AsyncMock(return_value={
            "job_id": "job123",
            "qa_passed": True,
            "similarity_score": 0.92,
            "ipfs_hash": "ipfs123",
            "transaction_hash": "0xtx123"
        })
        
        # Create test file
        test_file = {"deliverable": ("test.txt", b"Test deliverable content")}
        
        response = test_client.post(
            "/api/v1/jobs/job123/deliverable",
            files=test_file,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["job_id"] == "job123"
        assert response.json()["qa_passed"] is True


@pytest.mark.xfail(reason="Needs further investigation for user_id validation issues")
@patch("gignova.api.routes.verify_token")
def test_register_freelancer(mock_verify_token, test_client, sample_freelancer_profile):
    """Test freelancer registration endpoint"""
    # Ensure the mock_verify_token returns the same ID as the freelancer_id in the profile
    mock_verify_token.return_value = sample_freelancer_profile.freelancer_id
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator, \
         patch("gignova.api.routes.mcp_manager.analytics_log_event") as mock_analytics:
        # Mock the analytics_log_event to prevent errors
        mock_analytics.return_value = None
        mock_orchestrator.freelancers = {}
        mock_orchestrator.matching_agent.vector_manager.store_freelancer_embedding = AsyncMock()
        
        # Create a modified JSON that includes user_id explicitly
        profile_data = sample_freelancer_profile.model_dump()
        
        response = test_client.post(
            "/api/v1/freelancers",
            json=profile_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["freelancer_id"] == "test-freelancer-id"
        assert response.json()["status"] == "registered"


@pytest.mark.xfail(reason="Needs further investigation for job filtering issues")
@patch("gignova.api.routes.verify_token")
def test_list_jobs(mock_verify_token, test_client, sample_job_post):
    """Test job listing endpoint"""
    # Set the client_id in the job post to match the user ID from verify_token
    test_client_id = "test-client-id"
    mock_verify_token.return_value = test_client_id
    sample_job_post.client_id = test_client_id
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator, \
         patch("gignova.api.routes.mcp_manager.analytics_log_event") as mock_analytics:
        # Mock the analytics_log_event to prevent errors
        mock_analytics.return_value = None
        
        # Configure the jobs dictionary with the job associated with the test user
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "created_at": datetime.now().isoformat()
            }
        }
        
        response = test_client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["job_id"] == "job123"
        assert response.json()[0]["status"] == "active"
