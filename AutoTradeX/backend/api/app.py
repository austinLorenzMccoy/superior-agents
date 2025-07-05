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

from backend.mcp.protocol import ModelContextProtocol
from backend.mcp.context import AgentContext
from backend.mcp.memory import VectorMemory
from backend.mcp.orchestrator import AgentOrchestrator
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

# Initialize MCP components
mcp = ModelContextProtocol()
memory = VectorMemory(
    storage_type="qdrant",
    collection_name="autotradex_memories",
    qdrant_url=get_config_value("qdrant.url", None),
    qdrant_api_key=get_config_value("qdrant.api_key", None)
)
# Initialize the orchestrator with default parameters
orchestrator = AgentOrchestrator(use_langgraph=False)

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
        # Create a new context for this request
        context = mcp.create_context()
        
        # Use the orchestrator to get market data
        market_data = await orchestrator.get_market_data(context.id)
        
        # Classify the market regime
        btc_dominance = market_data.get("btc_dominance", 0)
        eth_dominance = market_data.get("eth_dominance", 0)
        
        # Simple classification logic
        if btc_dominance > 52:
            regime = "BTC_DOMINANT"
        elif eth_dominance > 20 and btc_dominance < 45:
            regime = "ALT_SEASON"
        else:
            regime = "NEUTRAL"
            
        return {
            "regime": regime,
            "btc_dominance": btc_dominance,
            "eth_dominance": eth_dominance,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/context")
async def get_market_context():
    """Get comprehensive market context"""
    try:
        # Create a new context for this request
        agent_context = mcp.create_context()
        
        # Use the orchestrator to get market data
        market_data = await orchestrator.get_market_data(agent_context.id)
        
        # Add additional context information
        market_data["timestamp"] = datetime.now().isoformat()
        
        return market_data
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/generate")
async def generate_strategy(request: Dict[str, Any]):
    """Generate a trading strategy"""
    try:
        # Create a new context for this request
        agent_context = mcp.create_context()
        
        # Add request data to context
        for key, value in request.items():
            mcp.update_context_state(agent_context.id, key, value)
        
        # Generate strategy using the orchestrator
        strategy = await orchestrator.generate_strategy(
            context_id=agent_context.id,
            market_regime=request.get("market_regime", "NEUTRAL"),
            portfolio_value=request.get("portfolio_value", 10000),
            risk_profile=request.get("risk_profile", "moderate")
        )
        
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
        memory_id = memory.record_trade_outcome(
            strategy_id=memory_data.get("strategy_id", "unknown"),
            outcome=memory_data.get("outcome", 1.0),
            market_conditions=memory_data.get("market_conditions", {}),
            lessons=memory_data.get("lessons", [])
        )
        
        return {"success": bool(memory_id), "memory_id": memory_id}
    except Exception as e:
        logger.error(f"Error recording memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/similar")
async def get_similar_memories(query: str, limit: int = 5):
    """Get memories similar to the query"""
    try:
        memories = memory.retrieve_similar(query, n_results=limit)
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error retrieving similar memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/regime/{regime}")
async def get_regime_memories(regime: str, limit: int = 10):
    """Get memories for a specific market regime"""
    try:
        # Use filter to get memories for a specific regime
        filter_condition = {"market_conditions.market_regime": regime}
        memories = memory.retrieve_similar("", n_results=limit, filter=filter_condition)
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error retrieving regime memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evolution/performance/{regime}")
async def get_regime_performance(regime: str):
    """Get performance statistics for a specific market regime"""
    try:
        # Use filter to get memories for a specific regime
        filter_condition = {"market_conditions.market_regime": regime}
        memories = memory.retrieve_similar("", n_results=100, filter=filter_condition)
        
        # Calculate performance statistics
        if not memories:
            return {"regime": regime, "avg_outcome": 0, "count": 0}
            
        outcomes = [mem.get("metadata", {}).get("outcome", 1.0) for mem in memories]
        avg_outcome = sum(outcomes) / len(outcomes) if outcomes else 0
        
        return {
            "regime": regime,
            "avg_outcome": avg_outcome,
            "count": len(memories),
            "best_outcome": max(outcomes) if outcomes else 0,
            "worst_outcome": min(outcomes) if outcomes else 0
        }
    except Exception as e:
        logger.error(f"Error getting regime performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evolution/evolve")
async def evolve_strategy(request: Dict[str, Any]):
    """Evolve strategies for a specific market regime"""
    try:
        regime = request.get("regime")
        if not regime:
            # Create a new context for this request
            agent_context = mcp.create_context()
            
            # Use the orchestrator to get market data
            market_data = await orchestrator.get_market_data(agent_context.id)
            
            # Classify the market regime
            btc_dominance = market_data.get("btc_dominance", 0)
            eth_dominance = market_data.get("eth_dominance", 0)
            
            # Simple classification logic
            if btc_dominance > 52:
                regime = "BTC_DOMINANT"
            elif eth_dominance > 20 and btc_dominance < 45:
                regime = "ALT_SEASON"
            else:
                regime = "NEUTRAL"
        
        # Use the orchestrator to evolve strategies
        result = await orchestrator.evolve_strategies(regime)
        
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
        # Use filter to get evolution-related memories
        filter_condition = {"type": "evolution"}
        history = memory.retrieve_similar("", n_results=limit, filter=filter_condition)
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
