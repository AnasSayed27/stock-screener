import pytest
import os
import time
from security_utils import safe_join, sanitize_ticker, validate_uuid
from storage import atomic_write_json, safe_read_json
from models import ThesisCreate, PostmortemCreate
from thesis import (
    save_thesis,
    get_thesis,
    delete_thesis,
    get_all_theses,
    save_postmortem,
    get_postmortem,
    update_postmortem,
    delete_postmortem,
    THESES_DIR,
    POSTMORTEMS_DIR,
)

def test_sanitize_ticker():
    assert sanitize_ticker("tcs") == "TCS"
    assert sanitize_ticker("RELIANCE.NS") == "RELIANCE.NS"
    with pytest.raises(ValueError):
        sanitize_ticker("../secret")
    with pytest.raises(ValueError):
        sanitize_ticker("")

def test_validate_uuid():
    valid = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_uuid(valid) == valid
    with pytest.raises(ValueError):
        validate_uuid("../etc/passwd")

def test_safe_join(tmp_path):
    base = str(tmp_path)
    joined = safe_join(base, "sub", "file.json")
    assert joined.startswith(base)
    with pytest.raises(ValueError):
        safe_join(base, "../evil.json")

def test_atomic_storage(tmp_path):
    target = str(tmp_path / "test.json")
    data = {"hello": "world", "num": 42}
    atomic_write_json(target, data)
    
    assert safe_read_json(target) == data
    
    # Check no temp files left
    files = os.listdir(str(tmp_path))
    assert files == ["test.json"]

def test_thesis_date_preservation(tmp_path, monkeypatch):
    # Route storage to tmp_path
    monkeypatch.setattr("thesis.THESES_DIR", str(tmp_path))
    
    t1 = save_thesis(ThesisCreate(ticker="TEST_TCS", why_interested="Initial"))
    c1 = t1.date_created
    assert c1 != ""
    
    time.sleep(0.01)
    t2 = save_thesis(ThesisCreate(ticker="TEST_TCS", why_interested="Updated"))
    assert t2.date_created == c1
    assert t2.date_updated != ""
    assert t2.why_interested == "Updated"

def test_postmortem_crud(tmp_path, monkeypatch):
    monkeypatch.setattr("thesis.POSTMORTEMS_DIR", str(tmp_path))
    
    pm = save_postmortem(PostmortemCreate(
        ticker="TEST_INFY",
        why_bought="Growth",
        why_sold="Hit target",
        entry_price=100.0,
        exit_price=150.0
    ))
    pm_id = pm.id
    assert pm_id != ""
    
    fetched = get_postmortem(pm_id)
    assert fetched is not None
    assert fetched.exit_price == 150.0
    
    updated = update_postmortem(pm_id, PostmortemCreate(
        ticker="TEST_INFY",
        why_bought="Growth",
        why_sold="Hit target",
        entry_price=100.0,
        exit_price=160.0
    ))
    assert updated.exit_price == 160.0
    assert updated.id == pm_id
    
    assert delete_postmortem(pm_id) is True
    assert get_postmortem(pm_id) is None
