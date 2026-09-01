"""
Screener module — quality checks and scoring.

Each ``check_*`` function evaluates one criterion and returns a
``CriterionResult``.  ``calculate_quality_score`` aggregates them into a
``QualityScore``.  ``get_conviction`` maps quality + margin-of-safety to a
conviction label.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from config import (
    CONVICTION,
    FINANCIAL_SECTORS,
    SECTOR_OVERRIDES,
    THRESHOLDS,
    WEIGHTS,
)
from models import CriterionResult, QualityScore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(val: Any) -> Optional[float]:
    """Coerce *val* to float, returning None on failure."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _years_sorted(stmt: dict) -> list[str]:
    """Return year keys sorted chronologically."""
    return sorted(stmt.keys())


def get_sector_thresholds(sector: Optional[str]) -> dict[str, float]:
    """
    Merge base thresholds with any sector-specific overrides.
    """
    merged = dict(THRESHOLDS)
    if sector and sector in SECTOR_OVERRIDES:
        merged.update(SECTOR_OVERRIDES[sector])
    return merged


# ---------------------------------------------------------------------------
# Gate criterion
# ---------------------------------------------------------------------------

def check_market_cap(data: dict, thresholds: dict) -> CriterionResult:
    """Market-cap gate — stock must pass this to be considered."""
    info = data.get("info", {})
    mcap = _safe(info.get("marketCap"))
    threshold = thresholds["market_cap_min"]
    passed = mcap is not None and mcap >= threshold
    threshold_str = f"≥ ₹{threshold / 1e7:,.0f} Cr"
    return CriterionResult(
        name="Market Cap",
        passed=passed,
        value=round(mcap / 1e7, 2) if mcap else None,  # show in Cr
        threshold=threshold_str,
        weight=0,  # gate, not scored
    )


# ---------------------------------------------------------------------------
# Quality criteria
# ---------------------------------------------------------------------------

def check_roic(data: dict, thresholds: dict) -> CriterionResult:
    """
    ROIC = NOPAT / Invested Capital.
    Invested Capital = Total Assets − Current Liabilities − Cash.
    Averaged over available years.
    """
    income = data.get("income_stmt", {})
    balance = data.get("balance_sheet", {})
    years = sorted(set(income.keys()) & set(balance.keys()))

    roic_values: list[float] = []
    for yr in years:
        ebit = _safe(income[yr].get("ebit") or income[yr].get("operating_income"))
        tax = _safe(income[yr].get("tax_provision"))
        total_assets = _safe(balance[yr].get("total_assets"))
        curr_liab = _safe(balance[yr].get("current_liabilities"))
        cash = _safe(balance[yr].get("cash"))

        if ebit is None or total_assets is None:
            continue

        # NOPAT: approximate tax rate or use 25 % default
        if tax is not None and ebit != 0:
            ni = _safe(income[yr].get("net_income"))
            if ni is not None and ebit != 0:
                tax_rate = max(0.0, min(1.0, tax / ebit)) if ebit > 0 else 0.25
            else:
                tax_rate = 0.25
        else:
            tax_rate = 0.25
        nopat = ebit * (1 - tax_rate)

        invested = total_assets - (curr_liab or 0) - (cash or 0)
        if invested <= 0:
            continue

        roic_values.append(nopat / invested)

    avg_roic = sum(roic_values) / len(roic_values) if roic_values else None
    threshold_val = thresholds.get("roic_min", 0.12)
    passed = avg_roic is not None and avg_roic >= threshold_val

    return CriterionResult(
        name="ROIC",
        passed=passed,
        value=round(avg_roic * 100, 2) if avg_roic is not None else None,
        threshold=f"≥ {threshold_val * 100:.0f}%",
        weight=WEIGHTS["roic"],
    )


def check_roe(data: dict, thresholds: dict) -> CriterionResult:
    """Return on Equity — from info dict or computed from statements."""
    info = data.get("info", {})
    roe = _safe(info.get("returnOnEquity"))

    # Fallback to computing from most recent statements if info is missing
    if roe is None:
        income = data.get("income_stmt", {})
        balance = data.get("balance_sheet", {})
        if income and balance:
            latest_inc = _years_sorted(income)[-1]
            latest_bs = _years_sorted(balance)[-1]
            ni = _safe(income[latest_inc].get("net_income"))
            equity = _safe(balance[latest_bs].get("total_equity"))
            if ni is not None and equity is not None and equity > 0:
                roe = ni / equity

    threshold_val = thresholds.get("roe_min", 0.15)
    passed = roe is not None and roe >= threshold_val

    return CriterionResult(
        name="ROE",
        passed=passed,
        value=round(roe * 100, 2) if roe is not None else None,
        threshold=f"≥ {threshold_val * 100:.0f}%",
        weight=WEIGHTS["roe"],
    )


