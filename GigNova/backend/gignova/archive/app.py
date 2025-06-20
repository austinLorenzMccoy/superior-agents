#!/usr/bin/env python3
"""
GigNova: Main Application
Enhanced with MCP integration
"""

import logging
import schedule
import time
import threading
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gignova.api.routes import router, orchestrator
from gignova.config.settings import Settings
from gignova.mcp.client import mcp_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background tasks
def run_scheduled_tasks():
    """Run scheduled tasks in background"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        pending = schedule.get_jobs()
        for job in pending:
            if job.should_run:
                # For async tasks
                if asyncio.iscoroutinefunction(job.job_func):
                    loop.run_until_complete(job.job_func())
                else:
                    job.run()
                
        schedule.run_pending()
        time.sleep(1)

# Use asynccontextmanager for lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting GigNova API with MCP integration")
    
    try:
        # Initialize MCP connections
        from gignova.api.routes_mcp import get_mcp_status
        mcp_status = await get_mcp_status(None)  # None for user_id since this is a system check
        
        if "error" in mcp_status:
            logger.warning(f"MCP initialization warning: {mcp_status.get('error')}")
            logger.warning("Some MCP services may not be available")
        else:
            logger.info(f"MCP connections initialized: {mcp_status}")
            
            # Log MCP server status
            for server_type, status in mcp_status.items():
                if status:
                    logger.info(f"✅ {server_type} connection successful")
                else:
                    logger.warning(f"⚠️ {server_type} connection failed")
    
    except Exception as e:
        logger.error(f"Error initializing MCP connections: {e}")
        logger.warning("Starting with limited functionality")
    
    # Schedule agent evolution weekly
    schedule.every().monday.at("00:00").do(orchestrator.evolve_agents)
    
    # Also schedule a daily health check for MCP services
    schedule.every().day.at("04:00").do(check_mcp_health)
    
    # Start background task thread
    background_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    background_thread.start()
    
    logger.info("GigNova API started successfully with MCP integration")
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown
    logger.info("Shutting down GigNova API")

async def check_mcp_health():
    """Daily health check for MCP services"""
    try:
        # Get MCP status from router endpoint
        from gignova.api.routes_mcp import get_mcp_status
        mcp_status = await get_mcp_status(None)  # None for user_id since this is a system check
        
        # Log to analytics
        await mcp_manager.analytics_log_event(
            event_type="system_health_check",
            event_data={
                "timestamp": datetime.now().timestamp(),
                "mcp_status": mcp_status
            }
        )
        
        logger.info(f"MCP health check completed: {mcp_status}")
        return mcp_status
    except Exception as e:
        logger.error(f"MCP health check failed: {e}")
        return {"error": str(e)}

# Create FastAPI app
app = FastAPI(
    title=f"{Settings.API_TITLE} with MCP",
    description=f"{Settings.API_DESCRIPTION}\nEnhanced with MCP integration for production-grade services.",
    version=Settings.API_VERSION,
    debug=Settings.DEBUG,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add root health endpoint
@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": "GigNova API is running with MCP integration",
        "mcp_enabled": True
    }

@app.get("/health")
async def health():
    # Check MCP services health
    mcp_health = await check_mcp_health()
    
    return {
        "status": "healthy" if "error" not in mcp_health else "degraded",
        "timestamp": datetime.now().isoformat(),
        "mcp_status": mcp_health
    }

# Include API routes
app.include_router(router)

# Add MCP-specific endpoints
@app.get("/mcp/status")
async def mcp_status():
    """Get status of all MCP connections"""
    return await orchestrator.initialize_mcp_connections()

@app.post("/mcp/refresh")
async def refresh_mcp_connections():
    """Refresh all MCP connections"""
    return await orchestrator.initialize_mcp_connections()

def run_app():
    """Run the application"""
    import os
    port = int(os.environ.get("PORT", 8888))
    uvicorn.run(
        "gignova.app_mcp:app",
        host="0.0.0.0",
        port=port,
        reload=Settings.DEBUG
    )


if __name__ == "__main__":
    run_app()
