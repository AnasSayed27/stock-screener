"""
Security Utilities for StockLens.
Provides canonical path traversal prevention, ticker sanitization, and UUID validation.
"""
import os
import re
import uuid
from typing import Optional


def sanitize_ticker(ticker: str) -> str:
    """
    Sanitizes a stock ticker to ensure it only contains valid characters
    and does not contain path traversal sequences (like '..').
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string.")
    
    raw = ticker.strip()
    if "/" in raw or "\\" in raw or ".." in raw or raw.startswith("."):
        raise ValueError(f"Invalid ticker format: {ticker}")

    cleaned = re.sub(r"[^A-Z0-9_.-]", "", raw.upper())
    if not cleaned:
        raise ValueError(f"Invalid ticker format: {ticker}")
        
    return cleaned


def validate_uuid(id_str: str) -> str:
    """
    Validates that a string is a valid UUID to prevent path traversal
    in ID-based filesystem lookups.
    """
    if not id_str or not isinstance(id_str, str):
        raise ValueError("ID must be a non-empty string.")
        
    try:
        parsed = uuid.UUID(id_str.strip())
        return str(parsed)
    except Exception:
        raise ValueError(f"Invalid identifier format (UUID required): {id_str}")


def safe_join(base_dir: str, *paths: str) -> str:
    """
    Safely joins paths ensuring the resulting absolute path is strictly
    contained within base_dir. Prevents directory traversal attacks.
    """
    base_abs = os.path.abspath(base_dir)
    
    for p in paths:
        if not p or not isinstance(p, str):
            continue
        if ".." in p:
            raise ValueError(f"Path traversal sequence detected in '{p}'")
        if os.path.isabs(p) or p.startswith(("/", "\\")):
            raise ValueError(f"Absolute path not permitted as subpath: '{p}'")
            
    target_abs = os.path.abspath(os.path.join(base_abs, *paths))
    
    # Ensure target path starts with base directory path
    if not (target_abs == base_abs or target_abs.startswith(base_abs + os.path.sep)):
        raise ValueError(f"Path traversal detected: '{target_abs}' is outside '{base_abs}'")
        
    return target_abs


def is_safe_filename(filename: str) -> bool:
    """
    Verifies that a filename is safe, contains no directory separators,
    and is not empty.
    """
    if not filename or not isinstance(filename, str):
        return False
    basename = os.path.basename(filename)
    return basename == filename and ".." not in filename and not filename.startswith(".")
