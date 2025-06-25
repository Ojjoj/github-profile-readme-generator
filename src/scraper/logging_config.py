"""
Logging configuration for GitHub Profile README Generator

This module provides centralized logging setup for all components.

Author: Your Name
Date: 2025
"""

import logging
import os
from typing import Optional


def setup_logging(
        logger_name: str = 'github_scraper',
        log_file: str = 'scraper.log',
        log_level: int = logging.INFO,
        console_output: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        logger_name (str): Name of the logger
        log_file (str): Name of the log file
        log_level (int): Logging level
        console_output (bool): Whether to output to console

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    log_file_path = os.path.join(logs_dir, log_file)
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(log_level)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    if console_output:
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = 'github_scraper') -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)