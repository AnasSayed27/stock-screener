"""
Configuration module for the stock screener.

All thresholds, weights, and assumptions are hardcoded here.
No user configuration in MVP — change values in this file to adjust strategy.
"""

import os

# ---------------------------------------------------------------------------
# Quality-criteria weights  (total max = 27, normalized to 0-100)
# ---------------------------------------------------------------------------
WEIGHTS: dict[str, int] = {
    "roic": 4,
    "roe": 3,
    "earnings_consistency": 3,
    "fcf_consistency": 3,
    "debt_to_equity": 2,
    "debt_coverage": 2,
    "current_ratio": 1,
    "operating_margins": 2,
    "share_dilution": 2,
    "fcf_ni_ratio": 2,
    "earnings_yield": 3,
}

# ---------------------------------------------------------------------------
# Default (base) thresholds
# ---------------------------------------------------------------------------
THRESHOLDS: dict[str, float] = {
    "market_cap_min": 4_000_00_00_000,       # ₹4,000 Cr in absolute value
    "roic_min": 0.12,
    "roe_min": 0.15,
    "debt_to_equity_max": 1.0,
    "debt_coverage_max_years": 5,
    "current_ratio_min": 1.5,
    "operating_margin_min": 0.10,
    "fcf_ni_ratio_min": 0.7,
    "fcf_ni_ratio_max": 1.5,
    "earnings_yield_min": 0.06,
}

# ---------------------------------------------------------------------------
# Sector-adjusted threshold overrides
# ---------------------------------------------------------------------------
SECTOR_OVERRIDES: dict[str, dict[str, float]] = {
    "Technology": {"operating_margin_min": 0.15},
    "Consumer Defensive": {"current_ratio_min": 1.0},
    "Consumer Cyclical": {"current_ratio_min": 1.0},
    "Healthcare": {"operating_margin_min": 0.12},
    "Industrials": {"debt_to_equity_max": 1.5, "operating_margin_min": 0.08},
    "Basic Materials": {"debt_to_equity_max": 1.5, "operating_margin_min": 0.08},
    "Utilities": {
        "debt_to_equity_max": 2.0,
        "current_ratio_min": 1.0,
        "operating_margin_min": 0.08,
    },
    "Energy": {
        "debt_to_equity_max": 2.0,
        "current_ratio_min": 1.0,
        "operating_margin_min": 0.08,
    },
}

# ---------------------------------------------------------------------------
# Financial-sector flag
# ---------------------------------------------------------------------------
FINANCIAL_SECTORS: list[str] = ["Financial Services", "Financial"]

# ---------------------------------------------------------------------------
# Conviction-level thresholds
# ---------------------------------------------------------------------------
CONVICTION: dict[str, float] = {
    "quality_high": 70,       # percentage of max quality score
    "quality_low": 40,
    "mos_strong": 0.25,       # 25 % margin of safety
    "mos_positive": 0.0,
}

# ---------------------------------------------------------------------------
# DCF assumptions
# ---------------------------------------------------------------------------
DCF: dict[str, float] = {
    "discount_rate": 0.12,
    "terminal_growth": 0.03,
    "bear_growth": 0.05,
    "base_growth": 0.08,
    "bull_growth": 0.12,
    "projection_years": 10,
}

# ---------------------------------------------------------------------------
# Cache TTL
# ---------------------------------------------------------------------------
CACHE_TTL_HOURS: int = 24

# ---------------------------------------------------------------------------
# Data directories (relative to repo root, one level above backend/)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
THESES_DIR = os.path.join(DATA_DIR, "theses")
POSTMORTEMS_DIR = os.path.join(DATA_DIR, "postmortems")

# ---------------------------------------------------------------------------
# AI Research Module (optional — requires GEMINI_API_KEY in .env)
# ---------------------------------------------------------------------------
AI_ENABLED = bool(os.environ.get("GEMINI_API_KEY_1") or os.environ.get("GEMINI_API_KEY_2") or os.environ.get("GEMINI_API_KEY"))
AI_MODEL = os.environ.get("AI_MODEL", "gemini-3.5-flash-lite")
EVALUATOR_MODEL = os.environ.get("EVALUATOR_MODEL", "gemini-3.7-flash")
AI_TEMP_DIR = os.path.join(DATA_DIR, "ai_temp")
AI_REPORTS_DIR = os.path.join(DATA_DIR, "ai_reports")
DISCOVERY_DIR = os.path.join(DATA_DIR, "discoveries")
SYNTHESIS_DIR = os.path.join(DATA_DIR, "syntheses")
SYNTHESIS_CHATS_DIR = os.path.join(DATA_DIR, "synthesis_chats")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Ensure directories exist at import time
for _d in (CACHE_DIR, THESES_DIR, POSTMORTEMS_DIR, AI_TEMP_DIR, AI_REPORTS_DIR, DISCOVERY_DIR, SYNTHESIS_DIR, SYNTHESIS_CHATS_DIR):
    os.makedirs(_d, exist_ok=True)

