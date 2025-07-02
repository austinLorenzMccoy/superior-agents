# Setting Up CoinGecko MCP Server: A Step-by-Step Guide

This guide will walk you through the process of setting up and configuring the CoinGecko Market Cap Percentage (MCP) server for use with AutoTradeX. This server provides crucial market dominance data that powers the adaptive trading strategies.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting a CoinGecko API Key](#getting-a-coingecko-api-key)
3. [Setting Up the MCP Server](#setting-up-the-mcp-server)
4. [Testing the MCP Server](#testing-the-mcp-server)
5. [Configuring AutoTradeX to Use Your MCP Server](#configuring-autotradex)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:

- Python 3.10 or higher installed
- Git installed
- Basic knowledge of terminal/command line
- A free CoinGecko account (or willingness to create one)

## Getting a CoinGecko API Key

1. **Create a CoinGecko account**:
   - Go to [CoinGecko's website](https://www.coingecko.com/)
   - Click on "Sign Up" in the top right corner
   - Complete the registration process

2. **Subscribe to the free API plan**:
   - Log into your CoinGecko account
   - Navigate to "API" from the top menu or go to [CoinGecko API](https://www.coingecko.com/en/api)
   - Click on "Get Started for Free"
   - Follow the prompts to subscribe to the free tier

3. **Generate your API key**:
   - Once subscribed, go to your dashboard
   - Look for "API Keys" section
   - Click "Generate New Key"
   - Give your key a name (e.g., "AutoTradeX MCP")
   - Copy the generated API key and store it securely

## Setting Up the MCP Server

### Option 1: Using the Built-in MCP Server

AutoTradeX includes a built-in MCP server that you can run locally:

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/yourusername/autotradex.git
   cd autotradex
   ```

2. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Create a .env file** for your API keys:
   ```bash
   cp .env.example .env
   ```

4. **Edit the .env file** with your CoinGecko API key:
   ```
   COINGECKO_API_KEY=your_api_key_here
   ```

5. **Start the MCP server**:
   ```bash
   python -m autotradex.data.mcp_server --port 8080
   ```

### Option 2: Setting Up a Dedicated MCP Server

For production environments or if you want a separate MCP server:

1. **Create a new directory for your MCP server**:
   ```bash
   mkdir mcp-server
   cd mcp-server
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Create a requirements.txt file** with the following content:
   ```
   fastapi==0.104.0
   uvicorn[standard]==0.24.0
   requests==2.31.0
   python-dotenv==1.0.0
   ```

4. **Install the requirements**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a .env file** with your CoinGecko API key:
   ```
   COINGECKO_API_KEY=your_api_key_here
   ```

6. **Create an mcp_server.py file** with the following content:
   ```python
   import os
   import requests
   from fastapi import FastAPI, HTTPException
   from fastapi.middleware.cors import CORSMiddleware
   import uvicorn
   from dotenv import load_dotenv
   from datetime import datetime

   # Load environment variables
   load_dotenv()

   # Initialize FastAPI app
   app = FastAPI(
       title="CoinGecko MCP Server",
       description="Market Cap Percentage data provider",
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
       raise ValueError("COINGECKO_API_KEY environment variable not set")

   # CoinGecko API base URL
   COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

   @app.get("/")
   async def root():
       """Root endpoint"""
       return {
           "name": "CoinGecko MCP Server",
           "version": "1.0.0",
           "status": "online",
           "timestamp": datetime.now().isoformat()
       }

   @app.get("/current")
   async def get_current_mcp():
       """Get current market cap percentages"""
       try:
           # Get global market data
           headers = {"x-cg-pro-api-key": API_KEY}
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
               "last_updated": datetime.now().timestamp()
           }
           
           # Add other top cryptocurrencies
           for key, value in market_cap_percentage.items():
               if key not in ["btc", "eth"]:
                   result[f"{key}_mcp"] = value
           
           return result
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @app.get("/historical")
   async def get_historical_mcp(days: int = 30):
       """Get historical MCP data (simplified)"""
       try:
           # Get historical market data
           # Note: Free tier has limited historical data
           # This is a simplified implementation
           headers = {"x-cg-pro-api-key": API_KEY}
           
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
           
           return result
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8080)
   ```

7. **Start the MCP server**:
   ```bash
   python mcp_server.py
   ```

## Testing the MCP Server

Once your MCP server is running, you can test it using the following methods:

### Using a Web Browser

1. Open your web browser
2. Navigate to `http://localhost:8080/current`
3. You should see a JSON response with market cap percentages

### Using curl

```bash
curl http://localhost:8080/current
```

### Using Python requests

```python
import requests
response = requests.get("http://localhost:8080/current")
print(response.json())
```

## Configuring AutoTradeX

Now that your MCP server is running, you need to configure AutoTradeX to use it:

1. **Edit your .env file** in the AutoTradeX directory:
   ```
   MCP_BASE_URL=http://localhost:8080
   COINGECKO_API_KEY=your_api_key_here
   ```

2. **Verify the configuration**:
   ```bash
   python -m autotradex.data.mcp_integration
   ```

## Troubleshooting

### API Rate Limits

CoinGecko's free tier has rate limits. If you encounter rate limit errors:

1. Implement caching in your MCP server
2. Consider upgrading to a paid CoinGecko plan
3. Add retry logic with exponential backoff

### Connection Issues

If you can't connect to your MCP server:

1. Verify the server is running (`ps aux | grep mcp_server`)
2. Check if the port is in use (`netstat -tuln | grep 8080`)
3. Ensure firewall rules allow connections to the port

### Authentication Issues

If you encounter authentication errors with CoinGecko:

1. Verify your API key is correct
2. Check if your API key has expired
3. Ensure you're sending the API key in the correct header format

## Next Steps

Once your MCP server is running successfully:

1. Consider setting up a systemd service (Linux) or Windows service for automatic startup
2. Implement proper logging and monitoring
3. Add caching to reduce API calls to CoinGecko
4. Consider deploying to a cloud provider for 24/7 availability

---

Congratulations! You now have a functioning MCP server that provides market cap percentage data to your AutoTradeX system. This data will enable your trading agents to adapt to changing market regimes and make more informed decisions.
