"""
Tests for the CoinGecko MCP integration module
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))



@pytest.fixture
def mock_mcp_data():
    """Mock MCP data for testing"""
    return {
        "btc_mcp": 55.0,
        "eth_mcp": 15.0,
        "total_market_cap": 2500000000000,
        "last_updated": datetime.utcnow().timestamp()
    }


@pytest.fixture
def mock_mcp_client():
    """Create a mocked MCP client"""
    with patch("autotradex.data.mcp_integration.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "btc_mcp": 55.0,
            "eth_mcp": 15.0,
            "total_market_cap": 2500000000000,
            "last_updated": datetime.utcnow().timestamp()
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch("autotradex.data.mcp_integration.get_config_value") as mock_config:
            mock_config.return_value = "mock_value"
            yield CoinGeckoMCP()


class TestCoinGeckoMCP:
    """Test suite for CoinGeckoMCP class"""
    
    def test_init(self):
        """Test initialization"""
        with patch("autotradex.data.mcp_integration.get_config_value") as mock_config:
            mock_config.return_value = "mock_value"
            client = CoinGeckoMCP()
            assert client.api_key == "mock_value"
            assert client.base_url == "mock_value"
    
    def test_get_current_mcp(self, mock_mcp_client):
        """Test getting current MCP data"""
        mcp_data = mock_mcp_client.get_current_mcp()
        assert "btc_mcp" in mcp_data
        assert "eth_mcp" in mcp_data
        assert "total_market_cap" in mcp_data
    
    def test_classify_regime_btc_dominant(self, mock_mcp_client, mock_mcp_data):
        """Test regime classification - BTC dominant"""
        mock_mcp_data["btc_mcp"] = 55.0
        mock_mcp_data["eth_mcp"] = 15.0
        
        regime = mock_mcp_client.classify_regime(mock_mcp_data)
        assert regime == "BTC_DOMINANT"
    
    def test_classify_regime_alt_season(self, mock_mcp_client, mock_mcp_data):
        """Test regime classification - ALT season"""
        mock_mcp_data["btc_mcp"] = 40.0
        mock_mcp_data["eth_mcp"] = 25.0
        
        regime = mock_mcp_client.classify_regime(mock_mcp_data)
        assert regime == "ALT_SEASON"
    
    def test_classify_regime_neutral(self, mock_mcp_client, mock_mcp_data):
        """Test regime classification - Neutral"""
        mock_mcp_data["btc_mcp"] = 48.0
        mock_mcp_data["eth_mcp"] = 18.0
        
        regime = mock_mcp_client.classify_regime(mock_mcp_data)
        assert regime == "NEUTRAL"
    
    def test_get_market_context(self, mock_mcp_client):
        """Test getting market context"""
        with patch.object(mock_mcp_client, "get_current_mcp") as mock_get_mcp:
            mock_get_mcp.return_value = {
                "btc_mcp": 55.0,
                "eth_mcp": 15.0,
                "total_market_cap": 2500000000000,
                "last_updated": datetime.utcnow().timestamp()
            }
            
            with patch.object(mock_mcp_client, "_detect_sector_rotations") as mock_rotations:
                mock_rotations.return_value = ["DeFi", "AI", "Gaming"]
                
                context = mock_mcp_client.get_market_context()
                
                # Debug print to see what's actually being returned
                print(f"DEBUG - Context returned: {context}")
                
                assert "timestamp" in context
                assert "btc_dominance" in context
                assert "eth_dominance" in context
                assert "market_regime" in context
                assert "top_rotations" in context
                assert context["market_regime"] == "BTC_DOMINANT"
    
    def test_fallback_mcp(self, mock_mcp_client):
        """Test fallback MCP data"""
        fallback = mock_mcp_client._fallback_mcp()
        assert "btc_mcp" in fallback
        assert "eth_mcp" in fallback
        assert "total_market_cap" in fallback
        assert "last_updated" in fallback
