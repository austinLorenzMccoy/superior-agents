#!/usr/bin/env python3
"""
GigNova: Configuration Settings
"""

import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Settings:
    """Application settings"""
    
    # API settings
    API_TITLE = "GigNova API"
    API_DESCRIPTION = "Blockchain-powered talent marketplace with autonomous AI agents"
    API_VERSION = "0.1.0"
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
    DEBUG = ENVIRONMENT == "dev"
    DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_key_change_in_production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # LLM API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Blockchain
    WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "http://localhost:8545")
    WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
    
    # Vector Database
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # IPFS
    IPFS_API_URL = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
    
    # Agent Configuration
    AGENT_CONFIG = {
        "confidence_threshold": float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.7")),
        "negotiation_rounds": int(os.getenv("AGENT_NEGOTIATION_ROUNDS", "3")),
        "qa_similarity_threshold": float(os.getenv("AGENT_QA_THRESHOLD", "0.8")),
        "learning_rate": float(os.getenv("AGENT_LEARNING_RATE", "0.05"))
    }
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items() 
            if not key.startswith('_') and not callable(value)
        }


# Validate required environment variables
def validate_env_vars():
    """Validate required environment variables"""
    required_vars = []
    
    # In production, these are required
    if Settings.ENVIRONMENT != "dev":
        required_vars.extend([
            "JWT_SECRET",
            "OPENAI_API_KEY",
            "GROQ_API_KEY",
            "WEB3_PROVIDER_URI",
            "WALLET_PRIVATE_KEY",
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "IPFS_API_URL"
        ])
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        if Settings.ENVIRONMENT != "dev":
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Validate on import
validate_env_vars()
