"""
Thesis & postmortem persistence — atomic JSON-file storage.

Each thesis is saved as ``data/theses/{TICKER}.json``.
Each postmortem is saved as ``data/postmortems/{ID}.json``.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from config import POSTMORTEMS_DIR, THESES_DIR
from models import (
    PostmortemCreate,
    PostmortemResponse,
    ThesisCreate,
    ThesisResponse,
)
from security_utils import safe_join, sanitize_ticker, validate_uuid
from storage import atomic_write_json, safe_read_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thesis CRUD
# ---------------------------------------------------------------------------

def save_thesis(thesis: ThesisCreate) -> ThesisResponse:
    """
    Create or update a thesis. Preserves original date_created if updating.
    Returns the persisted ``ThesisResponse``.
    """
    safe = sanitize_ticker(thesis.ticker)
    path = safe_join(THESES_DIR, f"{safe}.json")

    existing_created_at = None
    if os.path.isfile(path):
        existing_data = safe_read_json(path)
        if existing_data and isinstance(existing_data, dict):
            existing_created_at = existing_data.get("date_created") or existing_data.get("created_at")

    payload = thesis.model_dump()
    now_iso = datetime.now().isoformat()
    payload["date_created"] = existing_created_at or now_iso
    payload["date_updated"] = now_iso

    atomic_write_json(path, payload)
    logger.info("Thesis atomically saved for %s", thesis.ticker)
    return ThesisResponse(**payload)


def get_all_theses() -> list[ThesisResponse]:
    """Read every thesis JSON file and return a list, isolating any corrupted files."""
    results: list[ThesisResponse] = []
    if not os.path.isdir(THESES_DIR):
        return results
    for fname in sorted(os.listdir(THESES_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            path = safe_join(THESES_DIR, fname)
            data = safe_read_json(path)
            if data and isinstance(data, dict):
                results.append(ThesisResponse(**data))
        except Exception as exc:
            logger.warning("Failed to load thesis %s (skipping): %s", fname, exc)
    return results


def get_thesis(ticker: str) -> Optional[ThesisResponse]:
    """Load a single thesis by ticker. Returns None if not found."""
    try:
        safe = sanitize_ticker(ticker)
        path = safe_join(THESES_DIR, f"{safe}.json")
    except ValueError:
        return None

    if not os.path.isfile(path):
        return None
    try:
        data = safe_read_json(path)
        if data and isinstance(data, dict):
            return ThesisResponse(**data)
        return None
    except Exception as exc:
        logger.warning("Failed to load thesis for %s: %s", ticker, exc)
        return None


def delete_thesis(ticker: str) -> bool:
    """Delete a thesis file. Returns True if deleted, False if not found."""
    try:
        safe = sanitize_ticker(ticker)
        path = safe_join(THESES_DIR, f"{safe}.json")
    except ValueError:
        return False

    if os.path.isfile(path):
        try:
            os.remove(path)
            logger.info("Thesis deleted for %s", ticker)
            return True
        except Exception as exc:
            logger.error("Failed to delete thesis for %s: %s", ticker, exc)
            return False
    return False


# ---------------------------------------------------------------------------
# Postmortem CRUD
# ---------------------------------------------------------------------------

def save_postmortem(postmortem: PostmortemCreate) -> PostmortemResponse:
    """
    Save a new postmortem with a unique UUID. Returns the persisted ``PostmortemResponse``.
    """
    postmortem_id = postmortem.id or str(uuid.uuid4())
    safe_id = validate_uuid(postmortem_id)
    path = safe_join(POSTMORTEMS_DIR, f"{safe_id}.json")

    existing_created_at = None
    if os.path.isfile(path):
        existing_data = safe_read_json(path)
        if existing_data and isinstance(existing_data, dict):
            existing_created_at = existing_data.get("date_created") or existing_data.get("created_at")

    now_iso = datetime.now().isoformat()
    payload = postmortem.model_dump()
    payload["id"] = safe_id
    payload["date_created"] = existing_created_at or now_iso
    payload["date_updated"] = now_iso

    atomic_write_json(path, payload)
    logger.info("Postmortem saved with ID %s for %s", safe_id, postmortem.ticker)
    return PostmortemResponse(**payload)


def get_all_postmortems() -> list[PostmortemResponse]:
    """Read every postmortem JSON file and return a list, isolating any corrupted files."""
    results: list[PostmortemResponse] = []
    if not os.path.isdir(POSTMORTEMS_DIR):
        return results
    for fname in sorted(os.listdir(POSTMORTEMS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            path = safe_join(POSTMORTEMS_DIR, fname)
            data = safe_read_json(path)
            if data and isinstance(data, dict):
                # Ensure ID is populated even for legacy files
                if not data.get("id"):
                    data["id"] = fname.replace(".json", "")
                results.append(PostmortemResponse(**data))
        except Exception as exc:
            logger.warning("Failed to load postmortem %s (skipping): %s", fname, exc)
    return results


def get_postmortem(postmortem_id: str) -> Optional[PostmortemResponse]:
    """Fetch a single postmortem by ID."""
    if not postmortem_id:
        return None
    
    # Try direct UUID file first
    try:
        safe_id = validate_uuid(postmortem_id)
        path = safe_join(POSTMORTEMS_DIR, f"{safe_id}.json")
        if os.path.isfile(path):
            data = safe_read_json(path)
            if data and isinstance(data, dict):
                if not data.get("id"):
                    data["id"] = safe_id
                return PostmortemResponse(**data)
    except ValueError:
        pass

    # Legacy fallback by filename
    path = safe_join(POSTMORTEMS_DIR, f"{os.path.basename(postmortem_id)}.json")
    if os.path.isfile(path):
        data = safe_read_json(path)
        if data and isinstance(data, dict):
            if not data.get("id"):
                data["id"] = postmortem_id
            return PostmortemResponse(**data)
    return None


def update_postmortem(postmortem_id: str, postmortem: PostmortemCreate) -> Optional[PostmortemResponse]:
    """Update an existing postmortem by ID."""
    existing = get_postmortem(postmortem_id)
    if not existing:
        return None
    postmortem.id = existing.id
    return save_postmortem(postmortem)


def delete_postmortem(postmortem_id: str) -> bool:
    """Delete a postmortem file by ID."""
    if not postmortem_id:
        return False
    
    # Try UUID filename
    try:
        safe_id = validate_uuid(postmortem_id)
        path = safe_join(POSTMORTEMS_DIR, f"{safe_id}.json")
        if os.path.isfile(path):
            os.remove(path)
            logger.info("Postmortem %s deleted", safe_id)
            return True
    except ValueError:
        pass

    # Legacy filename fallback
    path = safe_join(POSTMORTEMS_DIR, f"{os.path.basename(postmortem_id)}.json")
    if os.path.isfile(path):
        try:
            os.remove(path)
            logger.info("Legacy postmortem %s deleted", postmortem_id)
            return True
        except Exception as exc:
            logger.error("Failed to delete postmortem %s: %s", postmortem_id, exc)
            return False

    return False
