import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_api_stocks_list():
    res = client.get("/api/stocks")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0

def test_api_stocks_search_local():
    res = client.get("/api/stocks/search?q=TCS")
    assert res.status_code == 200
    results = res.json()
    assert isinstance(results, list)
    symbols = [r["symbol"] for r in results]
    assert any("TCS" in s for s in symbols)

def test_api_theses_crud(tmp_path, monkeypatch):
    monkeypatch.setattr("thesis.THESES_DIR", str(tmp_path))
    
    # 1. Create thesis
    payload = {
        "ticker": "TEST_TCS",
        "why_interested": "Great competitive advantages",
        "sell_conditions": "If ROIC falls below 10%"
    }
    res = client.post("/api/theses", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "TEST_TCS"
    assert data["date_created"] != ""
    
    # 2. Get single thesis
    res_get = client.get("/api/theses/TEST_TCS")
    assert res_get.status_code == 200
    assert res_get.json()["why_interested"] == "Great competitive advantages"
    
    # 3. List theses
    res_list = client.get("/api/theses")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    
    # 4. Delete thesis
    res_del = client.delete("/api/theses/TEST_TCS")
    assert res_del.status_code == 200
    
    # 5. Verify deleted
    res_get2 = client.get("/api/theses/TEST_TCS")
    assert res_get2.status_code == 404

def test_api_postmortems_crud(tmp_path, monkeypatch):
    monkeypatch.setattr("thesis.POSTMORTEMS_DIR", str(tmp_path))
    
    # 1. Create postmortem
    payload = {
        "ticker": "TEST_INFY",
        "why_bought": "Growth",
        "why_sold": "Overvalued",
        "entry_price": 1200.0,
        "exit_price": 1600.0
    }
    res = client.post("/api/postmortems", json=payload)
    assert res.status_code == 200
    pm = res.json()
    pm_id = pm["id"]
    assert pm_id != ""
    
    # 2. Get single postmortem
    res_get = client.get(f"/api/postmortems/{pm_id}")
    assert res_get.status_code == 200
    assert res_get.json()["exit_price"] == 1600.0
    
    # 3. Update postmortem
    update_payload = {
        "ticker": "TEST_INFY",
        "why_bought": "Growth",
        "why_sold": "Overvalued target reached",
        "entry_price": 1200.0,
        "exit_price": 1700.0
    }
    res_put = client.put(f"/api/postmortems/{pm_id}", json=update_payload)
    assert res_put.status_code == 200
    assert res_put.json()["exit_price"] == 1700.0
    
    # 4. Delete postmortem
    res_del = client.delete(f"/api/postmortems/{pm_id}")
    assert res_del.status_code == 200
    
    # 5. Verify deleted
    res_get2 = client.get(f"/api/postmortems/{pm_id}")
    assert res_get2.status_code == 404
