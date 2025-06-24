#!/usr/bin/env python3
"""
Service Factory for GigNova
Provides a factory for creating service instances based on environment
"""

import logging
import os
from typing import Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceFactory:
    """
    Factory for creating service instances based on environment
    """
    
    @staticmethod
    def get_storage_manager(use_local: bool = None) -> Any:
        """
        Get the appropriate storage manager based on environment
        
        Args:
            use_local: Force use of local implementation (overrides environment)
            
        Returns:
            StorageManager instance
        """
        # Determine if we should use local implementation
        if use_local is None:
            use_local = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")
        
        if use_local:
            try:
                from gignova.storage.local_manager import local_storage_manager
                logger.info("Using local storage manager")
                return local_storage_manager
            except ImportError:
                logger.warning("Local storage manager not available, falling back to IPFS")
        
        try:
            from gignova.storage.manager import storage_manager
            logger.info("Using IPFS storage manager")
            return storage_manager
        except ImportError:
            logger.error("IPFS storage manager not available")
            raise ImportError("No storage manager available")
    
    @staticmethod
    def get_vector_manager(use_local: bool = None) -> Any:
        """
        Get the vector database manager
        
        Args:
            use_local: Force use of local implementation (overrides environment)
            
        Returns:
            VectorManager instance
        """
        # Determine if we should use local implementation
        if use_local is None:
            use_local = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")
        
        if use_local:
            try:
                from gignova.database.local_vector_manager import local_vector_manager
                logger.info("Using local vector manager")
                return local_vector_manager
            except ImportError:
                logger.warning("Local vector manager not available, falling back to ChromaDB")
        
        try:
            from gignova.database.vector_manager import vector_manager
            logger.info("Using ChromaDB vector manager")
            return vector_manager
        except ImportError:
            logger.error("Vector manager not available")
            raise ImportError("No vector manager available")
    
    @staticmethod
    def get_blockchain_manager(use_local: bool = None) -> Any:
        """
        Get the appropriate blockchain manager based on environment
        
        Args:
            use_local: Force use of local implementation (overrides environment)
            
        Returns:
            BlockchainManager instance
        """
        # Determine if we should use local implementation
        if use_local is None:
            use_local = os.environ.get("DEV_MODE", "true").lower() in ("true", "1", "yes")
        
        if use_local:
            try:
                from gignova.blockchain.local_manager import local_blockchain_manager
                logger.info("Using local blockchain manager")
                return local_blockchain_manager
            except ImportError:
                logger.warning("Local blockchain manager not available, falling back to Ethereum")
        
        try:
            from gignova.blockchain.manager import blockchain_manager
            logger.info("Using Ethereum blockchain manager")
            return blockchain_manager
        except ImportError:
            logger.error("Ethereum blockchain manager not available")
            raise ImportError("No blockchain manager available")

# Create a singleton instance
service_factory = ServiceFactory()
