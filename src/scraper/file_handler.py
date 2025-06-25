"""
File handling utilities for GitHub Profile README Generator

This module provides file I/O operations for saving and loading scraped data.

Author: Your Name
Date: 2025
"""

import json
import os
from datetime import datetime
from typing import Any, Dict
from dataclasses import asdict

from .logging_config import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handles file operations for the GitHub scraper."""

    def __init__(self, output_dir: str = None):
        """
        Initialize file handler.

        Args:
            output_dir (str): Directory to save output files. Defaults to 'output'
        """
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        else:
            self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")

    def save_to_json(self, data: Dict[str, Any], username: str) -> str:
        """
        Save scraped data to JSON file.

        Args:
            data (Dict[str, Any]): Complete scraped data
            username (str): GitHub username for filename

        Returns:
            str: Path to saved file

        Raises:
            Exception: If saving fails
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{username}_profile_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            # Convert dataclasses to dictionaries for JSON serialization
            json_data = self._convert_to_json_serializable(data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Data saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save data to JSON: {str(e)}")
            raise

    def load_from_json(self, filepath: str) -> Dict[str, Any]:
        """
        Load scraped data from JSON file.

        Args:
            filepath (str): Path to JSON file

        Returns:
            Dict[str, Any]: Loaded data

        Raises:
            Exception: If loading fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Data loaded from: {filepath}")
            return data

        except Exception as e:
            logger.error(f"Failed to load data from JSON: {str(e)}")
            raise

    def list_saved_profiles(self) -> list:
        """
        List all saved profile files.

        Returns:
            list: List of saved profile filenames
        """
        try:
            files = [f for f in os.listdir(self.output_dir) if f.endswith('_profile_*.json')]
            files.sort(reverse=True)  # Most recent first
            return files
        except Exception as e:
            logger.error(f"Failed to list saved profiles: {str(e)}")
            return []

    def _convert_to_json_serializable(self, data: Any) -> Any:
        """
        Convert dataclasses and other objects to JSON-serializable format.

        Args:
            data (Any): Data to convert

        Returns:
            Any: JSON-serializable data
        """
        if hasattr(data, '__dict__') and hasattr(data, '__dataclass_fields__'):
            # Handle dataclasses
            return asdict(data)
        elif isinstance(data, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_json_serializable(item) for item in data]
        else:
            return data

    def get_output_directory(self) -> str:
        """
        Get the current output directory path.

        Returns:
            str: Output directory path
        """
        return self.output_dir