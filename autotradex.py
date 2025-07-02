#!/usr/bin/env python3
"""
AutoTradeX: Self-Evolving Crypto Trading Agents
Main execution script with Groq integration
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid

# Core dependencies
import numpy as np
import pandas as pd
from groq import Groq
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import websockets
import asyncio
from fastapi import FastAPI, WebSocket
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradeOutcome:
    """Store trade outcome with context for learning"""
    strategy_id: str
    symbol: str
    entry_price: float
    exit_price: float
    roi: float
    market_conditions: Dict
    timestamp: str
    lessons_learned: List[str]
    agent_reasoning: str

@dataclass
class MarketData:
    """Current market data structure"""
    symbol: str
    price: float
    volume: float
    volatility: float
    rsi: float
    moving_avg_20: float
    sentiment_score: float
    timestamp: str

class GroqAgent:
    """Base AI agent using Groq for strategy generation"""
    
    def __init__(self, agent_type: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.agent_type = agent_type
        self.model = model
        self.memory = []
        
    def generate_strategy(self, market_data: MarketData, memory_context: List[Dict]) -> Dict:
        """Generate trading strategy using Groq"""
        
        # Create context from memory
        memory_summary = self._summarize_memory(memory_context)
        
        prompt = f"""
        You are an expert {self.agent_type} trading agent. Analyze the current market data and generate a trading strategy.
        
        Current Market Data:
        - Symbol: {market_data.symbol}
        - Price: ${market_data.price}
        - Volume: {market_data.volume}
        - Volatility: {market_data.volatility}
        - RSI: {market_data.rsi}
        - 20-day MA: ${market_data.moving_avg_20}
        - Sentiment Score: {market_data.sentiment_score} (-1 to 1)
        
        Previous Learning:
        {memory_summary}
        
        Generate a trading decision with:
        1. Action: BUY, SELL, or HOLD
        2. Confidence: 0-1 scale
        3. Position Size: percentage of portfolio (0-100%)
        4. Stop Loss: percentage below entry
        5. Take Profit: percentage above entry
        6. Reasoning: Why this decision
        
        Respond in JSON format only.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse JSON response
            strategy_text = response.choices[0].message.content
            # Clean potential markdown formatting
            if "```json" in strategy_text:
                strategy_text = strategy_text.split("```json")[1].split("```")[0]
            elif "```" in strategy_text:
                strategy_text = strategy_text.split("```")[1]
                
            strategy = json.loads(strategy_text.strip())
            strategy['agent_type'] = self.agent_type
            strategy['timestamp'] = datetime.now().isoformat()
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.1,
                "position_size": 0,
                "reasoning": f"Error in strategy generation: {str(e)}",
                "agent_type": self.agent_type
            }
    
    def _summarize_memory(self, memory_context: List[Dict]) -> str:
        """Summarize relevant memory for context"""
        if not memory_context:
            return "No previous trading history available."
        
        # Get recent outcomes
        recent = memory_context[-5:] if len(memory_context) > 5 else memory_context
        
        summary = "Recent Trading Lessons:\n"
        for i, outcome in enumerate(recent, 1):
            roi = outcome.get('roi', 0)
            lessons = outcome.get('lessons_learned', [])
            summary += f"{i}. ROI: {roi:.2%}, Lessons: {', '.join(lessons[:2])}\n"
        
        return summary

