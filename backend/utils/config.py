"""
Configuration utilities for AutoTradeX
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    "api": {
        "host": "127.0.0.1",
        "port": 8000,
        "debug": False
    },
    "trading": {
        "max_position_size": float(os.getenv("MAX_POSITION_SIZE", 0.1)),
        "risk_factor": float(os.getenv("RISK_FACTOR", 0.03)),
        "default_symbol": "bitcoin"
    },
    "groq": {
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama3-70b-8192")
    },
    "qdrant": {
        "url": os.getenv("QDRANT_URL", ""),
        "api_key": os.getenv("QDRANT_API_KEY", ""),
        "collection_name": "autotradex_memory"
    },
    "coingecko": {
        "api_key": os.getenv("COINGECKO_API_KEY", ""),
        "mcp_base_url": os.getenv("MCP_BASE_URL", "https://api.coingecko.com/mcp")
    },
    "evolution": {
        "cycle_days": 7,
        "min_trades_for_evolution": 50,
        "improvement_threshold": 0.03
    }
}

def get_config_path() -> Path:
    """Get the path to the config file"""
    config_dir = Path.home() / ".autotradex"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from file or create default"""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            # If loading fails, return default config
            return DEFAULT_CONFIG
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file"""
    config_path = get_config_path()
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

def get_config_value(key_path: str, default: Optional[Any] = None) -> Any:
    """
    Get a configuration value using dot notation
    Example: get_config_value("trading.max_position_size")
    """
    config = load_config()
    keys = key_path.split(".")
    
    value = config
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def update_config_value(key_path: str, value: Any) -> None:
    """
    Update a configuration value using dot notation
    Example: update_config_value("trading.max_position_size", 0.2)
    """
    config = load_config()
    keys = key_path.split(".")
    
    # Navigate to the correct nested dictionary
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Update the value
    current[keys[-1]] = value
    
    # Save the updated config
    save_config(config)
