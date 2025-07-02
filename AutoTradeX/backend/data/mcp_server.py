#!/usr/bin/env python3
"""
CoinGecko MCP Server
Provides a FastAPI server for Market Cap Percentage data
"""

import os
import argparse
import logging
import requests
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

# Initialize FastAPI app
app = FastAPI(
    title="CoinGecko MCP Server",
    description="Market Cap Percentage data provider for AutoTradeX",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CoinGecko API key
API_KEY = os.getenv("COINGECKO_API_KEY")
if not API_KEY:
    logger.warning("COINGECKO_API_KEY environment variable not set")

# CoinGecko API base URL
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Cache for MCP data to reduce API calls
mcp_cache = {
    "current": None,
    "current_timestamp": 0,
    "historical": {},
}

# Cache TTL in seconds
CACHE_TTL = 300  # 5 minutes

def get_api_key():
    """Get API key from environment variable"""
    if not API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="CoinGecko API key not configured"
        )
    return API_KEY

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CoinGecko MCP Server",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/current")
async def get_current_mcp(api_key: str = Depends(get_api_key)):
    """Get current market cap percentages"""
    global mcp_cache
    
    # Check cache
    current_time = datetime.now().timestamp()
    if (mcp_cache["current"] is not None and 
            current_time - mcp_cache["current_timestamp"] < CACHE_TTL):
        logger.debug("Returning cached MCP data")
        return mcp_cache["current"]
    
    try:
        logger.info("Fetching current MCP data from CoinGecko")
        # Get global market data
        headers = {"x-cg-pro-api-key": api_key}
        response = requests.get(
            f"{COINGECKO_API_URL}/global",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract market cap percentages
        market_cap_percentage = data.get("data", {}).get("market_cap_percentage", {})
        total_market_cap = data.get("data", {}).get("total_market_cap", {}).get("usd", 0)
        
        # Format response
        result = {
            "btc_mcp": market_cap_percentage.get("btc", 0),
            "eth_mcp": market_cap_percentage.get("eth", 0),
            "total_market_cap": total_market_cap,
            "last_updated": current_time
        }
        
        # Add other top cryptocurrencies
        for key, value in market_cap_percentage.items():
            if key not in ["btc", "eth"]:
                result[f"{key}_mcp"] = value
        
        # Update cache
        mcp_cache["current"] = result
        mcp_cache["current_timestamp"] = current_time
        
        return result
    except Exception as e:
        logger.error(f"Error fetching MCP data: {e}")
        # Return cached data if available, otherwise raise exception
        if mcp_cache["current"] is not None:
            logger.warning("Returning stale cached data due to API error")
            return mcp_cache["current"]
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/historical")
async def get_historical_mcp(days: int = 30, api_key: str = Depends(get_api_key)):
    """Get historical MCP data"""
    global mcp_cache
    
    # Check cache
    current_time = datetime.now().timestamp()
    cache_key = f"historical_{days}"
    if (cache_key in mcp_cache["historical"] and 
            current_time - mcp_cache["historical"][cache_key]["timestamp"] < CACHE_TTL * 4):
        logger.debug(f"Returning cached historical MCP data for {days} days")
        return mcp_cache["historical"][cache_key]["data"]
    
    try:
        logger.info(f"Fetching historical MCP data for {days} days from CoinGecko")
        headers = {"x-cg-pro-api-key": api_key}
        
        # Get BTC historical data
        btc_response = requests.get(
            f"{COINGECKO_API_URL}/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": days},
            headers=headers,
            timeout=10
        )
        btc_response.raise_for_status()
        btc_data = btc_response.json()
        
        # Get ETH historical data
        eth_response = requests.get(
            f"{COINGECKO_API_URL}/coins/ethereum/market_chart",
            params={"vs_currency": "usd", "days": days},
            headers=headers,
            timeout=10
        )
        eth_response.raise_for_status()
        eth_data = eth_response.json()
        
        # Get global market cap data
        global_response = requests.get(
            f"{COINGECKO_API_URL}/global/market_cap_chart",
            params={"days": days},
            headers=headers,
            timeout=10
        )
        global_response.raise_for_status()
        global_data = global_response.json()
        
        # Process and combine data
        result = {"data": []}
        
        # Use the shortest data series length
        min_length = min(
            len(btc_data.get("market_caps", [])),
            len(eth_data.get("market_caps", [])),
            len(global_data.get("market_caps", []))
        )
        
        for i in range(min_length):
            timestamp = btc_data["market_caps"][i][0]
            btc_mcap = btc_data["market_caps"][i][1]
            eth_mcap = eth_data["market_caps"][i][1]
            total_mcap = global_data["market_caps"][i][1]
            
            # Calculate percentages
            btc_percentage = (btc_mcap / total_mcap) * 100 if total_mcap > 0 else 0
            eth_percentage = (eth_mcap / total_mcap) * 100 if total_mcap > 0 else 0
            
            result["data"].append({
                "timestamp": timestamp,
                "btc_mcp": btc_percentage,
                "eth_mcp": eth_percentage,
                "total_market_cap": total_mcap
            })
        
        # Update cache
        mcp_cache["historical"][cache_key] = {
            "data": result,
            "timestamp": current_time
        }
        
        return result
    except Exception as e:
        logger.error(f"Error fetching historical MCP data: {e}")
        # Return cached data if available, otherwise raise exception
        if cache_key in mcp_cache["historical"]:
            logger.warning("Returning stale cached data due to API error")
            return mcp_cache["historical"][cache_key]["data"]
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/regime")
async def get_market_regime():
    """Get current market regime classification"""
    try:
        # Get current MCP data
        mcp_data = await get_current_mcp()
        
        # Classify regime
        btc_mcp = mcp_data.get("btc_mcp", 0)
        eth_mcp = mcp_data.get("eth_mcp", 0)
        
        if btc_mcp > 52:
            regime = "BTC_DOMINANT"
        elif eth_mcp > 20 and btc_mcp < 45:
            regime = "ALT_SEASON"
        else:
            regime = "NEUTRAL"
            
        return {
            "regime": regime,
            "btc_dominance": btc_mcp,
            "eth_dominance": eth_mcp,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error determining market regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clear-cache")
async def clear_cache():
    """Clear the MCP data cache"""
    global mcp_cache
    mcp_cache = {
        "current": None,
        "current_timestamp": 0,
        "historical": {},
    }
    return {"status": "cache_cleared", "timestamp": datetime.now().isoformat()}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CoinGecko MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)
    
    # Start server
    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="debug" if args.debug else "info")

if __name__ == "__main__":
    main()