def check_earnings_consistency(data: dict, thresholds: dict) -> CriterionResult:
    """All available years must show positive net income."""
    income = data.get("income_stmt", {})
    if not income:
        return CriterionResult(
            name="Earnings Consistency",
            passed=False,
            value=None,
            threshold="All years positive NI",
            weight=WEIGHTS["earnings_consistency"],
        )

    years = _years_sorted(income)
    positive_count = 0
    total_count = 0
    for yr in years:
        ni = _safe(income[yr].get("net_income"))
        if ni is not None:
            total_count += 1
            if ni > 0:
                positive_count += 1

    passed = total_count > 0 and positive_count == total_count
    return CriterionResult(
        name="Earnings Consistency",
        passed=passed,
        value=positive_count,
        threshold=f"All {total_count} years positive NI",
        weight=WEIGHTS["earnings_consistency"],
    )


def check_fcf_consistency(data: dict, thresholds: dict) -> CriterionResult:
    """At least 3 of 4 (or 75 % of available) years with positive FCF."""
    cashflow = data.get("cashflow", {})
    if not cashflow:
        return CriterionResult(
            name="FCF Consistency",
            passed=False,
            value=None,
            threshold="≥ 75% years positive FCF",
            weight=WEIGHTS["fcf_consistency"],
        )

    years = _years_sorted(cashflow)
    positive = 0
    total = 0
    for yr in years:
        fcf = _safe(cashflow[yr].get("fcf"))
        if fcf is not None:
            total += 1
            if fcf > 0:
                positive += 1

    required = max(1, int(total * 0.75))
    passed = total > 0 and positive >= required

    return CriterionResult(
        name="FCF Consistency",
        passed=passed,
        value=positive,
        threshold=f"≥ {required}/{total} years positive FCF",
        weight=WEIGHTS["fcf_consistency"],
    )


def check_debt_to_equity(data: dict, thresholds: dict) -> CriterionResult:
    """
    Debt-to-Equity ratio.
    yfinance returns debtToEquity as a percentage (e.g. 50 for 0.5×), so
    we divide by 100. Fallback to balance sheet if missing from info.
    """
    info = data.get("info", {})
    raw = _safe(info.get("debtToEquity"))
    de = raw / 100.0 if raw is not None else None

    # Fallback to computing from balance sheet
    if de is None:
        balance = data.get("balance_sheet", {})
        if balance:
            latest = _years_sorted(balance)[-1]
            debt = _safe(balance[latest].get("total_debt"))
            equity = _safe(balance[latest].get("total_equity"))
            if debt is not None and equity is not None and equity > 0:
                de = debt / equity
            elif debt is not None and debt == 0 and equity is not None and equity > 0:
                de = 0.0

    threshold_val = thresholds.get("debt_to_equity_max", 1.0)
    passed = de is not None and de <= threshold_val

    return CriterionResult(
        name="Debt/Equity",
        passed=passed,
        value=round(de, 2) if de is not None else None,
        threshold=f"≤ {threshold_val:.1f}×",
        weight=WEIGHTS["debt_to_equity"],
    )


def check_debt_coverage(data: dict, thresholds: dict) -> CriterionResult:
    """
    Debt Coverage = Long-term Debt / Average FCF.
    Must be repayable within *debt_coverage_max_years* years.
    """
    info = data.get("info", {})
    cashflow = data.get("cashflow", {})
    balance = data.get("balance_sheet", {})

    # Get long-term debt
    lt_debt: Optional[float] = None
    if balance:
        latest = sorted(balance.keys())[-1]
        lt_debt = _safe(balance[latest].get("long_term_debt") or balance[latest].get("total_debt"))
    if lt_debt is None:
        lt_debt = _safe(info.get("totalDebt"))

    # Average FCF
    fcf_vals = [
        _safe(cashflow[yr].get("fcf"))
        for yr in cashflow
        if _safe(cashflow[yr].get("fcf")) is not None
    ]
    avg_fcf = sum(v for v in fcf_vals if v) / len(fcf_vals) if fcf_vals else None

    if lt_debt is not None and avg_fcf is not None and avg_fcf > 0:
        years_to_repay = lt_debt / avg_fcf
    else:
        years_to_repay = None

    max_years = thresholds.get("debt_coverage_max_years", 5)
    passed = years_to_repay is not None and years_to_repay <= max_years

    # Zero debt is also fine
    if lt_debt is not None and lt_debt <= 0:
        passed = True
        years_to_repay = 0.0

    return CriterionResult(
        name="Debt Coverage",
        passed=passed,
        value=round(years_to_repay, 2) if years_to_repay is not None else None,
        threshold=f"≤ {max_years} years to repay",
        weight=WEIGHTS["debt_coverage"],
    )


