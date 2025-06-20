#!/usr/bin/env python3
"""
GigNova: MCP Client Manager
Handles connections to various MCP servers for the GigNova platform
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from mcp.client.session import ClientSession as Client

# Configure logging
logger = logging.getLogger(__name__)

class MCPClientManager:
    """
    Manages connections to MCP servers and provides a unified interface
    for interacting with them.
    """
    
    def __init__(self):
        """Initialize MCP client connections."""
        self.clients = {}
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize connections to all required MCP servers."""
        try:
            # Define MCP servers
            mcp_servers = {
                "vector": os.getenv("VECTOR_MCP_SERVER", "gignova-vector-mcp-server"),
                "blockchain": os.getenv("BLOCKCHAIN_MCP_SERVER", "gignova-blockchain-mcp-server"),
                "storage": os.getenv("STORAGE_MCP_SERVER", "gignova-storage-mcp-server"),
                "analytics": os.getenv("ANALYTICS_MCP_SERVER", "gignova-analytics-mcp-server"),
                "social": os.getenv("SOCIAL_MCP_SERVER", "gignova-social-mcp-server")
            }
            
            # Create clients for each server
            for server_type, server_name in mcp_servers.items():
                try:
                    self.clients[server_type] = Client(server_name)
                    logger.info(f"Connected to {server_type} MCP server: {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to connect to {server_type} MCP server: {e}")
                    self.clients[server_type] = None
                    
        except Exception as e:
            logger.error(f"Error initializing MCP clients: {e}")
    
    async def vector_store_embedding(self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Store a vector embedding with metadata."""
        try:
            if not self.clients.get("vector"):
                logger.error("Vector MCP server not available")
                return {"success": False, "error": "Vector MCP server not available"}
                
            result = await self.clients["vector"].call_tool("store_embedding", {
                "id": id,
                "vector": vector,
                "metadata": metadata or {}
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return {"success": False, "error": str(e)}
    
    async def vector_similarity_search(self, query_vector: List[float], threshold: float = 0.8, 
                                      limit: int = 10, filter_params: Optional[Dict[str, Any]] = None) -> Dict:
        """Find similar vectors using cosine similarity."""
        try:
            if not self.clients.get("vector"):
                logger.error("Vector MCP server not available")
                return {"success": False, "error": "Vector MCP server not available"}
                
            result = await self.clients["vector"].call_tool("similarity_search", {
                "query_vector": query_vector,
                "threshold": threshold,
                "limit": limit,
                "filter_params": filter_params or {}
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return {"success": False, "error": str(e)}
    
    async def blockchain_deploy_contract(self, contract_type: str, client_address: str, 
                                        freelancer_address: str, amount: float, 
                                        milestones: Optional[List[Dict[str, Any]]] = None) -> Dict:
        """Deploy a smart contract to the blockchain."""
        try:
            if not self.clients.get("blockchain"):
                logger.error("Blockchain MCP server not available")
                return {"success": False, "error": "Blockchain MCP server not available"}
                
            result = await self.clients["blockchain"].call_tool("deploy_contract", {
                "contract_type": contract_type,
                "client_address": client_address,
                "freelancer_address": freelancer_address,
                "amount": amount,
                "milestones": milestones or []
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            return {"success": False, "error": str(e)}
    
    async def blockchain_release_payment(self, contract_address: str, escrow_id: str) -> Dict:
        """Release payment from escrow contract."""
        try:
            if not self.clients.get("blockchain"):
                logger.error("Blockchain MCP server not available")
                return {"success": False, "error": "Blockchain MCP server not available"}
                
            result = await self.clients["blockchain"].call_tool("release_payment", {
                "contract_address": contract_address,
                "escrow_id": escrow_id
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error releasing payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def storage_store_file(self, file_data: bytes, metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Store a file in IPFS or other storage."""
        try:
            if not self.clients.get("storage"):
                logger.error("Storage MCP server not available")
                return {"success": False, "error": "Storage MCP server not available"}
                
            # Convert bytes to base64 for JSON serialization
            import base64
            encoded_data = base64.b64encode(file_data).decode('utf-8')
                
            result = await self.clients["storage"].call_tool("store_file", {
                "file_data_base64": encoded_data,
                "metadata": metadata or {}
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error storing file: {e}")
            return {"success": False, "error": str(e)}
    
    async def storage_get_file(self, file_hash: str) -> Dict:
        """Retrieve a file from storage."""
        try:
            if not self.clients.get("storage"):
                logger.error("Storage MCP server not available")
                return {"success": False, "error": "Storage MCP server not available"}
                
            result = await self.clients["storage"].call_tool("get_file", {
                "hash": file_hash
            })
            
            response = json.loads(result)
            
            # Convert base64 back to bytes if successful
            if response.get("success") and "file_data_base64" in response:
                import base64
                response["file_data"] = base64.b64decode(response["file_data_base64"])
                del response["file_data_base64"]
                
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            return {"success": False, "error": str(e)}
    
    async def analytics_log_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict:
        """Log an event to analytics."""
        try:
            if not self.clients.get("analytics"):
                logger.error("Analytics MCP server not available")
                return {"success": False, "error": "Analytics MCP server not available"}
                
            result = await self.clients["analytics"].call_tool("log_event", {
                "event_type": event_type,
                "event_data": event_data
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return {"success": False, "error": str(e)}
    
    async def analytics_get_metrics(self, metric_type: str, time_range: str, 
                                   filters: Optional[Dict[str, Any]] = None) -> Dict:
        """Get analytics metrics."""
        try:
            if not self.clients.get("analytics"):
                logger.error("Analytics MCP server not available")
                return {"success": False, "error": "Analytics MCP server not available"}
                
            result = await self.clients["analytics"].call_tool("get_metrics", {
                "metric_type": metric_type,
                "time_range": time_range,
                "filters": filters or {}
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"success": False, "error": str(e)}
    
    async def social_post_update(self, platforms: List[str], message: str, 
                               media_urls: Optional[List[str]] = None) -> Dict:
        """Post an update to social media platforms."""
        try:
            if not self.clients.get("social"):
                logger.error("Social MCP server not available")
                return {"success": False, "error": "Social MCP server not available"}
                
            result = await self.clients["social"].call_tool("post_update", {
                "platforms": platforms,
                "message": message,
                "media_urls": media_urls or []
            })
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error posting social update: {e}")
            return {"success": False, "error": str(e)}

# Global instance
mcp_manager = MCPClientManager()
