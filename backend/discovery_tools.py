# -*- coding: utf-8 -*-
"""
DiscoveryLens Multi-Tool Suite for Autonomous Research Agent.

Equips the agent with 4 deterministic tools:
1. search_web: Tavily web search for industry, policy, supply chain, and order book checks.
2. resolve_ticker: 3-tier ticker resolution (NSE indices -> Yahoo Search .NS/.BO -> null).
3. get_stock_financials: 4-year audited financial statements (P&L, Balance Sheet, Cash Flows, ROIC).
4. get_quality_scorecard: 11 fundamental criteria scoring (0-100) and Graham/DCF valuations.
"""

from __future__ import annotations

import os
import json
import logging
import urllib.parse
import urllib.request
from typing import Optional, Any, Callable

from google.genai import types

from security_utils import sanitize_ticker
from data_fetcher import (
    get_stock_data,
    get_nifty50_stocks,
    get_nifty500_stocks,
    get_niftymidcap150_stocks,
    get_niftynext50_stocks,
    get_niftysmallcap250_stocks,
    get_fno_stocks,
)
from screener import calculate_quality_score, get_conviction, check_market_cap, get_sector_thresholds
from valuator import calculate_valuation
from config import FINANCIAL_SECTORS
from usage_tracker import increment_tavily

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Tool: search_web (Tavily Web Search)
# ---------------------------------------------------------------------------
def tool_search_web(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    progress_callback: Optional[Callable[[str], None]] = None,
    check_cancellation_fn: Optional[Callable[[], None]] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> tuple[str, list[str]]:
    """
    Search the web using Tavily API with graceful retry support.
    Returns (formatted_summary_string, list_of_urls).
    """
    if check_cancellation_fn:
        check_cancellation_fn()

    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        logger.warning("TAVILY_API_KEY is missing from environment variables.")
        return "Web search is unavailable: TAVILY_API_KEY is not configured.", []

    payload = {
        "api_key": tavily_key,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
    }

    tavily_attempt = 0
    tavily_max_retries = 3

    while True:
        if check_cancellation_fn:
            check_cancellation_fn()
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=12) as res:
                res_data = json.loads(res.read().decode("utf-8"))

            increment_tavily()

            results = res_data.get("results", [])
            if not results:
                return f"No search results found for query: '{query}'", []

            summary_parts = []
            urls = []
            for idx, r in enumerate(results, 1):
                title = r.get("title", "No Title")
                url = r.get("url", "")
                content = r.get("content", "")
                summary_parts.append(f"[{idx}] {title}\nURL: {url}\nContent: {content}\n")
                if url:
                    urls.append(url)

            return "\n".join(summary_parts), urls

        except Exception as e:
            from discovery import DiscoveryCancelledException
            if isinstance(e, DiscoveryCancelledException):
                raise
            tavily_attempt += 1
            if tavily_attempt > tavily_max_retries:
                logger.error("Tavily search failed for query '%s' after %d retries: %s", query, tavily_max_retries, e)
                return f"Web search failed due to error: {str(e)}", []

            wait_secs = 2 * tavily_attempt
            logger.warning(
                "Tavily search failed (Attempt %d/%d) for query '%s': %s. Retrying in %ds...",
                tavily_attempt,
                tavily_max_retries,
                query,
                e,
                wait_secs,
            )
            if progress_callback:
                progress_callback(
                    f"⚠️ Tavily error: {str(e)[:60]}... Retrying in {wait_secs}s (Attempt {tavily_attempt}/{tavily_max_retries})..."
                )
            if sleep_fn:
                sleep_fn(wait_secs)


_CACHED_NSE_UNIVERSE = None

