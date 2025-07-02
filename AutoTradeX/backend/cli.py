#!/usr/bin/env python3
"""
AutoTradeX Command Line Interface
Provides command-line functionality for running and managing AutoTradeX
"""

import os
import sys
import argparse
import logging
import asyncio
from pathlib import Path

from backend.utils.config import load_config
import sys
import os

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="AutoTradeX: Self-Evolving Crypto Trading Ecosystem"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run AutoTradeX system")
    run_parser.add_argument(
        "--port", type=int, default=8000, help="Port for web interface"
    )
    run_parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host for web interface"
    )
    run_parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )
    
    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run backtesting")
    backtest_parser.add_argument(
        "--symbol", type=str, default="bitcoin", help="Symbol to backtest"
    )
    backtest_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to backtest"
    )
    
    # Evolution command
    evolve_parser = subparsers.add_parser("evolve", help="Run evolution cycle")
    evolve_parser.add_argument(
        "--regime", type=str, choices=["BTC_DOMINANT", "ALT_SEASON", "NEUTRAL"],
        help="Market regime to evolve for"
    )
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup environment")
    
    return parser.parse_args()

async def run_system(args):
    """Run the AutoTradeX system"""
    from backend.api.app import start_app
    
    logger.info(f"Starting AutoTradeX on {args.host}:{args.port}")
    await start_app(host=args.host, port=args.port, debug=args.debug)

def run_backtest(args):
    """Run backtesting"""
    from backend.training.backtest import run_backtest
    
    logger.info(f"Running backtest for {args.symbol} over {args.days} days")
    results = run_backtest(symbol=args.symbol, days=args.days)
    logger.info(f"Backtest results: {results}")

def run_evolution(args):
    """Run evolution cycle"""
    from backend.training.evolver import AgentEvolver
    
    logger.info(f"Running evolution cycle for regime: {args.regime}")
    evolver = AgentEvolver()
    new_agent = evolver.evolve_agents(args.regime or "NEUTRAL")
    logger.info(f"Evolution complete. New agent: {new_agent}")

def run_setup():
    """Run setup process"""
    from setup import main as setup_main
    
    logger.info("Running AutoTradeX setup")
    setup_main()

async def main():
    """Main entry point"""
    args = parse_args()
    setup_logging(debug=getattr(args, "debug", False))
    
    try:
        if args.command == "run":
            await run_system(args)
        elif args.command == "backtest":
            run_backtest(args)
        elif args.command == "evolve":
            run_evolution(args)
        elif args.command == "setup":
            run_setup()
        else:
            # Default to running the system
            await run_system(argparse.Namespace(
                host="127.0.0.1", port=8000, debug=False
            ))
    except KeyboardInterrupt:
        logger.info("Shutting down AutoTradeX")
    except Exception as e:
        logger.error(f"Error running AutoTradeX: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
