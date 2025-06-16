#!/usr/bin/env python3
"""
GigNova: Utility Helper Functions
"""

import json
import uuid
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def serialize_datetime(obj: Any) -> Any:
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def safe_json_dumps(data: Any) -> str:
    """Safely convert data to JSON string"""
    try:
        return json.dumps(data, default=serialize_datetime)
    except Exception as e:
        logger.error(f"JSON serialization failed: {e}")
        return "{}"


def safe_json_loads(json_str: str) -> Dict:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return {}


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import numpy as np
    
    if not vec1 or not vec2:
        return 0.0
        
    try:
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        return 0.0


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"
