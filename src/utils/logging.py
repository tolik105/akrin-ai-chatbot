"""
Logging configuration for AKRIN AI Chatbot
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
import os


def setup_logging(name: str = None) -> logging.Logger:
    """
    Setup structured logging with JSON format
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or "akrin_chatbot")
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create file handler
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler(
        f"logs/akrin_chatbot_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.INFO)
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Development formatter (human-readable)
    dev_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Use JSON format in production, human-readable in development
    if os.getenv("APP_ENV") == "production":
        console_handler.setFormatter(json_formatter)
        file_handler.setFormatter(json_formatter)
    else:
        console_handler.setFormatter(dev_formatter)
        file_handler.setFormatter(json_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Create module-specific loggers
chat_logger = setup_logging("akrin.chat")
knowledge_logger = setup_logging("akrin.knowledge")
integration_logger = setup_logging("akrin.integration")
security_logger = setup_logging("akrin.security")