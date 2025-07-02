"""
Logging configuration for AutoTradeX
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def get_log_dir() -> Path:
    """Get the directory for log files"""
    log_dir = Path.home() / ".autotradex" / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    return log_dir

def setup_logging(debug: bool = False) -> None:
    """Configure logging for AutoTradeX"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format for better parsing)
    log_file = get_log_dir() / f"autotradex_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(funcName)s %(lineno)d"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)  # Always log at INFO level to file
    root_logger.addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup information
    logging.info(f"AutoTradeX logging initialized (level: {'DEBUG' if debug else 'INFO'})")
    logging.debug(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)
