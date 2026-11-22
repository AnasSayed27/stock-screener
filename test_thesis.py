import requests

# Test thesis creation
payload = {
    "ticker": "TCS",
    "why_interested": "Market leader in IT services with exceptionally high ROIC, cash conversion and growth.",
    "what_would_make_me_wrong": "Massive decrease in corporate IT spending, loss of key clients.",
    "sell_conditions": "Valuation becomes extremely high (PE > 50) or ROIC drops below 20%.",
    "governance": {
        "promoter_holding": True,
        "pledge_free": True,
        "auditor_clean": True,
        "no_related_party": True,
        "mgmt_compensation": True,
        "consistent_dividend": True,
        "transparent_comms": True,
        "no_legal_issues": True
    },
    "snapshot": {
        "quality_score": 27.0,
        "max_score": 27.0,
        "conviction": "Strong Candidate",
        "current_price": 3800.0,
        "margin_of_safety": 0.1,
        "sector": "Technology",
        "company_name": "Tata Consultancy Services Limited"
    }
}

print("--- Testing Thesis POST /api/theses ---")
r = requests.post("http://127.0.0.1:8000/api/theses", json=payload)
print(f"POST Status: {r.status_code}")
if r.status_code == 200:
    print("Thesis saved successfully!")

print("\n--- Testing Thesis GET /api/theses ---")
r_get = requests.get("http://127.0.0.1:8000/api/theses")
print(f"GET Status: {r_get.status_code}")
if r_get.status_code == 200:
    theses = r_get.json()
    print(f"Number of saved theses: {len(theses)}")
    if theses:
        first = theses[0]
        print(f"First saved thesis ticker: {first.get('ticker')}")
        print(f"what_would_make_me_wrong: {first.get('what_would_make_me_wrong')}")
        print(f"governance dict: {first.get('governance')}")
        print(f"snapshot dict: {first.get('snapshot')}")

# Test postmortem creation
pm_payload = {
    "ticker": "TCS",
    "entry_date": "2026-01-01",
    "exit_date": "2026-06-01",
    "entry_price": 3200.0,
    "exit_price": 3800.0,
    "why_bought": "Identified as a quality business with positive MoS.",
    "why_sold": "Target price reached, rebalancing portfolio.",
    "was_thesis_right": "Yes, earnings grew as projected and ROIC remained strong.",
    "key_lessons": "Discipline pays off.",
    "mistakes": "Could have held longer as trends were positive."
}

print("\n--- Testing Postmortem POST /api/postmortems ---")
pm_r = requests.post("http://127.0.0.1:8000/api/postmortems", json=pm_payload)
print(f"POST Status: {pm_r.status_code}")
if pm_r.status_code == 200:
    print("Postmortem saved successfully!")

print("\n--- Testing Postmortem GET /api/postmortems ---")
pm_get = requests.get("http://127.0.0.1:8000/api/postmortems")
print(f"GET Status: {pm_get.status_code}")
if pm_get.status_code == 200:
    pms = pm_get.json()
    print(f"Number of postmortems: {len(pms)}")
    if pms:
        print(f"First postmortem ticker: {pms[0].get('ticker')}")
        print(f"was_thesis_right: {pms[0].get('was_thesis_right')}")

# Clean up thesis
print("\n--- Testing Thesis DELETE /api/theses/TCS ---")
del_r = requests.delete("http://127.0.0.1:8000/api/theses/TCS")
print(f"DELETE Status: {del_r.status_code}")
