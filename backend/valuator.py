"""
Valuation module — Graham Number, Earnings Yield, PEG, DCF.

Every public function returns None when inputs are invalid or missing,
so callers never need to worry about crashes on bad data.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

from config import DCF as DCF_CONFIG
from models import ValuationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Individual valuation methods
# ---------------------------------------------------------------------------

def graham_number(eps: Optional[float], book_value: Optional[float]) -> Optional[float]:
    """
    Compute the Graham Number: √(22.5 × EPS × BVPS).

    Returns None if either input is None, negative, or zero.
    """
    if eps is None or book_value is None:
        return None
    if eps <= 0 or book_value <= 0:
        return None
    try:
        return math.sqrt(22.5 * eps * book_value)
    except (ValueError, OverflowError):
        return None


def earnings_yield(ebit: Optional[float], enterprise_value: Optional[float]) -> Optional[float]:
    """
    Earnings Yield = EBIT / Enterprise Value.

    Returns None when inputs are invalid.
    """
    if ebit is None or enterprise_value is None:
        return None
    if enterprise_value <= 0:
        return None
    try:
        return ebit / enterprise_value
    except (ZeroDivisionError, OverflowError):
        return None


def peg_ratio(pe: Optional[float], growth_rate: Optional[float]) -> Optional[float]:
    """
    PEG Ratio = PE / (growth_rate × 100).

    *growth_rate* is expected as a decimal (e.g. 0.12 for 12 %).
    Returns None when inputs are invalid.
    """
    if pe is None or growth_rate is None:
        return None
    if growth_rate <= 0 or pe <= 0:
        return None
    try:
        return pe / (growth_rate * 100)
    except (ZeroDivisionError, OverflowError):
        return None


def dcf_valuation(
    fcf_per_share: Optional[float],
    growth_rates: dict[str, float] | None = None,
    discount_rate: float | None = None,
    terminal_growth: float | None = None,
    years: int | None = None,
) -> dict[str, Optional[float]]:
    """
    Multi-scenario DCF valuation (bear / base / bull).

    Returns a dict with keys ``bear``, ``base``, ``bull``, each holding the
    intrinsic value per share, or None if computation fails.
    """
    if fcf_per_share is None or fcf_per_share <= 0:
        return {"bear": None, "base": None, "bull": None}

    discount_rate = discount_rate or DCF_CONFIG["discount_rate"]
    terminal_growth = terminal_growth or DCF_CONFIG["terminal_growth"]
    years = int(years or DCF_CONFIG["projection_years"])

    if growth_rates is None:
        growth_rates = {
            "bear": DCF_CONFIG["bear_growth"],
            "base": DCF_CONFIG["base_growth"],
            "bull": DCF_CONFIG["bull_growth"],
        }

    results: dict[str, Optional[float]] = {}
    for scenario, g in growth_rates.items():
        try:
            pv_sum = 0.0
            projected_fcf = fcf_per_share
            for yr in range(1, years + 1):
                projected_fcf *= (1 + g)
                pv_sum += projected_fcf / ((1 + discount_rate) ** yr)

            # Terminal value (Gordon growth)
            terminal_fcf = projected_fcf * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** years)

            intrinsic = pv_sum + pv_terminal
            results[scenario] = round(intrinsic, 2) if intrinsic > 0 else None
        except (ZeroDivisionError, OverflowError, ValueError) as exc:
            logger.warning("DCF %s scenario failed: %s", scenario, exc)
            results[scenario] = None

    return results


def margin_of_safety(
    intrinsic_value: Optional[float], current_price: Optional[float]
) -> Optional[float]:
    """
    Margin of Safety = (intrinsic − price) / intrinsic.

    Positive means undervalued; negative means overvalued.
    """
    if intrinsic_value is None or current_price is None:
        return None
    if intrinsic_value <= 0:
        return None
    try:
        return (intrinsic_value - current_price) / intrinsic_value
    except (ZeroDivisionError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# Aggregate valuation entry-point
# ---------------------------------------------------------------------------

def calculate_valuation(data: dict[str, Any]) -> ValuationResult:
    """
    Run all valuation methods on the normalised stock *data* dict and return
    a ``ValuationResult`` model.
    """
    info = data.get("info", {})

    eps = info.get("trailingEps") or info.get("eps")
    bv = info.get("bookValue")
    pe = info.get("trailingPE") or info.get("forwardPE")
    ebit_val = info.get("ebitda")  # yfinance often only has ebitda
    ev = info.get("enterpriseValue")
    growth = info.get("earningsGrowth") or info.get("revenueGrowth")
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    shares = info.get("sharesOutstanding")

    # ----- individual metrics -----
    gn = graham_number(eps, bv)
    ey = earnings_yield(ebit_val, ev)
    peg = peg_ratio(pe, growth)

    # FCF per share for DCF
    fcf_ps: Optional[float] = None
    cashflow_years = data.get("cashflow", {})
    if cashflow_years and shares and shares > 0:
        fcf_values = [
            yr.get("fcf") for yr in cashflow_years.values()
            if yr.get("fcf") is not None
        ]
        if fcf_values:
            avg_fcf = sum(fcf_values) / len(fcf_values)
            fcf_ps = avg_fcf / shares

    dcf = dcf_valuation(fcf_ps)

    # ----- margins of safety -----
    mos_graham = margin_of_safety(gn, current)
    mos_dcf_bear = margin_of_safety(dcf.get("bear"), current)

    # ----- Backlog Financing & Working Capital Health Check -----
    # Flags companies executing massive backlogs with excessive debt or stretched working capital
    de_ratio = info.get("debtToEquity")
    if de_ratio is not None and de_ratio > 10.0:
        # yfinance often reports debtToEquity as a percentage (e.g. 150 for 1.5)
        de_ratio = de_ratio / 100.0

    financing_warning = None
    if de_ratio is not None and de_ratio > 1.2:
        financing_warning = f"High Debt-to-Equity ({de_ratio:.2f}x): order execution may require heavy debt service or working capital dilution."

    mos_candidates = [
        v for v in [mos_graham, mos_dcf_bear]
        if v is not None
    ]
    best_mos = min(mos_candidates) if mos_candidates else None

    # Apply financing drag penalty to margin of safety if balance sheet is over-leveraged
    if best_mos is not None and de_ratio is not None and de_ratio > 1.5:
        best_mos = max(-1.0, best_mos - 0.10)  # 10% penalty for over-leveraged backlog risk

    # Let's map DCF
    dcf_val = None
    if dcf.get("bear") is not None or dcf.get("base") is not None or dcf.get("bull") is not None:
        from models import DCFValuation, DCFAssumptions, DCFScenarios, DCFScenario
        dcf_val = DCFValuation(
            assumptions=DCFAssumptions(
                growth_rate=DCF_CONFIG["base_growth"],
                discount_rate=DCF_CONFIG["discount_rate"],
                terminal_growth=DCF_CONFIG["terminal_growth"],
            ),
            scenarios=DCFScenarios(
                bear=DCFScenario(fair_value=dcf.get("bear"), growth_rate=DCF_CONFIG["bear_growth"]),
                base=DCFScenario(fair_value=dcf.get("base"), growth_rate=DCF_CONFIG["base_growth"]),
                bull=DCFScenario(fair_value=dcf.get("bull"), growth_rate=DCF_CONFIG["bull_growth"]),
            )
        )

    return ValuationResult(
        current_price=round(current, 2) if current else None,
        graham_number=round(gn, 2) if gn else None,
        earnings_yield=round(ey, 4) if ey else None,
        peg_ratio=round(peg, 2) if peg else None,
        margin_of_safety_pct=round(best_mos, 4) if best_mos is not None else None,
        dcf=dcf_val,
        debt_to_equity=round(de_ratio, 2) if de_ratio is not None else None,
        financing_drag_warning=financing_warning,
    )
