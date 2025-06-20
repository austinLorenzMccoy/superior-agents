#!/usr/bin/env python3
"""
GigNova: Test Configuration
"""

import os
import pytest
from fastapi.testclient import TestClient

from gignova.app import app
from gignova.models.base import JobPost, FreelancerProfile, AgentConfig
from gignova.agents.matching import MatchingAgent
from gignova.agents.negotiation import NegotiationAgent
from gignova.agents.qa import QAAgent
from gignova.agents.payment import PaymentAgent
from gignova.orchestrator import GigNovaOrchestrator


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app with authentication bypass"""
    # Create a test user ID to use in tests
    test_user_id = "test-user-id"
    
    # Override the verify_token dependency for testing
    def mock_verify_token():
        return test_user_id
    
    app.dependency_overrides = {}
    # Override the security dependency
    from gignova.api.routes import verify_token
    app.dependency_overrides[verify_token] = mock_verify_token
    
    client = TestClient(app)
    yield client
    
    # Clean up after tests
    app.dependency_overrides = {}


@pytest.fixture
def agent_config():
    """Create a test agent configuration"""
    return AgentConfig(
        confidence_threshold=0.7,
        negotiation_rounds=3,
        qa_similarity_threshold=0.8,
        learning_rate=0.05
    )


@pytest.fixture
def matching_agent(agent_config):
    """Create a test matching agent"""
    return MatchingAgent(agent_config)


@pytest.fixture
def negotiation_agent(agent_config):
    """Create a test negotiation agent"""
    return NegotiationAgent(agent_config)


@pytest.fixture
def qa_agent(agent_config):
    """Create a test QA agent"""
    return QAAgent(agent_config)


@pytest.fixture
def payment_agent(agent_config):
    """Create a test payment agent"""
    return PaymentAgent(agent_config)


@pytest.fixture
def orchestrator():
    """Create a test orchestrator"""
    return GigNovaOrchestrator()


@pytest.fixture
def sample_job_post():
    """Create a sample job post"""
    return JobPost(
        title="Test Web Application",
        description="Build a responsive web application using React and FastAPI",
        skills=["react", "fastapi", "python", "javascript"],
        budget_min=1000.0,
        budget_max=2000.0,
        deadline_days=14,
        client_id="test-client-id"
    )


@pytest.fixture
def sample_freelancer_profile():
    """Create a sample freelancer profile"""
    return FreelancerProfile(
        freelancer_id="test-freelancer-id",
        name="Test Freelancer",
        bio="Experienced developer with 5 years of experience in web development",
        skills=["react", "fastapi", "python", "javascript", "typescript"],
        hourly_rate=50.0,
        availability="full-time"
    )


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    # In a real test, you would generate a valid JWT token
    return {"Authorization": "Bearer test_token"}
