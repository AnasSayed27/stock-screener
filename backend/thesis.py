"""
Thesis & postmortem persistence — simple JSON-file storage.

Each thesis is saved as ``data/theses/{TICKER}.json``.
Each postmortem is saved as ``data/postmortems/{TICKER}_{timestamp}.json``.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

from config import POSTMORTEMS_DIR, THESES_DIR
from models import (
    PostmortemCreate,
    PostmortemResponse,
    ThesisCreate,
    ThesisResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_ticker(ticker: str) -> str:
    """Sanitise ticker for use in filenames."""
    return ticker.replace(".", "_").replace("/", "_").replace("\\", "_").upper()


# ---------------------------------------------------------------------------
# Thesis CRUD
# ---------------------------------------------------------------------------

def save_thesis(thesis: ThesisCreate) -> ThesisResponse:
    """
    Create or update a thesis.  Returns the persisted ``ThesisResponse``.
    """
    safe = _safe_ticker(thesis.ticker)
    path = os.path.join(THESES_DIR, f"{safe}.json")

    payload = thesis.model_dump()
    payload["date_created"] = datetime.now().isoformat()

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    logger.info("Thesis saved for %s", thesis.ticker)
    return ThesisResponse(**payload)


def get_all_theses() -> list[ThesisResponse]:
    """Read every thesis JSON file and return a list."""
    results: list[ThesisResponse] = []
    if not os.path.isdir(THESES_DIR):
        return results
    for fname in sorted(os.listdir(THESES_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(THESES_DIR, fname), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            results.append(ThesisResponse(**data))
        except Exception as exc:
            logger.warning("Failed to load thesis %s: %s", fname, exc)
    return results


def get_thesis(ticker: str) -> Optional[ThesisResponse]:
    """Load a single thesis by ticker.  Returns None if not found."""
    safe = _safe_ticker(ticker)
    path = os.path.join(THESES_DIR, f"{safe}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return ThesisResponse(**data)
    except Exception as exc:
        logger.warning("Failed to load thesis for %s: %s", ticker, exc)
        return None


def delete_thesis(ticker: str) -> bool:
    """Delete a thesis file.  Returns True if deleted, False if not found."""
    safe = _safe_ticker(ticker)
    path = os.path.join(THESES_DIR, f"{safe}.json")
    if os.path.isfile(path):
        os.remove(path)
        logger.info("Thesis deleted for %s", ticker)
        return True
    return False


# ---------------------------------------------------------------------------
# Postmortem CRUD
# ---------------------------------------------------------------------------

def save_postmortem(postmortem: PostmortemCreate) -> PostmortemResponse:
    """
    Save a new postmortem.  Returns the persisted ``PostmortemResponse``.
    """
    safe = _safe_ticker(postmortem.ticker)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(POSTMORTEMS_DIR, f"{safe}_{ts}.json")

    payload = postmortem.model_dump()
    payload["date_created"] = datetime.now().isoformat()

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    logger.info("Postmortem saved for %s", postmortem.ticker)
    return PostmortemResponse(**payload)


def get_all_postmortems() -> list[PostmortemResponse]:
    """Read every postmortem JSON file and return a list."""
    results: list[PostmortemResponse] = []
    if not os.path.isdir(POSTMORTEMS_DIR):
        return results
    for fname in sorted(os.listdir(POSTMORTEMS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(POSTMORTEMS_DIR, fname), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            results.append(PostmortemResponse(**data))
        except Exception as exc:
            logger.warning("Failed to load postmortem %s: %s", fname, exc)
    return results