class QdrantMemory:
    """Vector memory storage using Qdrant"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "autotradex_memory"
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            if not any(col.name == self.collection_name for col in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant: {e}")
    
    def store_outcome(self, outcome: TradeOutcome):
        """Store trade outcome in vector memory"""
        try:
            # Create embedding from outcome data
            text_data = f"Strategy: {outcome.strategy_id}, ROI: {outcome.roi:.2%}, Conditions: {outcome.market_conditions}, Lessons: {outcome.lessons_learned}"
            
            # Simple embedding (in production, use proper embedding model)
            vector = self._create_simple_embedding(text_data)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=asdict(outcome)
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored outcome: {outcome.strategy_id} with ROI {outcome.roi:.2%}")
            
        except Exception as e:
            logger.error(f"Error storing outcome: {e}")
    
    def retrieve_similar_outcomes(self, market_conditions: Dict, limit: int = 10) -> List[Dict]:
        """Retrieve similar trading outcomes"""
        try:
            # Create query vector from current conditions
            query_text = f"Market conditions: {market_conditions}"
            query_vector = self._create_simple_embedding(query_text)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            return [result.payload for result in results]
            
        except Exception as e:
            logger.error(f"Error retrieving outcomes: {e}")
            return []
    
    def _create_simple_embedding(self, text: str, size: int = 384) -> List[float]:
        """Create simple hash-based embedding (replace with proper model in production)"""
        # Simple hash-based embedding for demo
        hash_val = hash(text)
        np.random.seed(abs(hash_val) % (2**32))
        return np.random.normal(0, 1, size).tolist()

class MarketDataProvider:
    """Fetch real-time market data from CoinGecko"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
    
    def get_market_data(self, symbol: str = "bitcoin") -> MarketData:
        """Fetch current market data"""
        try:
            # Get price data
            price_url = f"{self.base_url}/simple/price"
            price_params = {
                "ids": symbol,
                "vs_currencies": "usd",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            price_response = self.session.get(price_url, params=price_params)
            price_data = price_response.json()
            
            # Get historical data for technical indicators
            history_url = f"{self.base_url}/coins/{symbol}/market_chart"
            history_params = {
                "vs_currency": "usd",
                "days": "30",
                "interval": "daily"
            }
            
            history_response = self.session.get(history_url, params=history_params)
            history_data = history_response.json()
            
            # Calculate technical indicators
            prices = [point[1] for point in history_data["prices"]]
            volumes = [point[1] for point in history_data["total_volumes"]]
            
            current_price = price_data[symbol]["usd"]
            volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) if len(prices) >= 20 else 0.1
            rsi = self._calculate_rsi(prices)
            moving_avg_20 = np.mean(prices[-20:]) if len(prices) >= 20 else current_price
            
            # Simple sentiment score based on 24h change
            change_24h = price_data[symbol].get("usd_24h_change", 0)
            sentiment_score = max(-1, min(1, change_24h / 10))  # Normalize to -1 to 1
            
            return MarketData(
                symbol=symbol,
                price=current_price,
                volume=volumes[-1] if volumes else 0,
                volatility=volatility,
                rsi=rsi,
                moving_avg_20=moving_avg_20,
                sentiment_score=sentiment_score,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            # Return dummy data as fallback
            return MarketData(
                symbol=symbol,
                price=50000.0,
                volume=1000000,
                volatility=0.2,
                rsi=50.0,
                moving_avg_20=49000.0,
                sentiment_score=0.0,
                timestamp=datetime.now().isoformat()
            )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas[-period:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-period:]]
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class AutoTradeXSystem:
    """Main AutoTradeX orchestration system"""
    
    def __init__(self):
        self.agents = {
            "strategy": GroqAgent("strategy"),
            "risk": GroqAgent("risk_management"),
            "sentiment": GroqAgent("sentiment_analysis")
        }
        self.memory = QdrantMemory()
        self.market_data_provider = MarketDataProvider()
        self.portfolio_value = 100000.0  # Starting with $100k simulation
        self.positions = {}
        self.trade_history = []
        self.evolution_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_roi": 0.0,
            "weekly_improvement": []
        }
    
    async def run_trading_cycle(self, symbol: str = "bitcoin"):
        """Execute one complete trading cycle"""
        logger.info(f"Starting trading cycle for {symbol}")
        
        # 1. Fetch market data
        market_data = self.market_data_provider.get_market_data(symbol)
        logger.info(f"Market data: {symbol} @ ${market_data.price}")
        
        # 2. Get relevant memory
        memory_context = self.memory.retrieve_similar_outcomes(
            {"volatility": market_data.volatility, "rsi": market_data.rsi}
        )
        
        # 3. Generate strategies from multiple agents
        strategies = {}
        for agent_name, agent in self.agents.items():
            strategy = agent.generate_strategy(market_data, memory_context)
            strategies[agent_name] = strategy
            logger.info(f"{agent_name} agent decision: {strategy.get('action', 'HOLD')}")
        
        # 4. Combine strategies (simple voting mechanism)
        final_decision = self._combine_strategies(strategies)
        
        # 5. Execute trade (simulation)
        trade_outcome = self._execute_trade(final_decision, market_data)
        
        # 6. Store outcome in memory
        if trade_outcome:
            self.memory.store_outcome(trade_outcome)
            self._update_evolution_stats(trade_outcome)
        
        return {
            "market_data": asdict(market_data),
            "strategies": strategies,
            "final_decision": final_decision,
            "trade_outcome": asdict(trade_outcome) if trade_outcome else None,
            "portfolio_value": self.portfolio_value
        }
    
    def _combine_strategies(self, strategies: Dict) -> Dict:
        """Combine multiple agent strategies using weighted voting"""
        actions = [s.get("action", "HOLD") for s in strategies.values()]
        confidences = [s.get("confidence", 0.1) for s in strategies.values()]
        
        # Weight votes by confidence
        action_weights = {"BUY": 0, "SELL": 0, "HOLD": 0}
        
        for action, confidence in zip(actions, confidences):
            action_weights[action] += confidence
        
        # Choose action with highest weighted vote
        final_action = max(action_weights, key=action_weights.get)
        
        # Average other parameters
        avg_confidence = np.mean(confidences)
        avg_position_size = np.mean([s.get("position_size", 0) for s in strategies.values()])
        
        return {
            "action": final_action,
            "confidence": avg_confidence,
            "position_size": min(avg_position_size, 10),  # Cap at 10% for safety
            "reasoning": f"Combined decision from {len(strategies)} agents",
            "vote_weights": action_weights
        }
    
    def _execute_trade(self, decision: Dict, market_data: MarketData) -> Optional[TradeOutcome]:
        """Execute trade in simulation"""
        if decision["action"] == "HOLD":
            return None
        
        symbol = market_data.symbol
        current_price = market_data.price
        position_size = decision["position_size"] / 100.0  # Convert percentage
        
        # Simulate trade execution
        if decision["action"] == "BUY":
            trade_amount = self.portfolio_value * position_size
            shares = trade_amount / current_price
            
            # Store position
            self.positions[symbol] = {
                "shares": shares,
                "entry_price": current_price,
                "entry_time": datetime.now()
            }
            
            logger.info(f"BUY: {shares:.6f} {symbol} at ${current_price}")
            
        elif decision["action"] == "SELL" and symbol in self.positions:
            position = self.positions[symbol]
            exit_price = current_price
            roi = (exit_price - position["entry_price"]) / position["entry_price"]
            
            # Update portfolio
            trade_value = position["shares"] * exit_price
            self.portfolio_value += (trade_value - (position["shares"] * position["entry_price"]))
            
            # Create outcome record
            outcome = TradeOutcome(
                strategy_id=f"combined_{datetime.now().strftime('%Y%m%d_%H%M')}",
                symbol=symbol,
                entry_price=position["entry_price"],
                exit_price=exit_price,
                roi=roi,
                market_conditions={
                    "volatility": market_data.volatility,
                    "rsi": market_data.rsi,
                    "sentiment": market_data.sentiment_score
                },
                timestamp=datetime.now().isoformat(),
                lessons_learned=self._extract_lessons(roi, market_data),
                agent_reasoning=decision["reasoning"]
            )
            
            # Remove position
            del self.positions[symbol]
            
            logger.info(f"SELL: {symbol} ROI: {roi:.2%}, Portfolio: ${self.portfolio_value:.2f}")
            
            return outcome
        
        return None
    
    def _extract_lessons(self, roi: float, market_data: MarketData) -> List[str]:
        """Extract lessons from trade outcome"""
        lessons = []
        
        if roi > 0.05:  # Profitable trade
            if market_data.rsi < 30:
                lessons.append("RSI oversold conditions often present buying opportunities")
            if market_data.volatility < 0.2:
                lessons.append("Low volatility periods can be good for position building")
        elif roi < -0.03:  # Loss
            if market_data.rsi > 70:
                lessons.append("Avoid buying when RSI is overbought")
            if market_data.volatility > 0.5:
                lessons.append("High volatility increases risk - reduce position sizes")
        
        return lessons
    
    def _update_evolution_stats(self, outcome: TradeOutcome):
        """Update evolution statistics"""
        self.evolution_stats["total_trades"] += 1
        self.evolution_stats["total_roi"] += outcome.roi
        
        if outcome.roi > 0:
            self.evolution_stats["winning_trades"] += 1
        
        # Weekly improvement tracking (simplified)
        current_week = datetime.now().isocalendar()[1]
        if not self.evolution_stats["weekly_improvement"] or \
           self.evolution_stats["weekly_improvement"][-1]["week"] != current_week:
            
            avg_roi = self.evolution_stats["total_roi"] / max(1, self.evolution_stats["total_trades"])
            self.evolution_stats["weekly_improvement"].append({
                "week": current_week,
                "avg_roi": avg_roi,
                "total_trades": self.evolution_stats["total_trades"]
            })
    
    def get_evolution_metrics(self) -> Dict:
        """Get current evolution metrics"""
        total_trades = self.evolution_stats["total_trades"]
        if total_trades == 0:
            return {"message": "No trades executed yet"}
        
        win_rate = self.evolution_stats["winning_trades"] / total_trades
        avg_roi = self.evolution_stats["total_roi"] / total_trades
        
        return {
            "total_trades": total_trades,
            "win_rate": f"{win_rate:.1%}",
            "average_roi": f"{avg_roi:.2%}",
            "portfolio_value": f"${self.portfolio_value:.2f}",
            "weekly_improvement": self.evolution_stats["weekly_improvement"],
            "current_positions": len(self.positions)
        }

