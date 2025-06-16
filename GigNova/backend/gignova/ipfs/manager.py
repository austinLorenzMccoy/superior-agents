#!/usr/bin/env python3
"""
GigNova: Local File Storage Manager (IPFS Alternative)
"""

import os
import json
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


class IPFSManager:
    def __init__(self):
        # Create a local storage directory for files
        self.storage_dir = Path(os.path.expanduser('~')) / '.gignova' / 'storage'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using local file storage at {self.storage_dir}")
    
    def store_deliverable(self, data: bytes) -> str:
        """Store deliverable in local storage and return its hash"""
        try:
            # Generate a hash of the file content
            file_hash = hashlib.sha256(data).hexdigest()
            
            # Save the data to our storage directory with the hash as filename
            target_path = self.storage_dir / file_hash
            with open(target_path, 'wb') as f:
                f.write(data)
            
            logger.info(f"Stored deliverable locally with hash: {file_hash}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Local file storage failed: {e}")
            raise
    
    def retrieve_deliverable(self, file_hash: str) -> bytes:
        """Retrieve deliverable from local storage"""
        try:
            # Get the path to the stored file
            target_path = self.storage_dir / file_hash
            
            # Check if the file exists
            if target_path.exists():
                with open(target_path, 'rb') as f:
                    return f.read()
            else:
                logger.error(f"Deliverable not found in local storage: {file_hash}")
                return b""
        
        except Exception as e:
            logger.error(f"Local file retrieval failed: {e}")
            return b""
