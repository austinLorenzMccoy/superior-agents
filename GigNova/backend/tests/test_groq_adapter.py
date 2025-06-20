#!/usr/bin/env python3
"""
Test suite for Groq adapter integration
"""

import os
import pytest
from unittest.mock import AsyncMock, patch

from gignova.llm.groq_adapter import GroqAdapter


@pytest.fixture
def mock_groq_adapter():
    """Create a mock Groq adapter for testing"""
    with patch('gignova.llm.groq_adapter.ChatGroq') as mock_chat_groq:
        # Configure the mock to return a response with content
        mock_instance = mock_chat_groq.return_value
        mock_response = AsyncMock()
        mock_response.content = "This is a mock response from Groq"
        mock_instance.invoke.return_value = mock_response
        
        # Create adapter with the mock
        adapter = GroqAdapter(model_name="test-model")
        yield adapter


@pytest.mark.asyncio
async def test_generate_text(mock_groq_adapter):
    """Test generating text with the Groq adapter"""
    # Call the generate_text method
    response = await mock_groq_adapter.generate_text(
        prompt="Test prompt",
        system_prompt="Test system prompt",
        temperature=0.5
    )
    
    # Verify the response
    assert response == "This is a mock response from Groq"
    
    # Verify the mock was called with the right parameters
    mock_groq_adapter.llm.invoke.assert_called_once()


@pytest.mark.asyncio
async def test_generate_structured_output(mock_groq_adapter):
    """Test generating structured output with the Groq adapter"""
    # Mock the generate_text method to return a JSON string
    mock_groq_adapter.generate_text = AsyncMock(return_value='{"key": "value"}')
    
    # Call the generate_structured_output method
    response = await mock_groq_adapter.generate_structured_output(
        prompt="Test prompt",
        system_prompt="Test system prompt",
        output_schema={"key": "str"}
    )
    
    # Verify the response
    assert response == {"key": "value"}
    
    # Verify the generate_text method was called
    mock_groq_adapter.generate_text.assert_called_once()


@pytest.mark.asyncio
async def test_generate_structured_output_error_handling(mock_groq_adapter):
    """Test error handling in generate_structured_output"""
    # Mock the generate_text method to return an invalid JSON string
    mock_groq_adapter.generate_text = AsyncMock(return_value='Not a JSON string')
    
    # Call the generate_structured_output method
    response = await mock_groq_adapter.generate_structured_output(
        prompt="Test prompt",
        output_schema={"key": "str"}
    )
    
    # Verify the response contains error information
    assert "error" in response
    assert "raw_response" in response
    assert response["raw_response"] == "Not a JSON string"
