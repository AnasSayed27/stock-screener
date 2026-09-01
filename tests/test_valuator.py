import pytest
from valuator import (
    graham_number,
    earnings_yield,
    peg_ratio,
    dcf_valuation,
    margin_of_safety,
    calculate_valuation,
)
from screener import get_conviction

def test_graham_number_valid():
    # sqrt(22.5 * 50 * 25) = sqrt(28125) = 167.705
    gn = graham_number(50.0, 25.0)
    assert gn is not None
    assert round(gn, 2) == 167.71

def test_graham_number_negative_or_zero():
    assert graham_number(-10.0, 25.0) is None
    assert graham_number(10.0, -5.0) is None
    assert graham_number(0.0, 25.0) is None
    assert graham_number(None, 25.0) is None

def test_earnings_yield():
    assert earnings_yield(100.0, 1000.0) == 0.10
    assert earnings_yield(100.0, -500.0) is None
    assert earnings_yield(None, 1000.0) is None

def test_dcf_valuation_scenarios():
    dcf = dcf_valuation(
        fcf_per_share=45.0,
        growth_rates={"bear": 0.05, "base": 0.10, "bull": 0.15},
        discount_rate=0.10,
        terminal_growth=0.03,
        years=5
    )
    assert dcf is not None
    assert dcf["bear"] is not None
    assert dcf["base"] is not None
    assert dcf["bull"] is not None
    assert dcf["bear"] < dcf["base"]
    assert dcf["base"] < dcf["bull"]

def test_margin_of_safety():
    # Fair value 100, current price 80 -> MoS = (100 - 80) / 100 = 0.20 (20%)
    mos = margin_of_safety(100.0, 80.0)
    assert mos == 0.20

    # Fair value 100, current price 120 -> MoS = (100 - 120) / 100 = -0.20 (-20%)
    mos_neg = margin_of_safety(100.0, 120.0)
    assert mos_neg == -0.20

def test_conviction_mapping():
    # 1. Strong Candidate: Quality >= 70%, MoS >= 20%
    c, desc = get_conviction(85.0, 0.25)
    assert c == "Strong Candidate"

    # 2. Candidate: Quality >= 70%, MoS >= 0%
    c, desc = get_conviction(75.0, 0.10)
    assert c == "Candidate"

    # 3. Watchlist / Overvalued: Quality >= 70%, MoS < 0%
    c, desc = get_conviction(80.0, -0.15)
    assert c == "Watchlist"
    assert "overvalued" in desc.lower()

    # 4. Needs Work: Quality >= 50% and MoS >= 20%
    c, desc = get_conviction(55.0, 0.25)
    assert c == "Needs Work"

    # 5. Avoid: Low quality (< 50%) or low MoS (< 20%)
    c, desc = get_conviction(40.0, 0.05)
    assert c == "Avoid"

    # 6. Valuation Unavailable: Quality >= 70%, MoS is None
    c, desc = get_conviction(75.0, None)
    assert c == "Watchlist"
    assert "Valuation data currently unavailable" in desc
