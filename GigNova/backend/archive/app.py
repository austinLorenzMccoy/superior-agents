#!/usr/bin/env python3
"""
GigNova: Main Application
"""

import logging
import schedule
import time
import threading
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gignova.api.routes import router, orchestrator
from gignova.config.settings import Settings

# Configure logging
logger = logging.getLogger(__name__)

# Background tasks
def run_scheduled_tasks():
    """Run scheduled tasks in background"""
    while True:
        schedule.run_pending()
        time.sleep(1)

# Use asynccontextmanager for lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting GigNova API")
    
    # Log development mode status
    if Settings.DEV_MODE:
        logger.info("Running in DEVELOPMENT MODE with local service implementations")
        logger.info("- Using in-memory vector database instead of Qdrant")
        logger.info("- Using local file storage instead of IPFS")
        logger.info("- Using local blockchain implementation")
    
    # Schedule agent evolution weekly
    schedule.every().monday.at("00:00").do(orchestrator.evolve_agents)
    
    # Start background task thread
    background_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    background_thread.start()
    
    logger.info("GigNova API started successfully")
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown
    logger.info("Shutting down GigNova API")

# Create FastAPI app
app = FastAPI(
    title=Settings.API_TITLE,
    description=Settings.API_DESCRIPTION,
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
    return {"status": "online", "message": "GigNova API is running in development mode"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Include API routes
app.include_router(router)




def run_app():
    """Run the application"""
    import os
    port = int(os.environ.get("PORT", 8888))
    uvicorn.run(
        "gignova.app:app",
        host="0.0.0.0",
        port=port,
        reload=Settings.DEBUG
    )


if __name__ == "__main__":
    run_app()