# FastAPI Web Interface
app = FastAPI(title="AutoTradeX", description="Self-Evolving Crypto Trading Agents")
trading_system = None

@app.on_event("startup")
async def startup_event():
    global trading_system
    trading_system = AutoTradeXSystem()
    logger.info("AutoTradeX system initialized")

@app.get("/")
async def root():
    return {"message": "AutoTradeX: Self-Evolving Crypto Trading Agents", "status": "running"}

@app.post("/trade/{symbol}")
async def execute_trade(symbol: str):
    """Execute a trading cycle for given symbol"""
    if not trading_system:
        return {"error": "Trading system not initialized"}
    
    result = await trading_system.run_trading_cycle(symbol)
    return result

@app.get("/metrics")
async def get_metrics():
    """Get evolution metrics"""
    if not trading_system:
        return {"error": "Trading system not initialized"}
    
    return trading_system.get_evolution_metrics()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic updates
            if trading_system:
                metrics = trading_system.get_evolution_metrics()
                await websocket.send_json({"type": "metrics", "data": metrics})
            
            await asyncio.sleep(30)  # Update every 30 seconds
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

async def main():
    """Main execution function"""
    logger.info("Starting AutoTradeX system...")
    
    # Initialize system
    system = AutoTradeXSystem()
    
    # Run a few trading cycles for demonstration
    symbols = ["bitcoin", "ethereum", "cardano"]
    
    for i in range(3):  # Run 3 cycles
        logger.info(f"\n--- Trading Cycle {i+1} ---")
        
        for symbol in symbols:
            try:
                result = await system.run_trading_cycle(symbol)
                logger.info(f"Cycle completed for {symbol}")
                await asyncio.sleep(2)  # Small delay between trades
                
            except Exception as e:
                logger.error(f"Error in trading cycle for {symbol}: {e}")
        
        # Show metrics after each round
        metrics = system.get_evolution_metrics()
        logger.info(f"Current metrics: {metrics}")
        
        await asyncio.sleep(10)  # Wait between cycles
    
    logger.info("Demo completed. Starting web server...")
    
    # Start web server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("AutoTradeX stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")