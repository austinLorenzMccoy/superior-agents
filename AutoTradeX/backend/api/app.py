"""
FastAPI Web Interface for AutoTradeX
Provides REST API and web dashboard for the trading system
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data.mcp_integration import CoinGeckoMCP
from backend.agents.mcp_strategy import MCPStrategyAgent, MarketContext
from backend.training.memory import QdrantMemory
from backend.training.evolver import AgentEvolver
from backend.utils.config import get_config_value

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AutoTradeX API",
    description="Self-Evolving Crypto Trading Ecosystem",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
mcp_client = CoinGeckoMCP()
strategy_agent = MCPStrategyAgent()
memory = QdrantMemory()
evolver = AgentEvolver()

# WebSocket connections
active_connections: List[WebSocket] = []

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AutoTradeX API",
        "version": "0.2.0",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/market/regime")
async def get_market_regime():
    """Get current market regime"""
    try:
        mcp_data = mcp_client.get_current_mcp()
        regime = mcp_client.classify_regime(mcp_data)
        return {
            "regime": regime,
            "btc_dominance": mcp_data.get("btc_mcp"),
            "eth_dominance": mcp_data.get("eth_mcp"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/context")
async def get_market_context():
    """Get comprehensive market context"""
    try:
        context = mcp_client.get_market_context()
        return context
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/generate")
async def generate_strategy(request: Dict[str, Any]):
    """Generate a trading strategy"""
    try:
        # Create market context
        context = MarketContext(
            btc_dominance=request.get("btc_dominance", 0),
            market_regime=request.get("market_regime", "NEUTRAL"),
            sectors=request.get("sectors", ["DeFi", "AI", "Gaming"]),
            portfolio_value=request.get("portfolio_value", 10000),
            risk_profile=request.get("risk_profile", "moderate"),
            recent_trades=request.get("recent_trades", "No trades"),
            portfolio_change=request.get("portfolio_change", 0)
        )
        
        # Generate strategy
        strategy = strategy_agent.generate_strategy(context)
        
        # Broadcast to websocket clients
        await broadcast_event("strategy_generated", {
            "strategy": strategy,
            "timestamp": datetime.now().isoformat()
        })
        
        return strategy
    except Exception as e:
        logger.error(f"Error generating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/record")
async def record_memory(memory_data: Dict[str, Any]):
    """Record a trade outcome in memory"""
    try:
        success = memory.record(
            strategy_id=memory_data.get("strategy_id", "unknown"),
            outcome=memory_data.get("outcome", 1.0),
            market_conditions=memory_data.get("market_conditions", {}),
            lessons=memory_data.get("lessons", [])
        )
        
        return {"success": success}
    except Exception as e:
        logger.error(f"Error recording memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/similar")
async def get_similar_memories(query: str, limit: int = 5):
    """Get memories similar to the query"""
    try:
        memories = memory.retrieve_similar(query, limit)
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error retrieving similar memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/regime/{regime}")
async def get_regime_memories(regime: str, limit: int = 10):
    """Get memories for a specific market regime"""
    try:
        memories = memory.retrieve_by_regime(regime, limit)
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error retrieving regime memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evolution/performance/{regime}")
async def get_regime_performance(regime: str):
    """Get performance statistics for a specific market regime"""
    try:
        performance = memory.get_regime_performance(regime)
        return performance
    except Exception as e:
        logger.error(f"Error getting regime performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evolution/evolve")
async def evolve_strategy(request: Dict[str, Any]):
    """Evolve strategies for a specific market regime"""
    try:
        regime = request.get("regime")
        if not regime:
            # Get current regime if not specified
            mcp_data = mcp_client.get_current_mcp()
            regime = mcp_client.classify_regime(mcp_data)
        
        result = evolver.evolve_agents(regime)
        
        # Broadcast to websocket clients
        await broadcast_event("evolution_complete", {
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    except Exception as e:
        logger.error(f"Error evolving strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evolution/history")
async def get_evolution_history(limit: int = 10):
    """Get history of evolved strategies"""
    try:
        history = evolver.get_evolution_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting evolution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial data
        await websocket.send_json({
            "event": "connected",
            "data": {
                "message": "Connected to AutoTradeX WebSocket",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "event": "echo",
                "data": json.loads(data)
            })
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_event(event: str, data: Dict[str, Any]):
    """Broadcast event to all connected WebSocket clients"""
    message = {
        "event": event,
        "data": data
    }
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")

async def start_app(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Start the FastAPI app with Uvicorn"""
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="debug" if debug else "info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
