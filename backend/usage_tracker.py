# -*- coding: utf-8 -*-
"""
Module to track and persist API call usage counts for Tavily and Gemini.
- Gemini resets daily.
- Tavily resets monthly on the 23rd of the month.
"""

import os
import json
import logging
import threading
from datetime import datetime, date

from config import DATA_DIR

logger = logging.getLogger(__name__)

USAGE_FILE = os.path.join(DATA_DIR, "api_usage.json")
_usage_lock = threading.Lock()


def get_tavily_period_start(d: date) -> date:
    """
    Calculate the start of the current Tavily billing period.
    The period starts on the 23rd of this month if today is >= 23rd,
    otherwise it starts on the 23rd of the previous month.
    """
    if d.day >= 23:
        return date(d.year, d.month, 23)
    else:
        # Handles transition to previous year (Jan -> Dec of prev year)
        if d.month == 1:
            return date(d.year - 1, 12, 23)
        else:
            return date(d.year, d.month - 1, 23)


def _load_raw_usage() -> dict:
    """Helper to load JSON without lock (caller must hold lock)."""
    from storage import safe_read_json
    data = safe_read_json(USAGE_FILE)
    return data if isinstance(data, dict) else {}


def _save_raw_usage(data: dict) -> None:
    """Helper to save JSON without lock (caller must hold lock)."""
    try:
        from storage import atomic_write_json
        atomic_write_json(USAGE_FILE, data)
    except Exception as e:
        logger.error("Failed to save API usage file: %s", e)


def get_current_usage() -> dict:
    """
    Retrieves current usage statistics, checking and performing resets if needed.
    Returns:
        dict: {
            "tavily_count": int,
            "gemini_count": int,
            "last_tavily_period_start": str (YYYY-MM-DD),
            "last_gemini_reset_day": str (YYYY-MM-DD)
        }
    """
    with _usage_lock:
        data = _load_raw_usage()
        today = date.today()

        # 1. Tavily reset checks (resets monthly on the 23rd)
        tavily_period_start = get_tavily_period_start(today)
        last_tavily_period_str = data.get("last_tavily_period_start")
        reset_tavily = False

        if not last_tavily_period_str:
            reset_tavily = True
        else:
            try:
                last_tavily_date = date.fromisoformat(last_tavily_period_str)
                if last_tavily_date < tavily_period_start:
                    reset_tavily = True
            except ValueError:
                reset_tavily = True

        if reset_tavily:
            data["tavily_count"] = 0
            data["last_tavily_period_start"] = tavily_period_start.isoformat()

        # 2. Gemini reset checks (resets daily)
        last_gemini_reset_str = data.get("last_gemini_reset_day")
        reset_gemini = False

        if not last_gemini_reset_str:
            reset_gemini = True
        else:
            try:
                last_gemini_date = date.fromisoformat(last_gemini_reset_str)
                if last_gemini_date < today:
                    reset_gemini = True
            except ValueError:
                reset_gemini = True

        if reset_gemini:
            data["gemini_count"] = 0
            data["last_gemini_reset_day"] = today.isoformat()

        # Fill default values if not present
        if "tavily_count" not in data:
            data["tavily_count"] = 0
        if "gemini_count" not in data:
            data["gemini_count"] = 0

        # Save immediately if we performed a reset or initialized defaults
        if reset_tavily or reset_gemini or len(data) < 4:
            _save_raw_usage(data)

        return data


def increment_tavily() -> int:
    """
    Increment Tavily API call counter. Returns the new count.
    """
    with _usage_lock:
        data = _load_raw_usage()
        today = date.today()

        # Tavily check
        tavily_period_start = get_tavily_period_start(today)
        last_tavily_period_str = data.get("last_tavily_period_start")
        reset_tavily = False
        if not last_tavily_period_str:
            reset_tavily = True
        else:
            try:
                last_tavily_date = date.fromisoformat(last_tavily_period_str)
                if last_tavily_date < tavily_period_start:
                    reset_tavily = True
            except ValueError:
                reset_tavily = True

        if reset_tavily:
            data["tavily_count"] = 0
            data["last_tavily_period_start"] = tavily_period_start.isoformat()

        # Gemini check
        last_gemini_reset_str = data.get("last_gemini_reset_day")
        reset_gemini = False
        if not last_gemini_reset_str:
            reset_gemini = True
        else:
            try:
                last_gemini_date = date.fromisoformat(last_gemini_reset_str)
                if last_gemini_date < today:
                    reset_gemini = True
            except ValueError:
                reset_gemini = True

        if reset_gemini:
            data["gemini_count"] = 0
            data["last_gemini_reset_day"] = today.isoformat()

        # Ensure keys exist
        if "tavily_count" not in data:
            data["tavily_count"] = 0
        if "gemini_count" not in data:
            data["gemini_count"] = 0

        # Increment Tavily
        data["tavily_count"] += 1
        _save_raw_usage(data)
        return data["tavily_count"]


def increment_gemini() -> int:
    """
    Increment Gemini API call counter. Returns the new count.
    """
    with _usage_lock:
        data = _load_raw_usage()
        today = date.today()

        # Tavily check
        tavily_period_start = get_tavily_period_start(today)
        last_tavily_period_str = data.get("last_tavily_period_start")
        reset_tavily = False
        if not last_tavily_period_str:
            reset_tavily = True
        else:
            try:
                last_tavily_date = date.fromisoformat(last_tavily_period_str)
                if last_tavily_date < tavily_period_start:
                    reset_tavily = True
            except ValueError:
                reset_tavily = True

        if reset_tavily:
            data["tavily_count"] = 0
            data["last_tavily_period_start"] = tavily_period_start.isoformat()

        # Gemini check
        last_gemini_reset_str = data.get("last_gemini_reset_day")
        reset_gemini = False
        if not last_gemini_reset_str:
            reset_gemini = True
        else:
            try:
                last_gemini_date = date.fromisoformat(last_gemini_reset_str)
                if last_gemini_date < today:
                    reset_gemini = True
            except ValueError:
                reset_gemini = True

        if reset_gemini:
            data["gemini_count"] = 0
            data["last_gemini_reset_day"] = today.isoformat()

        # Ensure keys exist
        if "tavily_count" not in data:
            data["tavily_count"] = 0
        if "gemini_count" not in data:
            data["gemini_count"] = 0

        # Increment Gemini
        data["gemini_count"] += 1
        _save_raw_usage(data)
        return data["gemini_count"]
