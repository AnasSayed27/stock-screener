"""
Analyzer module — orchestrates data fetching, quality scoring, and valuation
into a single ``StockAnalysis`` result.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from config import FINANCIAL_SECTORS
from data_fetcher import get_stock_data
from models import ScreenResult, StockAnalysis, Scorecard, ScorecardTrends
from screener import calculate_quality_score, check_market_cap, get_conviction, get_sector_thresholds
from valuator import calculate_valuation, margin_of_safety

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trend data extraction
# ---------------------------------------------------------------------------

def get_scorecard_trends(data: dict[str, Any]) -> ScorecardTrends:
    """
    Extract year-by-year revenue, net_income, fcf, total_debt for charting
    formatted as parallel lists for frontend consumption.
    """
    income = data.get("income_stmt", {})
    cashflow = data.get("cashflow", {})
    balance = data.get("balance_sheet", {})

    all_years = sorted(set(list(income.keys()) + list(cashflow.keys()) + list(balance.keys())))

    years = []
    revenue = []
    net_income = []
    fcf = []
    total_debt = []

    for yr in all_years:
        years.append(yr[:4] if len(yr) >= 4 else yr)
        
        rev_val = None
        ni_val = None
        fcf_val = None
        debt_val = None

        if yr in income:
            rev_val = income[yr].get("revenue")
            ni_val = income[yr].get("net_income")
        if yr in cashflow:
            fcf_val = cashflow[yr].get("fcf")
        if yr in balance:
            debt_val = balance[yr].get("total_debt") or balance[yr].get("long_term_debt")

        # Round values for cleaner API payload
        revenue.append(round(rev_val, 2) if rev_val is not None else None)
        net_income.append(round(ni_val, 2) if ni_val is not None else None)
        fcf.append(round(fcf_val, 2) if fcf_val is not None else None)
        total_debt.append(round(debt_val, 2) if debt_val is not None else None)

    return ScorecardTrends(
        years=years,
        revenue=revenue,
        net_income=net_income,
        fcf=fcf,
        total_debt=total_debt,
    )


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

def analyze_stock(ticker: str) -> Optional[StockAnalysis]:
    """
    Perform a complete analysis of *ticker*:

    1. Fetch data (with caching)
    2. Calculate quality score
    3. Calculate valuation
    4. Determine conviction level
    5. Bundle everything into a ``StockAnalysis``

    Returns None if data fetching fails entirely.
    """
    data = get_stock_data(ticker)
    if data is None:
        logger.warning("No data for %s — skipping analysis", ticker)
        return None

    info = data.get("info", {})
    name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector") or ""
    industry = info.get("industry") or ""

    # Financial sector flag
    is_financial = sector in FINANCIAL_SECTORS

    # Quality
    quality = calculate_quality_score(data)

    # Valuation
    valuation = calculate_valuation(data)
    best_mos = valuation.margin_of_safety_pct

    # Conviction
    conviction_label, conviction_desc = get_conviction(quality.percentage, best_mos)

    if is_financial:
        conviction_desc += (
            " ⚠️ Financial-sector stock — standard quality metrics "
            "(D/E, FCF, current ratio) may not be meaningful."
        )

    # Count data years
    income_years = len(data.get("income_stmt", {}))
    cf_years = len(data.get("cashflow", {}))
    data_years = max(income_years, cf_years)

    # Trends
    trends = get_scorecard_trends(data)

    # Scorecard
    scorecard = Scorecard(
        ticker=ticker,
        company_name=name,
        sector=sector,
        current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
        market_cap=info.get("marketCap"),
        total_score=quality.score,
        max_score=quality.max_score,
        percentage=quality.percentage,
        conviction=conviction_label,
        is_financial_sector=is_financial,
        criteria=quality.criteria,
        trends=trends,
    )

    return StockAnalysis(
        ticker=ticker,
        name=name,
        sector=sector,
        industry=industry,
        scorecard=scorecard,
        valuation=valuation,
        conviction=conviction_label,
        conviction_description=conviction_desc,
        is_financial_sector=is_financial,
        data_years=data_years,
    )


# ---------------------------------------------------------------------------
# Lightweight screen result (for the list view)
# ---------------------------------------------------------------------------

def screen_stock(ticker: str) -> Optional[ScreenResult]:
    """
    Analyse a single stock and return a lightweight ``ScreenResult``.

    Returns None if the stock fails to fetch or doesn't pass the market-cap
    gate.
    """
    data = get_stock_data(ticker)
    if data is None:
        return None

    info = data.get("info", {})
    sector = info.get("sector") or ""
    thresholds = get_sector_thresholds(sector)

    # Market-cap gate
    mcap_result = check_market_cap(data, thresholds)
    if not mcap_result.passed:
        logger.debug("%s failed market-cap gate", ticker)
        return None

    # Quality
    quality = calculate_quality_score(data)

    # Valuation (lightweight — just need MoS)
    valuation = calculate_valuation(data)
    best_mos = valuation.margin_of_safety_pct

    # Conviction
    conviction_label, _ = get_conviction(quality.percentage, best_mos)

    is_financial = sector in FINANCIAL_SECTORS

    return ScreenResult(
        ticker=ticker,
        name=info.get("longName") or info.get("shortName") or ticker,
        sector=sector,
        quality_score=quality.score,
        max_score=quality.max_score,
        quality_pct=quality.percentage,
        margin_of_safety=best_mos,
        conviction=conviction_label,
        is_financial_sector=is_financial,
    )
