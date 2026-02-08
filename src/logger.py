"""Logging configuration for Olympus Transcriber."""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import config from config package
# Using normal import now that config is properly structured
from src.config import config


def setup_logger(
    name: str = "olympus_transcriber",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """Setup centralized logging with file and console handlers.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    config.ensure_directories()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all, handlers will filter
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if log_to_file:
        try:
            file_handler = logging.FileHandler(config.LOG_FILE)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logger()