# ---------------------------------------------------------------------------
# 2. Tool: resolve_ticker (3-Tier Resolution: NSE -> Yahoo Search -> Null)
# ---------------------------------------------------------------------------
def tool_resolve_ticker(company_name: str) -> dict:
    """
    Deterministically resolves a company name to its active NSE or BSE ticker symbol.
    
    Returns:
    - found: bool
    - ticker: str | None (e.g. "TCS.NS" or "500112.BO" or None)
    - company_name: str
    - exchange: "NSE" | "BSE" | None
    - confidence: "high" | "medium" | "none"
    """
    global _CACHED_NSE_UNIVERSE

    if not company_name or not company_name.strip():
        return {
            "found": False,
            "ticker": None,
            "company_name": "",
            "exchange": None,
            "confidence": "none",
            "message": "Company name provided was empty.",
        }

    q = company_name.strip()
    q_lower = q.lower()

    # Tier 1: Match against local NSE stock universes
    try:
        if _CACHED_NSE_UNIVERSE is not None:
            all_stocks = _CACHED_NSE_UNIVERSE
        else:
            universe_getters = [
                get_nifty50_stocks,
                get_nifty500_stocks,
                get_niftynext50_stocks,
                get_niftymidcap150_stocks,
                get_niftysmallcap250_stocks,
                get_fno_stocks,
            ]

            seen_symbols = set()
            all_stocks = []
            for getter in universe_getters:
                try:
                    for s in getter():
                        sym = s.get("symbol", "")
                        if sym and sym not in seen_symbols:
                            seen_symbols.add(sym)
                            all_stocks.append(s)
                except Exception:
                    continue
            _CACHED_NSE_UNIVERSE = all_stocks

        # Exact symbol match
        for s in all_stocks:
            sym = s.get("symbol", "").upper()
            clean_q = q.upper().replace(".NS", "").replace(".BO", "")
            if sym == clean_q:
                return {
                    "found": True,
                    "ticker": f"{sym}.NS",
                    "company_name": s.get("name", q),
                    "exchange": "NSE",
                    "confidence": "high",
                    "source": "NSE Index Universe (Exact Symbol)",
                }

        # Exact name match
        for s in all_stocks:
            name = s.get("name", "").lower()
            if name == q_lower:
                return {
                    "found": True,
                    "ticker": f"{s['symbol']}.NS",
                    "company_name": s.get("name", q),
                    "exchange": "NSE",
                    "confidence": "high",
                    "source": "NSE Index Universe (Exact Name)",
                }

        # Substring / word match in NSE Universe
        stopwords = {"ltd", "limited", "industries", "india", "pvt", "corp", "corporation", "enterprises", "company"}
        query_words = [w for w in q_lower.split() if w not in stopwords and len(w) > 2]

        if query_words:
            for s in all_stocks:
                name_lower = s.get("name", "").lower()
                sym_lower = s.get("symbol", "").lower()
                if all(w in name_lower for w in query_words) or (len(query_words) == 1 and query_words[0] in sym_lower):
                    return {
                        "found": True,
                        "ticker": f"{s['symbol']}.NS",
                        "company_name": s.get("name", q),
                        "exchange": "NSE",
                        "confidence": "high",
                        "source": "NSE Index Universe (Matched Name)",
                    }
    except Exception as e:
        logger.warning("Local NSE ticker search encountered error: %s", e)

    # Tier 2: Query Yahoo Finance Search API for Indian Listings (.NS / .BO)
    try:
        quoted_q = urllib.parse.quote(q)
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={quoted_q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as res:
            data = json.loads(res.read().decode("utf-8"))

        quotes = data.get("quotes", [])
        # Prioritize .NS (NSE) first
        for quote in quotes:
            sym = quote.get("symbol", "")
            if sym.endswith(".NS"):
                return {
                    "found": True,
                    "ticker": sym,
                    "company_name": quote.get("longname") or quote.get("shortname") or q,
                    "exchange": "NSE",
                    "confidence": "high",
                    "source": "Yahoo Finance (NSE Listed)",
                }

        # Then .BO (BSE)
        for quote in quotes:
            sym = quote.get("symbol", "")
            if sym.endswith(".BO"):
                return {
                    "found": True,
                    "ticker": sym,
                    "company_name": quote.get("longname") or quote.get("shortname") or q,
                    "exchange": "BSE",
                    "confidence": "high",
                    "source": "Yahoo Finance (BSE Only Listed)",
                }
    except Exception as e:
        logger.warning("Yahoo Finance search failed during ticker resolution: %s", e)

    # Tier 3: Unlisted / Private / Unresolved
    return {
        "found": False,
        "ticker": None,
        "company_name": company_name,
        "exchange": None,
        "confidence": "none",
        "message": f"'{company_name}' is unlisted, private, or could not be found on NSE/BSE.",
    }


# ---------------------------------------------------------------------------
# 3. Tool: get_stock_financials (Audited 4-Year Fundamentals)
# ---------------------------------------------------------------------------
def tool_get_stock_financials(ticker: str) -> dict:
    """
    Fetches 4-year audited financial statements (P&L, Balance Sheet, Cash Flows)
    and key metrics for a given NSE/BSE ticker.
    """
    if not ticker or not ticker.strip():
        return {"error": "No ticker provided."}

    clean_sym = ticker.strip().upper()
    if not clean_sym.endswith(".NS") and not clean_sym.endswith(".BO"):
        clean_sym = f"{clean_sym}.NS"

    try:
        safe_sym = sanitize_ticker(clean_sym)
    except ValueError as e:
        return {"error": f"Invalid ticker format: {str(e)}"}

    raw_data = get_stock_data(safe_sym)
    if not raw_data:
        return {
            "ticker": safe_sym,
            "error": f"Could not retrieve audited financial data for {safe_sym}. It may be recently listed or delisted.",
        }

    info = raw_data.get("info", {})
    income_stmt = raw_data.get("income_stmt", {})
    balance_sheet = raw_data.get("balance_sheet", {})
    cashflow = raw_data.get("cashflow", {})

    # Helper to convert metric history to ₹ Crores
    def _extract_metric_inr_cr(stmt_dict: dict, metric_key: str) -> dict[str, float]:
        out = {}
        for yr, vals in sorted(stmt_dict.items()):
            val = vals.get(metric_key)
            if val is not None and not (isinstance(val, float) and (val != val)):
                out[str(yr)[:4]] = round(float(val) / 1e7, 2)
        return out

    revenue_cr = _extract_metric_inr_cr(income_stmt, "revenue")
    op_income_cr = _extract_metric_inr_cr(income_stmt, "operating_income")
    net_income_cr = _extract_metric_inr_cr(income_stmt, "net_income")

    total_debt_cr = _extract_metric_inr_cr(balance_sheet, "total_debt")
    total_equity_cr = _extract_metric_inr_cr(balance_sheet, "total_equity")
    cash_cr = _extract_metric_inr_cr(balance_sheet, "cash")

    op_cf_cr = _extract_metric_inr_cr(cashflow, "operating_cf")
    fcf_cr = _extract_metric_inr_cr(cashflow, "fcf")

    # Margin history
    margin_history = {}
    for yr in revenue_cr:
        if yr in op_income_cr and revenue_cr[yr] > 0:
            margin_history[yr] = f"{round((op_income_cr[yr] / revenue_cr[yr]) * 100, 2)}%"

    # Compute key ratios
    latest_roic = None
    latest_roe = None
    latest_de = None
    latest_cr = None

    sorted_years = sorted(income_stmt.keys())
    if sorted_years:
        latest_yr = sorted_years[-1]
        ebit = income_stmt[latest_yr].get("ebit") or income_stmt[latest_yr].get("operating_income")
        ni = income_stmt[latest_yr].get("net_income")
        equity = balance_sheet.get(latest_yr, {}).get("total_equity")
        debt = balance_sheet.get(latest_yr, {}).get("total_debt")
        ca = balance_sheet.get(latest_yr, {}).get("current_assets")
        cl = balance_sheet.get(latest_yr, {}).get("current_liabilities")

        if ebit and equity is not None and debt is not None:
            invested_cap = equity + debt
            if invested_cap > 0:
                latest_roic = round((ebit * 0.75 / invested_cap) * 100, 2)
        if ni and equity and equity > 0:
            latest_roe = round((ni / equity) * 100, 2)
        if debt is not None and equity and equity > 0:
            latest_de = round(debt / equity, 2)
        if ca and cl and cl > 0:
            latest_cr = round(ca / cl, 2)

    mcap_cr = round(info.get("marketCap", 0) / 1e7, 2) if info.get("marketCap") else None
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    return {
        "ticker": safe_sym,
        "company_name": info.get("longName") or info.get("shortName") or safe_sym,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "market_cap_inr_cr": mcap_cr,
        "current_price_inr": current_price,
        "audited_financials_inr_cr": {
            "revenue_history": revenue_cr,
            "operating_income_history": op_income_cr,
            "net_income_history": net_income_cr,
            "operating_margin_history": margin_history,
            "operating_cashflow_history": op_cf_cr,
            "free_cashflow_history": fcf_cr,
            "total_debt_history": total_debt_cr,
            "total_equity_history": total_equity_cr,
            "cash_history": cash_cr,
        },
        "key_ratios": {
            "latest_roic_pct": latest_roic,
            "latest_roe_pct": latest_roe,
            "debt_to_equity": latest_de,
            "current_ratio": latest_cr,
            "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
            "pb_ratio": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else None,
        },
    }


# ---------------------------------------------------------------------------
# 4. Tool: get_quality_scorecard (11-Criteria Scorecard & Intrinsic Value)
# ---------------------------------------------------------------------------
def tool_get_quality_scorecard(ticker: str) -> dict:
    """
    Runs the StockLens 11-criteria quality scoring model (0-100) and Graham / DCF
    valuations on a given ticker.
    """
    if not ticker or not ticker.strip():
        return {"error": "No ticker provided."}

    clean_sym = ticker.strip().upper()
    if not clean_sym.endswith(".NS") and not clean_sym.endswith(".BO"):
        clean_sym = f"{clean_sym}.NS"

    try:
        safe_sym = sanitize_ticker(clean_sym)
    except ValueError as e:
        return {"error": f"Invalid ticker format: {str(e)}"}

    raw_data = get_stock_data(safe_sym)
    if not raw_data:
        return {"ticker": safe_sym, "error": f"Could not calculate scorecard for {safe_sym}: missing financial data."}

    info = raw_data.get("info", {})
    sector = info.get("sector", "")
    is_financial = sector in FINANCIAL_SECTORS
    thresholds = get_sector_thresholds(sector)

    scorecard = calculate_quality_score(raw_data)
    valuation = calculate_valuation(raw_data)
    conviction = get_conviction(scorecard.percentage, valuation.margin_of_safety_pct)

    criteria_summary = []
    for c in scorecard.criteria:
        criteria_summary.append({
            "name": c.name,
            "passed": c.passed,
            "value": c.value,
            "threshold": c.threshold,
            "weight": c.weight,
        })

    dcf_bear = None
    dcf_base = None
    dcf_bull = None
    if valuation.dcf and valuation.dcf.scenarios:
        dcf_bear = valuation.dcf.scenarios.bear.fair_value if valuation.dcf.scenarios.bear else None
        dcf_base = valuation.dcf.scenarios.base.fair_value if valuation.dcf.scenarios.base else None
        dcf_bull = valuation.dcf.scenarios.bull.fair_value if valuation.dcf.scenarios.bull else None

    return {
        "ticker": safe_sym,
        "company_name": info.get("longName") or info.get("shortName") or safe_sym,
        "sector": sector,
        "is_financial_sector": is_financial,
        "quality_score_pct": scorecard.percentage,
        "quality_total_points": scorecard.score,
        "quality_max_points": scorecard.max_score,
        "conviction": conviction,
        "passed_gate_market_cap": check_market_cap(raw_data, thresholds).passed,
        "criteria_breakdown": criteria_summary,
        "valuation": {
            "current_price": valuation.current_price,
            "graham_number": valuation.graham_number,
            "earnings_yield_pct": round(valuation.earnings_yield * 100, 2) if valuation.earnings_yield else None,
            "dcf_bear": dcf_bear,
            "dcf_base": dcf_base,
            "dcf_bull": dcf_bull,
            "margin_of_safety_pct": round(valuation.margin_of_safety_pct * 100, 2) if valuation.margin_of_safety_pct is not None else None,
            "is_undervalued": (valuation.margin_of_safety_pct > 0) if valuation.margin_of_safety_pct is not None else False,
        },
    }


# ---------------------------------------------------------------------------
# Gemini Tool Declarations & Multi-Tool Registry
# ---------------------------------------------------------------------------
def get_discovery_gemini_tools() -> types.Tool:
    """
    Returns the comprehensive Gemini Tool object with all 4 agent tools declared.
    """
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search_web",
                description=(
                    "Search the web for current industry news, government policies, value chain relationships, "
                    "order books, concall summaries, and macro trends in India."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="The specific search query to run (e.g. 'Apar Industries power transmission order book 2025')."
                        )
                    },
                    required=["query"]
                )
            ),
            types.FunctionDeclaration(
                name="resolve_ticker",
                description=(
                    "Deterministically find and verify the NSE or BSE stock ticker symbol for an Indian company. "
                    "Returns exact symbol (e.g. 'APARINDS.NS') or null if unlisted/private."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "company_name": types.Schema(
                            type=types.Type.STRING,
                            description="The official or trade name of the company to resolve (e.g. 'Apar Industries' or 'Tata Motors')."
                        )
                    },
                    required=["company_name"]
                )
            ),
            types.FunctionDeclaration(
                name="get_stock_financials",
                description=(
                    "Fetch 4-year audited financial statements (P&L, Balance Sheet, Cash Flow, ROIC, debt-to-equity, "
                    "operating margins, free cash flow) directly from audited records for an NSE/BSE ticker."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticker": types.Schema(
                            type=types.Type.STRING,
                            description="The verified ticker symbol (e.g. 'APARINDS.NS' or 'TCS.NS')."
                        )
                    },
                    required=["ticker"]
                )
            ),
            types.FunctionDeclaration(
                name="get_quality_scorecard",
                description=(
                    "Calculate the StockLens 11-criteria fundamental quality score (0-100) and Graham / DCF intrinsic "
                    "valuations with margin of safety for a ticker."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "ticker": types.Schema(
                            type=types.Type.STRING,
                            description="The verified ticker symbol (e.g. 'APARINDS.NS')."
                        )
                    },
                    required=["ticker"]
                )
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Tool Dispatcher with Candidate Ledger Tracking
# ---------------------------------------------------------------------------
def execute_discovery_tool(
    name: str,
    args: dict,
    candidate_ledger: dict,
    search_depth: str = "basic",
    max_results: int = 5,
    progress_callback: Optional[Callable[[str], None]] = None,
    check_cancellation_fn: Optional[Callable[[], None]] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> tuple[dict | str, str, list[str]]:
    """
    Executes a tool call requested by Gemini, records verified facts into the Candidate Ledger,
    and returns (tool_result, human_log_message, urls_list).
    """
    if name == "search_web":
        query = args.get("query", "")
        log_msg = f"🔍 [Web Search] '{query}'"
        if progress_callback:
            progress_callback(log_msg)

        search_result, urls = tool_search_web(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            progress_callback=progress_callback,
            check_cancellation_fn=check_cancellation_fn,
            sleep_fn=sleep_fn,
        )
        return {"result": search_result}, log_msg, urls

    elif name == "resolve_ticker":
        company_name = args.get("company_name", "")
        log_msg = f"🏷️ [Ticker Resolution] Looking up '{company_name}'..."
        if progress_callback:
            progress_callback(log_msg)

        res = tool_resolve_ticker(company_name)
        ticker = res.get("ticker")

        if ticker:
            result_log = f"🏷️ [Ticker Resolution] Resolved '{company_name}' -> {ticker} ({res.get('exchange')})"
            if ticker not in candidate_ledger:
                candidate_ledger[ticker] = {
                    "company_name": res.get("company_name", company_name),
                    "ticker": ticker,
                    "exchange": res.get("exchange"),
                    "audited_financials": None,
                    "quality_scorecard": None,
                }
        else:
            result_log = f"🏷️ [Ticker Resolution] '{company_name}' is Unlisted / Private"

        if progress_callback:
            progress_callback(result_log)

        return res, result_log, []

    elif name == "get_stock_financials":
        ticker = args.get("ticker", "")
        log_msg = f"📊 [Financial Audit] Fetching audited balance sheets & P&L for {ticker}..."
        if progress_callback:
            progress_callback(log_msg)

        res = tool_get_stock_financials(ticker)
        clean_ticker = res.get("ticker", ticker)

        if "error" not in res:
            if clean_ticker not in candidate_ledger:
                candidate_ledger[clean_ticker] = {
                    "company_name": res.get("company_name", clean_ticker),
                    "ticker": clean_ticker,
                    "audited_financials": None,
                    "quality_scorecard": None,
                }
            candidate_ledger[clean_ticker]["audited_financials"] = res

            ratios = res.get("key_ratios", {})
            roic = ratios.get("latest_roic_pct")
            de = ratios.get("debt_to_equity")
            roic_str = f"ROIC: {roic}%" if roic is not None else ""
            de_str = f"D/E: {de}" if de is not None else ""
            stats_parts = [p for p in (roic_str, de_str) if p]
            stats_str = f" ({', '.join(stats_parts)})" if stats_parts else ""
            result_log = f"📊 [Financial Audit] Audited 4-yr statements verified for {clean_ticker}{stats_str}"
        else:
            result_log = f"⚠️ [Financial Audit] {res.get('error', 'Error fetching financials')}"

        if progress_callback:
            progress_callback(result_log)

        return res, result_log, []

    elif name == "get_quality_scorecard":
        ticker = args.get("ticker", "")
        log_msg = f"🎯 [Quality Scorecard] Running 11-criteria fundamental score & DCF for {ticker}..."
        if progress_callback:
            progress_callback(log_msg)

        res = tool_get_quality_scorecard(ticker)
        clean_ticker = res.get("ticker", ticker)

        if "error" not in res:
            if clean_ticker not in candidate_ledger:
                candidate_ledger[clean_ticker] = {
                    "company_name": res.get("company_name", clean_ticker),
                    "ticker": clean_ticker,
                    "audited_financials": None,
                    "quality_scorecard": None,
                }
            candidate_ledger[clean_ticker]["quality_scorecard"] = res

            score_pct = res.get("quality_score_pct", 0)
            mos = res.get("valuation", {}).get("margin_of_safety_pct")
            mos_str = f", MoS: {mos:+.1f}%" if mos is not None else ""
            result_log = f"🎯 [Quality Scorecard] {clean_ticker} scored {score_pct:.1f}/100{mos_str}"
        else:
            result_log = f"⚠️ [Quality Scorecard] {res.get('error', 'Error running scorecard')}"

        if progress_callback:
            progress_callback(result_log)

        return res, result_log, []

    else:
        return {"error": f"Unknown tool name: {name}"}, f"Unknown tool: {name}", []