def check_current_ratio(data: dict, thresholds: dict) -> CriterionResult:
    """Current Ratio from info dict or computed from balance sheet."""
    info = data.get("info", {})
    cr = _safe(info.get("currentRatio"))

    # Fallback to computing from balance sheet
    if cr is None:
        balance = data.get("balance_sheet", {})
        if balance:
            latest = _years_sorted(balance)[-1]
            ca = _safe(balance[latest].get("current_assets"))
            cl = _safe(balance[latest].get("current_liabilities"))
            if ca is not None and cl is not None and cl > 0:
                cr = ca / cl

    threshold_val = thresholds.get("current_ratio_min", 1.5)
    passed = cr is not None and cr >= threshold_val

    return CriterionResult(
        name="Current Ratio",
        passed=passed,
        value=round(cr, 2) if cr is not None else None,
        threshold=f"≥ {threshold_val:.1f}",
        weight=WEIGHTS["current_ratio"],
    )


def check_operating_margins(data: dict, thresholds: dict) -> CriterionResult:
    """Operating margins from info dict or computed from income statement."""
    info = data.get("info", {})
    om = _safe(info.get("operatingMargins"))

    # Fallback to computing from income statement
    if om is None:
        income = data.get("income_stmt", {})
        if income:
            latest = _years_sorted(income)[-1]
            op_inc = _safe(income[latest].get("operating_income") or income[latest].get("ebit"))
            rev = _safe(income[latest].get("revenue"))
            if op_inc is not None and rev is not None and rev > 0:
                om = op_inc / rev

    threshold_val = thresholds.get("operating_margin_min", 0.10)
    passed = om is not None and om >= threshold_val

    return CriterionResult(
        name="Operating Margins",
        passed=passed,
        value=round(om * 100, 2) if om is not None else None,
        threshold=f"≥ {threshold_val * 100:.0f}%",
        weight=WEIGHTS["operating_margins"],
    )


def check_share_dilution(data: dict, thresholds: dict) -> CriterionResult:
    """
    Check that shares outstanding have NOT increased significantly over
    available years.  We look at balance-sheet reported share counts.
    """
    balance = data.get("balance_sheet", {})
    years = _years_sorted(balance)

    shares: list[float] = []
    for yr in years:
        s = _safe(balance[yr].get("shares_outstanding"))
        if s is not None and s > 0:
            shares.append(s)

    if len(shares) < 2:
        # Can't assess trend — give benefit of doubt
        return CriterionResult(
            name="Share Dilution",
            passed=True,
            value=None,
            threshold="Shares not increasing",
            weight=WEIGHTS["share_dilution"],
        )

    # Check if most-recent is ≤ earliest (allow 2 % tolerance)
    earliest, latest = shares[0], shares[-1]
    dilution_pct = ((latest - earliest) / earliest) * 100 if earliest > 0 else 0
    passed = dilution_pct <= 2.0  # ≤ 2 % growth is acceptable

    return CriterionResult(
        name="Share Dilution",
        passed=passed,
        value=round(dilution_pct, 2),
        threshold="≤ 2% share increase",
        weight=WEIGHTS["share_dilution"],
    )


def check_fcf_ni_ratio(data: dict, thresholds: dict) -> CriterionResult:
    """
    Average FCF / Average Net Income should be between 0.7 and 1.5.
    Both average FCF and average Net Income must be positive (> 0).
    This checks that reported earnings are backed by real cash flow.
    """
    cashflow = data.get("cashflow", {})
    income = data.get("income_stmt", {})

    common_years = sorted(set(cashflow.keys()) & set(income.keys()))
    fcf_vals: list[float] = []
    ni_vals: list[float] = []

    for yr in common_years:
        fcf = _safe(cashflow[yr].get("fcf"))
        ni = _safe(income[yr].get("net_income"))
        if fcf is not None and ni is not None:
            fcf_vals.append(fcf)
            ni_vals.append(ni)

    if not ni_vals or not fcf_vals:
        return CriterionResult(
            name="FCF/NI Ratio",
            passed=False,
            value=None,
            threshold="0.7 – 1.5",
            weight=WEIGHTS["fcf_ni_ratio"],
        )

    avg_fcf = sum(fcf_vals) / len(fcf_vals)
    avg_ni = sum(ni_vals) / len(ni_vals)

    # Loss-making or cash-burning companies must fail this check
    if avg_fcf > 0 and avg_ni > 0:
        ratio = avg_fcf / avg_ni
    else:
        ratio = None

    lo = thresholds.get("fcf_ni_ratio_min", 0.7)
    hi = thresholds.get("fcf_ni_ratio_max", 1.5)
    passed = ratio is not None and lo <= ratio <= hi

    return CriterionResult(
        name="FCF/NI Ratio",
        passed=passed,
        value=round(ratio, 2) if ratio is not None else None,
        threshold=f"{lo} – {hi}",
        weight=WEIGHTS["fcf_ni_ratio"],
    )


