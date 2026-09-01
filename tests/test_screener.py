import pytest
from config import THRESHOLDS
from screener import (
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
    calculate_quality_score,
)

@pytest.fixture
def base_data():
    return {
        "info": {
            "returnOnEquity": 0.22,
            "debtToEquity": 45.0,
            "currentRatio": 2.1,
            "operatingMargins": 0.18,
            "trailingEps": 50.0,
            "bookValue": 25.0,
            "sharesOutstanding": 1000000,
            "ebitda": 180000.0,
            "enterpriseValue": 1000000.0,
        },
        "income_stmt": {
            "2020": {"ebit": 100.0, "tax_provision": 25.0, "net_income": 75.0, "operating_income": 100.0},
            "2021": {"ebit": 110.0, "tax_provision": 27.5, "net_income": 82.5, "operating_income": 110.0},
            "2022": {"ebit": 120.0, "tax_provision": 30.0, "net_income": 90.0, "operating_income": 120.0},
            "2023": {"ebit": 130.0, "tax_provision": 32.5, "net_income": 97.5, "operating_income": 130.0},
        },
        "balance_sheet": {
            "2020": {"total_assets": 500.0, "current_liabilities": 100.0, "cash": 50.0, "total_equity": 300.0, "total_debt": 50.0},
            "2021": {"total_assets": 550.0, "current_liabilities": 110.0, "cash": 55.0, "total_equity": 330.0, "total_debt": 55.0},
            "2022": {"total_assets": 600.0, "current_liabilities": 120.0, "cash": 60.0, "total_equity": 360.0, "total_debt": 60.0},
            "2023": {"total_assets": 650.0, "current_liabilities": 130.0, "cash": 65.0, "total_equity": 400.0, "total_debt": 65.0, "common_stock": 100.0},
        },
        "cashflow": {
            "2020": {"fcf": 70.0},
            "2021": {"fcf": 80.0},
            "2022": {"fcf": 90.0},
            "2023": {"fcf": 100.0},
        }
    }

def test_check_roic(base_data):
    res = check_roic(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value is not None

def test_check_roe(base_data):
    res = check_roe(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 22.0

def test_check_earnings_consistency(base_data):
    res = check_earnings_consistency(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 4.0

def test_check_fcf_consistency(base_data):
    res = check_fcf_consistency(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 4.0

def test_check_debt_to_equity(base_data):
    res = check_debt_to_equity(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 0.45

def test_check_debt_coverage(base_data):
    res = check_debt_coverage(base_data, THRESHOLDS)
    assert res.passed is True

def test_check_current_ratio(base_data):
    res = check_current_ratio(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 2.1

def test_check_operating_margins(base_data):
    res = check_operating_margins(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 18.0

def test_check_share_dilution(base_data):
    res = check_share_dilution(base_data, THRESHOLDS)
    assert res.passed is True

def test_check_fcf_ni_ratio_positive(base_data):
    res = check_fcf_ni_ratio(base_data, THRESHOLDS)
    assert res.passed is True

def test_check_fcf_ni_ratio_rejects_negative():
    # Loss-making negative FCF/NI division artifact must fail
    bad_data = {
        "cashflow": {"2020": {"fcf": -100.0}},
        "income_stmt": {"2020": {"net_income": -100.0}}
    }
    res = check_fcf_ni_ratio(bad_data, THRESHOLDS)
    assert res.passed is False

def test_check_earnings_yield(base_data):
    res = check_earnings_yield(base_data, THRESHOLDS)
    assert res.passed is True
    assert res.value == 18.0

def test_calculate_quality_score_full(base_data):
    score = calculate_quality_score(base_data)
    assert score.score > 20.0
    assert score.max_score == 27.0
    assert score.percentage > 75.0
