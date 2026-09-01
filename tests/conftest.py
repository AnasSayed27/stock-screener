import sys
import os
import pytest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

@pytest.fixture
def mock_stock_data():
    """Provides standard mock stock data for screener unit tests."""
    return {
        "ticker": "TEST",
        "name": "Test Technologies Ltd",
        "current_price": 500.0,
        "sector": "Technology",
        "is_financial_sector": False,
        "info": {
            "returnOnEquity": 0.22,
            "debtToEquity": 45.0,
            "currentRatio": 2.1,
            "operatingMargins": 0.18,
            "trailingEps": 50.0,
            "bookValue": 25.0,
            "sharesOutstanding": 1000000,
        },
        "financials": {
            "roic": 17.21,
            "debt_coverage_years": 1.23,
            "positive_ni_years": 4,
            "total_years_checked": 4,
            "positive_fcf_years": 4,
            "total_fcf_years": 4,
            "share_dilution_pct": 0.0,
            "fcf_to_ni_ratio": 1.0,
            "avg_fcf": 100000.0,
            "avg_ni": 100000.0,
            "eps": 50.0,
            "book_value_per_share": 25.0,
            "fcf_per_share": 45.0,
            "five_year_fcf_cagr": 0.12,
            "shares_outstanding": 1000000,
            "total_debt": 4500000,
            "cash_and_equivalents": 10000000,
            "historical_net_income": [100.0, 110.0, 120.0, 130.0],
            "historical_fcf": [90.0, 100.0, 115.0, 125.0],
        }
    }
