"""
MCP-aware Strategy Agent
Generates trading strategies based on market cap percentage data
"""

import os
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from autotradex.utils.config import get_config_value

logger = logging.getLogger(__name__)

@dataclass
class MarketContext:
    """Market context data structure"""
    btc_dominance: float
    market_regime: str
    sectors: List[str]
    portfolio_value: float
    risk_profile: str
    recent_trades: str = "No trades"
    portfolio_change: float = 0.0

class MCPStrategyAgent:
    """Agent that generates trading strategies based on MCP data"""
    
    def __init__(self):
        """Initialize the strategy agent with Groq LLM"""
        api_key = get_config_value("groq.api_key")
        model = get_config_value("groq.model", "llama3-70b-8192")
        
        logger.debug(f"Initializing MCPStrategyAgent with model: {model}")
        self.llm = ChatGroq(
            temperature=0.3,
            model=model,
            api_key=api_key
        )
        self.prompt = ChatPromptTemplate.from_template("""
        **Market Context Analysis**
        BTC Dominance: {btc_dominance}%
        Market Regime: {market_regime}
        Active Sectors: {sectors}
        Portfolio Value: ${portfolio_value:,.2f}
        Risk Tolerance: {risk_profile}
        
        **Recent Performance**
        Last 5 Trades: {recent_trades}
        24h Portfolio Change: {portfolio_change}%
        
        **Generate Trading Strategy**
        1. Asset allocation based on regime:
        2. Sector rotation opportunities:
        3. Risk management parameters:
        4. Key market indicators to monitor:
        
        Respond in JSON format with the following structure:
        ```json
        {
            "action": "BUY|SELL|HOLD",
            "confidence": 0.0-1.0,
            "position_size": 0-100,
            "target_assets": ["BTC", "ETH", ...],
            "sector_focus": ["DeFi", "AI", ...],
            "risk_parameters": {
                "stop_loss": 0.0-100.0,
                "take_profit": 0.0-100.0
            },
            "reasoning": "Detailed explanation"
        }
        ```
        """)
        
    def generate_strategy(self, context: MarketContext) -> Dict[str, Any]:
        """Generate a trading strategy based on market context"""
        logger.info(f"Generating strategy for regime: {context.market_regime}")
        
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "btc_dominance": context.btc_dominance,
                "market_regime": context.market_regime,
                "sectors": ", ".join(context.sectors),
                "portfolio_value": context.portfolio_value,
                "risk_profile": context.risk_profile,
                "recent_trades": context.recent_trades,
                "portfolio_change": context.portfolio_change
            })
            
            # Extract JSON from response
            content = response.content
            
            # Clean potential markdown formatting
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            import json
            strategy = json.loads(content.strip())
            
            logger.info(f"Generated strategy with action: {strategy.get('action')}")
            logger.debug(f"Strategy details: {strategy}")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.1,
                "position_size": 0,
                "target_assets": ["BTC"],
                "sector_focus": [],
                "risk_parameters": {"stop_loss": 5.0, "take_profit": 10.0},
                "reasoning": f"Error in strategy generation: {str(e)}"
            }
