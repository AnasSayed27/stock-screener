import requests

# Test stock analysis
r = requests.get("http://127.0.0.1:8000/api/stock/TCS")
d = r.json()
print(f"Status: {r.status_code}")
print(f"Name: {d.get('name', 'N/A')}")
print(f"Sector: {d.get('sector', 'N/A')}")
print(f"Financial Sector: {d.get('is_financial_sector', 'N/A')}")

scorecard = d.get("scorecard", {})
print(f"Quality Score: {scorecard.get('total_score', 'N/A')}/{scorecard.get('max_score', 'N/A')}")

criteria = scorecard.get("criteria", [])
for c in criteria:
    status = "PASS" if c.get("passed") else "FAIL"
    print(f"  [{status}] {c.get('name', '')}: {c.get('value', 'N/A')} (threshold: {c.get('threshold', '')})")

valuation = d.get("valuation", {})
print(f"\nCurrent Price: {valuation.get('current_price', 'N/A')}")
print(f"Graham Number: {valuation.get('graham_number', 'N/A')}")
print(f"Earnings Yield: {valuation.get('earnings_yield', 'N/A')}")
print(f"PEG Ratio: {valuation.get('peg_ratio', 'N/A')}")
print(f"Margin of Safety (Consolidated): {valuation.get('margin_of_safety_pct', 'N/A')}")

dcf = valuation.get("dcf", {})
if dcf:
    assumptions = dcf.get("assumptions", {})
    scenarios = dcf.get("scenarios", {})
    print(f"\nDCF Assumptions:")
    print(f"  Growth: {assumptions.get('growth_rate', 'N/A')}")
    print(f"  Discount: {assumptions.get('discount_rate', 'N/A')}")
    print(f"  Terminal: {assumptions.get('terminal_growth', 'N/A')}")
    print(f"DCF Scenarios:")
    for sc_name, sc_val in scenarios.items():
        if sc_val:
            print(f"  {sc_name.capitalize()}: {sc_val.get('fair_value', 'N/A')} (growth: {sc_val.get('growth_rate', 'N/A')})")

print(f"\nConviction: {d.get('conviction', 'N/A')}")
print(f"Description: {d.get('conviction_description', 'N/A')}")

# Test screening
print("\n--- Testing Screener POST /api/screen ---")
scr = requests.post("http://127.0.0.1:8000/api/screen", json={"tickers": ["TCS", "INFY"]})
print(f"Screener Status: {scr.status_code}")
if scr.status_code == 200:
    for item in scr.json():
        print(f"Ticker: {item['ticker']}, Name: {item['name']}, Quality Score: {item['quality_score']}/{item['max_score']}, MoS: {item['margin_of_safety']}, Conviction: {item['conviction']}")
