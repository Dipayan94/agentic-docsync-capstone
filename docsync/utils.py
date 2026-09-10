"""
Shared utilities for docsync: file I/O, logging, and error handling.

This module provides common functions used across all docsync modules
to keep code DRY and ensure consistent error handling.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing schema...")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def read_json(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file safely.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed JSON data as dict
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is malformed
    
    Example:
        >>> data = read_json("openapi.json")
        >>> print(data['info']['title'])
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """
    Write data to a JSON file safely, creating directories if needed.
    
    Args:
        file_path: Path to JSON file to write
        data: Data to serialize
        indent: JSON indentation (default 2)
    
    Raises:
        OSError: If write fails
    
    Example:
        >>> write_json("output.json", {"status": "ok"})
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except OSError as e:
        raise OSError(f"Failed to write JSON to {file_path}: {e}")


def read_file(file_path: str) -> str:
    """
    Read a text file safely.
    
    Args:
        file_path: Path to text file
    
    Returns:
        File contents as string
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    try:
        return Path(file_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")


def write_file(file_path: str, content: str) -> None:
    """
    Write text to a file safely, creating directories if needed.
    
    Args:
        file_path: Path to file to write
        content: Text content to write
    
    Raises:
        OSError: If write fails
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    except OSError as e:
        raise OSError(f"Failed to write file {file_path}: {e}")


def ensure_dir(dir_path: str) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        dir_path: Directory path
    
    Returns:
        Path object for the directory
    
    Example:
        >>> output_dir = ensure_dir("docs/api")
        >>> print(output_dir.exists())
        True
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
