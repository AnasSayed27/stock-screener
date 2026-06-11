"""
Pydantic models for all API request / response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------

class CriterionResult(BaseModel):
    """Result of a single quality-check criterion."""
    name: str
    passed: bool
    value: Optional[float] = None
    threshold: str = ""          # human-readable threshold description
    weight: int = 0


class QualityScore(BaseModel):
    """Aggregate quality score with per-criterion breakdown."""
    score: float
    max_score: float
    percentage: float = 0.0
    criteria: list[CriterionResult] = []


class ScorecardTrends(BaseModel):
    """Trends formatted for frontend charting."""
    years: list[str] = Field(default_factory=list)
    revenue: list[Optional[float]] = Field(default_factory=list)
    net_income: list[Optional[float]] = Field(default_factory=list)
    fcf: list[Optional[float]] = Field(default_factory=list)
    total_debt: list[Optional[float]] = Field(default_factory=list)


class Scorecard(BaseModel):
    """Scorecard object expected by the frontend."""
    ticker: str
    company_name: str = ""
    sector: str = ""
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    total_score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    conviction: str = "Insufficient Data"
    is_financial_sector: bool = False
    criteria: list[CriterionResult] = Field(default_factory=list)
    trends: Optional[ScorecardTrends] = None


# ---------------------------------------------------------------------------
# DCF Valuation structure
# ---------------------------------------------------------------------------

class DCFAssumptions(BaseModel):
    growth_rate: Optional[float] = None
    discount_rate: Optional[float] = None
    terminal_growth: Optional[float] = None


class DCFScenario(BaseModel):
    fair_value: Optional[float] = None
    growth_rate: Optional[float] = None


class DCFScenarios(BaseModel):
    bear: Optional[DCFScenario] = None
    base: Optional[DCFScenario] = None
    bull: Optional[DCFScenario] = None


class DCFValuation(BaseModel):
    assumptions: Optional[DCFAssumptions] = None
    scenarios: Optional[DCFScenarios] = None


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

class ValuationResult(BaseModel):
    """Computed valuation metrics for a stock."""
    current_price: Optional[float] = None
    graham_number: Optional[float] = None
    earnings_yield: Optional[float] = None
    peg_ratio: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    dcf: Optional[DCFValuation] = None


# ---------------------------------------------------------------------------
# Full stock analysis
# ---------------------------------------------------------------------------

class StockAnalysis(BaseModel):
    """Complete analysis bundle returned by /api/stock/{ticker}."""
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    scorecard: Optional[Scorecard] = None
    valuation: Optional[ValuationResult] = None
    conviction: str = "Insufficient Data"
    conviction_description: str = ""
    is_financial_sector: bool = False
    data_years: int = 0
    disclaimer: str = (
        "This analysis is for educational purposes only. "
        "Always do your own research before making investment decisions."
    )


# ---------------------------------------------------------------------------
# Screen result (lightweight)
# ---------------------------------------------------------------------------

class ScreenResult(BaseModel):
    """Lightweight result used in the screener list view."""
    ticker: str
    name: str = ""
    sector: str = ""
    quality_score: float = 0.0
    max_score: float = 0.0
    quality_pct: float = 0.0
    margin_of_safety: Optional[float] = None
    conviction: str = "Insufficient Data"
    is_financial_sector: bool = False


class ScreenRequest(BaseModel):
    """Request body for the /api/screen endpoint."""
    tickers: list[str] = Field(default_factory=list)
    universe: str = "nifty500"  # "nifty50" or "nifty500"


# ---------------------------------------------------------------------------
# Thesis / Postmortem
# ---------------------------------------------------------------------------

class ThesisSnapshot(BaseModel):
    quality_score: Optional[float] = None
    max_score: Optional[float] = None
    conviction: Optional[str] = None
    current_price: Optional[float] = None
    margin_of_safety: Optional[float] = None
    sector: Optional[str] = None
    company_name: Optional[str] = None


class ThesisCreate(BaseModel):
    """Payload to create or update an investment thesis."""
    ticker: str
    why_interested: str = ""
    what_would_make_me_wrong: str = ""
    sell_conditions: str = ""
    governance: dict[str, bool] = Field(default_factory=dict)
    snapshot: Optional[ThesisSnapshot] = None


class ThesisResponse(BaseModel):
    """Stored investment thesis (includes metadata)."""
    ticker: str
    why_interested: str = ""
    what_would_make_me_wrong: str = ""
    sell_conditions: str = ""
    governance: dict[str, bool] = Field(default_factory=dict)
    snapshot: Optional[ThesisSnapshot] = None
    date_created: str = ""


class PostmortemCreate(BaseModel):
    """Payload to create a postmortem."""
    ticker: str
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    why_bought: str = ""
    why_sold: str = ""
    was_thesis_right: str = ""
    key_lessons: str = ""
    mistakes: str = ""


class PostmortemResponse(BaseModel):
    """Stored postmortem (includes metadata)."""
    ticker: str
    entry_date: Optional[str] = None
    entry_price: Optional[float] = None
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    why_bought: str = ""
    why_sold: str = ""
    was_thesis_right: str = ""
    key_lessons: str = ""
    mistakes: str = ""
    date_created: str = ""
