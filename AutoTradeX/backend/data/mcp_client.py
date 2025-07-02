"""
CoinGecko MCP Client
Client for interacting with the official CoinGecko MCP Server
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

from autotradex.utils.config import get_config_value

logger = logging.getLogger(__name__)

class CoinGeckoMCPClient:
    """Client for interacting with CoinGecko MCP Server"""
    
    def __init__(self):
        """Initialize the CoinGecko MCP client"""
        self.base_url = get_config_value("coingecko.mcp_base_url", "https://mcp.api.coingecko.com")
        self.api_key = get_config_value("coingecko.api_key", "")
        self.environment = get_config_value("coingecko.environment", "")
        
        # Set up headers based on environment
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.environment == "pro":
                self.headers["X-CG-Pro-API-Key"] = self.api_key
            elif self.environment == "demo":
                self.headers["X-CG-Demo-API-Key"] = self.api_key
        
        logger.debug(f"Initialized CoinGeckoMCPClient with base URL: {self.base_url}")
    
    def get_current_price(self, coin_id: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price of a cryptocurrency"""
        try:
            logger.debug(f"Fetching current price for {coin_id} in {vs_currency}")
            endpoint = f"/api/v3/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            response = self._make_request("GET", endpoint, params=params)
            return response
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return {}
    
    def get_market_cap_percentage(self) -> Dict[str, Any]:
        """Get market cap percentage data"""
        try:
            logger.debug("Fetching market cap percentage data")
            endpoint = "/api/v3/global"
            
            response = self._make_request("GET", endpoint)
            
            if "data" in response and "market_cap_percentage" in response["data"]:
                result = {
                    "btc_mcp": response["data"]["market_cap_percentage"].get("btc", 0),
                    "eth_mcp": response["data"]["market_cap_percentage"].get("eth", 0),
                    "total_market_cap": response["data"]["total_market_cap"].get("usd", 0),
                    "last_updated": datetime.now().timestamp()
                }
                
                # Add other top cryptocurrencies
                for key, value in response["data"]["market_cap_percentage"].items():
                    if key not in ["btc", "eth"]:
                        result[f"{key}_mcp"] = value
                
                logger.debug(f"MCP data received: BTC={result['btc_mcp']}%, ETH={result['eth_mcp']}%")
                return result
            else:
                logger.warning("Unexpected response format from MCP server")
                return self._fallback_mcp()
        except Exception as e:
            logger.error(f"Error fetching MCP data: {e}")
            return self._fallback_mcp()
    
    def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending coins"""
        try:
            logger.debug("Fetching trending coins")
            endpoint = "/api/v3/search/trending"
            
            response = self._make_request("GET", endpoint)
            
            if "coins" in response:
                trending = []
                for item in response["coins"]:
                    if "item" in item:
                        trending.append({
                            "id": item["item"].get("id", ""),
                            "name": item["item"].get("name", ""),
                            "symbol": item["item"].get("symbol", ""),
                            "market_cap_rank": item["item"].get("market_cap_rank", 0)
                        })
                return trending
            else:
                logger.warning("Unexpected response format for trending coins")
                return []
        except Exception as e:
            logger.error(f"Error fetching trending coins: {e}")
            return []
    
    def classify_regime(self, mcp_data: Optional[Dict[str, Any]] = None) -> str:
        """Classify market regime based on MCP thresholds"""
        if not mcp_data:
            mcp_data = self.get_market_cap_percentage()
        
        btc_mcp = mcp_data.get('btc_mcp', 0)
        eth_mcp = mcp_data.get('eth_mcp', 0)
        
        if btc_mcp > 52:
            regime = "BTC_DOMINANT"
        elif eth_mcp > 20 and btc_mcp < 45:
            regime = "ALT_SEASON"
        else:
            regime = "NEUTRAL"
            
        logger.info(f"Market regime classified as: {regime} (BTC: {btc_mcp}%, ETH: {eth_mcp}%)")
        return regime
    
    def get_market_context(self) -> Dict[str, Any]:
        """Get comprehensive market context"""
        mcp_data = self.get_market_cap_percentage()
        trending = self.get_trending_coins()
        
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "btc_dominance": mcp_data.get('btc_mcp', 0),
            "eth_dominance": mcp_data.get('eth_mcp', 0),
            "total_mcap": mcp_data.get('total_market_cap', 0),
            "market_regime": self.classify_regime(mcp_data),
            "trending_coins": trending[:3] if trending else []
        }
        
        logger.debug(f"Generated market context: {context}")
        return context
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the MCP server"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, params=params, json=data, timeout=10)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return {}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {}
    
    def _fallback_mcp(self) -> Dict[str, Any]:
        """Fallback when MCP server fails"""
        logger.warning("Using fallback MCP data due to API failure")
        return {
            "btc_mcp": 48.5,
            "eth_mcp": 16.2,
            "total_market_cap": 2500000000000,
            "last_updated": datetime.utcnow().timestamp()
        }

# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = CoinGeckoMCPClient()
    
    # Test market cap percentage
    mcp_data = client.get_market_cap_percentage()
    print(f"Market Cap Percentages: BTC={mcp_data.get('btc_mcp')}%, ETH={mcp_data.get('eth_mcp')}%")
    
    # Test regime classification
    regime = client.classify_regime(mcp_data)
    print(f"Current Market Regime: {regime}")
    
    # Test trending coins
    trending = client.get_trending_coins()
    print(f"Trending Coins: {trending[:3] if trending else 'None found'}")
