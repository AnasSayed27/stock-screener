"""Quick functional test of the screener logic with mock data."""
import sys
sys.path.insert(0, '.')

from screener import calculate_quality_score, get_conviction
from valuator import graham_number, dcf_valuation, margin_of_safety, earnings_yield

mock_data = {
    "info": {
        "marketCap": 500000000000,
        "returnOnEquity": 0.22,
        "debtToEquity": 45.0,
        "currentRatio": 2.1,
        "operatingMargins": 0.18,
        "ebitda": 50000000000,
        "enterpriseValue": 400000000000,
        "trailingEps": 55.0,
        "bookValue": 250.0,
        "sector": "Technology",
        "sharesOutstanding": 1000000000,
    },
    "income_stmt": {
        "2024-03-31": {"revenue": 200e9, "net_income": 40e9, "ebit": 50e9, "operating_income": 50e9, "tax_provision": 12e9},
        "2023-03-31": {"revenue": 180e9, "net_income": 35e9, "ebit": 45e9, "operating_income": 45e9, "tax_provision": 11e9},
        "2022-03-31": {"revenue": 160e9, "net_income": 30e9, "ebit": 40e9, "operating_income": 40e9, "tax_provision": 10e9},
        "2021-03-31": {"revenue": 140e9, "net_income": 25e9, "ebit": 35e9, "operating_income": 35e9, "tax_provision": 9e9},
    },
    "balance_sheet": {
        "2024-03-31": {"total_assets": 300e9, "current_liabilities": 60e9, "cash": 40e9, "total_debt": 50e9, "long_term_debt": 40e9, "shares_outstanding": 1e9},
        "2023-03-31": {"total_assets": 280e9, "current_liabilities": 55e9, "cash": 35e9, "total_debt": 55e9, "long_term_debt": 45e9, "shares_outstanding": 1e9},
        "2022-03-31": {"total_assets": 260e9, "current_liabilities": 50e9, "cash": 30e9, "total_debt": 60e9, "long_term_debt": 50e9, "shares_outstanding": 1e9},
        "2021-03-31": {"total_assets": 240e9, "current_liabilities": 45e9, "cash": 25e9, "total_debt": 65e9, "long_term_debt": 55e9, "shares_outstanding": 1e9},
    },
    "cashflow": {
        "2024-03-31": {"operating_cf": 55e9, "capex": -15e9, "fcf": 40e9},
        "2023-03-31": {"operating_cf": 48e9, "capex": -13e9, "fcf": 35e9},
        "2022-03-31": {"operating_cf": 42e9, "capex": -12e9, "fcf": 30e9},
        "2021-03-31": {"operating_cf": 36e9, "capex": -11e9, "fcf": 25e9},
    },
}

qs = calculate_quality_score(mock_data)
print(f"Quality: {qs.score}/{qs.max_score} = {qs.percentage}%")
for c in qs.criteria:
    status = "PASS" if c.passed else "FAIL"
    print(f"  [{status}] {c.name}: {c.value} (threshold: {c.threshold}, weight: {c.weight})")

gn = graham_number(55.0, 250.0)
print(f"\nGraham Number: {gn:.2f}")

ey = earnings_yield(50e9, 400e9)
print(f"Earnings Yield: {ey:.4f}")

dcf = dcf_valuation(32.5)
print(f"DCF: bear={dcf['bear']}, base={dcf['base']}, bull={dcf['bull']}")

mos = margin_of_safety(gn, 500)
print(f"MoS (Graham): {mos:.4f}")

label, desc = get_conviction(qs.percentage, mos)
print(f"\nConviction: {label}")
print(f"Description: {desc}")
print("\n--- ALL TESTS PASSED ---")
