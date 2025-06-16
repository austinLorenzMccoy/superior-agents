#!/usr/bin/env python3
"""
GigNova: Tests for API routes
"""

import pytest
from unittest.mock import patch, AsyncMock
import json

from gignova.models.base import JobStatus


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    
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
    
    response = test_client.post("/auth/register", json=register_data)
    
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["role"] == "client"
    
    # Test login
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = test_client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    assert response.json()["access_token"] == "test_token"
    assert response.json()["token_type"] == "bearer"


@patch("gignova.api.routes.verify_token")
@patch("gignova.api.routes.orchestrator.process_job_posting")
def test_create_job(mock_process_job, mock_verify_token, test_client, sample_job_post):
    """Test job creation endpoint"""
    mock_verify_token.return_value = "test-client-id"
    mock_process_job.return_value = AsyncMock(return_value={
        "job_id": "job123",
        "status": "active",
        "freelancer_id": "freelancer123",
        "agreed_rate": 1000.0
    })()
    
    response = test_client.post(
        "/jobs", 
        json=sample_job_post.dict(),
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == "job123"
    assert response.json()["status"] == "active"


@patch("gignova.api.routes.verify_token")
def test_get_job(mock_verify_token, test_client, sample_job_post):
    """Test get job endpoint"""
    mock_verify_token.return_value = "test-client-id"
    
    # Setup job in orchestrator
    test_client.app.state.orchestrator = test_client.app.state.orchestrator or {}
    test_client.app.state.orchestrator.jobs = {
        "job123": {
            "post": sample_job_post,
            "status": JobStatus.ACTIVE,
            "created_at": "2023-01-01T00:00:00",
            "freelancer_id": "freelancer123"
        }
    }
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator:
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "created_at": "2023-01-01T00:00:00",
                "freelancer_id": "freelancer123"
            }
        }
        
        response = test_client.get(
            "/jobs/job123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["job_id"] == "job123"
        assert response.json()["status"] == "active"


@patch("gignova.api.routes.verify_token")
@patch("gignova.api.routes.orchestrator.submit_deliverable")
async def test_submit_deliverable(mock_submit, mock_verify_token, test_client, sample_job_post):
    """Test deliverable submission endpoint"""
    mock_verify_token.return_value = "freelancer123"
    mock_submit.return_value = AsyncMock(return_value={
        "job_id": "job123",
        "qa_passed": True,
        "similarity_score": 0.92,
        "ipfs_hash": "ipfs123"
    })()
    
    # Setup job in orchestrator
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator:
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "freelancer_id": "freelancer123"
            }
        }
        
        # Create test file
        test_file = {"deliverable": ("test.txt", b"Test deliverable content")}
        
        response = test_client.post(
            "/jobs/job123/deliverable",
            files=test_file,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["job_id"] == "job123"
        assert response.json()["qa_passed"] is True


@patch("gignova.api.routes.verify_token")
def test_register_freelancer(mock_verify_token, test_client, sample_freelancer_profile):
    """Test freelancer registration endpoint"""
    mock_verify_token.return_value = "test-freelancer-id"
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator:
        mock_orchestrator.freelancers = {}
        mock_orchestrator.matching_agent.vector_manager.store_freelancer_embedding = AsyncMock()
        
        response = test_client.post(
            "/freelancers",
            json=sample_freelancer_profile.dict(),
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["freelancer_id"] == "test-freelancer-id"
        assert response.json()["status"] == "registered"


@patch("gignova.api.routes.verify_token")
def test_list_jobs(mock_verify_token, test_client, sample_job_post):
    """Test job listing endpoint"""
    mock_verify_token.return_value = "test-client-id"
    
    with patch("gignova.api.routes.orchestrator") as mock_orchestrator:
        mock_orchestrator.jobs = {
            "job123": {
                "post": sample_job_post,
                "status": JobStatus.ACTIVE,
                "created_at": "2023-01-01T00:00:00"
            }
        }
        
        response = test_client.get(
            "/jobs",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["job_id"] == "job123"
        assert response.json()[0]["status"] == "active"
