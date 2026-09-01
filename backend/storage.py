"""
Atomic storage utilities for StockLens.
Guarantees crash-safe, atomic file writes using temp files and atomic rename (os.replace).
"""
import os
import tempfile
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Atomically write data as JSON to filepath.
    Writes to a temporary file in the target directory and atomically replaces the target.
    """
    abs_path = os.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    os.makedirs(directory, exist_ok=True)
    
    # Create temp file in the same directory to guarantee same filesystem for os.replace
    prefix = f".tmp_{os.path.basename(abs_path)}_"
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, abs_path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def safe_read_json(filepath: str) -> Optional[Any]:
    """
    Safely read JSON data from filepath. Returns None if file is missing or corrupted.
    """
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning("Error reading JSON file %s: %s", filepath, exc)
        return None
