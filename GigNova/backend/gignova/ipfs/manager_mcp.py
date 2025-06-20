#!/usr/bin/env python3
"""
GigNova: Storage Manager (MCP Implementation)
Replaces the local file storage with MCP storage server integration
"""

import os
import logging
from typing import Dict, Any, Optional

from gignova.mcp.client import mcp_manager

# Configure logging
logger = logging.getLogger(__name__)


class IPFSManager:
    def __init__(self):
        """Initialize storage manager with MCP integration"""
        logger.info("Initialized storage manager with MCP integration")
    
    async def store_deliverable(self, data: bytes) -> str:
        """Store deliverable via MCP storage server and return its hash"""
        try:
            # Store via MCP
            result = await mcp_manager.storage_store_file(
                file_data=data,
                metadata={
                    "type": "deliverable",
                    "content_type": "application/octet-stream"
                }
            )
            
            if not result.get("success"):
                logger.error(f"Failed to store file via MCP: {result.get('error')}")
                raise Exception(f"MCP storage failed: {result.get('error')}")
            
            file_hash = result.get("file_hash")
            logger.info(f"Stored deliverable via MCP with hash: {file_hash}")
            
            # Log to analytics
            await mcp_manager.analytics_log_event(
                event_type="file_stored",
                event_data={
                    "file_hash": file_hash,
                    "file_size": len(data),
                    "storage_type": "mcp"
                }
            )
            
            return file_hash
            
        except Exception as e:
            logger.error(f"MCP file storage failed: {e}")
            raise
    
    async def retrieve_deliverable(self, file_hash: str) -> bytes:
        """Retrieve deliverable from MCP storage server"""
        try:
            # Retrieve via MCP
            result = await mcp_manager.storage_get_file(file_hash)
            
            if not result.get("success"):
                logger.error(f"Failed to retrieve file via MCP: {result.get('error')}")
                return b""
            
            file_data = result.get("file_data", b"")
            logger.info(f"Retrieved file with hash: {file_hash} via MCP")
            
            # Log to analytics
            await mcp_manager.analytics_log_event(
                event_type="file_retrieved",
                event_data={
                    "file_hash": file_hash,
                    "file_size": len(file_data),
                    "storage_type": "mcp"
                }
            )
            
            return file_data
        
        except Exception as e:
            logger.error(f"MCP file retrieval failed: {e}")
            return b""
