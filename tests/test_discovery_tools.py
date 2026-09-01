# -*- coding: utf-8 -*-
"""
Unit and integration tests for DiscoveryLens Multi-Tool Suite and Candidate Ledger.
"""

import pytest
from discovery_tools import (
    tool_resolve_ticker,
    tool_get_stock_financials,
    tool_get_quality_scorecard,
    get_discovery_gemini_tools,
    execute_discovery_tool,
)


def test_tool_resolve_ticker_exact_and_fuzzy():
    # 1. Exact Name / Symbol Matching
    res_tcs = tool_resolve_ticker("Tata Consultancy Services")
    assert res_tcs["found"] is True
    assert res_tcs["ticker"] == "TCS.NS"
    assert res_tcs["exchange"] == "NSE"

    res_sym = tool_resolve_ticker("INFY")
    assert res_sym["found"] is True
    assert res_sym["ticker"] == "INFY.NS"


def test_tool_resolve_ticker_unlisted_and_empty():
    # 2. Unlisted / Private
    res_unlisted = tool_resolve_ticker("NonExistentIndianCompany99999XYZ")
    assert res_unlisted["found"] is False
    assert res_unlisted["ticker"] is None
    assert "unlisted" in res_unlisted["message"].lower()

    # 3. Empty input
    res_empty = tool_resolve_ticker("")
    assert res_empty["found"] is False
    assert res_empty["ticker"] is None


def test_tool_get_stock_financials():
    res = tool_get_stock_financials("TCS.NS")
    assert res["ticker"] == "TCS.NS"
    assert "audited_financials_inr_cr" in res

    fin = res["audited_financials_inr_cr"]
    assert "revenue_history" in fin
    assert "operating_income_history" in fin
    assert "net_income_history" in fin
    assert "operating_margin_history" in fin
    assert "free_cashflow_history" in fin
    assert "total_debt_history" in fin

    assert "key_ratios" in res
    assert "latest_roic_pct" in res["key_ratios"]


def test_tool_get_stock_financials_invalid():
    res_empty = tool_get_stock_financials("")
    assert "error" in res_empty


def test_tool_get_quality_scorecard():
    res = tool_get_quality_scorecard("TCS.NS")
    assert res["ticker"] == "TCS.NS"
    assert "quality_score_pct" in res
    assert res["quality_score_pct"] >= 0 and res["quality_score_pct"] <= 100
    assert "criteria_breakdown" in res
    assert len(res["criteria_breakdown"]) > 0
    assert "valuation" in res
    assert "graham_number" in res["valuation"]
    assert "margin_of_safety_pct" in res["valuation"]


def test_get_discovery_gemini_tools():
    tool_decl = get_discovery_gemini_tools()
    assert tool_decl is not None
    assert len(tool_decl.function_declarations) == 4

    names = {fn.name for fn in tool_decl.function_declarations}
    expected_names = {"search_web", "resolve_ticker", "get_stock_financials", "get_quality_scorecard"}
    assert names == expected_names


def test_execute_discovery_tool_candidate_ledger_tracking():
    ledger = {}

    # 1. Resolve ticker
    res1, log1, urls1 = execute_discovery_tool("resolve_ticker", {"company_name": "Tata Consultancy Services"}, ledger)
    assert "TCS.NS" in ledger
    assert ledger["TCS.NS"]["company_name"] != ""
    assert ledger["TCS.NS"]["exchange"] == "NSE"

    # 2. Get financials
    res2, log2, urls2 = execute_discovery_tool("get_stock_financials", {"ticker": "TCS.NS"}, ledger)
    assert ledger["TCS.NS"]["audited_financials"] is not None
    assert "audited_financials_inr_cr" in ledger["TCS.NS"]["audited_financials"]

    # 3. Get scorecard
    res3, log3, urls3 = execute_discovery_tool("get_quality_scorecard", {"ticker": "TCS.NS"}, ledger)
    assert ledger["TCS.NS"]["quality_scorecard"] is not None
    assert ledger["TCS.NS"]["quality_scorecard"]["quality_score_pct"] > 0


def test_role_key_independence_and_exhaustion():
    import sys
    sys.path.insert(0, './backend')
    from discovery import (
        reset_run_api_keys,
        get_role_key,
        mark_role_key_exhausted,
        is_role_key_exhausted,
        mark_model_exhausted,
        is_model_exhausted,
    )

    # 1. Start fresh run
    reset_run_api_keys()
    assert get_role_key("research") == 1
    assert get_role_key("evaluator") == 1
    assert get_role_key("synthesis") == 1

    # 2. Evaluator hits 429 on Key 1 -> switches to Key 2
    new_eval_key = mark_role_key_exhausted("evaluator", 1, "429 quota exhausted")
    assert new_eval_key == 2
    assert get_role_key("evaluator") == 2
    assert is_role_key_exhausted("evaluator", 1) is True

    # 3. Research is independent and MUST still be on Key 1!
    assert get_role_key("research") == 1
    assert is_role_key_exhausted("research", 1) is False

    # 4. Research hits 429 on Key 1 -> switches to Key 2
    new_research_key = mark_role_key_exhausted("research", 1, "429 quota exhausted")
    assert new_research_key == 2
    assert get_role_key("research") == 2

    # 5. Model exhaustion tracking
    assert is_model_exhausted("gemini-3.7-flash") is False
    mark_model_exhausted("gemini-3.7-flash", "503 high demand")
    assert is_model_exhausted("gemini-3.7-flash") is True

    # 6. Reset for new run clears everything
    reset_run_api_keys()
    assert get_role_key("research") == 1
    assert get_role_key("evaluator") == 1
    assert is_role_key_exhausted("evaluator", 1) is False
    assert is_model_exhausted("gemini-3.7-flash") is False


def test_phase3_and_phase5_prompt_tool_enhancements():
    from discovery_phases import PHASE_3_DEEPDIVE_PROMPT, PHASE_5_SYNTHESIS_PROMPT

    # 1. Phase 3 has tool usage protocol for the 3 tools
    assert "TOOL USAGE PROTOCOL (Phase 3):" in PHASE_3_DEEPDIVE_PROMPT
    assert "resolve_ticker(company_name)" in PHASE_3_DEEPDIVE_PROMPT
    assert "get_stock_financials(ticker)" in PHASE_3_DEEPDIVE_PROMPT
    assert "get_quality_scorecard(ticker)" in PHASE_3_DEEPDIVE_PROMPT
    assert "Use these audited tool results as your PRIMARY evidence" in PHASE_3_DEEPDIVE_PROMPT

    # 2. Phase 5 has audited data priority
    assert "AUDITED DATA PRIORITY" in PHASE_5_SYNTHESIS_PROMPT
    assert "AUDITED CANDIDATE LEDGER" in PHASE_5_SYNTHESIS_PROMPT
    assert "ALWAYS use the audited ledger values" in PHASE_5_SYNTHESIS_PROMPT

