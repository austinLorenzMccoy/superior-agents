#!/usr/bin/env python3
"""
GigNova: Tests for agent modules
"""

import pytest
from unittest.mock import patch, MagicMock

from gignova.models.base import AgentType, AgentConfig, JobPost
from gignova.agents.base import BaseAgent
from gignova.agents.matching import MatchingAgent
from gignova.agents.negotiation import NegotiationAgent
from gignova.agents.qa import QAAgent
from gignova.agents.payment import PaymentAgent


def test_base_agent_initialization(agent_config):
    """Test base agent initialization"""
    agent = BaseAgent(AgentType.MATCHING, agent_config)
    
    assert agent.agent_type == AgentType.MATCHING
    assert agent.config == agent_config
    assert hasattr(agent, 'vector_manager')
    assert len(agent.memory) == 0


def test_matching_agent_initialization(agent_config):
    """Test matching agent initialization"""
    agent = MatchingAgent(agent_config)
    
    assert agent.agent_type == AgentType.MATCHING
    assert agent.config == agent_config


def test_matching_agent_find_matches(matching_agent, sample_job_post):
    """Test matching agent find_matches method"""
    # Mock vector_manager.find_matches to return test data
    with patch.object(matching_agent.vector_manager, 'find_matches') as mock_find:
        mock_find.return_value = [
            {
                'freelancer_id': 'freelancer1',
                'score': 0.85,
                'payload': {'name': 'Test Freelancer 1'}
            },
            {
                'freelancer_id': 'freelancer2',
                'score': 0.65,
                'payload': {'name': 'Test Freelancer 2'}
            }
        ]
        
        matches = matching_agent.find_matches(sample_job_post)
        
        # Only the first match should be returned (score >= threshold)
        assert len(matches) == 1
        assert matches[0].freelancer_id == 'freelancer1'
        assert matches[0].confidence_score == 0.85


def test_negotiation_agent_negotiate(negotiation_agent):
    """Test negotiation agent negotiate method"""
    client_budget = (800.0, 1000.0)
    
    # Test successful negotiation (rate within budget)
    result = negotiation_agent.negotiate(client_budget, 900.0)
    assert result['success'] is True
    assert result['agreed_rate'] == 900.0
    assert result['rounds'] == 0
    
    # Test successful negotiation (rate slightly above budget)
    result = negotiation_agent.negotiate(client_budget, 1100.0)
    assert result['success'] is True
    assert 1000.0 <= result['agreed_rate'] <= 1100.0
    
    # Test failed negotiation (rate far above budget)
    result = negotiation_agent.negotiate(client_budget, 2000.0)
    assert result['success'] is False


@patch('gignova.ipfs.manager.IPFSManager')
def test_qa_agent_validate_deliverable(mock_ipfs, qa_agent):
    """Test QA agent validate_deliverable method"""
    # Mock IPFS manager to return test data
    mock_instance = MagicMock()
    mock_instance.retrieve_deliverable.return_value = b"This is a test deliverable with good quality content"
    qa_agent.ipfs_manager = mock_instance
    
    # Mock vector_manager.encoder to return test embeddings
    with patch.object(qa_agent.vector_manager, 'encoder') as mock_encoder:
        mock_encoder.encode.side_effect = [
            [0.1, 0.2, 0.3],  # First call (job requirements)
            [0.15, 0.25, 0.35]  # Second call (deliverable)
        ]
        
        result = qa_agent.validate_deliverable(
            "Test job requirements",
            "test_hash_123"
        )
        
        assert result.deliverable_hash == "test_hash_123"
        assert result.passed is True  # High similarity by default in our mock


def test_payment_agent_methods(payment_agent):
    """Test payment agent methods"""
    # Mock blockchain_manager methods
    with patch.object(payment_agent.blockchain_manager, 'create_escrow') as mock_create:
        mock_create.return_value = "0xtx_hash_123"
        
        job_data = {
            'job_id': 'job123',
            'client': 'client123',
            'freelancer': 'freelancer123',
            'amount': 1000.0,
            'ipfs_hash': 'ipfs_hash_123'
        }
        
        tx_hash = payment_agent.create_escrow(job_data)
        assert tx_hash == "0xtx_hash_123"
        
    # Test release_payment with QA passed
    with patch.object(payment_agent.blockchain_manager, 'release_payment') as mock_release:
        mock_release.return_value = "0xtx_hash_456"
        
        result = payment_agent.release_payment('job123', True)
        assert result['success'] is True
        assert result['tx_hash'] == "0xtx_hash_456"
        
    # Test release_payment with QA failed
    result = payment_agent.release_payment('job123', False)
    assert result['success'] is False
    assert result['tx_hash'] is None
