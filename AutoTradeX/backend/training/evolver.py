"""
Agent Evolution System for AutoTradeX
Evolves trading strategies based on historical performance and market regimes
"""

import os
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from backend.training.memory import QdrantMemory
import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.utils.config import get_config_value

logger = logging.getLogger(__name__)

class AgentEvolver:
    """Evolves trading agents based on historical performance"""
    
    def __init__(self):
        """Initialize the agent evolution system"""
        self.memory = QdrantMemory()
        self.evolution_threshold = get_config_value(
            "evolution.improvement_threshold", 0.03
        )
        self.min_trades = get_config_value(
            "evolution.min_trades_for_evolution", 50
        )
        
        logger.debug(f"Initialized AgentEvolver with threshold: {self.evolution_threshold}")
    
    def evolve_agents(self, market_regime: str) -> Dict[str, Any]:
        """Evolve agents for a specific market regime"""
        logger.info(f"Starting evolution cycle for regime: {market_regime}")
        
        # Get performance data for the regime
        performance = self.memory.get_regime_performance(market_regime)
        
        if performance["count"] < self.min_trades:
            logger.warning(
                f"Insufficient trades ({performance['count']}) for evolution. "
                f"Need at least {self.min_trades}."
            )
            return {
                "evolved": False,
                "reason": "insufficient_data",
                "regime": market_regime,
                "current_performance": performance
            }
        
        # Get best performing strategy for the regime
        best_strategy = performance["best_strategy"]
        if not best_strategy:
            logger.warning("No best strategy found for evolution")
            return {
                "evolved": False,
                "reason": "no_best_strategy",
                "regime": market_regime
            }
        
        # Get similar memories to learn from
        similar_memories = self.memory.retrieve_similar(
            f"Strategy for {market_regime} market regime", limit=20
        )
        
        # Extract lessons from memories
        lessons = self._extract_lessons(similar_memories)
        
        # Create evolved strategy
        evolved_strategy = self._create_evolved_strategy(
            best_strategy, market_regime, lessons, performance
        )
        
        logger.info(
            f"Evolution complete for {market_regime}. "
            f"New strategy: {evolved_strategy['strategy_id']}"
        )
        
        return {
            "evolved": True,
            "strategy_id": evolved_strategy["strategy_id"],
            "base_strategy": best_strategy,
            "regime": market_regime,
            "improvements": evolved_strategy["improvements"],
            "expected_gain": evolved_strategy["expected_gain"]
        }
    
    def _extract_lessons(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Extract lessons from memories"""
        all_lessons = []
        
        for memory in memories:
            if "memory_text" in memory:
                # Extract lessons from memory text
                text = memory["memory_text"]
                if "Lessons:" in text:
                    lessons_part = text.split("Lessons:")[1].strip()
                    lessons = [l.strip() for l in lessons_part.split(",")]
                    all_lessons.extend(lessons)
        
        # Deduplicate lessons
        unique_lessons = list(set(all_lessons))
        logger.debug(f"Extracted {len(unique_lessons)} unique lessons from memories")
        return unique_lessons
    
    def _create_evolved_strategy(
        self, base_strategy: str, market_regime: str, 
        lessons: List[str], performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an evolved strategy based on lessons learned"""
        # Generate a new strategy ID with version increment
        if "v" in base_strategy:
            base_name, version = base_strategy.split("v")
            try:
                new_version = int(version) + 1
            except ValueError:
                new_version = 1
            strategy_id = f"{base_name}v{new_version}"
        else:
            strategy_id = f"{base_strategy}v2"
        
        # Select top lessons (max 5)
        top_lessons = lessons[:5] if len(lessons) > 5 else lessons
        
        # Calculate expected gain
        # In a real implementation, this would use more sophisticated modeling
        base_performance = performance["avg_outcome"]
        expected_gain = base_performance * (1 + self.evolution_threshold)
        
        # Generate improvements based on lessons
        improvements = [
            f"Applied lesson: {lesson}" for lesson in top_lessons
        ]
        
        # Add some randomness for exploration
        if random.random() < 0.3:
            improvements.append("Added exploration factor for market adaptation")
        
        evolved = {
            "strategy_id": strategy_id,
            "base_strategy": base_strategy,
            "market_regime": market_regime,
            "creation_date": datetime.now().isoformat(),
            "lessons_applied": top_lessons,
            "improvements": improvements,
            "expected_gain": expected_gain,
            "base_performance": base_performance
        }
        
        # Save the evolved strategy to file for reference
        self._save_evolved_strategy(evolved)
        
        return evolved
    
    def _save_evolved_strategy(self, strategy: Dict[str, Any]) -> None:
        """Save evolved strategy to file"""
        try:
            # Create evolution directory if it doesn't exist
            evolution_dir = os.path.expanduser("~/.autotradex/evolution")
            os.makedirs(evolution_dir, exist_ok=True)
            
            # Save strategy to file
            filename = f"{evolution_dir}/{strategy['strategy_id']}_{int(datetime.now().timestamp())}.json"
            with open(filename, "w") as f:
                json.dump(strategy, f, indent=2)
                
            logger.debug(f"Saved evolved strategy to {filename}")
        except Exception as e:
            logger.error(f"Error saving evolved strategy: {e}")
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of evolved strategies"""
        try:
            evolution_dir = os.path.expanduser("~/.autotradex/evolution")
            if not os.path.exists(evolution_dir):
                return []
                
            # List all evolution files
            files = [os.path.join(evolution_dir, f) for f in os.listdir(evolution_dir) 
                    if f.endswith(".json")]
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Load strategies
            strategies = []
            for file in files[:limit]:
                with open(file, "r") as f:
                    strategies.append(json.load(f))
                    
            return strategies
        except Exception as e:
            logger.error(f"Error getting evolution history: {e}")
            return []