def check_earnings_yield(data: dict, thresholds: dict) -> CriterionResult:
    """Earnings Yield = EBIT (or Operating Income) / Enterprise Value."""
    info = data.get("info", {})
    ebit = _safe(info.get("ebitda"))
    ev = _safe(info.get("enterpriseValue"))

    # Fallback to income statement if ebit is missing
    if ebit is None:
        income = data.get("income_stmt", {})
        if income:
            latest = _years_sorted(income)[-1]
            ebit = _safe(income[latest].get("ebit") or income[latest].get("operating_income"))

    # Fallback to approximate EV if EV is missing
    if ev is None:
        mcap = _safe(info.get("marketCap"))
        balance = data.get("balance_sheet", {})
        if mcap is not None and balance:
            latest = _years_sorted(balance)[-1]
            debt = _safe(balance[latest].get("total_debt")) or 0.0
            cash = _safe(balance[latest].get("cash")) or 0.0
            computed_ev = mcap + debt - cash
            if computed_ev > 0:
                ev = computed_ev

    if ebit is not None and ev is not None and ev > 0:
        ey = ebit / ev
    else:
        ey = None

    threshold_val = thresholds.get("earnings_yield_min", 0.06)
    passed = ey is not None and ey >= threshold_val

    return CriterionResult(
        name="Earnings Yield",
        passed=passed,
        value=round(ey * 100, 2) if ey is not None else None,
        threshold=f"≥ {threshold_val * 100:.0f}%",
        weight=WEIGHTS["earnings_yield"],
    )


# ---------------------------------------------------------------------------
# Aggregate quality score
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_roic,
    check_roe,
    check_earnings_consistency,
    check_fcf_consistency,
    check_debt_to_equity,
    check_debt_coverage,
    check_current_ratio,
    check_operating_margins,
    check_share_dilution,
    check_fcf_ni_ratio,
    check_earnings_yield,
]


def calculate_quality_score(data: dict) -> QualityScore:
    """
    Run every quality check and return the aggregate ``QualityScore``.

    The market-cap gate is NOT included in the score — it's a pre-filter.
    """
    sector = (data.get("info") or {}).get("sector")
    thresholds = get_sector_thresholds(sector)

    criteria: list[CriterionResult] = []
    total_score = 0.0
    max_score = 0.0

    for check_fn in ALL_CHECKS:
        try:
            result = check_fn(data, thresholds)
            criteria.append(result)
            max_score += result.weight
            if result.passed:
                total_score += result.weight
        except Exception as exc:
            logger.warning("Check %s failed: %s", check_fn.__name__, exc)
            # Still register the criterion as failed
            criteria.append(CriterionResult(
                name=check_fn.__name__.replace("check_", "").replace("_", " ").title(),
                passed=False,
                weight=WEIGHTS.get(check_fn.__name__.replace("check_", ""), 0),
                threshold="Error",
            ))

    pct = (total_score / max_score * 100) if max_score > 0 else 0.0

    return QualityScore(
        score=total_score,
        max_score=max_score,
        percentage=round(pct, 1),
        criteria=criteria,
    )


# ---------------------------------------------------------------------------
# Conviction
# ---------------------------------------------------------------------------

def get_conviction(quality_pct: float, margin_of_safety: Optional[float]) -> tuple[str, str]:
    """
    Map quality percentage and margin of safety to a conviction label.
    Returns ``(label, description)`` tuple.
    """
    has_mos = margin_of_safety is not None
    mos = margin_of_safety if has_mos else -999

    high_q = quality_pct >= CONVICTION["quality_high"]
    low_q = quality_pct >= CONVICTION["quality_low"]
    strong_mos = mos >= CONVICTION["mos_strong"]
    positive_mos = mos >= CONVICTION["mos_positive"]

    if high_q and strong_mos:
        return (
            "Strong Candidate",
            "Quality business at a bargain. High quality score with significant margin of safety.",
        )
    if high_q and positive_mos:
        return (
            "Candidate",
            "Quality business at a reasonable price. Monitor for better entry point.",
        )
    if high_q:
        if not has_mos:
            return (
                "Watchlist",
                "Great business with high quality score. Valuation data currently unavailable to determine Margin of Safety.",
            )
        return (
            "Watchlist",
            "Great business but appears overvalued. Add to watchlist and wait for price pullback.",
        )
    if low_q and strong_mos:
        return (
            "Needs Work",
            "Cheap but quality is uncertain. Needs deeper due diligence before considering.",
        )
    return (
        "Avoid",
        "Does not meet minimum quality criteria. Insufficient quality score.",
    )
