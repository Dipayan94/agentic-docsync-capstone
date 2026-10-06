"""
Shared utilities for docsync: file I/O, logging, and error handling.

This module provides common functions used across all docsync modules
to keep code DRY and ensure consistent error handling.
"""

import json
import logging
import os
import tempfile
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
    return logging.getLogger(name)


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
    return safe_read_file(file_path)


def safe_read_file(file_path: str) -> str:
    """Read UTF-8 text without newline translation and name access errors."""
    try:
        with Path(file_path).open("r", encoding="utf-8", newline="") as source:
            return source.read()
    except UnicodeDecodeError as error:
        raise ValueError(f"File is not valid UTF-8 text: {file_path}: {error}") from error
    except OSError as error:
        raise OSError(f"Cannot read {file_path}: {error}") from error


def write_file(file_path: str, content: str) -> None:
    """
    Write text to a file safely, creating directories if needed.
    
    Args:
        file_path: Path to file to write
        content: Text content to write
    
    Raises:
        OSError: If write fails
    """
    safe_write_file(file_path, content)


def safe_write_file(file_path: str, content: str) -> None:
    """Atomically replace a UTF-8 text file using a temporary sibling file."""
    destination = Path(file_path)
    temporary_path: Optional[str] = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=str(destination.parent),
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, str(destination))
        temporary_path = None
    except OSError as error:
        raise OSError(f"Cannot atomically write {file_path}: {error}") from error
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            except OSError:
                logging.getLogger(__name__).warning("Could not remove temporary file %s", temporary_path)


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


def format_output(title: str, content: str) -> str:
    """Format a titled diagnostic without writing it to report output."""
    return f"{title}\n{'=' * len(title)}\n{content}"


def human_readable_size(byte_size: int) -> str:
    """Format a nonnegative byte count using binary size units."""
    if byte_size < 0:
        raise ValueError("byte_size must be nonnegative")
    size = float(byte_size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"
